function rollingWindowMin(array, windowSize) {
    let windows = Array();
    let meanValues = Array();
    let min;
    for (i=0; i<array.length; i++) {
        if (windowSize > array.length) {
            break;
        } else if (i + windowSize > array.length) {
            break;
        } else {
            windows.push(array.slice(i, i+windowSize));
        }
    }
    windows.forEach(win => {
    meanValues.push(win.reduce((a, b) => a + b, 0)/win.length);
    });
    min = meanValues.reduce((a, b) => Math.min(a, b), Infinity);
    return min;
}

// Print stats
let now = new Date();
let tomorrow = new Date(now.getTime() + 86400000)

let {year, month, day, hour, minute} = {
    year: String(now.getFullYear()), 
    month: String(now.getMonth() + 1).padStart(2, '0'), 
    day: String(now.getDate()).padStart(2, '0'), 
    hour: String(now.getHours()).padStart(2, '0'), 
    minute: String(now.getMinutes()).padStart(2, '0')
}

let {tomorrowYear, tomorrowMonth, tomorrowDay} = {
    tomorrowYear: String(tomorrow.getFullYear()),
    tomorrowMonth: String(tomorrow.getMonth() + 1).padStart(2, '0'), 
    tomorrowDay: String(tomorrow.getDate()).padStart(2, '0')
}

// Time strings
let todayStr = `${day}.${month}.${year}`;
let tomorrowStr = `${tomorrowDay}.${tomorrowMonth}.${tomorrowYear}`;
let nowHourStr = `${day}.${month}.${year} ${hour}:00`;
let nowHourCmpStr = `${year}${month}${day} ${hour}:00`;

// Stats for maxes, mins and means
const stats = {};
//stats["periods"] = {};
const strings = {};
strings["stats"] = {};
strings["periods"] = {};

// Array generation for easier navigation through dataset
let todayKeys = Array();
let tomorrowKeys = Array();
let futureKeys = Array();
let todayValues = Array();
let tomorrowValues = Array();
let futureValues = Array();

// Injects
const injects = Array();
let inject;

// Slice new section for stats
let jsonSection2 = jsonData.slice(-72);
jsonSection2.forEach(timePriceTuple => {
    // parse datetime from datetime-price tuples
    let front = timePriceTuple[0].split(" ")[0].split(".");
    let back = timePriceTuple[0].split(" ")[1].split(":");
    let tupleYear = front[2];
    let tupleMonth = front[1];
    let tupleDay = front[0];
    let tupleHour = back[0];
    let tupleMin = back[1];
    // create comparison strings
    let dayCmpStr = tupleYear + tupleMonth + tupleDay;
    let tupletimeCmpStr = front[2] + front[1] + front[0] + " " + back[0] + ":" + back[1];
    
    // today arrays
    if (timePriceTuple[0].includes(todayStr)) {
        todayKeys.push(timePriceTuple[0]);
        todayValues.push(timePriceTuple[1]);
    // tomorrow arrays
    } else if (timePriceTuple[0].search(tomorrowStr) >= 0) {
        tomorrowKeys.push(timePriceTuple[0]);
        tomorrowValues.push(timePriceTuple[1]);
    }
    // future arrays
    if (tupletimeCmpStr >= nowHourCmpStr) {
        futureKeys.push(timePriceTuple[0]);
        futureValues.push(timePriceTuple[1]);
    }
});
// Compute and format table strings //
// price now
for (let i=0; i<todayKeys.length; i++) {
    if (todayKeys[i] == nowHourStr) {
        stats["price-now"] = todayValues[i];
    }
}
// today values
stats["today-max"] = todayValues.reduce((a, b) => Math.max(a, b), 0);
stats["today-min"] = todayValues.reduce((a, b) => Math.min(a, b), Infinity);
stats["today-mean"] = todayValues.reduce((a, b) => a + b, 0) / todayValues.length;
// tomorrow values
if (tomorrowValues.length == 24) {
    stats["tomorrow-max"] = tomorrowValues.reduce((a, b) => Math.max(a, b), 0);
    stats["tomorrow-min"] = tomorrowValues.reduce((a, b) => Math.min(a, b), Infinity);
    stats["tomorrow-mean"] = tomorrowValues.reduce((a, b) => a + b, 0) / tomorrowValues.length;
}
// lowest cost periods
let min;
for (let i=2; i<=6; i++) {
    min = rollingWindowMin(futureValues, i);
    if (min == Infinity) {
        strings["periods"][`period-${i}hours`] = [`Halvin ${i}h jakso`, `${i}`, "-"];
    } else {
        strings["periods"][`period-${i}hours`] = [`Halvin ${i}h jakso`, `${i}`, String(min.toFixed(2)).replace(".", ",") + " snt/kWh"];
    }
}

// Format and inject strings //
let element;
for (let key of [
    "price-now", 
    "today-max", 
    "today-min", 
    "today-mean", 
    "tomorrow-max", 
    "tomorrow-min", 
    "tomorrow-mean"
]) {
    if (typeof(stats[key]) === "undefined") {
        strings["stats"][key] = "-";
    } else {
        strings["stats"][key] = String(stats[key].toFixed(2)).replace(".", ",") + " snt/kWh";
    }
    // injection
    element = document.getElementById(key);
    element.innerText = strings["stats"][key];
}
// lowest cost periods
injects.length = 0;
element = document.getElementById("periods-tbody");
for (let i in strings["periods"]) {
    console.log(i);
    injects.push(`<tr><td>${strings["periods"][i][0]}</td><td>${`-`}</td><td>${strings["periods"][i][2]}</td></tr>`);
}
console.log(`injects: ${injects}`);
inject = injects.join("");
console.log(`lowest cost inject: ${inject}`);
element.innerHTML = inject;

// day-ahead
injects.length = 0;
element = document.getElementById("future-tbody");
for (let i=0; i<futureValues.length; i++) {
    // parse datetime from datetime-price tuples
    let front = futureKeys[i].split(" ")[0].split(".");
    let back = futureKeys[i].split(" ")[1].split(":");
    let tmpYear = front[2];
    let tmpMonth = front[1];
    let tmpDay = front[0];
    let tmpHour = back[0];
    let tmpMin = back[1];
    
    let tmpDateStr = `${tmpDay}.${tmpMonth}.${tmpYear}`;
    let tmpTimeStr = `${tmpHour}:${tmpMin}`;
    let tmpValue = futureValues[i];
    let tmpString = String(tmpValue.toFixed(2)).replace(".", ",") + " snt/kWh";
    injects.push(`<tr><td>${tmpDateStr}</td><td>${tmpTimeStr}</td><td style="padding-left: 1em">${tmpString}</td></tr>`);
}
inject = injects.join("");
element.innerHTML = inject;
