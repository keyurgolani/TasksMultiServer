/**
 * useVirtualList Hook
 *
 * A hook that provides virtualization for large lists (50+ items).
 * Uses @tanstack/react-virtual for efficient rendering of only visible items.
 *
 * Requirements: 12.2
 * - Maintain smooth scrolling by using virtualization for lists exceeding 50 items
 */

import { useRef, useCallback, useMemo } from 'react';
import { useVirtualizer, type VirtualItem } from '@tanstack/react-virtual';

/** Threshold for enabling virtualization */
export const VIRTUALIZATION_THRESHOLD = 50;

/** Default estimated item size in pixels */
export const DEFAULT_ESTIMATED_SIZE = 200;

/** Default overscan count (items to render outside visible area) */
export const DEFAULT_OVERSCAN = 5;

/**
 * Configuration options for the virtual list
 */
export interface UseVirtualListOptions<T> {
  /** Array of items to virtualize */
  items: T[];
  /**
   * Estimated size of each item in pixels
   * @default 200
   */
  estimatedSize?: number;
  /**
   * Function to get the actual size of an item (for variable height items)
   */
  getItemSize?: (item: T, index: number) => number;
  /**
   * Number of items to render outside the visible area
   * @default 5
   */
  overscan?: number;
  /**
   * Whether to enable virtualization regardless of item count
   * @default false (only enables when items > 50)
   */
  forceVirtualization?: boolean;
  /**
   * Threshold for enabling virtualization
   * @default 50
   */
  threshold?: number;
}

/**
 * Virtualizer type for HTMLDivElement scroll containers
 */
type DivVirtualizer = ReturnType<typeof useVirtualizer<HTMLDivElement, Element>>;

/**
 * Return type for the useVirtualList hook
 */
export interface UseVirtualListReturn<T> {
  /** Whether virtualization is enabled */
  isVirtualized: boolean;
  /** Ref to attach to the scrollable container */
  parentRef: React.RefObject<HTMLDivElement | null>;
  /** Total height of the virtualized list */
  totalSize: number;
  /** Array of virtual items to render */
  virtualItems: VirtualItem[];
  /** Get the item at a virtual index */
  getItem: (virtualItem: VirtualItem) => T;
  /** Scroll to a specific index */
  scrollToIndex: (index: number, options?: { align?: 'start' | 'center' | 'end' | 'auto' }) => void;
  /** Measure an element (call when item size changes) */
  measureElement: (element: HTMLElement | null) => void;
  /** The virtualizer instance for advanced usage */
  virtualizer: DivVirtualizer | null;
}

/**
 * Hook for virtualizing large lists
 *
 * @example
 * ```tsx
 * const { isVirtualized, parentRef, totalSize, virtualItems, getItem } = useVirtualList({
 *   items: myLargeArray,
 *   estimatedSize: 150,
 * });
 *
 * if (!isVirtualized) {
 *   return <NormalList items={items} />;
 * }
 *
 * return (
 *   <div ref={parentRef} style={{ height: '100%', overflow: 'auto' }}>
 *     <div style={{ height: totalSize, position: 'relative' }}>
 *       {virtualItems.map((virtualItem) => (
 *         <div
 *           key={virtualItem.key}
 *           style={{
 *             position: 'absolute',
 *             top: virtualItem.start,
 *             height: virtualItem.size,
 *           }}
 *         >
 *           {renderItem(getItem(virtualItem))}
 *         </div>
 *       ))}
 *     </div>
 *   </div>
 * );
 * ```
 */
export function useVirtualList<T>({
  items,
  estimatedSize = DEFAULT_ESTIMATED_SIZE,
  getItemSize,
  overscan = DEFAULT_OVERSCAN,
  forceVirtualization = false,
  threshold = VIRTUALIZATION_THRESHOLD,
}: UseVirtualListOptions<T>): UseVirtualListReturn<T> {
  const parentRef = useRef<HTMLDivElement>(null);

  // Determine if virtualization should be enabled
  const isVirtualized = useMemo(() => {
    return forceVirtualization || items.length > threshold;
  }, [forceVirtualization, items.length, threshold]);

  // Create the virtualizer (only when virtualization is enabled)
  const virtualizer = useVirtualizer({
    count: isVirtualized ? items.length : 0,
    getScrollElement: () => parentRef.current,
    estimateSize: useCallback(
      (index: number) => {
        if (getItemSize && items[index]) {
          return getItemSize(items[index], index);
        }
        return estimatedSize;
      },
      [getItemSize, items, estimatedSize]
    ),
    overscan,
    enabled: isVirtualized,
  });

  // Get item at virtual index
  const getItem = useCallback(
    (virtualItem: VirtualItem): T => {
      return items[virtualItem.index];
    },
    [items]
  );

  // Scroll to index
  const scrollToIndex = useCallback(
    (index: number, options?: { align?: 'start' | 'center' | 'end' | 'auto' }) => {
      if (isVirtualized && virtualizer) {
        virtualizer.scrollToIndex(index, options);
      }
    },
    [isVirtualized, virtualizer]
  );

  // Measure element
  const measureElement = useCallback(
    (element: HTMLElement | null) => {
      if (isVirtualized && virtualizer && element) {
        virtualizer.measureElement(element);
      }
    },
    [isVirtualized, virtualizer]
  );

  return {
    isVirtualized,
    parentRef,
    totalSize: isVirtualized ? virtualizer.getTotalSize() : 0,
    virtualItems: isVirtualized ? virtualizer.getVirtualItems() : [],
    getItem,
    scrollToIndex,
    measureElement,
    virtualizer: isVirtualized ? virtualizer : null,
  };
}

export default useVirtualList;
