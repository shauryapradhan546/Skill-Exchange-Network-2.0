document.addEventListener('DOMContentLoaded', function () {
    initializeCounters();
    initializeAnimations();
    initializeFormValidation();
    initializeNavbar();
    initializeParticles();
    initializeTooltips();
});


function initializeCounters() {
    const counters = document.querySelectorAll('.live-counter, .stat-number');

    const animateCounter = (element) => {
        const target = parseInt(element.textContent) || 0;
        const duration = 2000;
        const startTime = Date.now();

        const updateCounter = () => {
            const elapsed = Date.now() - startTime;
            const progress = Math.min(elapsed / duration, 1);
            const easeOutQuart = 1 - Math.pow(1 - progress, 4);
            const current = Math.floor(target * easeOutQuart);
            element.textContent = current;
            if (progress < 1) {
                requestAnimationFrame(updateCounter);
            } else {
                element.textContent = target;
            }
        };

        updateCounter();
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting && !entry.target.dataset.animated) {
                animateCounter(entry.target);
                entry.target.dataset.animated = 'true';
            }
        });
    }, { threshold: 0.5 });

    counters.forEach(counter => observer.observe(counter));
}


function initializeAnimations() {
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
        });
    });

    const shapes = document.querySelectorAll('.shape');
    if (shapes.length > 0) {
        let ticking = false;
        document.addEventListener('mousemove', (e) => {
            if (!ticking) {
                window.requestAnimationFrame(() => {
                    const mouseX = e.clientX / window.innerWidth;
                    const mouseY = e.clientY / window.innerHeight;
                    shapes.forEach((shape, index) => {
                        const speed = (index + 1) * 0.02;
                        shape.style.transform = `translate(${mouseX * speed * 100}px, ${mouseY * speed * 100}px)`;
                    });
                    ticking = false;
                });
                ticking = true;
            }
        });
    }
}


function initializeNavbar() {
    const navbar = document.querySelector('.navbar');
    if (!navbar) return;
    window.addEventListener('scroll', () => {
        navbar.classList.toggle('scrolled', window.pageYOffset > 50);
    });
}


function initializeFormValidation() {
    document.querySelectorAll('form').forEach(form => {
        form.addEventListener('submit', function () {
            const submitBtn = form.querySelector('button[type="submit"]');
            if (submitBtn && !submitBtn.disabled) {
                const originalText = submitBtn.innerHTML;
                submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Processing...';
                submitBtn.disabled = true;
                setTimeout(() => {
                    submitBtn.innerHTML = originalText;
                    submitBtn.disabled = false;
                }, 5000);
            }
        });
    });
}


function initializeParticles() {
    const heroSection = document.querySelector('.hero-section');
    if (!heroSection) return;

    const particlesContainer = document.createElement('div');
    particlesContainer.className = 'particles-container';
    particlesContainer.style.cssText = `
        position: absolute; top: 0; left: 0;
        width: 100%; height: 100%;
        overflow: hidden; pointer-events: none; z-index: 1;
    `;
    heroSection.appendChild(particlesContainer);

    for (let i = 0; i < 30; i++) {
        const particle = document.createElement('div');
        particle.style.cssText = `
            position: absolute;
            width: ${Math.random() * 4 + 2}px;
            height: ${Math.random() * 4 + 2}px;
            background: rgba(255, 255, 255, ${Math.random() * 0.5 + 0.2});
            border-radius: 50%;
            top: ${Math.random() * 100}%;
            left: ${Math.random() * 100}%;
            animation: float ${Math.random() * 10 + 10}s linear infinite;
            animation-delay: ${Math.random() * 5}s;
        `;
        particlesContainer.appendChild(particle);
    }
}


function initializeTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    if (typeof bootstrap !== 'undefined') {
        tooltipTriggerList.map(el => new bootstrap.Tooltip(el));
    }
}


function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `premium-notification ${type}`;
    notification.innerHTML = `
        <div class="notification-content">
            <i class="fas ${getNotificationIcon(type)} me-2"></i>
            <span>${message}</span>
        </div>
        <button class="notification-close" onclick="this.parentElement.remove()">
            <i class="fas fa-times"></i>
        </button>
    `;
    document.body.appendChild(notification);
    setTimeout(() => notification.classList.add('show'), 10);
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => notification.remove(), 300);
    }, 5000);
}

function getNotificationIcon(type) {
    const icons = {
        success: 'fa-check-circle',
        error: 'fa-exclamation-circle',
        warning: 'fa-exclamation-triangle',
        info: 'fa-info-circle'
    };
    return icons[type] || icons.info;
}


function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}


const customStyles = document.createElement('style');
customStyles.textContent = `
    .premium-notification {
        position: fixed;
        top: 100px;
        right: -400px;
        min-width: 350px;
        max-width: 450px;
        padding: 1.2rem 1.5rem;
        background: var(--bg-card, rgba(255, 255, 255, 0.97));
        backdrop-filter: blur(20px);
        border-radius: 16px;
        box-shadow: 0 10px 40px rgba(0,0,0,0.2);
        z-index: 9999;
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        display: flex;
        align-items: center;
        justify-content: space-between;
        border-left: 4px solid #667eea;
    }
    .premium-notification.show { right: 20px; }
    .premium-notification.success { border-left-color: #4facfe; }
    .premium-notification.error { border-left-color: #fa709a; }
    .premium-notification.warning { border-left-color: #fee140; }
    .notification-content {
        display: flex; align-items: center;
        color: var(--text-main, #2d3748); font-weight: 600; flex: 1;
    }
    .notification-close {
        background: none; border: none;
        color: #2d3748; opacity: 0.5;
        cursor: pointer; padding: 0.5rem;
        transition: opacity 0.2s;
    }
    .notification-close:hover { opacity: 1; }
    @keyframes float {
        0%, 100% { transform: translateY(0) translateX(0); opacity: 0; }
        10%, 90% { opacity: 1; }
        50% { transform: translateY(-100vh) translateX(50px); }
    }
`;
document.head.appendChild(customStyles);
