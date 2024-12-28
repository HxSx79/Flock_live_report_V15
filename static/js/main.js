// Global chart variables
let line1Chart, line2Chart;

// Initialize Socket.IO connection
const socket = io();

// Initialize page
document.addEventListener('DOMContentLoaded', function() {
    // Only create charts if they don't exist
    if (!line1Chart && !line2Chart) {
        createCharts();
    }
    
    // Load initial production data
    fetch('/production_data')
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('Initial data loaded:', data);
            updateUI(data);
        })
        .catch(error => {
            console.error('Error loading initial data:', error);
        });
});

// Listen for production updates
socket.on('production_update', function(data) {
    updateProductionData(data);
});

// Listen for scrap updates
socket.on('scrap_update', function(data) {
    // Update only scrap-related elements
    updateScrapData(data);
});

// Initialize charts
function createCharts() {
    const commonConfig = {
        type: 'bar',
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: {
                    type: 'time',
                    time: {
                        unit: 'hour',
                        parser: 'HH:mm:ss',
                        displayFormats: {
                            hour: 'HH:mm'
                        },
                        stepSize: 1
                    },
                    min: moment().startOf('day').add(6, 'hours'),
                    max: moment().startOf('day').add(23, 'hours'),
                    grid: {
                        color: function(context) {
                            if (context.tick && 
                                moment(context.tick.value).format('HH:mm') === '14:00') {
                                return 'rgba(0, 0, 0, 0.3)';
                            }
                            return 'rgba(0, 0, 0, 0.1)';
                        },
                        lineWidth: function(context) {
                            if (context.tick && 
                                moment(context.tick.value).format('HH:mm') === '14:00') {
                                return 2;
                            }
                            return 1;
                        }
                    },
                    ticks: {
                        font: {
                            size: 10
                        }
                    }
                },
                y: {
                    beginAtZero: true,
                    min: 0,
                    max: 140,
                    position: 'left',
                    title: {
                        display: true,
                        text: 'Quantity',
                        font: {
                            size: 10
                        }
                    },
                    ticks: {
                        stepSize: 10,
                        font: {
                            size: 10
                        }
                    }
                },
                y1: {
                    beginAtZero: true,
                    min: 0,
                    max: 140,
                    position: 'right',
                    title: {
                        display: true,
                        text: 'Parts/Hour',
                        font: {
                            size: 10
                        }
                    },
                    grid: {
                        drawOnChartArea: false
                    },
                    ticks: {
                        stepSize: 10,
                        font: {
                            size: 10
                        }
                    }
                }
            },
            plugins: {
                legend: {
                    position: 'top',
                    labels: {
                        font: {
                            size: 10
                        }
                    }
                },
                tooltip: {
                    mode: 'index',
                    intersect: false,
                    titleFont: {
                        size: 10
                    },
                    bodyFont: {
                        size: 10
                    }
                }
            }
        }
    };

    // Create initial data points
    const initialData = [];
    for (let hour = 6; hour <= 23; hour++) {
        initialData.push({
            x: moment().startOf('day').add(hour, 'hours').format('HH:mm:ss'),
            y: 0
        });
    }

    // Create Line 1 Chart with separate datasets
    const ctx1 = document.getElementById('line1-chart').getContext('2d');
    line1Chart = new Chart(ctx1, {
        ...commonConfig,
        data: {
            datasets: [
                {
                    label: 'Target',
                    data: initialData.map(point => ({...point})),
                    backgroundColor: 'rgba(54, 162, 235, 0.5)',
                    borderColor: 'rgb(54, 162, 235)',
                    borderWidth: 1,
                    order: 1,
                    type: 'bar'
                },
                {
                    label: 'Quantity',
                    data: initialData.map(point => ({...point})),
                    backgroundColor: 'rgba(75, 192, 192, 0.5)',
                    borderColor: 'rgb(75, 192, 192)',
                    borderWidth: 1,
                    order: 2,
                    type: 'bar'
                },
                {
                    label: 'Parts/Hour',
                    data: initialData.map(point => ({...point, y: null})),
                    borderColor: 'rgb(0, 0, 255)',
                    backgroundColor: 'rgb(0, 0, 255)',
                    borderWidth: 2,
                    type: 'line',
                    yAxisID: 'y1',
                    fill: false,
                    tension: 0,
                    pointRadius: 4,
                    pointStyle: 'circle',
                    pointHoverRadius: 4,
                    showLine: false
                }
            ]
        }
    });

    // Create Line 2 Chart with separate datasets
    const ctx2 = document.getElementById('line2-chart').getContext('2d');
    line2Chart = new Chart(ctx2, {
        ...commonConfig,
        data: {
            datasets: [
                {
                    label: 'Target',
                    data: initialData.map(point => ({...point})),
                    backgroundColor: 'rgba(54, 162, 235, 0.5)',
                    borderColor: 'rgb(54, 162, 235)',
                    borderWidth: 1,
                    order: 1,
                    type: 'bar'
                },
                {
                    label: 'Quantity',
                    data: initialData.map(point => ({...point})),
                    backgroundColor: 'rgba(75, 192, 192, 0.5)',
                    borderColor: 'rgb(75, 192, 192)',
                    borderWidth: 1,
                    order: 2,
                    type: 'bar'
                },
                {
                    label: 'Parts/Hour',
                    data: initialData.map(point => ({...point, y: null})),
                    borderColor: 'rgb(0, 0, 255)',
                    backgroundColor: 'rgb(0, 0, 255)',
                    borderWidth: 2,
                    type: 'line',
                    yAxisID: 'y1',
                    fill: false,
                    tension: 0,
                    pointRadius: 4,
                    pointStyle: 'circle',
                    pointHoverRadius: 4,
                    showLine: false
                }
            ]
        }
    });
}

// Add this at the top with other global variables
let currentTarget1 = 0;
let currentTarget2 = 0;
let currentClass1 = '';
let currentClass2 = '';

// Update chart data
function updateCharts(data) {
    const currentHour = moment().startOf('hour').format('HH:mm:ss');
    
    console.log('Debug - Chart Update:', {
        currentClass1,
        newClass1: data.line1_part.class_name,
        currentClass2,
        newClass2: data.line2_part.class_name,
        currentTarget1,
        currentTarget2
    });

    // Update Line 1 Chart only when there's a crossing on Line 1
    if (data.line1_part.track_id !== window.previousLine1?.track_id) {
        // Only update target if class name has changed or not set yet
        if (data.line1_part.class_name !== currentClass1 || currentTarget1 === 0) {
            console.log('Debug - Line 1 Target Update:');
            console.log('  Raw target value:', data.line1_part.target);
            console.log('  Current class:', currentClass1);
            console.log('  New class:', data.line1_part.class_name);
            currentTarget1 = parseInt(data.line1_part.target, 10) || 0;
            currentClass1 = data.line1_part.class_name;
            console.log('  Updated target value:', currentTarget1);
        }

        console.log('Debug - Line 1 Chart Update:');
        console.log('  Current target:', currentTarget1);
        console.log('  Current quantity:', data.line1_production.quantity);

        // Calculate Parts/Hour
        const partsPerHour = data.line1_production.quantity > 0 && data.total_tbp_line1 > 0 
            ? Math.round(3600 / (data.total_tbp_line1 / data.line1_production.quantity))
            : 0;

        console.log('  Parts/Hour:', partsPerHour);

        // Determine circle color based on Parts/Hour vs Target comparison
        let circleColor;
        if (partsPerHour > currentTarget1) {
            circleColor = 'rgb(0, 255, 0)';  // Green
        } else if (partsPerHour < currentTarget1) {
            circleColor = 'rgb(255, 0, 0)';  // Red
        } else {
            circleColor = 'rgb(0, 0, 255)';  // Blue
        }
        line1Chart.data.datasets[2].borderColor = circleColor;
        line1Chart.data.datasets[2].backgroundColor = circleColor;

        // Update target and quantity datasets
        line1Chart.data.datasets[0].data = line1Chart.data.datasets[0].data.map(point => ({
            x: point.x,
            y: moment(point.x, 'HH:mm:ss').format('HH:mm:ss') === currentHour ? currentTarget1 : 0
        }));

        line1Chart.data.datasets[1].data = line1Chart.data.datasets[1].data.map(point => ({
            x: point.x,
            y: moment(point.x, 'HH:mm:ss').format('HH:mm:ss') === currentHour ? data.line1_production.quantity : 0
        }));

        // Update Parts/Hour dataset - show only circles from current hour onwards
        line1Chart.data.datasets[2].data = line1Chart.data.datasets[2].data.map(point => {
            const pointHour = moment(point.x, 'HH:mm:ss');
            const currentMoment = moment(currentHour, 'HH:mm:ss');
            
            // Only show values from current hour onwards
            if (pointHour.isSameOrAfter(currentMoment)) {
                if (pointHour.format('HH:mm:ss') === currentHour) {
                    return {
                        x: point.x,
                        y: partsPerHour
                    };
                }
                return point;  // Keep existing values for future hours
            }
            return {
                x: point.x,
                y: null  // Hide points before current hour
            };
        });
        
        line1Chart.update();
    }

    // Update Line 2 Chart only when there's a crossing on Line 2
    if (data.line2_part.track_id !== window.previousLine2?.track_id) {
        // Only update target if class name has changed or not set yet
        if (data.line2_part.class_name !== currentClass2 || currentTarget2 === 0) {
            console.log('Debug - Line 2 Target Update:');
            console.log('  Raw target value:', data.line2_part.target);
            console.log('  Current class:', currentClass2);
            console.log('  New class:', data.line2_part.class_name);
            currentTarget2 = parseInt(data.line2_part.target, 10) || 0;
            currentClass2 = data.line2_part.class_name;
            console.log('  Updated target value:', currentTarget2);
        }

        console.log('Debug - Line 2 Chart Update:');
        console.log('  Current target:', currentTarget2);
        console.log('  Current quantity:', data.line2_production.quantity);

        // Calculate Parts/Hour
        const partsPerHour = data.line2_production.quantity > 0 && data.total_tbp_line2 > 0 
            ? Math.round(3600 / (data.total_tbp_line2 / data.line2_production.quantity))
            : 0;

        console.log('  Parts/Hour:', partsPerHour);

        // Determine circle color based on Parts/Hour vs Target comparison
        let circleColor;
        if (partsPerHour > currentTarget2) {
            circleColor = 'rgb(0, 255, 0)';  // Green
        } else if (partsPerHour < currentTarget2) {
            circleColor = 'rgb(255, 0, 0)';  // Red
        } else {
            circleColor = 'rgb(0, 0, 255)';  // Blue
        }
        line2Chart.data.datasets[2].borderColor = circleColor;
        line2Chart.data.datasets[2].backgroundColor = circleColor;

        // Update target and quantity datasets
        line2Chart.data.datasets[0].data = line2Chart.data.datasets[0].data.map(point => ({
            x: point.x,
            y: moment(point.x, 'HH:mm:ss').format('HH:mm:ss') === currentHour ? currentTarget2 : 0
        }));

        line2Chart.data.datasets[1].data = line2Chart.data.datasets[1].data.map(point => ({
            x: point.x,
            y: moment(point.x, 'HH:mm:ss').format('HH:mm:ss') === currentHour ? data.line2_production.quantity : 0
        }));

        // Update Parts/Hour dataset - show only circles from current hour onwards
        line2Chart.data.datasets[2].data = line2Chart.data.datasets[2].data.map(point => {
            const pointHour = moment(point.x, 'HH:mm:ss');
            const currentMoment = moment(currentHour, 'HH:mm:ss');
            
            // Only show values from current hour onwards
            if (pointHour.isSameOrAfter(currentMoment)) {
                if (pointHour.format('HH:mm:ss') === currentHour) {
                    return {
                        x: point.x,
                        y: partsPerHour
                    };
                }
                return point;  // Keep existing values for future hours
            }
            return {
                x: point.x,
                y: null  // Hide points before current hour
            };
        });
        
        line2Chart.update();
    }
}

// Update UI function
function updateUI(data) {
    // Update DOM elements
    updateDOMElements(data);
    // Update charts
    updateCharts(data);
    // Show notifications if needed
    checkForNewParts(data);
}

// Handle video upload
document.getElementById('video-upload').addEventListener('change', function(event) {
    const file = event.target.files[0];
    if (file) {
        const formData = new FormData();
        formData.append('video', file);

        fetch('/upload_video', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                console.log('Video uploaded successfully');
                // Refresh the video feed
                const videoFeed = document.querySelector('.video-container img');
                if (videoFeed) {
                    // Add timestamp to force browser to reload the image
                    const timestamp = new Date().getTime();
                    const currentSrc = videoFeed.src.split('?')[0];
                    videoFeed.src = `${currentSrc}?t=${timestamp}`;
                }
                // Request initial data after video upload
                fetch('/production_data')
                    .then(response => response.json())
                    .then(data => {
                        console.log('Initial data after video upload:', data);
                        updateUI(data);
                    })
                    .catch(error => {
                        console.error('Error getting initial data:', error);
                    });
            } else {
                console.error('Error uploading video:', data.error || 'Unknown error');
                alert('Error uploading video: ' + (data.error || 'Unknown error'));
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Error uploading video: ' + error);
        });
    }
});

// Helper function to format scrap rate
function formatScrapRate(rate) {
    return (rate === undefined || rate === null || isNaN(rate)) ? '0' : rate;
}

// Helper function to update DOM elements
function updateDOMElements(data) {
    // Update line 1 data
    document.getElementById('program-1').textContent = data.line1_part.program || 'No Part';
    document.getElementById('part-number-1').textContent = data.line1_part.part_number || 'No Part';
    document.getElementById('part-description-1').textContent = data.line1_part.part_description || 'No Part';
    document.getElementById('quantity-1').textContent = data.line1_production.quantity;
    
    // Update delta 1 with color and sign
    const delta1Element = document.getElementById('delta-1');
    const delta1Value = data.line1_production.delta;
    delta1Element.textContent = (delta1Value > 0 ? '+' : '-') + Math.abs(delta1Value);  // Add + or - sign
    delta1Element.parentElement.classList.toggle('positive', delta1Value > 0);
    
    document.getElementById('scrap-1').textContent = data.line1_scrap.total || '0';
    document.getElementById('scrap-rate-1').textContent = formatScrapRate(data.line1_scrap.rate) + '%';

    // Update line 2 data
    document.getElementById('program-2').textContent = data.line2_part.program || 'No Part';
    document.getElementById('part-number-2').textContent = data.line2_part.part_number || 'No Part';
    document.getElementById('part-description-2').textContent = data.line2_part.part_description || 'No Part';
    document.getElementById('quantity-2').textContent = data.line2_production.quantity;
    
    // Update delta 2 with color and sign
    const delta2Element = document.getElementById('delta-2');
    const delta2Value = data.line2_production.delta;
    delta2Element.textContent = (delta2Value > 0 ? '+' : '-') + Math.abs(delta2Value);  // Add + or - sign
    delta2Element.parentElement.classList.toggle('positive', delta2Value > 0);
    
    document.getElementById('scrap-2').textContent = data.line2_scrap.total || '0';
    document.getElementById('scrap-rate-2').textContent = formatScrapRate(data.line2_scrap.rate) + '%';

    // Update totals
    document.getElementById('total-quantity').textContent = data.total_quantity;
    const totalDeltaValue = data.total_delta;
    document.getElementById('total-delta').textContent = (totalDeltaValue > 0 ? '+' : '-') + Math.abs(totalDeltaValue);  // Add + or - sign
    document.getElementById('total-scrap').textContent = data.total_scrap || '0';
    document.getElementById('average-scrap-rate').textContent = formatScrapRate(data.average_scrap_rate) + '%';

    // Update last refresh time
    document.getElementById('last-refresh').textContent = data.current_time;
}

// Helper function to check for new parts and show notifications
function checkForNewParts(data) {
    // Store previous values in window object if not exists
    window.previousLine1 = window.previousLine1 || { program: '', track_id: '' };
    window.previousLine2 = window.previousLine2 || { program: '', track_id: '' };
    
    // Check Line 1 for new part
    if (data.line1_part.track_id && data.line1_part.track_id !== window.previousLine1.track_id) {
        showNotification(
            'Line 1',
            data.line1_part.program,
            data.line1_part.part_number,
            data.line1_part.part_description,
            data.line1_part.track_id
        );
        window.previousLine1 = {
            program: data.line1_part.program,
            track_id: data.line1_part.track_id
        };
    }
    
    // Check Line 2 for new part
    if (data.line2_part.track_id && data.line2_part.track_id !== window.previousLine2.track_id) {
        showNotification(
            'Line 2',
            data.line2_part.program,
            data.line2_part.part_number,
            data.line2_part.part_description,
            data.line2_part.track_id
        );
        window.previousLine2 = {
            program: data.line2_part.program,
            track_id: data.line2_part.track_id
        };
    }
}

// Helper function to show notifications
function showNotification(line, program, partNumber, description, objectId) {
    const notification = document.getElementById('notification');
    const content = notification.querySelector('.notification-content');
    
    // Create notification message with HTML formatting
    const message = `
        <strong>Part Detected!</strong><br>
        <table style="margin-top: 5px;">
            <tr><td><strong>Line:</strong></td><td>${line}</td></tr>
            <tr><td><strong>Program:</strong></td><td>${program}</td></tr>
            <tr><td><strong>Part Number:</strong></td><td>${partNumber}</td></tr>
            <tr><td><strong>Description:</strong></td><td>${description}</td></tr>
            <tr><td><strong>Object ID:</strong></td><td>${objectId}</td></tr>
        </table>
    `;
    
    content.innerHTML = message;
    
    // Show notification
    notification.classList.add('show');
    
    // Hide after 5 seconds
    setTimeout(() => {
        notification.classList.remove('show');
    }, 5000);
}

function updateProductionData(data) {
    // Update line 1 data
    document.getElementById('program-1').textContent = data.line1_part.program || 'No Part';
    document.getElementById('part-number-1').textContent = data.line1_part.part_number || 'No Part';
    document.getElementById('part-description-1').textContent = data.line1_part.part_description || 'No Part';
    document.getElementById('quantity-1').textContent = data.line1_production.quantity;
    
    // Update delta 1 with color and sign
    const delta1Element = document.getElementById('delta-1');
    const delta1Value = data.line1_production.delta;
    delta1Element.textContent = (delta1Value > 0 ? '+' : '-') + Math.abs(delta1Value);  // Add + or - sign
    delta1Element.parentElement.classList.toggle('positive', delta1Value > 0);

    // Update line 2 data
    document.getElementById('program-2').textContent = data.line2_part.program || 'No Part';
    document.getElementById('part-number-2').textContent = data.line2_part.part_number || 'No Part';
    document.getElementById('part-description-2').textContent = data.line2_part.part_description || 'No Part';
    document.getElementById('quantity-2').textContent = data.line2_production.quantity;
    
    // Update delta 2 with color and sign
    const delta2Element = document.getElementById('delta-2');
    const delta2Value = data.line2_production.delta;
    delta2Element.textContent = (delta2Value > 0 ? '+' : '-') + Math.abs(delta2Value);  // Add + or - sign
    delta2Element.parentElement.classList.toggle('positive', delta2Value > 0);

    // Update totals
    document.getElementById('total-quantity').textContent = data.total_quantity;
    const totalDeltaValue = data.total_delta;
    document.getElementById('total-delta').textContent = (totalDeltaValue > 0 ? '+' : '-') + Math.abs(totalDeltaValue);

    // Update last refresh time
    document.getElementById('last-refresh').textContent = data.current_time;

    // Recalculate scrap rates with new production quantities
    const line1Quantity = data.line1_production.quantity;
    const line2Quantity = data.line2_production.quantity;
    
    // Get current scrap totals from the DOM
    const line1ScrapTotal = parseInt(document.getElementById('scrap-1').textContent) || 0;
    const line2ScrapTotal = parseInt(document.getElementById('scrap-2').textContent) || 0;
    
    // Recalculate Line 1 scrap rate
    const line1TotalParts = line1Quantity + line1ScrapTotal;
    const line1ScrapRate = line1TotalParts > 0 ? ((line1ScrapTotal / line1TotalParts) * 100).toFixed(1) : '0.0';
    document.getElementById('scrap-rate-1').textContent = line1ScrapRate + '%';
    
    // Recalculate Line 2 scrap rate
    const line2TotalParts = line2Quantity + line2ScrapTotal;
    const line2ScrapRate = line2TotalParts > 0 ? ((line2ScrapTotal / line2TotalParts) * 100).toFixed(1) : '0.0';
    document.getElementById('scrap-rate-2').textContent = line2ScrapRate + '%';
    
    // Recalculate total scrap rate
    const totalScrap = line1ScrapTotal + line2ScrapTotal;
    const totalProduction = line1Quantity + line2Quantity;
    const totalParts = totalProduction + totalScrap;
    const averageScrapRate = totalParts > 0 ? ((totalScrap / totalParts) * 100).toFixed(1) : '0.0';
    document.getElementById('average-scrap-rate').textContent = averageScrapRate + '%';

    // Update charts
    updateCharts(data);
    
    // Check for new parts
    checkForNewParts(data);
}

function updateScrapData(data) {
    // Get current production quantities from the DOM
    const line1Quantity = parseInt(document.getElementById('quantity-1').textContent) || 0;
    const line2Quantity = parseInt(document.getElementById('quantity-2').textContent) || 0;
    
    // Update Line 1 scrap
    const line1ScrapTotal = data.line1_scrap.total;
    const line1TotalParts = line1Quantity + line1ScrapTotal;
    const line1ScrapRate = line1TotalParts > 0 ? ((line1ScrapTotal / line1TotalParts) * 100).toFixed(1) : '0.0';
    
    document.getElementById('scrap-1').textContent = line1ScrapTotal;
    document.getElementById('scrap-rate-1').textContent = line1ScrapRate + '%';
    
    // Update Line 2 scrap
    const line2ScrapTotal = data.line2_scrap.total;
    const line2TotalParts = line2Quantity + line2ScrapTotal;
    const line2ScrapRate = line2TotalParts > 0 ? ((line2ScrapTotal / line2TotalParts) * 100).toFixed(1) : '0.0';
    
    document.getElementById('scrap-2').textContent = line2ScrapTotal;
    document.getElementById('scrap-rate-2').textContent = line2ScrapRate + '%';
    
    // Update total scrap and calculate average rate
    const totalScrap = data.total_scrap;
    const totalProduction = line1Quantity + line2Quantity;
    const totalParts = totalProduction + totalScrap;
    const averageScrapRate = totalParts > 0 ? ((totalScrap / totalParts) * 100).toFixed(1) : '0.0';
    
    document.getElementById('total-scrap').textContent = totalScrap;
    document.getElementById('average-scrap-rate').textContent = averageScrapRate + '%';
}