function initializeStandardsCharts(lineData, barData) {
    // Line Chart (Standards by Year)
    const lineCtx = document.getElementById('standardsByYearChart').getContext('2d');
    new Chart(lineCtx, {
        type: 'line',
        data: {
            labels: lineData.labels,
            datasets: [{
                label: 'Количество проф. стандартов',
                data: lineData.values,
                borderColor: '#36A2EB',
                backgroundColor: 'rgba(54, 162, 235, 0.2)',
                fill: true,
                tension: 0.4,
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
                    text: 'Рост количества профессиональных стандартов по годам'
                }
            },
            scales: {
                x: {
                    title: {
                        display: true,
                        text: 'Год утверждения'
                    }
                },
                y: {
                    title: {
                        display: true,
                        text: 'Количество стандартов'
                    },
                    beginAtZero: true
                }
            }
        }
    });

    // Bar Chart (Standards by Qualification)
    const barCtx = document.getElementById('standardsByQualChart').getContext('2d');
    new Chart(barCtx, {
        type: 'bar',
        data: {
            labels: barData.labels,
            datasets: [{
                label: 'Количество проф. стандартов',
                data: barData.values,
                backgroundColor: [
                    '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF'
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
                    text: 'Количество профессиональных стандартов по квалификациям'
                }
            },
            scales: {
                x: {
                    title: {
                        display: true,
                        text: 'Квалификация'
                    }
                },
                y: {
                    title: {
                        display: true,
                        text: 'Количество стандартов'
                    },
                    beginAtZero: true
                }
            }
        }
    });
}
