document.addEventListener('DOMContentLoaded', () => {
    // Copy to clipboard
    const copyBtn = document.getElementById('copy-btn');
    if (copyBtn) {
        copyBtn.addEventListener('click', () => {
            navigator.clipboard.writeText('pip install agentloopguard').then(() => {
                const originalHTML = copyBtn.innerHTML;
                copyBtn.innerHTML = '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#34d399" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>';
                setTimeout(() => {
                    copyBtn.innerHTML = originalHTML;
                }, 2000);
            });
        });
    }

    // Section Reveal via IntersectionObserver
    const observerOptions = {
        root: null,
        rootMargin: '0px',
        threshold: 0.1
    };

    const observer = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('visible');
                observer.unobserve(entry.target);
            }
        });
    }, observerOptions);

    document.querySelectorAll('.section-reveal').forEach(section => {
        observer.observe(section);
    });

    // Cost counter animation logic (purely visual for demo)
    const costObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                setTimeout(() => {
                    const msg = document.getElementById('intervention-msg');
                    if (msg) msg.style.opacity = '1';
                }, 1500);
                costObserver.unobserve(entry.target);
            }
        });
    }, { threshold: 0.5 });
    
    const problemSection = document.getElementById('problem');
    if (problemSection) {
        // Hide intervention msg initially via script
        const msg = document.getElementById('intervention-msg');
        if(msg) msg.style.opacity = '0';
        if(msg) msg.style.transition = 'opacity 0.3s ease-in';
        costObserver.observe(problemSection);
    }
});
