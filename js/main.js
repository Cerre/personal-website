// Update copyright year
document.getElementById('year').textContent = new Date().getFullYear();

// Optional: Add smooth scrolling for navigation (if you add navigation links later)
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        document.querySelector(this.getAttribute('href')).scrollIntoView({
            behavior: 'smooth'
        });
    });
});

// Optional: Simple animation on scroll - make elements fade in as they come into view
document.addEventListener('DOMContentLoaded', function() {
    // Add this class to any element you want to animate
    const animatedElements = document.querySelectorAll('.project-card, .social-link');
    
    // Simple check if element is in viewport
    const isInViewport = (el) => {
        const rect = el.getBoundingClientRect();
        return (
            rect.top >= 0 &&
            rect.left >= 0 &&
            rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) &&
            rect.right <= (window.innerWidth || document.documentElement.clientWidth)
        );
    };
    
    // Apply initial state
    animatedElements.forEach(el => {
        el.style.opacity = "0";
        el.style.transform = "translateY(20px)";
        el.style.transition = "opacity 0.6s ease, transform 0.6s ease";
    });
    
    // Function to check if elements are in viewport and animate them
    const animateOnScroll = () => {
        animatedElements.forEach(el => {
            if (isInViewport(el)) {
                el.style.opacity = "1";
                el.style.transform = "translateY(0)";
            }
        });
    };
    
    // Run once on load
    animateOnScroll();
    
    // Run on scroll
    window.addEventListener('scroll', animateOnScroll);
}); 