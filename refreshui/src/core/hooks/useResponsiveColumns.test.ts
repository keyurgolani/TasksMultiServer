import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import {
  useResponsiveColumns,
  getColumnCountForWidth,
  getActiveBreakpoint,
  DEFAULT_COLUMN_BREAKPOINTS,
} from './useResponsiveColumns';

describe('useResponsiveColumns', () => {
  const originalInnerWidth = window.innerWidth;

  beforeEach(() => {
    // Reset window width to a default value
    Object.defineProperty(window, 'innerWidth', {
      writable: true,
      configurable: true,
      value: 1400,
    });
  });

  afterEach(() => {
    Object.defineProperty(window, 'innerWidth', {
      writable: true,
      configurable: true,
      value: originalInnerWidth,
    });
  });

  describe('getColumnCountForWidth', () => {
    it('returns 1 column for width below 600px', () => {
      expect(getColumnCountForWidth(0, DEFAULT_COLUMN_BREAKPOINTS)).toBe(1);
      expect(getColumnCountForWidth(300, DEFAULT_COLUMN_BREAKPOINTS)).toBe(1);
      expect(getColumnCountForWidth(599, DEFAULT_COLUMN_BREAKPOINTS)).toBe(1);
    });

    it('returns 2 columns for width 600-1199px', () => {
      expect(getColumnCountForWidth(600, DEFAULT_COLUMN_BREAKPOINTS)).toBe(2);
      expect(getColumnCountForWidth(900, DEFAULT_COLUMN_BREAKPOINTS)).toBe(2);
      expect(getColumnCountForWidth(1199, DEFAULT_COLUMN_BREAKPOINTS)).toBe(2);
    });

    it('returns 3 columns for width 1200px and above', () => {
      expect(getColumnCountForWidth(1200, DEFAULT_COLUMN_BREAKPOINTS)).toBe(3);
      expect(getColumnCountForWidth(1500, DEFAULT_COLUMN_BREAKPOINTS)).toBe(3);
      expect(getColumnCountForWidth(2000, DEFAULT_COLUMN_BREAKPOINTS)).toBe(3);
    });

    it('handles custom breakpoints', () => {
      const customBreakpoints = { 0: 1, 768: 2, 1024: 3, 1440: 4 };
      expect(getColumnCountForWidth(500, customBreakpoints)).toBe(1);
      expect(getColumnCountForWidth(800, customBreakpoints)).toBe(2);
      expect(getColumnCountForWidth(1100, customBreakpoints)).toBe(3);
      expect(getColumnCountForWidth(1500, customBreakpoints)).toBe(4);
    });

    it('handles empty breakpoints', () => {
      expect(getColumnCountForWidth(1000, {})).toBe(1);
    });
  });

  describe('getActiveBreakpoint', () => {
    it('returns correct active breakpoint', () => {
      expect(getActiveBreakpoint(500, DEFAULT_COLUMN_BREAKPOINTS)).toBe(0);
      expect(getActiveBreakpoint(700, DEFAULT_COLUMN_BREAKPOINTS)).toBe(600);
      expect(getActiveBreakpoint(1300, DEFAULT_COLUMN_BREAKPOINTS)).toBe(1200);
    });

    it('handles edge cases at breakpoint boundaries', () => {
      expect(getActiveBreakpoint(600, DEFAULT_COLUMN_BREAKPOINTS)).toBe(600);
      expect(getActiveBreakpoint(1200, DEFAULT_COLUMN_BREAKPOINTS)).toBe(1200);
    });
  });

  describe('useResponsiveColumns hook', () => {
    it('returns correct column count for desktop viewport', () => {
      Object.defineProperty(window, 'innerWidth', { value: 1400, configurable: true });
      
      const { result } = renderHook(() => useResponsiveColumns());
      
      expect(result.current.columnCount).toBe(3);
      expect(result.current.isDesktop).toBe(true);
      expect(result.current.isTablet).toBe(false);
      expect(result.current.isMobile).toBe(false);
    });

    it('returns correct column count for tablet viewport', () => {
      Object.defineProperty(window, 'innerWidth', { value: 800, configurable: true });
      
      const { result } = renderHook(() => useResponsiveColumns());
      
      expect(result.current.columnCount).toBe(2);
      expect(result.current.isDesktop).toBe(false);
      expect(result.current.isTablet).toBe(true);
      expect(result.current.isMobile).toBe(false);
    });

    it('returns correct column count for mobile viewport', () => {
      Object.defineProperty(window, 'innerWidth', { value: 400, configurable: true });
      
      const { result } = renderHook(() => useResponsiveColumns());
      
      expect(result.current.columnCount).toBe(1);
      expect(result.current.isDesktop).toBe(false);
      expect(result.current.isTablet).toBe(false);
      expect(result.current.isMobile).toBe(true);
    });

    it('respects overrideCount option', () => {
      Object.defineProperty(window, 'innerWidth', { value: 1400, configurable: true });
      
      const { result } = renderHook(() => useResponsiveColumns({ overrideCount: 5 }));
      
      expect(result.current.columnCount).toBe(5);
    });

    it('uses custom breakpoints', () => {
      Object.defineProperty(window, 'innerWidth', { value: 1000, configurable: true });
      
      const customBreakpoints = { 0: 1, 800: 4, 1600: 6 };
      const { result } = renderHook(() => useResponsiveColumns({ breakpoints: customBreakpoints }));
      
      expect(result.current.columnCount).toBe(4);
    });

    it('responds to window resize events', async () => {
      Object.defineProperty(window, 'innerWidth', { value: 1400, configurable: true });
      
      const { result } = renderHook(() => useResponsiveColumns());
      
      expect(result.current.columnCount).toBe(3);
      expect(result.current.isDesktop).toBe(true);

      // Simulate resize to mobile
      await act(async () => {
        Object.defineProperty(window, 'innerWidth', { value: 400, configurable: true });
        window.dispatchEvent(new Event('resize'));
      });

      expect(result.current.columnCount).toBe(1);
      expect(result.current.isMobile).toBe(true);
    });

    it('returns viewport width', () => {
      Object.defineProperty(window, 'innerWidth', { value: 1024, configurable: true });
      
      const { result } = renderHook(() => useResponsiveColumns());
      
      expect(result.current.viewportWidth).toBe(1024);
    });

    it('returns active breakpoint', () => {
      Object.defineProperty(window, 'innerWidth', { value: 900, configurable: true });
      
      const { result } = renderHook(() => useResponsiveColumns());
      
      expect(result.current.activeBreakpoint).toBe(600);
    });
  });

  describe('DEFAULT_COLUMN_BREAKPOINTS', () => {
    it('follows Requirements 7.2 specification', () => {
      // Requirement 7.2: 1 column below 600px, 2 columns 600-1200px, 3+ columns above 1200px
      expect(DEFAULT_COLUMN_BREAKPOINTS[0]).toBe(1);
      expect(DEFAULT_COLUMN_BREAKPOINTS[600]).toBe(2);
      expect(DEFAULT_COLUMN_BREAKPOINTS[1200]).toBe(3);
    });
  });
});
