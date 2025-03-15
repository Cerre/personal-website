// Main script.js file

// Initialize any event listeners
document.addEventListener('DOMContentLoaded', function() {
    // Theme toggle functionality if needed
    const themeToggle = document.getElementById('themeToggle');
    if (themeToggle) {
        themeToggle.addEventListener('click', function() {
            document.body.classList.toggle('dark-theme');
            // Save preference to localStorage
            const isDarkTheme = document.body.classList.contains('dark-theme');
            localStorage.setItem('darkTheme', isDarkTheme);
        });
        
        // Check for saved theme preference
        const savedTheme = localStorage.getItem('darkTheme');
        if (savedTheme === 'true') {
            document.body.classList.add('dark-theme');
        }
    }
    
    // Add more initialization code as needed
}); 