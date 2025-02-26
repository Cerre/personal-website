// Update copyright year
document.addEventListener('DOMContentLoaded', function() {
    const yearSpan = document.getElementById('year');
    if (yearSpan) {
        yearSpan.textContent = new Date().getFullYear();
    }
});

// Add smooth scrolling for navigation
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        document.querySelector(this.getAttribute('href')).scrollIntoView({
            behavior: 'smooth'
        });
    });
});

// Enhanced animations on scroll and page load
document.addEventListener('DOMContentLoaded', function() {
    // Elements to animate
    const animatedElements = document.querySelectorAll('.project-card, .social-link');
    const headerElements = document.querySelectorAll('.name, .tagline');
    const sectionHeadings = document.querySelectorAll('section h2');
    
    // Enhanced check if element is in viewport with offset
    const isInViewport = (el, offset = 0) => {
        const rect = el.getBoundingClientRect();
        return (
            rect.top <= (window.innerHeight || document.documentElement.clientHeight) - offset &&
            rect.bottom >= 0 &&
            rect.left <= (window.innerWidth || document.documentElement.clientWidth) &&
            rect.right >= 0
        );
    };
    
    // Apply initial states
    animatedElements.forEach(el => {
        el.style.opacity = "0";
        el.style.transform = "translateY(30px)";
        el.style.transition = "opacity 0.7s ease, transform 0.7s ease";
    });
    
    sectionHeadings.forEach(el => {
        el.style.opacity = "0";
        el.style.transform = "translateY(20px)";
        el.style.transition = "opacity 0.8s ease, transform 0.8s ease";
    });
    
    // Staggered animation for header elements
    headerElements.forEach((el, index) => {
        el.style.opacity = "0";
        el.style.transform = "translateY(20px)";
        el.style.transition = "opacity 0.8s ease, transform 0.8s ease";
        
        // Staggered delay
        setTimeout(() => {
            el.style.opacity = "1";
            el.style.transform = "translateY(0)";
        }, 300 + (index * 200));
    });
    
    // Function to animate elements when they enter viewport
    const animateOnScroll = () => {
        // Animate section headings
        sectionHeadings.forEach(el => {
            if (isInViewport(el, 100)) {
                el.style.opacity = "1";
                el.style.transform = "translateY(0)";
            }
        });
        
        // Animate project cards and social links with staggered effect
        let delay = 0;
        animatedElements.forEach(el => {
            if (isInViewport(el, 150)) {
                setTimeout(() => {
                    el.style.opacity = "1";
                    el.style.transform = "translateY(0)";
                }, delay);
                delay += 100; // Increase delay for next element
            }
        });
    };
    
    // Add hover effects for project cards
    document.querySelectorAll('.project-card').forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.transform = "translateY(-10px) scale(1.02)";
            this.style.boxShadow = "0 15px 30px rgba(0, 0, 0, 0.4)";
        });
        
        card.addEventListener('mouseleave', function() {
            this.style.transform = "translateY(0) scale(1)";
            this.style.boxShadow = "0 10px 20px rgba(0, 0, 0, 0.3)";
        });
    });
    
    // Add interactive effects for social links
    document.querySelectorAll('.social-link').forEach(link => {
        link.addEventListener('mouseenter', function() {
            this.style.transform = "translateY(-8px) scale(1.05)";
            this.style.boxShadow = "0 12px 25px rgba(0, 0, 0, 0.4)";
            // Find the icon and add pulse effect
            const icon = this.querySelector('i');
            if (icon) {
                icon.style.transform = "scale(1.1)";
                icon.style.transition = "transform 0.3s ease";
            }
        });
        
        link.addEventListener('mouseleave', function() {
            this.style.transform = "translateY(0) scale(1)";
            this.style.boxShadow = "0 10px 20px rgba(0, 0, 0, 0.3)";
            // Reset icon
            const icon = this.querySelector('i');
            if (icon) {
                icon.style.transform = "scale(1)";
            }
        });
    });
    
    // Run animations on page load
    animateOnScroll();
    
    // Run animations on scroll
    window.addEventListener('scroll', animateOnScroll);
    
    // Optional: Add typing effect to the name (uncomment to enable)
    /*
    const nameElement = document.querySelector('.name');
    if (nameElement) {
        const name = nameElement.textContent;
        nameElement.textContent = '';
        nameElement.style.opacity = "1";
        
        let i = 0;
        const typeEffect = setInterval(() => {
            if (i < name.length) {
                nameElement.textContent += name.charAt(i);
                i++;
            } else {
                clearInterval(typeEffect);
            }
        }, 100);
    }
    */
}); 