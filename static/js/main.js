// --- Theme Toggle ---
const themeToggle = document.getElementById('theme-toggle');
const body = document.body;
const sunIcon = document.getElementById('theme-icon-sun');
const moonIcon = document.getElementById('theme-icon-moon');

// Function to apply theme
function applyTheme(theme) {
    if (theme === 'dark') {
        body.classList.add('dark-mode');
        sunIcon.classList.add('d-none');
        moonIcon.classList.remove('d-none');
    } else {
        body.classList.remove('dark-mode');
        sunIcon.classList.remove('d-none');
        moonIcon.classList.add('d-none');
    }
}

// Check saved theme preference
const savedTheme = localStorage.getItem('theme') || 'light'; // Default to light
applyTheme(savedTheme);

// Toggle button event listener
themeToggle.addEventListener('click', () => {
    let newTheme = body.classList.contains('dark-mode') ? 'light' : 'dark';
    applyTheme(newTheme);
    localStorage.setItem('theme', newTheme); // Save preference
});

// --- Image Zoom Modal ---
// Check if the modal exists before initializing
const imageZoomModalElement = document.getElementById('imageZoomModal');
let imageZoomModal;
if (imageZoomModalElement) {
    imageZoomModal = new bootstrap.Modal(imageZoomModalElement);
}
const zoomedImage = document.getElementById('zoomedImage');
const modalTitle = document.getElementById('imageZoomModalLabel');

// Add click listeners to images that should be zoomable
document.querySelectorAll('.zoomable-image, .table-img').forEach(img => {
    img.style.cursor = 'zoom-in'; // Ensure cursor shows
    img.addEventListener('click', () => {
        if (zoomedImage && modalTitle && imageZoomModal) { // Check if modal elements exist
            zoomedImage.src = img.src; // Set the modal image source
            // Try to get filename from alt text or a data attribute if available
            modalTitle.textContent = img.alt || 'Image Viewer'; // Default title
            imageZoomModal.show();
        } else {
            console.error("Image Zoom Modal elements not found.");
        }
    });
});


// --- Form Loading Spinners ---
document.querySelectorAll('.form-with-loader').forEach(form => {
    // Create spinner overlay div dynamically
    const overlay = document.createElement('div');
    overlay.classList.add('form-loading-overlay');
    overlay.innerHTML = `
        <div class="spinner-border text-primary" role="status">
            <span class="visually-hidden">Loading...</span>
        </div>
    `;
    form.appendChild(overlay); // Append to the form

    form.addEventListener('submit', (e) => {
        // Basic check if form is valid (for required fields)
        if (form.checkValidity()) {
             overlay.classList.add('active'); // Show spinner
             const submitButton = form.querySelector('button[type="submit"]');
             if (submitButton) submitButton.disabled = true;
        } else {
            console.log("Form validation failed, not showing spinner.");
        }
        // NOTE: Spinner will hide automatically on page reload.
    });
});


// --- Chart.js on Results Page ---
const ctx = document.getElementById('resultsChart');

if (ctx && typeof chartData !== 'undefined') {
    // Use English class names from chartData passed by Flask
    const predictedLabels = chartData.predicted_labels || [];
    const predictedValues = chartData.predicted_values || [];

    const chartConfig = {
        type: 'doughnut',
        data: {
            // Map the English labels from Flask data to chart labels
            labels: predictedLabels.map(label => label === 'Defect' ? 'Predicted Defects' : 'Predicted No Defects'),
            datasets: [{
                label: 'Initial Predictions', // Translated dataset label
                data: predictedValues,
                backgroundColor: [
                    'rgba(220, 53, 69, 0.7)', // Danger (Defect)
                    'rgba(25, 135, 84, 0.7)'  // Success (No Defect)
                ],
                borderColor: [
                    'rgba(220, 53, 69, 1)',
                    'rgba(25, 135, 84, 1)'
                ],
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'top',
                    labels: {
                        // Dynamically set color based on theme
                        color: document.body.classList.contains('dark-mode') ? '#f8f9fa' : '#212529'
                    }
                },
                title: {
                    display: true,
                    text: 'Distribution of Initial Predictions', // Translated title
                    // Dynamically set color based on theme
                    color: document.body.classList.contains('dark-mode') ? '#f8f9fa' : '#212529'
                },
                tooltip: { // Optional: Enhance tooltips
                    callbacks: {
                        label: function(context) {
                            let label = context.label || '';
                            if (label) {
                                label += ': ';
                            }
                            if (context.parsed !== null) {
                                label += context.parsed;
                            }
                            // Add percentage calculation
                            const total = context.dataset.data.reduce((acc, value) => acc + value, 0);
                            const percentage = total > 0 ? ((context.parsed / total) * 100).toFixed(1) + '%' : '0%';
                            label += ` (${percentage})`;
                            return label;
                        }
                    }
                }
            }
        }
    };

   const resultsChart = new Chart(ctx, chartConfig);

   // Update chart colors if theme changes
   themeToggle.addEventListener('click', () => {
         const isDark = document.body.classList.contains('dark-mode');
         const textColor = isDark ? '#f8f9fa' : '#212529';
         // Update colors in the chart's options and redraw
         if (resultsChart.options.plugins.legend) { // Check if legend exists
             resultsChart.options.plugins.legend.labels.color = textColor;
         }
         if (resultsChart.options.plugins.title) { // Check if title exists
            resultsChart.options.plugins.title.color = textColor;
         }
         resultsChart.update();
   });

} else if (ctx) {
    console.warn("Chart canvas found, but chartData is missing or undefined.");
    const container = ctx.parentElement;
    // Display user-friendly message if chart data is unavailable
    container.innerHTML = '<p class="text-muted text-center mt-3">Chart data is currently unavailable.</p>';
}
