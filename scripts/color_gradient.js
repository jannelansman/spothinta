function gradient(price) {
    let a;
    let b;
    let k;
    // Setting constraints
    if (price < 0) {
        return Array(0, 255, 0, 0.2);
    } else if (price > 25) {
        return Array(255, 0, 0, 0.2);
    } else {
        k = price/25;
        if (k <= 0.5) {
            a = 510*k;
            b = 255;
        } else {
            a = 255;
            b = 255 - (k - 0.5)*510;
        }
        return Array(a, b, 0, 0.2);
    }
}
