import { useState, useCallback, type MouseEvent } from 'react';
import { useTheme } from '../context/ThemeContext';

interface TiltValues {
  rotateX: number;
  rotateY: number;
  scale: number;
  translateX: number;
  translateY: number;
}

interface UseTiltOptions {
  effect?: 'lift' | 'shift' | 'none';
  scale?: number;
}

export const useTilt = (options: UseTiltOptions = {}) => {
  const { effect = 'lift', scale = 1.02 } = options;
  const { activeEffectSettings } = useTheme();
  const [style, setStyle] = useState<TiltValues>({ 
    rotateX: 0, 
    rotateY: 0, 
    scale: 1,
    translateX: 0,
    translateY: 0
  });
  const [isHovered, setIsHovered] = useState(false);

  const onMouseMove = useCallback((e: MouseEvent<HTMLElement>) => {
    setIsHovered(true);
    
    // Base transform values for lift/shift
    let tx = 0;
    let ty = 0;
    
    if (effect === 'lift') {
      ty = -4; // Move up
    } else if (effect === 'shift') {
      tx = 4; // Move right
    }

    // Parallax logic
    let rx = 0;
    let ry = 0;

    if (activeEffectSettings.parallaxStrength && activeEffectSettings.parallaxStrength > 0) {
      const card = e.currentTarget;
      const rect = card.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;
      
      const centerX = rect.width / 2;
      const centerY = rect.height / 2;
      
      const normalizedX = (x - centerX) / centerX;
      const normalizedY = (y - centerY) / centerY;
      
      const maxTilt = activeEffectSettings.parallaxStrength / 5;
      
      rx = -normalizedY * maxTilt;
      ry = normalizedX * maxTilt;
    }

    setStyle({
      rotateX: rx,
      rotateY: ry,
      scale: scale,
      translateX: tx,
      translateY: ty
    });
  }, [activeEffectSettings.parallaxStrength, effect, scale]);

  const onMouseLeave = useCallback(() => {
    setIsHovered(false);
    setStyle({ 
      rotateX: 0, 
      rotateY: 0, 
      scale: 1,
      translateX: 0,
      translateY: 0
    });
  }, []);

  const transformStyle = {
    transform: `
      perspective(1000px) 
      rotateX(${style.rotateX}deg) 
      rotateY(${style.rotateY}deg) 
      scale(${style.scale})
      translate3d(${style.translateX}px, ${style.translateY}px, 0)
    `,
    transition: isHovered ? 'transform 0.1s ease-out' : 'transform 0.3s ease-out',
    willChange: 'transform',
    zIndex: isHovered ? 10 : 1 // Bring to front on hover
  };

  return { onMouseMove, onMouseLeave, style: transformStyle, isHovered };
};
