document.addEventListener('DOMContentLoaded', function() {
    const scrapForm = document.getElementById('scrap-form');
    const lineSelect = document.getElementById('line-select');
    const programSelect = document.getElementById('program-select');
    const partSelect = document.getElementById('part-select');
    const defectCodeSelect = document.getElementById('defect-code');
    const defectDescriptionSelect = document.getElementById('defect-description');
    const scrapHistoryBody = document.getElementById('scrap-history-body');
    const submitButton = document.querySelector('.submit-button');

    // Function to validate form
    function validateForm() {
        const requiredFields = [
            { element: lineSelect, name: 'Line' },
            { element: programSelect, name: 'Program' },
            { element: partSelect, name: 'Part Number' },
            { element: defectCodeSelect, name: 'Defect Code' },
            { element: defectDescriptionSelect, name: 'Description' }
        ];

        let isValid = true;
        let emptyFields = [];

        requiredFields.forEach(field => {
            if (!field.element.value) {
                isValid = false;
                emptyFields.push(field.name);
                field.element.classList.add('invalid');
            } else {
                field.element.classList.remove('invalid');
            }
        });

        if (!isValid) {
            showNotification(`Please fill in all required fields: ${emptyFields.join(', ')}`, 'error');
        }

        return isValid;
    }

    // Add input event listeners to remove invalid class when user starts typing
    [lineSelect, programSelect, partSelect, defectCodeSelect, defectDescriptionSelect].forEach(element => {
        element.addEventListener('change', function() {
            this.classList.remove('invalid');
        });
    });

    // Handle form submission
    scrapForm.addEventListener('submit', async function(e) {
        e.preventDefault();

        if (!validateForm()) {
            return;
        }

        const formData = {
            line: lineSelect.value,
            program: programSelect.value,
            part_number: partSelect.value,
            defect_code: defectCodeSelect.value,
            defect_description: defectDescriptionSelect.value,
            comments: document.getElementById('comments').value
        };

        try {
            const response = await fetch('/submit_scrap', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(formData)
            });

            if (response.ok) {
                const result = await response.json();
                addScrapHistoryEntry(result);
                scrapForm.reset();
                partSelect.disabled = true;
                showNotification('Scrap report submitted successfully', 'success');
            } else {
                showNotification('Error submitting scrap report', 'error');
            }
        } catch (error) {
            console.error('Error:', error);
            showNotification('Error submitting scrap report', 'error');
        }
    });

    // Function to show notification
    function showNotification(message, type = 'success') {
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.innerHTML = `<p class="notification-content">${message}</p>`;
        document.body.appendChild(notification);

        // Trigger reflow
        notification.offsetHeight;

        // Add show class
        notification.classList.add('show');

        // Remove notification after delay
        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => {
                notification.remove();
            }, 300);
        }, 3000);
    }

    // Function to add a new entry to the history table
    function addScrapHistoryEntry(data) {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${data.time}</td>
            <td>Line ${data.line}</td>
            <td>${data.program}</td>
            <td>${data.part_number}</td>
            <td>${data.defect_code}</td>
            <td>${data.defect_description}</td>
            <td>${data.comments}</td>
        `;
        scrapHistoryBody.insertBefore(row, scrapHistoryBody.firstChild);
    }

    // Load initial data
    loadPrograms();
    loadDefectCodes();
    loadDefectDescriptions();

    // Handle program selection change
    programSelect.addEventListener('change', function() {
        const selectedProgram = this.value;
        if (selectedProgram) {
            loadPartNumbers(selectedProgram);
            partSelect.disabled = false;
        } else {
            partSelect.disabled = true;
            partSelect.innerHTML = '<option value="">Select Part Number</option>';
        }
    });

    // Load programs from BOM
    async function loadPrograms() {
        try {
            const response = await fetch('/get_programs');
            if (response.ok) {
                const programs = await response.json();
                programSelect.innerHTML = '<option value="">Select Program</option>';
                programs.forEach(program => {
                    const option = document.createElement('option');
                    option.value = program;
                    option.textContent = program;
                    programSelect.appendChild(option);
                });
            }
        } catch (error) {
            console.error('Error loading programs:', error);
            showNotification('Error loading programs', 'error');
        }
    }

    // Load part numbers for selected program
    async function loadPartNumbers(program) {
        try {
            const response = await fetch(`/get_parts/${encodeURIComponent(program)}`);
            if (response.ok) {
                const parts = await response.json();
                partSelect.innerHTML = '<option value="">Select Part Number</option>';
                parts.forEach(part => {
                    const option = document.createElement('option');
                    option.value = part.part_number;
                    option.textContent = part.part_number;
                    partSelect.appendChild(option);
                });
            }
        } catch (error) {
            console.error('Error loading part numbers:', error);
            showNotification('Error loading part numbers', 'error');
        }
    }

    // Handle defect code selection change
    defectCodeSelect.addEventListener('change', async function() {
        const selectedCode = this.value;
        if (selectedCode) {
            try {
                const response = await fetch(`/get_description/${encodeURIComponent(selectedCode)}`);
                if (response.ok) {
                    const data = await response.json();
                    defectDescriptionSelect.value = data.description;
                }
            } catch (error) {
                console.error('Error getting description:', error);
            }
        } else {
            defectDescriptionSelect.value = '';
        }
    });

    // Handle description selection change
    defectDescriptionSelect.addEventListener('change', async function() {
        const selectedDescription = this.value;
        if (selectedDescription) {
            try {
                const response = await fetch(`/get_code/${encodeURIComponent(selectedDescription)}`);
                if (response.ok) {
                    const data = await response.json();
                    defectCodeSelect.value = data.code;
                }
            } catch (error) {
                console.error('Error getting code:', error);
            }
        } else {
            defectCodeSelect.value = '';
        }
    });

    // Load defect codes from Scrap Book
    async function loadDefectCodes() {
        try {
            const response = await fetch('/get_defect_codes');
            if (response.ok) {
                const codes = await response.json();
                defectCodeSelect.innerHTML = '<option value="">Select Defect Code</option>';
                codes.forEach(code => {
                    const option = document.createElement('option');
                    option.value = code;
                    option.textContent = code;
                    defectCodeSelect.appendChild(option);
                });
            }
        } catch (error) {
            console.error('Error loading defect codes:', error);
            showNotification('Error loading defect codes', 'error');
        }
    }

    // Load descriptions from Scrap Book
    async function loadDefectDescriptions() {
        try {
            const response = await fetch('/get_defect_descriptions');
            if (response.ok) {
                const descriptions = await response.json();
                defectDescriptionSelect.innerHTML = '<option value="">Select Description</option>';
                descriptions.forEach(description => {
                    const option = document.createElement('option');
                    option.value = description;
                    option.textContent = description;
                    defectDescriptionSelect.appendChild(option);
                });
            }
        } catch (error) {
            console.error('Error loading descriptions:', error);
            showNotification('Error loading descriptions', 'error');
        }
    }

    // Load initial scrap history
    async function loadScrapHistory() {
        try {
            const response = await fetch('/get_scrap_history');
            if (response.ok) {
                const history = await response.json();
                history.forEach(entry => addScrapHistoryEntry(entry));
            }
        } catch (error) {
            console.error('Error loading scrap history:', error);
        }
    }

    // Load history when page loads
    loadScrapHistory();
}); 