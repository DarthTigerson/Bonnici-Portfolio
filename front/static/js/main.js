// JavaScript for portfolio website
document.addEventListener('DOMContentLoaded', function() {
    console.log('Portfolio website loaded successfully');
    
    // Animated Background
    initParticleNetworkBackground();
    
    // Read More Button Functionality
    const readMoreBtn = document.getElementById('read-more-btn');
    const expandableContent = document.getElementById('about-expandable');
    
    if (readMoreBtn && expandableContent) {
        readMoreBtn.addEventListener('click', function() {
            if (expandableContent.style.display === 'none') {
                expandableContent.style.display = 'block';
                readMoreBtn.textContent = 'Read Less';
                readMoreBtn.classList.add('expanded');
            } else {
                expandableContent.style.display = 'none';
                readMoreBtn.textContent = 'Read More';
                readMoreBtn.classList.remove('expanded');
            }
        });
    }
    
    // Navigation Functionality
    const navLinks = document.querySelectorAll('.nav-item a');
    const mainPanel = document.querySelector('.main-panel');
    const aboutView = document.getElementById('about-view');
    const contactView = document.getElementById('contact-view');
    
    // Switch between views with smooth transitions
    function switchView(viewId) {
        // Add transitioning class to create a fade out effect
        mainPanel.classList.add('transitioning');
        
        // After fade out animation, switch views and fade back in
        setTimeout(() => {
            // Hide all views
            aboutView.classList.remove('active');
            contactView.classList.remove('active');
            
            // Show the requested view
            if (viewId === '#about') {
                aboutView.classList.add('active');
            } else if (viewId === '#contact') {
                contactView.classList.add('active');
            }
            
            // Remove the transitioning class to fade back in
            setTimeout(() => {
                mainPanel.classList.remove('transitioning');
                
                // Scroll to the top of the panel
                mainPanel.scrollTop = 0;
            }, 50);
        }, 300); // Matches the transition duration from CSS
    }
    
    // Handle navigation clicks
    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            
            // Get the target view id
            const targetId = this.getAttribute('href');
            
            // Only switch if not already on this view
            const isAboutView = targetId === '#about' && aboutView.classList.contains('active');
            const isContactView = targetId === '#contact' && contactView.classList.contains('active');
            
            if (!isAboutView && !isContactView) {
                // Update active nav item
                navLinks.forEach(navLink => {
                    navLink.parentElement.classList.remove('active');
                });
                this.parentElement.classList.add('active');
                
                // Switch to the target view
                switchView(targetId);
            }
        });
    });
    
    // Contact Form Submission
    const contactForm = document.getElementById('contact-form');
    
    if (contactForm) {
        // The form now submits directly to the server with the action and method attributes
        // This code is just to provide feedback to the user after the form is submitted
        contactForm.addEventListener('submit', function(e) {
            // We don't prevent default anymore, letting the form submit normally
            
            // Optionally, you can add form validation here if needed
            console.log('Form submitted via standard HTML form submission');
            
            // Form will be reset automatically after submission and page reload
        });
    }
    
    // Close error notification
    const errorNotification = document.querySelector('.error-notification');
    const closeBtn = document.querySelector('.error-notification .close-btn');
    
    if (errorNotification && closeBtn) {
        closeBtn.addEventListener('click', function() {
            errorNotification.style.display = 'none';
        });
        
        // Auto-hide after 5 seconds
        setTimeout(() => {
            errorNotification.style.display = 'none';
        }, 5000);
    }
});

// Interactive Particle Network Background Animation
function initParticleNetworkBackground() {
    const canvas = document.getElementById('background-canvas');
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    
    // Network settings
    const particleSettings = {
        count: 0, // Will be calculated based on screen size
        color: 'rgba(255, 215, 0, 0.7)', // Gold color for particles
        radius: { min: 1, max: 3 },
        speed: { min: 0.1, max: 0.4 },
        connectionDistance: 150,
        connectionWidth: { min: 0.2, max: 0.8 },
        connectionOpacity: { min: 0.02, max: 0.12 },
        mouseInteractionRadius: 150
    };
    
    // Dark background with slight gradient
    const backgroundColor = {
        start: [18, 18, 18], // Dark background (almost black)
        gradient: 'radial-gradient(circle at 30% 30%, rgba(25, 25, 30, 1) 0%, rgba(18, 18, 18, 1) 70%)'
    };
    
    let particles = [];
    let mousePosition = { x: null, y: null };
    let isMouseMoving = false;
    let mouseTimeout;
    
    // Mouse interaction
    canvas.addEventListener('mousemove', (e) => {
        const rect = canvas.getBoundingClientRect();
        mousePosition.x = e.clientX - rect.left;
        mousePosition.y = e.clientY - rect.top;
        
        // Set flag for mouse movement
        isMouseMoving = true;
        clearTimeout(mouseTimeout);
        
        // Reset after 2 seconds of no movement
        mouseTimeout = setTimeout(() => {
            isMouseMoving = false;
        }, 2000);
    });
    
    // When mouse leaves, gradually reset position
    canvas.addEventListener('mouseleave', () => {
        // Don't set to null immediately, let it fade
        setTimeout(() => {
            mousePosition.x = null;
            mousePosition.y = null;
            isMouseMoving = false;
        }, 1000);
    });
    
    // Resize handler
    function resizeCanvas() {
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
        
        // Create gradient background
        const gradient = ctx.createRadialGradient(
            canvas.width * 0.3, canvas.height * 0.3, 0,
            canvas.width * 0.3, canvas.height * 0.3, canvas.width * 0.7
        );
        gradient.addColorStop(0, 'rgba(25, 25, 30, 1)');
        gradient.addColorStop(1, 'rgba(18, 18, 18, 1)');
        
        // Fill with gradient
        ctx.fillStyle = gradient;
        ctx.fillRect(0, 0, canvas.width, canvas.height);
        
        // Calculate particle count based on screen size
        particleSettings.count = Math.floor((canvas.width * canvas.height) / 10000);
        
        // Recreate particles
        initParticles();
    }
    
    // Create particles
    function initParticles() {
        particles = [];
        
        for (let i = 0; i < particleSettings.count; i++) {
            const radius = Math.random() * (particleSettings.radius.max - particleSettings.radius.min) + particleSettings.radius.min;
            
            // Random position
            const x = Math.random() * canvas.width;
            const y = Math.random() * canvas.height;
            
            // Random movement direction
            const vx = (Math.random() - 0.5) * (particleSettings.speed.max - particleSettings.speed.min) + particleSettings.speed.min;
            const vy = (Math.random() - 0.5) * (particleSettings.speed.max - particleSettings.speed.min) + particleSettings.speed.min;
            
            // Add to particles array
            particles.push({
                x, y,
                vx, vy,
                radius,
                originalRadius: radius,
                color: particleSettings.color,
                drawn: false // Flag to track if the particle was drawn in the current frame
            });
        }
    }
    
    // Calculate distance between two points
    function getDistance(x1, y1, x2, y2) {
        return Math.sqrt(Math.pow(x2 - x1, 2) + Math.pow(y2 - y1, 2));
    }
    
    // Draw connections between particles
    function drawConnections() {
        // Iterate through each particle
        for (let i = 0; i < particles.length; i++) {
            const particle1 = particles[i];
            
            // Connect with other particles if they're close enough
            for (let j = i + 1; j < particles.length; j++) {
                const particle2 = particles[j];
                
                const distance = getDistance(particle1.x, particle1.y, particle2.x, particle2.y);
                
                // Only draw connection if particles are close enough
                if (distance < particleSettings.connectionDistance) {
                    // Calculate opacity based on distance (closer = more opaque)
                    const opacity = 
                        ((particleSettings.connectionDistance - distance) / particleSettings.connectionDistance) * 
                        (particleSettings.connectionOpacity.max - particleSettings.connectionOpacity.min) + 
                        particleSettings.connectionOpacity.min;
                    
                    // Calculate line width based on distance (closer = thicker)
                    const lineWidth = 
                        ((particleSettings.connectionDistance - distance) / particleSettings.connectionDistance) * 
                        (particleSettings.connectionWidth.max - particleSettings.connectionWidth.min) + 
                        particleSettings.connectionWidth.min;
                    
                    // Draw connection line
                    ctx.beginPath();
                    ctx.moveTo(particle1.x, particle1.y);
                    ctx.lineTo(particle2.x, particle2.y);
                    ctx.strokeStyle = `rgba(255, 215, 0, ${opacity})`;
                    ctx.lineWidth = lineWidth;
                    ctx.stroke();
                    
                    // Mark particles as drawn
                    particle1.drawn = true;
                    particle2.drawn = true;
                }
            }
            
            // Check connection with mouse if mouse is present
            if (mousePosition.x && mousePosition.y) {
                const mouseDistance = getDistance(particle1.x, particle1.y, mousePosition.x, mousePosition.y);
                
                if (mouseDistance < particleSettings.mouseInteractionRadius) {
                    // Calculate opacity and width based on distance to mouse
                    const mouseOpacity = 
                        ((particleSettings.mouseInteractionRadius - mouseDistance) / particleSettings.mouseInteractionRadius) * 0.2;
                    
                    const mouseLineWidth = 
                        ((particleSettings.mouseInteractionRadius - mouseDistance) / particleSettings.mouseInteractionRadius) * 1.5;
                    
                    // Draw connection to mouse
                    ctx.beginPath();
                    ctx.moveTo(particle1.x, particle1.y);
                    ctx.lineTo(mousePosition.x, mousePosition.y);
                    ctx.strokeStyle = `rgba(255, 215, 0, ${mouseOpacity})`;
                    ctx.lineWidth = mouseLineWidth;
                    ctx.stroke();
                    
                    // Make particles bigger when near mouse
                    particle1.radius = particle1.originalRadius * (1 + (1 - mouseDistance / particleSettings.mouseInteractionRadius) * 2);
                    
                    // Mark particle as drawn
                    particle1.drawn = true;
                } else {
                    // Reset particle size if not affected by mouse
                    particle1.radius = particle1.originalRadius;
                }
            } else {
                // Reset particle size if mouse is not present
                particle1.radius = particle1.originalRadius;
            }
        }
    }
    
    // Draw and update particles
    function drawParticles() {
        // Reset all particles' drawn flag
        particles.forEach(p => p.drawn = false);
        
        // Draw connections first (which also sets drawn flags)
        drawConnections();
        
        // Then draw and update particles
        particles.forEach(particle => {
            // Draw particle
            ctx.beginPath();
            ctx.arc(particle.x, particle.y, particle.radius, 0, Math.PI * 2);
            
            // Use a slightly brighter color for particles that are connected
            ctx.fillStyle = particle.drawn ? 'rgba(255, 225, 10, 0.8)' : particle.color;
            ctx.fill();
            
            // Update position
            particle.x += particle.vx;
            particle.y += particle.vy;
            
            // Edge bouncing
            if (particle.x < 0 || particle.x > canvas.width) particle.vx = -particle.vx;
            if (particle.y < 0 || particle.y > canvas.height) particle.vy = -particle.vy;
            
            // If mouse is moving, add slight attraction
            if (isMouseMoving && mousePosition.x && mousePosition.y) {
                const dx = mousePosition.x - particle.x;
                const dy = mousePosition.y - particle.y;
                const distance = Math.sqrt(dx * dx + dy * dy);
                
                if (distance < particleSettings.mouseInteractionRadius * 2) {
                    particle.vx += dx * 0.0001;
                    particle.vy += dy * 0.0001;
                    
                    // Apply some speed limit
                    const speed = Math.sqrt(particle.vx * particle.vx + particle.vy * particle.vy);
                    if (speed > particleSettings.speed.max * 1.5) {
                        particle.vx = (particle.vx / speed) * particleSettings.speed.max * 1.5;
                        particle.vy = (particle.vy / speed) * particleSettings.speed.max * 1.5;
                    }
                }
            }
        });
    }
    
    // Animation loop
    function animate() {
        // Create gradient background
        const gradient = ctx.createRadialGradient(
            canvas.width * 0.3, canvas.height * 0.3, 0,
            canvas.width * 0.3, canvas.height * 0.3, canvas.width * 0.7
        );
        gradient.addColorStop(0, 'rgba(25, 25, 30, 1)');
        gradient.addColorStop(1, 'rgba(18, 18, 18, 1)');
        
        // Fill with gradient
        ctx.fillStyle = gradient;
        ctx.fillRect(0, 0, canvas.width, canvas.height);
        
        // Draw network
        drawParticles();
        
        requestAnimationFrame(animate);
    }
    
    // Initialize
    window.addEventListener('resize', resizeCanvas);
    
    resizeCanvas();
    animate();
} 