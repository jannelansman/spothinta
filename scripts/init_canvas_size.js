// Initialize canvas size
let canvas = document.getElementById("electricityChart");
canvas.width = window.innerWidth;
canvas.height = window.innerHeight;

window.addEventListener('orientationchange', handleResize);

function handleResize() {
    location.reload();
}
