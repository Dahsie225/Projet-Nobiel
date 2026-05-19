/**
 * three-scene.js — Nobiel
 * Remplace la scène 3D du hero par une illustration statique
 * du soleil levant, avec un léger effet de parallaxe.
 */
(function () {
    'use strict';

    var heroEl = document.querySelector('.hero');
    if (!heroEl) return;

    var existingVisual = document.getElementById('hero-3d-canvas');
    if (existingVisual) {
        existingVisual.remove();
    }

    var image = document.createElement('img');
    image.id = 'hero-3d-canvas';
    image.className = 'hero-illustration';
    image.src = '/static/images/nazz.png';
    image.alt = 'Illustration du soleil levant Nobiel';
    image.decoding = 'async';
    image.loading = 'eager';
    image.setAttribute('aria-hidden', 'true');

    heroEl.insertBefore(image, heroEl.firstChild);

    var hasLoaded = false;

    function syncOpacity() {
        if (!hasLoaded) return;
        image.style.opacity = mediaQuery.matches ? '0.26' : '1';
    }

    image.addEventListener('load', function () {
        hasLoaded = true;
        syncOpacity();
    }, { once: true });

    var mediaQuery = window.matchMedia('(max-width: 768px)');
    var targetX = 0;
    var targetY = 0;
    var currentX = 0;
    var currentY = 0;
    var rafId = null;

    function applyLayout() {
        if (mediaQuery.matches) {
            image.style.right = '4%';
            image.style.top = '78%';
            image.style.width = 'min(48vw, 220px)';
            image.style.maxWidth = '48vw';
        } else {
            image.style.right = 'clamp(24px, 7vw, 96px)';
            image.style.top = '50%';
            image.style.width = 'clamp(360px, 34vw, 560px)';
            image.style.maxWidth = '44%';
        }

        syncOpacity();
    }

    function render() {
        currentX += (targetX - currentX) * 0.08;
        currentY += (targetY - currentY) * 0.08;
        image.style.transform = 'translate3d(' + currentX.toFixed(2) + 'px, calc(-50% + ' + currentY.toFixed(2) + 'px), 0)';
        rafId = window.requestAnimationFrame(render);
    }

    window.addEventListener('mousemove', function (event) {
        if (mediaQuery.matches) {
            targetX = 0;
            targetY = 0;
            return;
        }
        targetX = (event.clientX / window.innerWidth - 0.5) * -18;
        targetY = (event.clientY / window.innerHeight - 0.5) * -12;
    }, { passive: true });

    mediaQuery.addEventListener('change', function () {
        targetX = 0;
        targetY = 0;
        applyLayout();
    });

    applyLayout();
    rafId = window.requestAnimationFrame(render);

    window.addEventListener('beforeunload', function () {
        if (rafId !== null) {
            window.cancelAnimationFrame(rafId);
        }
    }, { once: true });
})();
