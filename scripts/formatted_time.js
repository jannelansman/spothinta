function getCurrentTimeFormatted() {
    let now = new Date();

    let hours = now.getHours().toString().padStart(2, '0');
    let minutes = "00";
    let day = now.getDate().toString().padStart(2, '0');
    let month = (now.getMonth() + 1).toString().padStart(2, '0'); // +1 because months are 0-indexed
    let year = now.getFullYear();

    //return `${day}.${month}.${year} ${hours}:${minutes}`;
    return `${day}.${month}.${year} ${hours}:${minutes}`;
}
