import { describe, it, expect, vi } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useSpotlight, getSpotlightGradient } from './useSpotlight';
import React from 'react';

// Mock the ThemeContext
vi.mock('../../context/ThemeContext', () => ({
  useTheme: () => ({
    activeEffectSettings: {
      glowStrength: 50,
      glassOpacity: 70,
      glassBlur: 10,
      shadowStrength: 40,
      borderRadius: 12,
      fabRoundness: 25,
      parallaxStrength: 20,
      animationSpeed: 1.0,
    },
  }),
}));

describe('useSpotlight', () => {
  describe('initialization', () => {
    it('should initialize with default values', () => {
      const { result } = renderHook(() => useSpotlight());

      expect(result.current.position).toEqual({ x: 50, y: 50 });
      expect(result.current.isActive).toBe(false);
      expect(result.current.style['--mouse-x']).toBe('50%');
      expect(result.current.style['--mouse-y']).toBe('50%');
      expect(result.current.style['--spotlight-opacity']).toBe('0');
    });

    it('should return event handlers', () => {
      const { result } = renderHook(() => useSpotlight());

      expect(typeof result.current.onMouseEnter).toBe('function');
      expect(typeof result.current.onMouseMove).toBe('function');
      expect(typeof result.current.onMouseLeave).toBe('function');
    });

    it('should return a ref', () => {
      const { result } = renderHook(() => useSpotlight());

      expect(result.current.ref).toBeDefined();
      expect(result.current.ref.current).toBeNull();
    });
  });

  describe('mouse enter', () => {
    it('should activate spotlight on mouse enter', () => {
      const { result } = renderHook(() => useSpotlight());

      act(() => {
        result.current.onMouseEnter();
      });

      expect(result.current.isActive).toBe(true);
    });

    it('should not activate when disabled', () => {
      const { result } = renderHook(() => useSpotlight({ enabled: false }));

      act(() => {
        result.current.onMouseEnter();
      });

      expect(result.current.isActive).toBe(false);
    });
  });

  describe('mouse move', () => {
    it('should update position on mouse move', () => {
      const { result } = renderHook(() => useSpotlight());

      const mockElement = {
        getBoundingClientRect: () => ({
          left: 0,
          top: 0,
          width: 200,
          height: 100,
        }),
      } as HTMLElement;

      const mockEvent = {
        currentTarget: mockElement,
        clientX: 100, // 50% of width
        clientY: 50,  // 50% of height
      } as React.MouseEvent<HTMLElement>;

      act(() => {
        result.current.onMouseMove(mockEvent);
      });

      expect(result.current.position.x).toBe(50);
      expect(result.current.position.y).toBe(50);
      expect(result.current.isActive).toBe(true);
    });

    it('should clamp position to 0-100 range', () => {
      const { result } = renderHook(() => useSpotlight());

      const mockElement = {
        getBoundingClientRect: () => ({
          left: 100,
          top: 100,
          width: 200,
          height: 100,
        }),
      } as HTMLElement;

      // Mouse position outside element bounds (to the left)
      const mockEvent = {
        currentTarget: mockElement,
        clientX: 50, // Before element left edge
        clientY: 50, // Before element top edge
      } as React.MouseEvent<HTMLElement>;

      act(() => {
        result.current.onMouseMove(mockEvent);
      });

      // Should be clamped to 0
      expect(result.current.position.x).toBe(0);
      expect(result.current.position.y).toBe(0);
    });

    it('should not update when disabled', () => {
      const { result } = renderHook(() => useSpotlight({ enabled: false }));

      const mockElement = {
        getBoundingClientRect: () => ({
          left: 0,
          top: 0,
          width: 200,
          height: 100,
        }),
      } as HTMLElement;

      const mockEvent = {
        currentTarget: mockElement,
        clientX: 100,
        clientY: 50,
      } as React.MouseEvent<HTMLElement>;

      act(() => {
        result.current.onMouseMove(mockEvent);
      });

      // Position should remain at default
      expect(result.current.position).toEqual({ x: 50, y: 50 });
      expect(result.current.isActive).toBe(false);
    });
  });

  describe('mouse leave', () => {
    it('should deactivate spotlight on mouse leave', () => {
      const { result } = renderHook(() => useSpotlight());

      // First activate
      act(() => {
        result.current.onMouseEnter();
      });
      expect(result.current.isActive).toBe(true);

      // Then leave
      act(() => {
        result.current.onMouseLeave();
      });

      expect(result.current.isActive).toBe(false);
      expect(result.current.position).toEqual({ x: 50, y: 50 });
    });
  });

  describe('CSS variables', () => {
    it('should update CSS variables based on position', () => {
      const { result } = renderHook(() => useSpotlight());

      const mockElement = {
        getBoundingClientRect: () => ({
          left: 0,
          top: 0,
          width: 200,
          height: 100,
        }),
      } as HTMLElement;

      const mockEvent = {
        currentTarget: mockElement,
        clientX: 150, // 75% of width
        clientY: 25,  // 25% of height
      } as React.MouseEvent<HTMLElement>;

      act(() => {
        result.current.onMouseMove(mockEvent);
      });

      expect(result.current.style['--mouse-x']).toBe('75%');
      expect(result.current.style['--mouse-y']).toBe('25%');
    });

    it('should set spotlight opacity based on glow strength when active', () => {
      const { result } = renderHook(() => useSpotlight());

      act(() => {
        result.current.onMouseEnter();
      });

      // With glowStrength of 50, opacity should be (50/100) * 0.5 = 0.25
      expect(result.current.style['--spotlight-opacity']).toBe('0.25');
    });

    it('should use custom opacity when provided', () => {
      const { result } = renderHook(() => useSpotlight({ opacity: 0.8 }));

      act(() => {
        result.current.onMouseEnter();
      });

      expect(result.current.style['--spotlight-opacity']).toBe('0.8');
    });

    it('should set opacity to 0 when inactive', () => {
      const { result } = renderHook(() => useSpotlight());

      expect(result.current.style['--spotlight-opacity']).toBe('0');
    });
  });

  describe('options', () => {
    it('should respect enabled option', () => {
      const { result } = renderHook(() => useSpotlight({ enabled: false }));

      act(() => {
        result.current.onMouseEnter();
      });

      expect(result.current.isActive).toBe(false);
      expect(result.current.style['--spotlight-opacity']).toBe('0');
    });
  });
});

describe('getSpotlightGradient', () => {
  it('should return a radial gradient string with default values', () => {
    const gradient = getSpotlightGradient();

    expect(gradient).toContain('radial-gradient');
    expect(gradient).toContain('200px circle');
    expect(gradient).toContain('var(--mouse-x, 50%)');
    expect(gradient).toContain('var(--mouse-y, 50%)');
    expect(gradient).toContain('var(--primary-rgb)');
    expect(gradient).toContain('var(--spotlight-opacity, 0)');
    expect(gradient).toContain('transparent');
  });

  it('should use custom color when provided', () => {
    const gradient = getSpotlightGradient('255, 0, 0');

    expect(gradient).toContain('255, 0, 0');
  });

  it('should use custom size when provided', () => {
    const gradient = getSpotlightGradient('var(--primary-rgb)', 300);

    expect(gradient).toContain('300px circle');
  });
});
