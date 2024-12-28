// Add to your existing socket.on('update') handler
socket.on('update', function(data) {
    // Existing update code
    updateProductionData(data);
    updateScrapData(data);
    updateCharts(data);
    
    // Update production details if data is valid
    if (data && typeof data === 'object') {
        updateProductionDetails(data);
    }
});

function updateProductionDetails(data) {
    const detailsList = document.getElementById('part-details-list');
    if (!detailsList) return;  // Guard against missing element
    
    detailsList.innerHTML = ''; // Clear existing items
    
    // Combine data from both lines
    const partCounts = {};
    
    // Process Line 1
    if (data.line1_production && data.line1_production.part_counts) {
        for (const [part, count] of Object.entries(data.line1_production.part_counts)) {
            partCounts[part] = (partCounts[part] || 0) + count;
        }
    }
    
    // Process Line 2
    if (data.line2_production && data.line2_production.part_counts) {
        for (const [part, count] of Object.entries(data.line2_production.part_counts)) {
            partCounts[part] = (partCounts[part] || 0) + count;
        }
    }
    
    // Create and append items
    for (const [part, count] of Object.entries(partCounts)) {
        const item = document.createElement('div');
        item.className = 'part-detail-item';
        item.innerHTML = `
            <span>${part}</span>
            <span>${count}</span>
        `;
        detailsList.appendChild(item);
    }
} 