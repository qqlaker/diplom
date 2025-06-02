function initializeProfilesChart(data) {
    const ctx = document.getElementById('profilesChart').getContext('2d');
    new Chart(ctx, {
        type: 'pie',
        data: {
            labels: data.labels,
            datasets: [{
                data: data.values,
                backgroundColor: [
                    '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF',
                    '#FF9F40', '#C9CBCF', '#7BC043', '#D81B60', '#3F51B5'
                ],
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'top',
                },
                title: {
                    display: true,
                    text: 'Распределение профилей по программам'
                }
            }
        }
    });
}

document.addEventListener('DOMContentLoaded', () => {
    const standardsSection = document.getElementById('standards-section');
    const detailsSection = document.getElementById('details-section');
    const detailsBody = document.getElementById('details-body');

    document.querySelectorAll('.show-standards').forEach(button => {
        button.addEventListener('click', () => {
            const programId = button.dataset.programId;
            // Hide all standards tbody elements
            document.querySelectorAll('.standards-data').forEach(tbody => {
                tbody.style.display = 'none';
            });
            // Show standards for the selected program
            const standardsTbody = document.querySelector(`.standards-data[data-program-id="${programId}"]`);
            if (standardsTbody) {
                standardsTbody.style.display = '';
            }
            standardsSection.style.display = 'block';
            detailsSection.style.display = 'none';
            // Smooth scroll to standards section
            standardsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
        });
    });

    document.querySelectorAll('.show-details').forEach(button => {
        button.addEventListener('click', () => {
            const programId = button.dataset.programId;
            // Hide all details rows
            detailsBody.querySelectorAll('.details-data').forEach(row => {
                row.style.display = 'none';
            });
            // Show details for the selected program
            const detailsRows = detailsBody.querySelectorAll(`.details-data[data-program-id="${programId}"]`);
            detailsRows.forEach(row => {
                row.style.display = '';
            });
            detailsSection.style.display = 'block';
            standardsSection.style.display = 'none';
            // Smooth scroll to details section
            detailsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
        });
    });
});
