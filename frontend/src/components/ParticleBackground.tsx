import React, { useEffect, useRef } from 'react';

export const ParticleBackground: React.FC = () => {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animationFrameId: number;
    let width = (canvas.width = window.innerWidth);
    let height = (canvas.height = window.innerHeight);

    const handleResize = () => {
      if (!canvas) return;
      width = canvas.width = window.innerWidth;
      height = canvas.height = window.innerHeight;
    };

    window.addEventListener('resize', handleResize);

    // Particle class definition
    class Particle {
      x: number;
      y: number;
      vx: number;
      vy: number;
      radius: number;
      color: string;

      constructor() {
        this.x = Math.random() * width;
        this.y = Math.random() * height;
        this.vx = (Math.random() - 0.5) * 0.4;
        this.vy = (Math.random() - 0.5) * 0.4;
        this.radius = Math.random() * 2 + 1;
        // Curated HSL colors matching space-dark, blue, and violet
        const hue = Math.random() > 0.5 ? 240 : 280; // Blue vs Purple
        this.color = `hsla(${hue}, 80%, 70%, ${Math.random() * 0.3 + 0.1})`;
      }

      update() {
        this.x += this.vx;
        this.y += this.vy;

        if (this.x < 0 || this.x > width) this.vx *= -1;
        if (this.y < 0 || this.y > height) this.vy *= -1;
      }

      draw(c: CanvasRenderingContext2D) {
        c.beginPath();
        c.arc(this.x, this.y, this.radius, 0, Math.PI * 2);
        c.fillStyle = this.color;
        c.shadowBlur = 10;
        c.shadowColor = this.color;
        c.fill();
        c.shadowBlur = 0; // Reset shadow
      }
    }

    const particlesCount = Math.min(60, Math.floor((width * height) / 25000));
    const particlesArray: Particle[] = [];
    for (let i = 0; i < particlesCount; i++) {
      particlesArray.push(new Particle());
    }

    // Connect particles near each other
    const connectParticles = (c: CanvasRenderingContext2D) => {
      const maxDistance = 140;
      for (let a = 0; a < particlesArray.length; a++) {
        for (let b = a + 1; b < particlesArray.length; b++) {
          const dx = particlesArray[a].x - particlesArray[b].x;
          const dy = particlesArray[a].y - particlesArray[b].y;
          const dist = Math.sqrt(dx * dx + dy * dy);

          if (dist < maxDistance) {
            const alpha = (1 - dist / maxDistance) * 0.08;
            c.strokeStyle = `rgba(99, 102, 241, ${alpha})`;
            c.lineWidth = 0.8;
            c.beginPath();
            c.moveTo(particlesArray[a].x, particlesArray[a].y);
            c.lineTo(particlesArray[b].x, particlesArray[b].y);
            c.stroke();
          }
        }
      }
    };

    const render = () => {
      ctx.fillStyle = 'rgba(3, 7, 18, 0.2)'; // Faint trail
      ctx.fillRect(0, 0, width, height);

      particlesArray.forEach((particle) => {
        particle.update();
        particle.draw(ctx);
      });

      connectParticles(ctx);
      animationFrameId = requestAnimationFrame(render);
    };

    render();

    return () => {
      window.removeEventListener('resize', handleResize);
      cancelAnimationFrame(animationFrameId);
    };
  }, []);

  return <canvas ref={canvasRef} className="fixed inset-0 w-full h-full pointer-events-none z-0" />;
};
