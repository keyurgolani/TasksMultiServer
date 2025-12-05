import { useState, useEffect, useCallback, useMemo } from 'react';

/**
 * Default breakpoints following Requirements 7.2:
 * - 1 column below 600px
 * - 2 columns 600-1200px
 * - 3+ columns above 1200px
 */
export const DEFAULT_COLUMN_BREAKPOINTS: Record<number, number> = {
  0: 1,      // Below 600px: 1 column
  600: 2,    // 600-1200px: 2 columns
  1200: 3,   // Above 1200px: 3 columns
};

/**
 * Options for configuring the useResponsiveColumns hook
 */
export interface UseResponsiveColumnsOptions {
  /**
   * Custom breakpoints mapping viewport widths to column counts
   * Keys are minimum viewport widths, values are column counts
   * @default DEFAULT_COLUMN_BREAKPOINTS
   */
  breakpoints?: Record<number, number>;
  /**
   * Override column count (ignores breakpoints when set)
   */
  overrideCount?: number;
  /**
   * Initial column count for SSR or before first measurement
   * @default 1
   */
  initialCount?: number;
}

/**
 * Return type for the useResponsiveColumns hook
 */
export interface UseResponsiveColumnsReturn {
  /** Current column count based on viewport width */
  columnCount: number;
  /** Current viewport width in pixels */
  viewportWidth: number;
  /** The active breakpoint threshold */
  activeBreakpoint: number;
  /** Whether the viewport is considered mobile (< 600px) */
  isMobile: boolean;
  /** Whether the viewport is considered tablet (600-1200px) */
  isTablet: boolean;
  /** Whether the viewport is considered desktop (>= 1200px) */
  isDesktop: boolean;
}

/**
 * Get column count for a given viewport width based on breakpoints
 * 
 * @param width - Current viewport width in pixels
 * @param breakpoints - Mapping of minimum widths to column counts
 * @returns The column count for the given width
 */
export const getColumnCountForWidth = (
  width: number,
  breakpoints: Record<number, number>
): number => {
  // Sort breakpoints in descending order by width
  const sortedBreakpoints = Object.entries(breakpoints)
    .map(([w, count]) => [parseInt(w, 10), count] as [number, number])
    .sort((a, b) => b[0] - a[0]);

  // Find the first breakpoint that the width exceeds
  for (const [breakpoint, count] of sortedBreakpoints) {
    if (width >= breakpoint) {
      return count;
    }
  }

  // Fallback to the smallest breakpoint's count or 1
  return sortedBreakpoints[sortedBreakpoints.length - 1]?.[1] ?? 1;
};

/**
 * Get the active breakpoint threshold for a given viewport width
 * 
 * @param width - Current viewport width in pixels
 * @param breakpoints - Mapping of minimum widths to column counts
 * @returns The active breakpoint threshold
 */
export const getActiveBreakpoint = (
  width: number,
  breakpoints: Record<number, number>
): number => {
  const sortedBreakpoints = Object.keys(breakpoints)
    .map(w => parseInt(w, 10))
    .sort((a, b) => b - a);

  for (const breakpoint of sortedBreakpoints) {
    if (width >= breakpoint) {
      return breakpoint;
    }
  }

  return sortedBreakpoints[sortedBreakpoints.length - 1] ?? 0;
};

/**
 * useResponsiveColumns Hook
 * 
 * A hook for determining the number of columns to display based on
 * viewport width and configurable breakpoints.
 * 
 * Requirements: 7.2
 * - Recalculates column count when viewport width changes
 * - 1 column below 600px
 * - 2 columns 600-1200px
 * - 3+ columns above 1200px
 * 
 * @example
 * ```tsx
 * // Using default breakpoints
 * const { columnCount, isMobile, isDesktop } = useResponsiveColumns();
 * 
 * // Using custom breakpoints
 * const { columnCount } = useResponsiveColumns({
 *   breakpoints: { 0: 1, 768: 2, 1024: 3, 1440: 4 }
 * });
 * 
 * // With override (ignores breakpoints)
 * const { columnCount } = useResponsiveColumns({ overrideCount: 2 });
 * ```
 */
export const useResponsiveColumns = (
  options: UseResponsiveColumnsOptions = {}
): UseResponsiveColumnsReturn => {
  const {
    breakpoints = DEFAULT_COLUMN_BREAKPOINTS,
    overrideCount,
    initialCount = 1,
  } = options;

  // Get initial viewport width (handle SSR)
  const getInitialWidth = useCallback(() => {
    if (typeof window === 'undefined') return 0;
    return window.innerWidth;
  }, []);

  const [viewportWidth, setViewportWidth] = useState(getInitialWidth);

  // Calculate column count based on viewport width or override
  const columnCount = useMemo(() => {
    if (overrideCount !== undefined) {
      return overrideCount;
    }
    if (viewportWidth === 0) {
      return initialCount;
    }
    return getColumnCountForWidth(viewportWidth, breakpoints);
  }, [viewportWidth, breakpoints, overrideCount, initialCount]);

  // Calculate active breakpoint
  const activeBreakpoint = useMemo(() => {
    if (viewportWidth === 0) return 0;
    return getActiveBreakpoint(viewportWidth, breakpoints);
  }, [viewportWidth, breakpoints]);

  // Calculate device type flags based on default breakpoints
  const isMobile = viewportWidth < 600;
  const isTablet = viewportWidth >= 600 && viewportWidth < 1200;
  const isDesktop = viewportWidth >= 1200;

  // Handle resize events
  useEffect(() => {
    if (typeof window === 'undefined') return;

    const handleResize = () => {
      setViewportWidth(window.innerWidth);
    };

    // Set initial value
    handleResize();

    // Add resize listener
    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
    };
  }, []);

  return {
    columnCount,
    viewportWidth,
    activeBreakpoint,
    isMobile,
    isTablet,
    isDesktop,
  };
};

export default useResponsiveColumns;
