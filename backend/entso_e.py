import datetime
import re
import json
import requests
import polars as pl
import pytz
from bs4 import BeautifulSoup


class Entso:
    """
    Functions for initializing and updating Entso-E API data to Parquet database and JSON
    file.
    """

    def __init__(self):
        self.df = self.read_parquet()
        self.newdf = pl.DataFrame()
        self.utc_timezone = pytz.timezone("UTC")
        self.cet_timezone = pytz.timezone("CET")
        self.eet_timezone = pytz.timezone("Europe/Helsinki")

    def update_everything(self):
        """
        Update manager. Takes no arguments.
        """
        self.update_polars()
        df = self.df
        json_data = json.dumps(
            [i for i in zip(df["Aika"].to_list(), df["Alv-hinta snt/kWh"].to_list())]
        )
        if not self._is_json_updated():
            # First updates the spot data in current directory.
            with open("../frontend/data/spotdata.json", "w", encoding="utf-8") as file:
                file.write(json_data)
            print("JSON updated.")
        return

    def update_polars(self):
        """
        Manages requesting and updating new data to Parquet database. Takes no arguments.
        """
        if not self._is_parquet_updated():
            df = self.df
            start = df["utcTime"][-1].strftime("%Y%m%d%H%M")
            end = (datetime.datetime.now() + datetime.timedelta(days=2)).strftime(
                "%Y%m%d0000"
            )
            newdf = self._request_to_polars(start, end)
            df = pl.concat([df, newdf])
            if not all(df.is_unique()):
                df = df.unique()
            if not df["epochTime"].is_sorted():
                df = df.sort("epochTime")
            self._write_update_to_parquet(df)
            return
        else:
            print("Parquet already up to date.")
            return

    def _is_parquet_updated(self):
        cet_timezone = self.cet_timezone
        df = self.df
        cet_time_now = datetime.datetime.now(cet_timezone)
        cet_time_tomorrow_cutoff = datetime.datetime.now(
            cet_timezone
        ) + datetime.timedelta(days=1)
        cet_time_tomorrow_cutoff = cet_time_tomorrow_cutoff.replace(
            hour=23, minute=0, second=0, microsecond=0
        )
        last_cet_hour_in_db = df["utcTime"][-1].astimezone(cet_timezone)
        if cet_time_now.hour < 12 and cet_time_now.minute < 30:
            if last_cet_hour_in_db < cet_time_now:
                return False
        elif last_cet_hour_in_db < cet_time_tomorrow_cutoff:
            return False
        else:
            return True

    def _is_json_updated(self):
        with open("../frontend/data/spotdata.json", "r", encoding="utf-8") as file:
            json_data = json.loads(file.read())
        return json_data[-1][0] == self.df["Aika"][-1]

    def read_parquet(self):
        """
        Reads Parquet database from file for Entso class. Takes no arguments.
        """
        df = pl.read_parquet("database.parquet")
        df = df.unique()
        df = df.sort("epochTime")
        return df

    def _write_update_to_parquet(self, newdf):
        df = self.df
        if self._is_parquet_updated():
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
            newdf.write_parquet(
                file="./database.parquet", compression="zstd", compression_level=8
            )
            self.df = newdf
            print("Parquet database updated.")
            return

    def _request_to_polars(self, start, end):
        """
        Arguments: start and end dates in '%Y%m%d%H%M' format, eg.
        '202312240000'.
        Returns: Response from Entso-E transparency API parsed to Polars df.
        """
        xml = self._request_xml(start, end)
        self.newdf = self._xml_to_polars(xml)
        return self.newdf

    def _request_xml(self, start, end):
        """
        Arguments: start and end dates in '%Y%m%d%H%M' format, eg.
        '202312240000'.
        Returns: Unparsed xml from Entso-E transparency API.
        """
        if not self._is_valid_date_format(start) and self._is_valid_date_format(end):
            print(
                "API requests was given invalid date string. Valid format is '%Y%m%d%H%M'."
            )
            return
        base_url = "https://web-api.tp.entsoe.eu/api?"
        params = {
            "securityToken": "146ed7fe-f411-4c90-afb5-0b2af98f97eb",
            "documentType": "A44",
            "in_Domain": "10YFI-1--------U",
            "out_Domain": "10YFI-1--------U",
            "periodStart": start,
            "periodEnd": end,
        }
        response = requests.get(base_url, params, timeout=10)
        response.raise_for_status()
        return response.text

    def _xml_to_polars(self, xml_text):
        soup = BeautifulSoup(xml_text, "xml")
        results = soup.find_all("TimeSeries")

        dslist = []
        for result in results:
            dslist.append(self._parse_soup(result))

        dflist = []
        for ds in dslist:
            dflist.append(pl.from_dicts(ds))

        df = pl.concat(dflist)
        df = df.with_columns(df["price_amount"].cast(pl.Float64))
        start_utc = df["start"].str.strptime(pl.Datetime, "%Y-%m-%dT%H:%MZ")
        time_deltas = pl.duration(hours=df["position"].cast(pl.Int64) - 1)
        utc_time = pl.select(start_utc + time_deltas)["start"].alias("utcTime")
        df = df.with_columns(utc_time)
        df = df.with_columns(pl.col("utcTime").dt.timestamp().alias("epochTime"))
        df = df.sort("epochTime")
        df = df.with_columns(
            df["utcTime"]
            .dt.timestamp()
            .map_elements(
                lambda x: datetime.datetime.fromtimestamp(
                    x / 1e6, tz=self.eet_timezone
                ).strftime("%d.%m.%Y %H:%M")
            )
            .alias("Aika")
        )

        # Timezones
        df = df.with_columns(df["utcTime"].dt.replace_time_zone("UTC"))
        df = df.with_columns(
            df["utcTime"].dt.convert_time_zone("Europe/Helsinki").alias("eetTime")
        )

        # Taking into account the period of exceptional added value tax (ALV) and
        # exclusion of ALV when the price is negative.
        # Start date of 10% ALV exception: "2022-12-01".
        # End date of 10% ALV exception: "2023-04-30".
        start_date = pl.datetime(2022, 12, 1, 0, time_zone="Europe/Helsinki")
        end_date = pl.datetime(2023, 5, 1, 0, time_zone="Europe/Helsinki")

        df = df.with_columns((df["price_amount"] / 10).alias("Hinta snt/kWh"))
        df = df.with_columns(
            pl.when((pl.col("eetTime") >= start_date) & (pl.col("eetTime") < end_date))
            .then(1.1)
            .otherwise(1.24)
            .alias("Alv")
        )

        df = df.with_columns((df["price_amount"] / 10).alias("Hinta snt/kWh"))
        df = df.with_columns(
            pl.when((df["eetTime"] >= start_date) & (df["eetTime"] < end_date))
            .then(pl.when(df["price_amount"] >= 0).then(1.1).otherwise(1.0))
            .otherwise(pl.when(df["price_amount"] >= 0).then(1.24).otherwise(1.0))
            .alias("Alv")
        )
        df = df.with_columns(
            (df["Hinta snt/kWh"] * df["Alv"]).alias("Alv-hinta snt/kWh")
        )
        df = df[
            [
                "epochTime",
                "utcTime",
                "eetTime",
                "Aika",
                "Hinta snt/kWh",
                "Alv-hinta snt/kWh",
                "Alv",
            ]
        ]
        return df

    def _parse_soup(self, result):
        """
        Takes one result of soup.find_all("TimeSeries") as an argument, where the
        soup is BeautifulSoup(xml_text, 'xml') and xml_text is day-ahead prices
        from Entso-E API.
        """
        # Initialize dictionary to hold parsed data
        dslist = []
        time_series_data = {}

        # Extracting individual elements
        currency = result.find("currency_Unit.name").text.strip()
        unit = result.find("price_Measure_Unit.name").text.strip()

        # Handling the 'Period' section
        period = result.find("Period")
        resolution = period.find("resolution").text.strip()
        start = period.find("start").text.strip()

        # Extracting data from each 'Point'
        for point in period.find_all("Point"):
            time_series_data = {}
            time_series_data["position"] = point.find("position").text.strip()
            time_series_data["resolution"] = resolution
            time_series_data["start"] = start
            time_series_data["price_amount"] = point.find("price.amount").text.strip()
            time_series_data["currency"] = currency
            time_series_data["power_unit"] = unit
            dslist.append(time_series_data)
        return dslist

    def _is_valid_date_format(self, date_str):
        # Regular expression pattern for the date format YYYYMMDDHHMM
        pattern = r"^\d{4}(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])([01]\d|2[0-3])[0-5]\d$"

        # Match the pattern from the start of the string
        if re.match(pattern, date_str):
            return True
        else:
            return False

    def std_round(self, value, decimals=0):
        """
        Standard rounding. Returns a float.
        """
        if not (isinstance(value, float) or isinstance(value, int)):
            raise TypeError(
                f"Expected value to round to be type int or type float, but the type was: {type(value)}."
            )
        if not isinstance(decimals, int):
            raise TypeError(
                f"Expected number of decimals to be type int, but the type was: {type(decimals)}."
            )
        value = value * 10**decimals
        value = int(value + 0.5)
        return value / 10**decimals


def main():
    """
    Main function simply updates existing database---if necessary---on runtime.
    """
    e = Entso()
    e.update_everything()


if __name__ == "__main__":
    main()
