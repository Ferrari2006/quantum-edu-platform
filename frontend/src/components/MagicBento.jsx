import { useEffect, useRef, useState } from "react";
import { gsap } from "gsap";
import "./MagicBento.css";

function useMotionDisabled(disableAnimations) {
  const [shouldDisable, setShouldDisable] = useState(Boolean(disableAnimations));

  useEffect(() => {
    const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
    const compactViewport = window.matchMedia("(max-width: 768px)");
    const update = () => setShouldDisable(Boolean(disableAnimations) || reducedMotion.matches || compactViewport.matches);

    update();
    reducedMotion.addEventListener("change", update);
    compactViewport.addEventListener("change", update);
    return () => {
      reducedMotion.removeEventListener("change", update);
      compactViewport.removeEventListener("change", update);
    };
  }, [disableAnimations]);

  return shouldDisable;
}

export default function MagicBento({
  children,
  className = "",
  glowColor = "103, 232, 249",
  spotlightRadius = 240,
  disableAnimations = false,
}) {
  const gridRef = useRef(null);
  const spotlightRef = useRef(null);
  const shouldDisable = useMotionDisabled(disableAnimations);

  useEffect(() => {
    const grid = gridRef.current;
    const spotlight = spotlightRef.current;
    if (!grid || !spotlight || shouldDisable) return undefined;

    const updateGlow = (event) => {
      const gridRect = grid.getBoundingClientRect();
      const x = event.clientX - gridRect.left;
      const y = event.clientY - gridRect.top;

      gsap.set(spotlight, { x, y, opacity: 1 });
      grid.querySelectorAll(".magic-bento-card").forEach((card) => {
        const rect = card.getBoundingClientRect();
        const localX = event.clientX - rect.left;
        const localY = event.clientY - rect.top;
        const distance = Math.hypot(event.clientX - (rect.left + rect.width / 2), event.clientY - (rect.top + rect.height / 2));
        const intensity = Math.max(0, 1 - distance / spotlightRadius);
        card.style.setProperty("--magic-glow-x", `${localX}px`);
        card.style.setProperty("--magic-glow-y", `${localY}px`);
        card.style.setProperty("--magic-glow-intensity", intensity.toFixed(3));
      });
    };

    const clearGlow = () => {
      gsap.to(spotlight, { opacity: 0, duration: 0.2, overwrite: true });
      grid.querySelectorAll(".magic-bento-card").forEach((card) => {
        card.style.setProperty("--magic-glow-intensity", "0");
      });
    };

    grid.addEventListener("pointermove", updateGlow);
    grid.addEventListener("pointerleave", clearGlow);
    return () => {
      grid.removeEventListener("pointermove", updateGlow);
      grid.removeEventListener("pointerleave", clearGlow);
      gsap.killTweensOf(spotlight);
    };
  }, [shouldDisable, spotlightRadius]);

  return (
    <div
      ref={gridRef}
      className={`magic-bento-grid ${shouldDisable ? "magic-bento-static" : ""} ${className}`.trim()}
      style={{ "--magic-glow-rgb": glowColor, "--magic-spotlight-size": `${spotlightRadius * 2}px` }}
    >
      <div ref={spotlightRef} className="magic-bento-spotlight" aria-hidden="true" />
      {children}
    </div>
  );
}

export function MagicBentoCard({
  as: Element = "article",
  children,
  className = "",
  glowColor,
  enableStars = false,
  particleCount = 5,
  clickEffect = true,
  disableAnimations = false,
  onPointerEnter,
  onPointerDown,
  ...props
}) {
  const cardRef = useRef(null);
  const particleTweens = useRef([]);
  const shouldDisable = useMotionDisabled(disableAnimations);

  const clearParticles = () => {
    particleTweens.current.forEach((tween) => tween.kill());
    particleTweens.current = [];
    cardRef.current?.querySelectorAll(".magic-bento-particle").forEach((particle) => particle.remove());
  };

  useEffect(() => clearParticles, []);

  const handlePointerEnter = (event) => {
    onPointerEnter?.(event);
    if (!enableStars || shouldDisable || !cardRef.current) return;

    clearParticles();
    const card = cardRef.current;
    const rect = card.getBoundingClientRect();
    for (let index = 0; index < particleCount; index += 1) {
      const particle = document.createElement("span");
      particle.className = "magic-bento-particle";
      particle.style.left = `${15 + Math.random() * 70}%`;
      particle.style.top = `${15 + Math.random() * 70}%`;
      card.appendChild(particle);

      const angle = Math.random() * Math.PI * 2;
      const distance = 18 + Math.random() * Math.min(rect.width, rect.height) * 0.24;
      const tween = gsap.fromTo(
        particle,
        { x: 0, y: 0, scale: 0, opacity: 0 },
        {
          x: Math.cos(angle) * distance,
          y: Math.sin(angle) * distance,
          scale: 1,
          opacity: 0.75,
          duration: 0.45,
          yoyo: true,
          repeat: 1,
          ease: "power2.out",
          onComplete: () => particle.remove(),
        },
      );
      particleTweens.current.push(tween);
    }
  };

  const handlePointerDown = (event) => {
    onPointerDown?.(event);
    if (!clickEffect || shouldDisable || !cardRef.current) return;

    const rect = cardRef.current.getBoundingClientRect();
    const ripple = document.createElement("span");
    const size = Math.max(rect.width, rect.height) * 1.8;
    ripple.className = "magic-bento-ripple";
    ripple.style.width = `${size}px`;
    ripple.style.height = `${size}px`;
    ripple.style.left = `${event.clientX - rect.left}px`;
    ripple.style.top = `${event.clientY - rect.top}px`;
    cardRef.current.appendChild(ripple);
    gsap.fromTo(
      ripple,
      { scale: 0.08, opacity: 0.32 },
      { scale: 1, opacity: 0, duration: 0.55, ease: "power2.out", onComplete: () => ripple.remove() },
    );
  };

  return (
    <Element
      ref={cardRef}
      className={`magic-bento-card ${shouldDisable ? "magic-bento-static" : ""} ${className}`.trim()}
      style={glowColor ? { "--magic-glow-rgb": glowColor } : undefined}
      onPointerEnter={handlePointerEnter}
      onPointerDown={handlePointerDown}
      {...props}
    >
      {children}
    </Element>
  );
}
