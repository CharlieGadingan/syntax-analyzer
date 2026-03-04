// Interactive elements
document.addEventListener('DOMContentLoaded', function() {
    // Student card click event
    const studentCard = document.getElementById('studentCard');
    if (studentCard) {
        studentCard.addEventListener('click', function() {
            // alert('Opening detailed analytics for Dexter Facelo...');
        });
    }

    // Update due date countdown
    function updateCountdown() {
        const dueDate = new Date('2026-02-15');
        const now = new Date();
        const diffTime = dueDate - now;
        const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
        
        const countdownElement = document.querySelector('.countdown');
        if (countdownElement) {
            if (diffDays > 0) {
                countdownElement.textContent = `${diffDays} days left`;
                countdownElement.style.color = '#f85149';
            } else if (diffDays === 0) {
                countdownElement.textContent = 'Due today';
                countdownElement.style.color = '#f85149';
            } else {
                countdownElement.textContent = `Overdue by ${Math.abs(diffDays)} days`;
                countdownElement.style.color = '#f85149';
            }
        }
    }

    // Update progress circle based on percentage
    function updateProgressCircle() {
        const circle = document.getElementById('progressCircle');
        if (circle) {
            // This would be dynamic in a real app
            const percentage = 75;
            circle.style.background = `conic-gradient(#2ea44f ${percentage}%, #30363d 0)`;
            circle.setAttribute('data-percentage', `${percentage}%`);
        }
    }

    // Format activity times relative to now
    function updateActivityTimes() {
        const activityTimes = document.querySelectorAll('.activity-time');
        const timeData = [
            { text: '8 mins ago', ms: 8 * 60 * 1000 },
            { text: '1 hour ago', ms: 60 * 60 * 1000 },
            { text: '3 hours ago', ms: 3 * 60 * 60 * 1000 }
        ];

        activityTimes.forEach((timeElement, index) => {
            if (index < timeData.length) {
                // Simulate updating time by adding small increments
                const originalTime = new Date(Date.now() - timeData[index].ms);
                const currentTime = new Date();
                const diffMs = currentTime - originalTime;
                
                let displayText;
                if (diffMs < 60000) {
                    displayText = 'just now';
                } else if (diffMs < 3600000) {
                    const minutes = Math.floor(diffMs / 60000);
                    displayText = `${minutes} minute${minutes !== 1 ? 's' : ''} ago`;
                } else if (diffMs < 86400000) {
                    const hours = Math.floor(diffMs / 3600000);
                    displayText = `${hours} hour${hours !== 1 ? 's' : ''} ago`;
                } else {
                    const days = Math.floor(diffMs / 86400000);
                    displayText = `${days} day${days !== 1 ? 's' : ''} ago`;
                }
                
                timeElement.textContent = displayText;
            }
        });
    }

    // Initialize
    updateCountdown();
    updateProgressCircle();
    updateActivityTimes();
    
    // Update activity times every minute
    setInterval(updateActivityTimes, 60000);
    
    // Update countdown every hour
    setInterval(updateCountdown, 3600000);
    
    // Simulate live updates
    setInterval(() => {
        console.log('Checking for updates...');
        // This would fetch real data in a production app
    }, 30000);
});