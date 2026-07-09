/* ==========================================================================
   DINO SMART - PREMIUM INTERACTIVE ENGINE
   Lenis Smooth Scroll + GSAP ScrollTrigger + Interactive Mascot Companion
   ========================================================================== */

document.addEventListener("DOMContentLoaded", () => {
    
    // 1. Initialize Lenis Smooth Scroll
    const lenis = new Lenis({
        duration: 1.2,
        easing: (t) => Math.min(1, 1.001 - Math.pow(2, -10 * t)),
        orientation: 'vertical',
        gestureOrientation: 'vertical',
        smoothWheel: true,
        wheelMultiplier: 1,
        touchMultiplier: 2,
        infinite: false,
    });

    function raf(time) {
        lenis.raf(time);
        requestAnimationFrame(raf);
    }
    requestAnimationFrame(raf);

    // Sync ScrollTrigger with Lenis
    lenis.on('scroll', ScrollTrigger.update);
    
    gsap.registerPlugin(ScrollTrigger);

    // 2. GSAP Animations

    // Hero Text Reveal
    const heroWords = document.querySelectorAll(".word-reveal");
    gsap.from(heroWords, {
        opacity: 0,
        y: 80,
        duration: 1.2,
        stagger: 0.2,
        ease: "power4.out"
    });

    // Hero Description & CTA Fade In
    gsap.from(".hero-description, .hero-cta-box", {
        opacity: 0,
        y: 30,
        duration: 1.4,
        delay: 0.6,
        ease: "power3.out"
    });

    // Arrow Sketch Reveal (dash offset)
    const arrowPath = document.querySelector(".hero-arrow path");
    if (arrowPath) {
        const length = arrowPath.getTotalLength();
        arrowPath.style.strokeDasharray = length;
        arrowPath.style.strokeDashoffset = length;
        
        gsap.to(arrowPath, {
            strokeDashoffset: 0,
            duration: 1.5,
            delay: 1.2,
            ease: "power2.out"
        });
    }

    // Scroll Triggered Card reveals (physical paper slide up)
    const cards = document.querySelectorAll(".feature-card");
    gsap.from(cards, {
        scrollTrigger: {
            trigger: ".section-features",
            start: "top 75%",
            toggleActions: "play none none none"
        },
        opacity: 0,
        y: 60,
        duration: 1.0,
        stagger: 0.15,
        ease: "power3.out"
    });

    // Polaroid Photo tilt reveal
    gsap.from(".polaroid-photo", {
        scrollTrigger: {
            trigger: ".section-about",
            start: "top 65%",
        },
        opacity: 0,
        scale: 0.9,
        rotation: -10,
        duration: 1.2,
        ease: "back.out(1.7)"
    });

    // Sticky Note reveal
    gsap.from(".sticky-note", {
        scrollTrigger: {
            trigger: ".section-about",
            start: "top 50%",
        },
        opacity: 0,
        y: 40,
        rotation: 12,
        duration: 1.0,
        ease: "back.out(1.5)"
    });

    // Table rows reveal
    const tableRows = document.querySelectorAll(".brutalist-table tbody tr");
    gsap.from(tableRows, {
        scrollTrigger: {
            trigger: ".section-documentation",
            start: "top 70%",
        },
        opacity: 0,
        x: -20,
        duration: 0.8,
        stagger: 0.1,
        ease: "power2.out"
    });

    // Mascot Dynamic Scroll Reaction
    let lastScrollY = window.scrollY;
    
    lenis.on('scroll', (e) => {
        const mascot = document.getElementById("dino-mascot");
        if (!mascot) return;

        const currentScrollY = window.scrollY;
        const scrollDelta = currentScrollY - lastScrollY;
        lastScrollY = currentScrollY;

        // Calculate a slight rotation based on scroll speed / direction
        const rotationAngle = Math.max(-15, Math.min(15, scrollDelta * 0.2));
        const bounceScale = 1 + Math.abs(scrollDelta * 0.003);

        // Apply physical spring reaction
        gsap.to(".dino-svg", {
            rotation: rotationAngle,
            scaleY: Math.max(0.85, Math.min(1.15, 2 - bounceScale)),
            scaleX: Math.max(0.85, Math.min(1.15, bounceScale)),
            duration: 0.3,
            overwrite: "auto",
            onComplete: () => {
                gsap.to(".dino-svg", {
                    rotation: 0,
                    scale: 1,
                    duration: 0.6,
                    ease: "elastic.out(1, 0.3)"
                });
            }
        });

        // Toggle speech bubble state dynamically at milestones
        const bubble = document.getElementById("mascot-speech");
        const docSection = document.getElementById("documentation").getBoundingClientRect();
        
        if (currentScrollY > 150 && currentScrollY < 300) {
            showSpeech("We are entering the philosophy archives.");
        } else if (docSection.top < window.innerHeight && docSection.bottom > 0) {
            showSpeech("This is our raw, printed journal record.");
        } else {
            hideSpeech();
        }
    });

    // Mascot Blinking Behavior
    const eye = document.querySelector(".dino-eye");
    const blinkEye = document.querySelector(".dino-eye-blink");
    
    function blink() {
        if (eye && blinkEye) {
            eye.style.display = "none";
            blinkEye.style.display = "block";
            
            setTimeout(() => {
                eye.style.display = "block";
                blinkEye.style.display = "none";
            }, 180);
        }
        // Blink again at a random interval between 3 and 7 seconds
        setTimeout(blink, Math.random() * 4000 + 3000);
    }
    setTimeout(blink, 2000);

    // Speech bubble controller
    const speechBubble = document.getElementById("mascot-speech");
    let bubbleTimeout;

    function showSpeech(text) {
        if (!speechBubble) return;
        speechBubble.textContent = text;
        speechBubble.classList.add("active");
        
        clearTimeout(bubbleTimeout);
        bubbleTimeout = setTimeout(hideSpeech, 4500);
    }

    function hideSpeech() {
        if (!speechBubble) return;
        speechBubble.classList.remove("active");
    }

    // Click Mascot triggers random quote
    const mascotContainer = document.getElementById("dino-mascot");
    if (mascotContainer) {
        const quotes = [
            "Handcrafted is human.",
            "Try to print this page!",
            "Stay focused, stay calm.",
            "No colors, no clutter.",
            "Satoshi is a beautiful grotesque.",
            "Active recall beats passive reading.",
            "Did you know dinosaurs loved books?"
        ];
        mascotContainer.addEventListener("click", () => {
            const randomQuote = quotes[Math.floor(Math.random() * quotes.length)];
            showSpeech(randomQuote);
            
            // Jump animation
            gsap.to(".dino-svg", {
                y: -25,
                duration: 0.15,
                yoyo: true,
                repeat: 1,
                ease: "power2.out"
            });
        });
    }
});
