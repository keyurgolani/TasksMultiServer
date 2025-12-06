import { useState, useEffect, useCallback, RefObject } from 'react';

/**
 * Size breakpoints for responsive card layouts
 * These define the width thresholds for different layout modes
 */
export const CARD_SIZE_BREAKPOINTS = {
  /** Cards narrower than this show compact layout */
  compact: 200,
  /** Cards narrower than this show reduced layout */
  reduced: 280,
  /** Cards wider than this show full layout */
  full: 280,
} as const;

/**
 * Layout mode based on element width
 */
export type CardLayoutMode = 'compact' | 'reduced' | 'full';

/**
 * Return type for the useElementSize hook
 */
export interface UseElementSizeReturn {
  /** Current element width in pixels */
  width: number;
  /** Current element height in pixels */
  height: number;
  /** Layout mode based on width breakpoints */
  layoutMode: CardLayoutMode;
  /** Whether the element is in compact mode (narrowest) */
  isCompact: boolean;
  /** Whether the element is in reduced mode (medium) */
  isReduced: boolean;
  /** Whether the element is in full mode (widest) */
  isFull: boolean;
}

/**
 * Determines the layout mode based on element width
 * Returns 'full' for width of 0 (initial state / test environment)
 * to ensure all content is rendered by default
 */
const getLayoutMode = (width: number): CardLayoutMode => {
  // Default to 'full' when width is 0 (initial state or test environment)
  // This ensures all content is rendered until actual measurements are available
  if (width === 0) {
    return 'full';
  }
  if (width < CARD_SIZE_BREAKPOINTS.compact) {
    return 'compact';
  }
  if (width < CARD_SIZE_BREAKPOINTS.reduced) {
    return 'reduced';
  }
  return 'full';
};

/**
 * useElementSize Hook
 * 
 * A hook for detecting the size of an element and determining
 * the appropriate layout mode for responsive card layouts.
 * Uses ResizeObserver for efficient size tracking.
 * 
 * Requirements: 3.8, 5.9, 7.10
 * - Detect card width and adapt internal elements
 * - Show compact variants of elements when narrow
 * - Hide or resize secondary information on narrow cards
 * 
 * @example
 * ```tsx
 * const cardRef = useRef<HTMLDivElement>(null);
 * const { width, layoutMode, isCompact } = useElementSize(cardRef);
 * 
 * return (
 *   <div ref={cardRef}>
 *     {!isCompact && <SecondaryInfo />}
 *   </div>
 * );
 * ```
 */
export const useElementSize = (
  ref: RefObject<HTMLElement | null>
): UseElementSizeReturn => {
  const [size, setSize] = useState({ width: 0, height: 0 });

  const updateSize = useCallback((entries: ResizeObserverEntry[]) => {
    if (entries[0]) {
      const { width, height } = entries[0].contentRect;
      setSize({ width, height });
    }
  }, []);

  useEffect(() => {
    const element = ref.current;
    if (!element) return;

    // Set initial size
    const { width, height } = element.getBoundingClientRect();
    setSize({ width, height });

    // Check if ResizeObserver is available (not in jsdom test environment)
    if (typeof ResizeObserver === 'undefined') {
      return;
    }

    // Create ResizeObserver
    const resizeObserver = new ResizeObserver(updateSize);
    resizeObserver.observe(element);

    return () => {
      resizeObserver.disconnect();
    };
  }, [ref, updateSize]);

  const layoutMode = getLayoutMode(size.width);

  return {
    width: size.width,
    height: size.height,
    layoutMode,
    isCompact: layoutMode === 'compact',
    isReduced: layoutMode === 'reduced',
    isFull: layoutMode === 'full',
  };
};

export default useElementSize;
