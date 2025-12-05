/**
 * VirtualizedList Component
 *
 * A virtualized list component for rendering large lists (50+ items) efficiently.
 * Uses @tanstack/react-virtual to only render visible items, maintaining smooth
 * scrolling performance.
 *
 * Requirements: 12.2
 * - Maintain smooth scrolling by using virtualization for lists exceeding 50 items
 *
 * @example
 * ```tsx
 * <VirtualizedList
 *   items={largeArray}
 *   renderItem={(item) => <ItemCard item={item} />}
 *   estimatedItemHeight={150}
 * />
 * ```
 */

import React, { useCallback, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useVirtualList, VIRTUALIZATION_THRESHOLD } from '../../core/hooks/useVirtualList';
import { cn } from '../../lib/utils';
import styles from './VirtualizedList.module.css';

/**
 * Item interface for virtualized list
 */
export interface VirtualizedListItem {
  /** Unique identifier for the item */
  id: string;
  /** Optional height hint for better virtualization */
  height?: number;
}

/**
 * Props for the VirtualizedList component
 */
export interface VirtualizedListProps<T extends VirtualizedListItem> {
  /** Array of items to render */
  items: T[];
  /** Function to render each item */
  renderItem: (item: T, index: number) => React.ReactNode;
  /**
   * Estimated height of each item in pixels
   * @default 200
   */
  estimatedItemHeight?: number;
  /**
   * Function to get the actual height of an item
   * If provided, enables variable height items
   */
  getItemHeight?: (item: T, index: number) => number;
  /**
   * Height of the scrollable container
   * @default '100%'
   */
  height?: string | number;
  /**
   * Gap between items in pixels
   * @default 16
   */
  gap?: number;
  /**
   * Number of items to render outside visible area
   * @default 5
   */
  overscan?: number;
  /**
   * Whether to force virtualization regardless of item count
   * @default false
   */
  forceVirtualization?: boolean;
  /**
   * Threshold for enabling virtualization
   * @default 50
   */
  threshold?: number;
  /**
   * Whether to animate items
   * @default true
   */
  animate?: boolean;
  /** Additional CSS class name */
  className?: string;
  /** CSS class name for the inner container */
  innerClassName?: string;
  /** CSS class name for each item wrapper */
  itemClassName?: string;
  /** Callback when scroll position changes */
  onScroll?: (scrollTop: number) => void;
  /** Test ID for the component */
  'data-testid'?: string;
}

/**
 * Animation variants for list items
 */
const itemVariants = {
  hidden: { opacity: 0, y: 10 },
  visible: { opacity: 1, y: 0 },
  exit: { opacity: 0, y: -10 },
};

/**
 * VirtualizedList Component
 *
 * Renders a virtualized list that only renders visible items for optimal performance.
 * Automatically falls back to a regular list when item count is below the threshold.
 */
export function VirtualizedList<T extends VirtualizedListItem>({
  items,
  renderItem,
  estimatedItemHeight = 200,
  getItemHeight,
  height = '100%',
  gap = 16,
  overscan = 5,
  forceVirtualization = false,
  threshold = VIRTUALIZATION_THRESHOLD,
  animate = true,
  className,
  innerClassName,
  itemClassName,
  onScroll,
  'data-testid': testId = 'virtualized-list',
}: VirtualizedListProps<T>): React.ReactElement {
  // Calculate item size including gap
  const getItemSize = useCallback(
    (item: T, index: number) => {
      const baseHeight = getItemHeight
        ? getItemHeight(item, index)
        : item.height ?? estimatedItemHeight;
      // Add gap to all items except the last one
      return index < items.length - 1 ? baseHeight + gap : baseHeight;
    },
    [getItemHeight, estimatedItemHeight, gap, items.length]
  );

  const {
    isVirtualized,
    parentRef,
    totalSize,
    virtualItems,
    getItem,
    measureElement,
  } = useVirtualList({
    items,
    estimatedSize: estimatedItemHeight + gap,
    getItemSize,
    overscan,
    forceVirtualization,
    threshold,
  });

  // Handle scroll events
  const handleScroll = useCallback(
    (e: React.UIEvent<HTMLDivElement>) => {
      if (onScroll) {
        onScroll(e.currentTarget.scrollTop);
      }
    },
    [onScroll]
  );

  // Render non-virtualized list for small item counts
  const renderNonVirtualizedList = useMemo(() => {
    if (isVirtualized) return null;

    return (
      <div
        className={cn(styles.container, className)}
        style={{ height }}
        data-testid={testId}
        data-virtualized="false"
      >
        <div
          className={cn(styles.inner, innerClassName)}
          style={{ gap: `${gap}px` }}
        >
          {animate ? (
            <AnimatePresence mode="popLayout">
              {items.map((item, index) => (
                <motion.div
                  key={item.id}
                  variants={itemVariants}
                  initial="hidden"
                  animate="visible"
                  exit="exit"
                  transition={{ duration: 0.2, delay: index * 0.02 }}
                  className={cn(styles.item, itemClassName)}
                >
                  {renderItem(item, index)}
                </motion.div>
              ))}
            </AnimatePresence>
          ) : (
            items.map((item, index) => (
              <div key={item.id} className={cn(styles.item, itemClassName)}>
                {renderItem(item, index)}
              </div>
            ))
          )}
        </div>
      </div>
    );
  }, [isVirtualized, items, renderItem, gap, height, animate, className, innerClassName, itemClassName, testId]);

  // Return non-virtualized list if below threshold
  if (!isVirtualized) {
    return renderNonVirtualizedList!;
  }

  // Render virtualized list
  return (
    <div
      ref={parentRef}
      className={cn(styles.container, styles.virtualized, className)}
      style={{ height }}
      onScroll={handleScroll}
      data-testid={testId}
      data-virtualized="true"
    >
      <div
        className={cn(styles.inner, innerClassName)}
        style={{
          height: `${totalSize}px`,
          position: 'relative',
        }}
      >
        {virtualItems.map((virtualItem) => {
          const item = getItem(virtualItem);
          return (
            <div
              key={virtualItem.key}
              ref={measureElement}
              data-index={virtualItem.index}
              className={cn(styles.virtualItem, itemClassName)}
              style={{
                position: 'absolute',
                top: 0,
                left: 0,
                width: '100%',
                transform: `translateY(${virtualItem.start}px)`,
              }}
            >
              {renderItem(item, virtualItem.index)}
            </div>
          );
        })}
      </div>
    </div>
  );
}

VirtualizedList.displayName = 'VirtualizedList';

export default VirtualizedList;
