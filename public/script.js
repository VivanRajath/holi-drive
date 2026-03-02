/* ============================================
   LCC Holi Color Donation Drive - Script
   ============================================ */

(function () {
    'use strict';

    // --- Configuration ---
    const API_URL = '/api/participate';
    const CAPTION = `I just participated in the LCC Holi Color Donation Drive!
Turning discarded Holi-colored clothes into meaningful donations.
Join the movement and spread the colors of kindness.

#HoliForGood #LCCDrive #LeafClothingCompany`;

    // Pink, yellow, warm Holi-themed colors
    const PARTICLE_COLORS = [
        '#E91E63', '#F48FB1', '#C2185B',
        '#FFB300', '#FFD54F', '#F57F17',
        '#FF7043', '#FF6D00', '#FF9800',
        '#AB47BC', '#F44336', '#FF80AB'
    ];

    // --- DOM Elements ---
    const particlesContainer = document.getElementById('particles-container');
    const form = document.getElementById('participation-form');
    const submitBtn = document.getElementById('submit-btn');
    const badgeSection = document.getElementById('badge-section');
    const badgeImage = document.getElementById('badge-image');
    const downloadBtn = document.getElementById('download-btn');
    const copyCaptionBtn = document.getElementById('copy-caption-btn');
    const copyLinkBtn = document.getElementById('copy-link-btn');
    const shareTwitter = document.getElementById('share-twitter');
    const shareFacebook = document.getElementById('share-facebook');
    const shareWhatsapp = document.getElementById('share-whatsapp');
    const shareLinkedin = document.getElementById('share-linkedin');
    const participateAgainBtn = document.getElementById('participate-again-btn');
    const confettiContainer = document.getElementById('confetti-container');
    const captionText = document.getElementById('caption-text');
    const toast = document.getElementById('toast');
    const toastMessage = document.getElementById('toast-message');

    let currentBadgeBase64 = '';
    let participantName = '';

    // --- Floating Particles ---
    function createParticles() {
        const count = window.innerWidth < 768 ? 12 : 24;

        for (let i = 0; i < count; i++) {
            const particle = document.createElement('div');
            particle.className = 'particle';
            const size = Math.random() * 10 + 3;
            const color = PARTICLE_COLORS[Math.floor(Math.random() * PARTICLE_COLORS.length)];
            const left = Math.random() * 100;
            const duration = Math.random() * 18 + 12;
            const delay = Math.random() * 18;

            particle.style.cssText = `
                width: ${size}px;
                height: ${size}px;
                background: ${color};
                left: ${left}%;
                animation-duration: ${duration}s;
                animation-delay: ${delay}s;
            `;
            particlesContainer.appendChild(particle);
        }
    }

    // --- Toast Notification ---
    function showToast(message, duration = 3000) {
        toastMessage.textContent = message;
        toast.classList.remove('hidden');
        void toast.offsetWidth;
        toast.classList.add('show');

        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => toast.classList.add('hidden'), 400);
        }, duration);
    }

    // --- Form Validation ---
    function validateForm() {
        let valid = true;
        const name = document.getElementById('name');
        const email = document.getElementById('email');
        const nameError = document.getElementById('name-error');
        const emailError = document.getElementById('email-error');

        nameError.textContent = '';
        emailError.textContent = '';

        if (!name.value.trim()) {
            nameError.textContent = 'Please enter your full name';
            valid = false;
        }

        if (!email.value.trim()) {
            emailError.textContent = 'Please enter your email address';
            valid = false;
        } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.value.trim())) {
            emailError.textContent = 'Please enter a valid email address';
            valid = false;
        }

        return valid;
    }

    // --- Holi Splash Effect ---
    function triggerSplashEffect() {
        const overlay = document.createElement('div');
        overlay.className = 'splash-overlay';
        document.body.appendChild(overlay);

        for (let i = 0; i < 6; i++) {
            const circle = document.createElement('div');
            circle.className = 'splash-circle';
            const color = PARTICLE_COLORS[Math.floor(Math.random() * PARTICLE_COLORS.length)];
            const size = Math.random() * 180 + 80;
            circle.style.cssText = `
                width: ${size}px;
                height: ${size}px;
                background: ${color};
                top: ${Math.random() * 100}%;
                left: ${Math.random() * 100}%;
                animation-delay: ${i * 0.1}s;
            `;
            overlay.appendChild(circle);
        }

        setTimeout(() => overlay.remove(), 1500);
    }

    // --- Confetti Effect ---
    function triggerConfetti() {
        for (let i = 0; i < 50; i++) {
            const piece = document.createElement('div');
            piece.className = 'confetti-piece';
            const color = PARTICLE_COLORS[Math.floor(Math.random() * PARTICLE_COLORS.length)];
            const left = Math.random() * 100;
            const duration = Math.random() * 2 + 1.5;
            const delay = Math.random() * 0.8;
            const rotation = Math.random() * 360;

            piece.style.cssText = `
                background: ${color};
                left: ${left}%;
                top: -10px;
                animation-duration: ${duration}s;
                animation-delay: ${delay}s;
                transform: rotate(${rotation}deg);
                width: ${Math.random() * 10 + 5}px;
                height: ${Math.random() * 10 + 5}px;
                border-radius: ${Math.random() > 0.5 ? '50%' : '2px'};
            `;
            confettiContainer.appendChild(piece);
        }

        setTimeout(() => {
            confettiContainer.innerHTML = '';
        }, 4000);
    }

    // --- Form Submission ---
    async function handleSubmit(e) {
        e.preventDefault();

        if (!validateForm()) return;

        const formData = {
            name: document.getElementById('name').value.trim(),
            email: document.getElementById('email').value.trim(),
            phone: document.getElementById('phone').value.trim(),
            city: document.getElementById('city').value.trim()
        };

        participantName = formData.name;

        submitBtn.disabled = true;
        submitBtn.classList.add('loading');

        triggerSplashEffect();

        try {
            const response = await fetch(API_URL, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(formData)
            });

            // read full body as text once (avoid consuming stream twice)
            const text = await response.text();
            let data;
            try {
                data = JSON.parse(text);
            } catch (err) {
                console.error('Non-JSON response body:', text);
                throw err; // propagate so upper catch handles it
            }

            if (!response.ok) {
                throw new Error(data.error || 'Something went wrong');
            }

            currentBadgeBase64 = data.badge;
            badgeImage.src = `data:image/png;base64,${data.badge}`;

            badgeSection.classList.remove('hidden');

            setTimeout(() => {
                badgeSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }, 300);

            setTimeout(triggerConfetti, 500);

            if (data.email_sent) {
                showToast('Badge generated and emailed to you!');
            } else {
                showToast('Badge generated successfully!');
            }

        } catch (error) {
            console.error('Submission error:', error);
            showToast('Error: ' + error.message, 4000);
        } finally {
            submitBtn.disabled = false;
            submitBtn.classList.remove('loading');
        }
    }

    // --- Download Badge ---
    function downloadBadge() {
        if (!currentBadgeBase64) return;

        const link = document.createElement('a');
        link.href = `data:image/png;base64,${currentBadgeBase64}`;
        link.download = `LCC_Holi_Badge_${participantName.replace(/\s+/g, '_')}.png`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);

        showToast('Badge downloaded!');
    }

    // --- Copy Caption ---
    function copyCaption() {
        navigator.clipboard.writeText(CAPTION).then(() => {
            showToast('Caption copied to clipboard!');
        }).catch(() => {
            const textarea = document.createElement('textarea');
            textarea.value = CAPTION;
            document.body.appendChild(textarea);
            textarea.select();
            document.execCommand('copy');
            document.body.removeChild(textarea);
            showToast('Caption copied to clipboard!');
        });
    }

    function copyLink() {
        const textToCopy = `${CAPTION}\n\n${window.location.href}`;
        navigator.clipboard.writeText(textToCopy).then(() => {
            showToast('Link and caption copied!');
        }).catch(() => {
            const textarea = document.createElement('textarea');
            textarea.value = textToCopy;
            document.body.appendChild(textarea);
            textarea.select();
            document.execCommand('copy');
            document.body.removeChild(textarea);
            showToast('Link and caption copied!');
        });
    }

    // --- Social Sharing ---
    function shareOnTwitter() {
        const text = encodeURIComponent(CAPTION);
        window.open(`https://twitter.com/intent/tweet?text=${text}`, '_blank');
    }

    function shareOnFacebook() {
        const url = encodeURIComponent(window.location.href);
        window.open(`https://www.facebook.com/sharer/sharer.php?u=${url}`, '_blank');
    }

    function shareOnWhatsApp() {
        const text = encodeURIComponent(CAPTION + '\n\n' + window.location.href);
        window.open(`https://wa.me/?text=${text}`, '_blank');
    }

    function shareOnLinkedIn() {
        const url = encodeURIComponent(window.location.href);
        window.open(`https://www.linkedin.com/sharing/share-offsite/?url=${url}`, '_blank');
    }

    // --- Participate Again ---
    function participateAgain() {
        badgeSection.classList.add('hidden');
        form.reset();
        currentBadgeBase64 = '';
        participantName = '';

        document.getElementById('participate').scrollIntoView({ behavior: 'smooth' });
    }

    // --- Smooth Scroll for CTA ---
    function handleCTAClick(e) {
        e.preventDefault();
        document.getElementById('participate').scrollIntoView({ behavior: 'smooth' });
    }

    // --- Intersection Observer for Animations ---
    function setupScrollAnimations() {
        const observer = new IntersectionObserver(
            (entries) => {
                entries.forEach((entry) => {
                    if (entry.isIntersecting) {
                        entry.target.style.opacity = '1';
                        entry.target.style.transform = 'translateY(0)';
                    }
                });
            },
            { threshold: 0.1, rootMargin: '0px 0px -50px 0px' }
        );

        document.querySelectorAll('.step-card').forEach((card) => {
            card.style.opacity = '0';
            card.style.transform = 'translateY(30px)';
            card.style.transition = `opacity 0.6s ease ${card.style.getPropertyValue('--delay')}, transform 0.6s ease ${card.style.getPropertyValue('--delay')}`;
            observer.observe(card);
        });
    }

    // --- Initialize ---
    function init() {
        createParticles();
        setupScrollAnimations();

        form.addEventListener('submit', handleSubmit);
        downloadBtn.addEventListener('click', downloadBadge);
        copyCaptionBtn.addEventListener('click', copyCaption);
        shareTwitter.addEventListener('click', shareOnTwitter);
        shareFacebook.addEventListener('click', shareOnFacebook);
        shareWhatsapp.addEventListener('click', shareOnWhatsApp);
        shareLinkedin.addEventListener('click', shareOnLinkedIn);
        copyLinkBtn && copyLinkBtn.addEventListener('click', copyLink);
        participateAgainBtn.addEventListener('click', participateAgain);

        const ctaBtn = document.getElementById('cta-participate');
        ctaBtn.addEventListener('click', handleCTAClick);

        captionText.textContent = CAPTION;
        const shareableLink = document.getElementById('shareable-link');
        if (shareableLink) {
            shareableLink.textContent = window.location.href;
            shareableLink.href = window.location.href;
        }
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
