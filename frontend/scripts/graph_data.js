// Your provided dataset
let jsonSection;
jsonSection = jsonData.slice(-Math.max(36, Math.floor(window.innerWidth/10)));
const prices = jsonSection.map(tuple => Math.round(tuple[1]*100)/100);

// Labels for the x-axis
const hours = jsonSection.map(tuple => tuple[0]);

// Prepare background colors for each bar
const backgroundColors = [];
const currentHour = getCurrentTimeFormatted();
for (let i = 0; i < hours.length; i++) {
    let hourFromLabel = hours[i];
    let colors = gradient(prices[i]);
    // Color the bars. Current hour bar and bars for different price ranges.
    if (hourFromLabel === currentHour) {
        backgroundColors.push(`rgba(0, 0, 0, 0.8)`); // Different color for current hour
    } else {
        backgroundColors.push(`rgba(${colors[0]}, ${colors[1]}, 0, 0.6)`);
    }
    // Extract hour from the label
    if (i != 0 && i != hours.length - 1 && !hours[i].includes("00:00")) {
        hours[i] = hours[i].slice(-5);
    }
}

var ctx = document.getElementById('electricityChart').getContext('2d');
var myChart = new Chart(ctx, {
    type: 'bar',
    data: {
        labels: hours,
        datasets: [{
            label: 'Sähkön arvonlisäverollinen hinta (snt/kWh)',
            data: prices,
            backgroundColor: backgroundColors,
            borderColor:  'rgba(54, 162, 235, 1)',
            borderWidth: 0
        }]
    },
    options: {
        scales: {
            y: {
                beginAtZero: true,
                title: {
                    display: true,
                    text: 'Hinta (snt/kWh)'
                }
            },
            x: {
                title: {
                    display: true,
                    text: 'Aika'
                }
            }
        },
        // Updated Zoom and pan configuration
        plugins: {
            zoom: {
                pan: {
                    enabled: true,
                    mode: 'x' // 'x' for horizontal panning
                },
                zoom: {
                    wheel: {
                        enabled: true
                    },
                    drag: {
                        enabled: true
                    },
                    mode: 'x' // 'x' for horizontal zooming
                }
            }
        }
    }
});
