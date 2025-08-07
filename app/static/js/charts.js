/**
 * Chart.js configurations and utilities
 */

// Default chart colors (Replit dark theme compatible)
const CHART_COLORS = {
    primary: '#0969da',
    success: '#1a7f37',
    danger: '#cf222e',
    warning: '#bf8700',
    info: '#0550ae',
    light: '#f6f8fa',
    dark: '#24292f'
};

// Chart default options
const DEFAULT_CHART_OPTIONS = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
        legend: {
            labels: {
                color: '#f6f8fa',
                font: {
                    family: '-apple-system, BlinkMacSystemFont, "Segoe UI", "Noto Sans", Helvetica, Arial, sans-serif'
                }
            }
        },
        tooltip: {
            backgroundColor: 'rgba(36, 41, 47, 0.9)',
            titleColor: '#f6f8fa',
            bodyColor: '#f6f8fa',
            borderColor: '#30363d',
            borderWidth: 1
        }
    },
    scales: {
        x: {
            ticks: {
                color: '#8b949e'
            },
            grid: {
                color: '#30363d'
            }
        },
        y: {
            ticks: {
                color: '#8b949e'
            },
            grid: {
                color: '#30363d'
            }
        }
    }
};

/**
 * Create a progress doughnut chart
 */
function createProgressChart(elementId, correct, total, label = 'Progress') {
    const ctx = document.getElementById(elementId);
    if (!ctx) return null;
    
    const incorrect = total - correct;
    const percentage = total > 0 ? Math.round((correct / total) * 100) : 0;
    
    return new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Correct', 'Incorrect'],
            datasets: [{
                data: [correct, incorrect],
                backgroundColor: [CHART_COLORS.success, CHART_COLORS.danger],
                borderWidth: 0,
                cutout: '70%'
            }]
        },
        options: {
            ...DEFAULT_CHART_OPTIONS,
            plugins: {
                ...DEFAULT_CHART_OPTIONS.plugins,
                legend: {
                    position: 'bottom'
                },
                tooltip: {
                    ...DEFAULT_CHART_OPTIONS.plugins.tooltip,
                    callbacks: {
                        label: function(context) {
                            const label = context.label || '';
                            const value = context.parsed;
                            const percentage = total > 0 ? Math.round((value / total) * 100) : 0;
                            return `${label}: ${value} (${percentage}%)`;
                        }
                    }
                }
            },
            // Add center text
            elements: {
                center: {
                    text: `${percentage}%`,
                    color: '#f6f8fa',
                    fontStyle: 'Arial',
                    sidePadding: 20,
                    minFontSize: 20,
                    lineHeight: 25
                }
            }
        }
    });
}

/**
 * Create a subject performance radar chart
 */
function createSubjectRadarChart(elementId, subjectData) {
    const ctx = document.getElementById(elementId);
    if (!ctx) return null;
    
    const subjects = Object.keys(subjectData);
    const accuracies = subjects.map(subject => subjectData[subject].accuracy * 100);
    
    return new Chart(ctx, {
        type: 'radar',
        data: {
            labels: subjects,
            datasets: [{
                label: 'Accuracy %',
                data: accuracies,
                borderColor: CHART_COLORS.primary,
                backgroundColor: `${CHART_COLORS.primary}20`,
                pointBackgroundColor: CHART_COLORS.primary,
                pointBorderColor: '#fff',
                pointHoverBackgroundColor: '#fff',
                pointHoverBorderColor: CHART_COLORS.primary,
                fill: true
            }]
        },
        options: {
            ...DEFAULT_CHART_OPTIONS,
            scales: {
                r: {
                    angleLines: {
                        color: '#30363d'
                    },
                    grid: {
                        color: '#30363d'
                    },
                    pointLabels: {
                        color: '#f6f8fa'
                    },
                    ticks: {
                        color: '#8b949e',
                        backdropColor: 'transparent'
                    },
                    min: 0,
                    max: 100
                }
            }
        }
    });
}

/**
 * Create a time-based line chart
 */
function createTimelineChart(elementId, timeData, label = 'Performance') {
    const ctx = document.getElementById(elementId);
    if (!ctx) return null;
    
    return new Chart(ctx, {
        type: 'line',
        data: {
            labels: timeData.labels,
            datasets: [{
                label: label,
                data: timeData.values,
                borderColor: CHART_COLORS.primary,
                backgroundColor: `${CHART_COLORS.primary}20`,
                fill: true,
                tension: 0.4,
                pointRadius: 4,
                pointHoverRadius: 6
            }]
        },
        options: {
            ...DEFAULT_CHART_OPTIONS,
            plugins: {
                ...DEFAULT_CHART_OPTIONS.plugins,
                legend: {
                    display: false
                }
            }
        }
    });
}

/**
 * Create a bar chart for topic comparison
 */
function createTopicBarChart(elementId, topicData) {
    const ctx = document.getElementById(elementId);
    if (!ctx) return null;
    
    const topics = Object.keys(topicData);
    const accuracies = topics.map(topic => topicData[topic] * 100);
    
    // Color bars based on performance
    const backgroundColors = accuracies.map(accuracy => {
        if (accuracy >= 80) return CHART_COLORS.success;
        if (accuracy >= 60) return CHART_COLORS.warning;
        return CHART_COLORS.danger;
    });
    
    return new Chart(ctx, {
        type: 'bar',
        data: {
            labels: topics,
            datasets: [{
                label: 'Accuracy %',
                data: accuracies,
                backgroundColor: backgroundColors,
                borderWidth: 0,
                borderRadius: 4
            }]
        },
        options: {
            ...DEFAULT_CHART_OPTIONS,
            plugins: {
                ...DEFAULT_CHART_OPTIONS.plugins,
                legend: {
                    display: false
                }
            },
            scales: {
                ...DEFAULT_CHART_OPTIONS.scales,
                y: {
                    ...DEFAULT_CHART_OPTIONS.scales.y,
                    min: 0,
                    max: 100
                }
            }
        }
    });
}

/**
 * Create streak chart
 */
function createStreakChart(elementId, streakData) {
    const ctx = document.getElementById(elementId);
    if (!ctx) return null;
    
    return new Chart(ctx, {
        type: 'line',
        data: {
            labels: streakData.dates,
            datasets: [{
                label: 'Daily Streak',
                data: streakData.streaks,
                borderColor: CHART_COLORS.warning,
                backgroundColor: `${CHART_COLORS.warning}20`,
                fill: true,
                stepped: true,
                pointRadius: 3,
                pointHoverRadius: 5
            }]
        },
        options: {
            ...DEFAULT_CHART_OPTIONS,
            plugins: {
                ...DEFAULT_CHART_OPTIONS.plugins,
                legend: {
                    display: false
                }
            }
        }
    });
}

/**
 * Update chart data
 */
function updateChart(chart, newData) {
    if (!chart || !newData) return;
    
    chart.data = newData;
    chart.update('none'); // No animation for performance
}

/**
 * Destroy chart safely
 */
function destroyChart(chart) {
    if (chart && typeof chart.destroy === 'function') {
        chart.destroy();
    }
}

/**
 * Create a simple metric card chart
 */
function createMetricCard(elementId, value, label, trend = null) {
    const element = document.getElementById(elementId);
    if (!element) return;
    
    const trendIcon = trend > 0 ? '↗' : trend < 0 ? '↘' : '→';
    const trendColor = trend > 0 ? CHART_COLORS.success : trend < 0 ? CHART_COLORS.danger : CHART_COLORS.info;
    
    element.innerHTML = `
        <div class="metric-value">${value}</div>
        <div class="metric-label">${label}</div>
        ${trend !== null ? `<div class="metric-trend" style="color: ${trendColor}">${trendIcon} ${Math.abs(trend)}%</div>` : ''}
    `;
}

/**
 * Initialize charts based on data attributes
 */
function initializeChartsFromData() {
    // Auto-initialize charts with data attributes
    document.querySelectorAll('[data-chart]').forEach(element => {
        const chartType = element.dataset.chart;
        const chartData = JSON.parse(element.dataset.chartData || '{}');
        
        switch (chartType) {
            case 'progress':
                createProgressChart(element.id, chartData.correct, chartData.total);
                break;
            case 'radar':
                createSubjectRadarChart(element.id, chartData);
                break;
            case 'timeline':
                createTimelineChart(element.id, chartData);
                break;
            case 'bar':
                createTopicBarChart(element.id, chartData);
                break;
            case 'streak':
                createStreakChart(element.id, chartData);
                break;
        }
    });
}

// Chart.js plugin for center text in doughnut charts
Chart.register({
    id: 'centerText',
    afterDraw: function(chart) {
        if (chart.config.options.elements && chart.config.options.elements.center) {
            const centerConfig = chart.config.options.elements.center;
            const ctx = chart.ctx;
            
            const centerX = (chart.chartArea.left + chart.chartArea.right) / 2;
            const centerY = (chart.chartArea.top + chart.chartArea.bottom) / 2;
            
            ctx.save();
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';
            ctx.font = `${centerConfig.minFontSize}px ${centerConfig.fontStyle}`;
            ctx.fillStyle = centerConfig.color;
            ctx.fillText(centerConfig.text, centerX, centerY);
            ctx.restore();
        }
    }
});

// Initialize charts when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeChartsFromData();
});

// Export for use in other scripts
window.Charts = {
    createProgressChart,
    createSubjectRadarChart,
    createTimelineChart,
    createTopicBarChart,
    createStreakChart,
    createMetricCard,
    updateChart,
    destroyChart,
    CHART_COLORS
};