import os
import requests
import polars as pl
import datetime
import pytz
import re
from bs4 import BeautifulSoup
import json

class Entso:
    def __init__(self):
        self.df = self.readParquet()
        self.utc_timezone = pytz.timezone("UTC")
        self.cet_timezone = pytz.timezone("CET")
        self.eet_timezone = pytz.timezone("Europe/Helsinki")
    
    def updateEverything(self):
        self.updatePolars()
        df = self.df
        jsonData = json.dumps([i for i in zip(df["Aika"].to_list(), df["Alv-hinta snt/kWh"].to_list())])
        if not self._isJsonUpdated():
            # First updates the spot data in current directory.
            with open("spotdata.json", "w", encoding="utf-8") as file:
                file.write(jsonData)
            print("JSON updated.")
        return

    def updatePolars(self):
        if not self._isParquetUpdated():
            df = self.df
            start = df["utcTime"][-1].strftime("%Y%m%d%H%M")
            end = (datetime.datetime.now() + datetime.timedelta(days=2)).strftime("%Y%m%d0000")
            newdf = self._requestToPolars(start, end)
            df = pl.concat([df, newdf])
            if not all(df.is_unique()):
                df = df.unique()
            if not df["epochTime"].is_sorted():
                df = df.sort("epochTime")
            self._writeUpdateToParquet(df)
            return
        else:
            print("Already up to date.")
            return
    
    def _isParquetUpdated(self):
        cet_timezone = self.cet_timezone
        df = self.df
        cetTimeNow = datetime.datetime.now(cet_timezone)
        cetTimeTomorrowCutoff = (datetime.datetime.now(cet_timezone) + datetime.timedelta(days=1)).replace(hour=23, minute=0, second=0, microsecond=0)
        cetLastDbHour = df["utcTime"][-1].astimezone(cet_timezone)
        if cetTimeNow.hour < 12 and cetTimeNow.minute < 30:
            if cetLastDbHour < cetTimeNow:
                return False
        elif cetLastDbHour < cetTimeTomorrowCutoff:
                return False
        else:
            return True
        
    def _isJsonUpdated(self):
        cet_timezone = self.cet_timezone
        df = self.df
        with open("spotdata.json", "r", encoding="utf-8") as file:
            jsonData = json.loads(file.read())
        return jsonData[-1][0] == self.df["Aika"][-1]

    def readParquet(self):
        df = pl.read_parquet("database.parquet")
        df = df.unique()
        df = df.sort("epochTime")
        return df
    
    def _writeUpdateToParquet(self, newdf):     
        df = self.df
        if self._isParquetUpdated():
            print("The database is up to date.")
            return
        if df.frame_equal(newdf):
            msg = """
            \rIt seems that Entso-E hasn't updated their tomorrow's prices yet try
            \ragain in few minutes."""
            print(msg)
            return
        if newdf.shape[1] != self.df.shape[1]:
            msg = """
            \rWriting parquet database aborted, because column number of the new df
            \rdidn't match the column number of the old one."""
            print(msg)
            return
        if newdf.shape[0] < self.df.shape[0]:
            msg = """
            \rWriting parquet database aborted, because the size of the new database
            \rwas smaller than the size of the old one."""
            print(msg)
            return
        else:
            newdf.write_parquet(file="./database.parquet", compression="zstd", compression_level=8)
            self.df = newdf
            print("Parquet database updated.")
            return
    
    def _requestToPolars(self, start, end):
        """
        Arguments: start and end dates in '%Y%m%d%H%M' format, eg. 
        '202312240000'.
        Returns: Response from Entso-E transparency API parsed to Polars df.
        """
        xml = self._requestXml(start, end)
        self.newdf = self._xmlToPolars(xml)
        return self.newdf

    def _requestXml(self, start, end):
        """
        Arguments: start and end dates in '%Y%m%d%H%M' format, eg. 
        '202312240000'.
        Returns: Unparsed xml from Entso-E transparency API.
        """
        if not self._isValidDateFormat(start) and self._isValidDateFormat(end):
            print("API requests was given invalid date string. Valid format is '%Y%m%d%H%M'.")
            return
        baseUrl = "https://web-api.tp.entsoe.eu/api?"
        params = {
            'securityToken': '146ed7fe-f411-4c90-afb5-0b2af98f97eb',
            'documentType': 'A44',
            'in_Domain': '10YFI-1--------U',
            'out_Domain': '10YFI-1--------U',
            'periodStart': start,
            'periodEnd': end
            }
        response = requests.get(baseUrl, params)
        response.raise_for_status()
        return response.text

    def _xmlToPolars(self, xmlText):
        soup = BeautifulSoup(xmlText, 'xml')
        results = soup.find_all("TimeSeries")

        dslist = []
        for result in results:
            dslist.append(self._parseSoup(result))
        
        dflist = []
        for ds in dslist:
            dflist.append(pl.from_dicts(ds))

        df = pl.concat(dflist)
        df = df.with_columns(df["price_amount"].cast(pl.Float64))
        startUtf = df["start"].str.strptime(pl.Datetime, "%Y-%m-%dT%H:%MZ")
        timeDeltas = pl.duration(hours=df["position"].cast(pl.Int64) - 1)
        utcTime = pl.select(startUtf + timeDeltas)["start"].alias("utcTime")
        df = df.with_columns(utcTime)
        df = df.with_columns(pl.col("utcTime").dt.timestamp().alias("epochTime"))
        df = df.sort("epochTime")
        df = df.with_columns(df["utcTime"].dt.timestamp().map_elements(lambda x: datetime.datetime.fromtimestamp(x/1e6).strftime("%d.%m.%Y %H:%M")).alias("Aika"))

        # Timezones
        df = df.with_columns(df["utcTime"].dt.replace_time_zone("UTC"))
        df = df.with_columns(df["utcTime"].dt.convert_time_zone("Europe/Helsinki").alias("eetTime"))
        
        """
        Taking into account the period of exceptional added value tax (ALV) and 
        exclusion of ALV when the price is negative.
        Start date of 10% ALV exception: "2022-12-01".
        End date of 10% ALV exception: "2023-04-30".
        """
        start_date = pl.datetime(2022, 12, 1, 0, time_zone="Europe/Helsinki")
        end_date = pl.datetime(2023, 5, 1, 0, time_zone="Europe/Helsinki")
        
        df = df.with_columns((df["price_amount"]/10).alias("Hinta snt/kWh"))
        df = df.with_columns(pl
            .when((pl.col("eetTime") >= start_date) & (pl.col("eetTime") < end_date))
            .then(1.1)
            .otherwise(1.24)
            .alias("Alv")
        )
        
        df = df.with_columns((df["price_amount"]/10).alias("Hinta snt/kWh"))
        df = df.with_columns(
            pl.when((df["eetTime"] >= start_date) & (df["eetTime"] < end_date))
            .then(pl.when(df["price_amount"] >= 0).then(1.1).otherwise(1.0))
            .otherwise(pl.when(df["price_amount"] >= 0).then(1.24).otherwise(1.0))
            .alias("Alv")
            )
        df = df.with_columns((df["Hinta snt/kWh"]*df["Alv"]).alias("Alv-hinta snt/kWh"))
        # df = df.with_columns(
        #     pl.when(
        #         (pl.col("eetTime") >= start_date) & (pl.col("eetTime") < end_date)
        #     ).then(
        #         pl.col("Hinta snt/kWh") * 1.1  # Assuming you want to double the price_amount
        #     ).otherwise(
        #         pl.col("Hinta snt/kWh")  * 1.24
        #     ).alias("Alv-hinta snt/kWh")
        # )
        df = df[["epochTime", "utcTime", "eetTime", "Aika", "Hinta snt/kWh", "Alv-hinta snt/kWh", "Alv"]]
        return df

    def _parseSoup(self, result):
        """
        Takes one result of soup.find_all("TimeSeries") as an argument, where the
        soup is BeautifulSoup(xmlText, 'xml') and xmlText is day-ahead prices 
        from Entso-E API.
        """
        # Initialize dictionary to hold parsed data
        dslist = []
        time_series_data = {}

        # Extracting individual elements
        currency = result.find('currency_Unit.name').text.strip()
        unit = result.find('price_Measure_Unit.name').text.strip()

        # Handling the 'Period' section
        period = result.find('Period')
        resolution = period.find('resolution').text.strip()
        start = period.find('start').text.strip()

        # Extracting data from each 'Point'
        for point in period.find_all('Point'):
            time_series_data = {}
            time_series_data["position"] = point.find('position').text.strip()
            time_series_data["resolution"] = resolution
            time_series_data["start"] = start
            time_series_data["price_amount"] = point.find('price.amount').text.strip()
            time_series_data["currency"] = currency
            time_series_data["power_unit"] = unit
            dslist.append(time_series_data)
        return dslist
    
    def _isValidDateFormat(self, dateStr):
        # Regular expression pattern for the date format YYYYMMDDHHMM
        pattern = r'^\d{4}(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])([01]\d|2[0-3])[0-5]\d$'
        
        # Match the pattern from the start of the string
        if re.match(pattern, dateStr):
            return True
        else:
            return False
        
    def stdRound(self, value, decimal=0):
        """
        Standard rounding. Returns a float.
        """
        from math import floor
        if not isinstance(value, float):
            raise TypeError("Expected value to be float.")
        if not isinstance(decimal, int):
            raise TypeError("Excpected decimal to be int.")
        value = value*10**decimal
        value = floor(value + 0.5)
        return value/10**decimal
    
def main():
    e = Entso()
    e.updateEverything()

if __name__ == "__main__":
    main()
