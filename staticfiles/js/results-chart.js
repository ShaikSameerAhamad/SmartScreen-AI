document.addEventListener('DOMContentLoaded', function() {
    const gaugeCanvas = document.getElementById('gaugeChart');
    
    // Only run the script if the gauge chart canvas exists on the page
    if (gaugeCanvas) {
        // Read the score from the canvas element's data-score attribute
        const improvementScore = parseFloat(gaugeCanvas.dataset.score);

        if (improvementScore !== null && !isNaN(improvementScore)) {
            const ctx = gaugeCanvas.getContext('2d');
            const gaugeValueElement = document.getElementById('gaugeValue');

            // --- Logic to convert improvement score to a value from 0 to 180 ---
            let score = 50 + (improvementScore * 2); // e.g., +10% improvement -> 70 on a 0-100 scale
            score = Math.max(0, Math.min(100, score)); // Clamp between 0 and 100
            
            const needleValue = (score / 100) * 180;

            // Display the text value
            if (improvementScore > 0) {
                gaugeValueElement.textContent = `+${improvementScore.toFixed(1)}% Improved`;
                gaugeValueElement.style.color = '#198754'; // Green
            } else if (improvementScore < 0) {
                gaugeValueElement.textContent = `${improvementScore.toFixed(1)}%`;
                gaugeValueElement.style.color = '#dc3545'; // Red
            } else {
                gaugeValueElement.textContent = `No Change`;
                gaugeValueElement.style.color = '#6c757d'; // Gray
            }

            new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: ['Danger', 'Moderate', 'Good'],
                    datasets: [{
                        data: [33, 34, 33],
                        backgroundColor: ['rgba(220, 53, 69, 0.7)', 'rgba(255, 193, 7, 0.7)', 'rgba(25, 135, 84, 0.7)'],
                        borderColor: '#fff',
                        borderWidth: 2
                    }]
                },
                options: {
                    rotation: -90,
                    circumference: 180,
                    cutout: '60%',
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { display: false },
                        tooltip: { enabled: false }
                    }
                },
                plugins: [{
                    id: 'gaugeNeedle',
                    afterDraw: (chart) => {
                        const { ctx, chartArea } = chart;
                        if (chartArea.bottom && chart.innerRadius) {
                           const { bottom, left, right } = chartArea;
                           const angle = Math.PI + (needleValue / 180) * Math.PI;
                           const cx = (left + right) / 2;
                           const cy = bottom;
                           
                           ctx.save();
                           ctx.translate(cx, cy);
                           ctx.rotate(angle);
                           
                           // Draw Needle
                           ctx.beginPath();
                           ctx.moveTo(0, -5);
                           ctx.lineTo(chart.innerRadius - 10, 0);
                           ctx.lineTo(0, 5);
                           ctx.fillStyle = '#444';
                           ctx.fill();
                           
                           // Draw Needle Circle
                           ctx.beginPath();
                           ctx.arc(0, 0, 8, 0, 2 * Math.PI);
                           ctx.fillStyle = '#444';
                           ctx.fill();
                           
                           ctx.restore();
                        }
                    }
                }]
            });
        }
    }
});
