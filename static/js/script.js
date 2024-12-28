console.log('Production details script loaded');

// Object to store class name counts and quantities
let classNameData = {};
let lastProcessedData = {
    line1: null,
    line2: null
};

// Helper function to format scrap rate
function formatScrapRate(rate) {
    return (rate === undefined || rate === null || isNaN(rate)) ? '0' : rate;
}

function updateProductionDetails(data) {
    if (!data) {
        console.error('No data provided to updateProductionDetails');
        return;
    }

    // Update scrap rates if they're undefined
    if (data.line1_scrap) {
        data.line1_scrap.rate = formatScrapRate(data.line1_scrap.rate);
    }
    if (data.line2_scrap) {
        data.line2_scrap.rate = formatScrapRate(data.line2_scrap.rate);
    }
    if (data.average_scrap_rate === undefined || data.average_scrap_rate === null) {
        data.average_scrap_rate = '0';
    }

    console.log('Updating production details with data:', {
        line1: {
            class_name: data.line1_part?.class_name,
            part_description: data.line1_part?.part_description
        },
        line2: {
            class_name: data.line2_part?.class_name,
            part_description: data.line2_part?.part_description
        }
    });
    
    const detailsList = document.getElementById('part-details-list');
    if (!detailsList) {
        console.error('Could not find part-details-list element');
        return;
    }

    try {
        // Process Line 1
        if (data.line1_part?.class_name) {
            const className = data.line1_part.class_name.trim();
            const currentData = JSON.stringify(data.line1_part);
            
            if (className && className !== 'undefined' && className !== 'null' && 
                currentData !== lastProcessedData.line1) {
                if (!classNameData[className]) {
                    classNameData[className] = {
                        quantity: 0,
                        partDescription: data.line1_part.part_description || 'Unknown Part'
                    };
                }
                classNameData[className].quantity += 1;
                lastProcessedData.line1 = currentData;
                console.log('Updated Line 1 class data:', className, classNameData[className]);
            }
        }

        // Process Line 2
        if (data.line2_part?.class_name) {
            const className = data.line2_part.class_name.trim();
            const currentData = JSON.stringify(data.line2_part);
            
            if (className && className !== 'undefined' && className !== 'null' && 
                currentData !== lastProcessedData.line2) {
                if (!classNameData[className]) {
                    classNameData[className] = {
                        quantity: 0,
                        partDescription: data.line2_part.part_description || 'Unknown Part'
                    };
                }
                classNameData[className].quantity += 1;
                lastProcessedData.line2 = currentData;
                console.log('Updated Line 2 class data:', className, classNameData[className]);
            }
        }

        // Clear and rebuild the list
        detailsList.innerHTML = '';
        
        // Add entries for each class name
        Object.entries(classNameData).forEach(([className, info]) => {
            if (className && className !== 'undefined' && className !== 'null') {
                const item = document.createElement('div');
                item.className = 'part-detail-item';
                item.innerHTML = `
                    <span>${info.partDescription}</span>
                    <span>${info.quantity}</span>
                `;
                detailsList.appendChild(item);
                console.log('Added item to list:', className, info);
            }
        });

        console.log('Final classNameData:', classNameData);
    } catch (error) {
        console.error('Error in updateProductionDetails:', error);
    }
}

// Start polling when the page loads
document.addEventListener('DOMContentLoaded', function() {
    console.log('Production details script loaded, starting data updates');
    
    // Set up WebSocket connection for production details
    const socket = io();
    
    socket.on('connect', function() {
        console.log('WebSocket connected for production details');
    });
    
    socket.on('disconnect', function() {
        console.log('WebSocket disconnected for production details');
    });
    
    socket.on('production_update', function(data) {
        console.log('WebSocket production update received for details:', data);
        updateProductionDetails(data);
    });
    
    // Initial load of production details
    fetch('/production_data')
        .then(response => response.json())
        .then(data => {
            console.log('Initial production details data:', data);
            updateProductionDetails(data);
        })
        .catch(error => console.error('Error fetching initial production details:', error));
}); 