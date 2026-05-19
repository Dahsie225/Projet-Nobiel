// JavaScript de base
document.addEventListener('DOMContentLoaded', function() {
    // Fermer les alertes
    const closeButtons = document.querySelectorAll('.alert .close');
    closeButtons.forEach(btn => {
        btn.addEventListener('click', function() {
            this.parentElement.style.display = 'none';
        });
    });

    // Auto-hide alerts après 5 secondes
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.style.transition = 'opacity 0.3s ease';
            alert.style.opacity = '0';
            setTimeout(() => {
                alert.style.display = 'none';
            }, 300);
        }, 5000);
    });

    // ── Navbar hide on scroll down / show on scroll up ──────────────
    (function () {
        var navbar    = document.querySelector('.navbar');
        var lastY     = window.scrollY;
        var threshold = 80;
        var useGsap   = typeof gsap !== 'undefined';

        function showNavbar() {
            if (useGsap) {
                gsap.to(navbar, { yPercent: 0, duration: 0.3, ease: 'power2.out', overwrite: true });
            } else {
                navbar.classList.remove('navbar--hidden');
            }
        }
        function hideNavbar() {
            if (useGsap) {
                gsap.to(navbar, { yPercent: -110, duration: 0.3, ease: 'power2.in', overwrite: true });
            } else {
                navbar.classList.add('navbar--hidden');
            }
        }

        window.addEventListener('scroll', function () {
            var currentY = window.scrollY;
            if (currentY < threshold) {
                showNavbar();
            } else if (currentY > lastY) {
                hideNavbar();
            } else {
                showNavbar();
            }
            lastY = currentY;
        }, { passive: true });
    })();

    // Menu hamburger (mobile)
    const navToggle = document.getElementById('navToggle');
    const navCollapse = document.getElementById('navCollapse');

    if (navToggle && navCollapse) {
        navToggle.addEventListener('click', function() {
            const isOpen = navCollapse.classList.toggle('open');
            navToggle.classList.toggle('active', isOpen);
            navToggle.setAttribute('aria-expanded', isOpen);
        });

        // Fermer le menu en cliquant en dehors
        document.addEventListener('click', function(e) {
            if (!navToggle.contains(e.target) && !navCollapse.contains(e.target)) {
                navCollapse.classList.remove('open');
                navToggle.classList.remove('active');
                navToggle.setAttribute('aria-expanded', 'false');
            }
        });

        // Fermer le menu au redimensionnement (retour desktop)
        window.addEventListener('resize', function() {
            if (window.innerWidth > 768) {
                navCollapse.classList.remove('open');
                navToggle.classList.remove('active');
                navToggle.setAttribute('aria-expanded', 'false');
            }
        });
    }
});
