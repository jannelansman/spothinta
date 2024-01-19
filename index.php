<?php
    $file = file_get_contents('./resources/spotdata.json');
    $jsonData = json_decode($file, true);
?>

<!DOCTYPE html>
<html lang="fi">
<head>
    <meta charset="UTF-8">
    <title>Sähkön spothinta</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<!--    <script src="https://cdnjs.cloudflare.com/ajax/libs/hammer.js/2.0.8/hammer.min.js"></script> -->
    <script src="https://cdnjs.cloudflare.com/ajax/libs/chartjs-plugin-zoom/1.1.1/chartjs-plugin-zoom.min.js"></script>
</head>
<body>

<canvas id="electricityChart"></canvas>

<div id="spacer" style="height: 100px;"></div>
<div id="stats">
    <table>
        <thead>
            <tr><th style="colspan: 2">Hinta tänään</th></tr>
        </thead>
        <tbody>
            <tr><td>Juuri nyt</td><td id="price-now"></td></tr>
            <tr><td>Kallein</td><td id="today-max"></td></tr>
            <tr><td>Halvin</td><td id="today-min"></td></tr>
            <tr><td>Keskiarvo</td><td id="today-mean"></td></tr>
        </tbody>
    </table>
    <br>
    <table>
        <thead>
            <tr><th style="colspan: 2">Hinta huomenna</th></tr>
        </thead>
        <tbody>
            <tr><td>Kallein</td><td id="tomorrow-max"></td></tr>
            <tr><td>Halvin</td><td id="tomorrow-min"></td></tr>
            <tr><td>Keskiarvo</td><td id="tomorrow-mean"></td></tr>
        </tbody>
    </table>
    <br>
    <table>
        <thead>
            <tr><th>Halvimmat jaksot</th><th>Klo</th><th>Hinta</th></tr>
        </thead>
        <tbody id="periods-tbody">
        </tbody>
    </table>
    <br>
    <table>
        <thead>
            <tr><th style="colspan: 3; text-align: left;">Tulevat</th></tr>
            <tr><th>Päivä</th><th>Kello</th><th>Hinta</th></tr>
        </thead>
        <tbody id="future-tbody">
        </tbody>
    </table>
</div>

<script src="./scripts/init_canvas_size.js"></script>
<script src="./scripts/formatted_time.js"></script>
<script src="./scripts/color_gradient.js"></script>
<script>const jsonData = <?php echo json_encode($jsonData); ?>;</script>
<script src="./scripts/graph_data.js"></script>
<script src="./scripts/stats.js"></script>
</body>
</html>