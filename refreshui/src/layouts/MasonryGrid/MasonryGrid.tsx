import React, { useMemo, useCallback, useRef } from 'react';
import { motion, AnimatePresence, LayoutGroup } from 'framer-motion';
import { useVirtualizer } from '@tanstack/react-virtual';
import { useMasonry, type MasonryItem } from '../../core/hooks/useMasonry';
import { useResponsiveColumns, DEFAULT_COLUMN_BREAKPOINTS } from '../../core/hooks/useResponsiveColumns';
import { VIRTUALIZATION_THRESHOLD } from '../../core/hooks/useVirtualList';
import styles from './MasonryGrid.module.css';
import clsx from 'clsx';

/**
 * Props for items that can be rendered in the MasonryGrid
 */
export type MasonryGridItem = MasonryItem;

/**
 * Props for the MasonryGrid component
 */
export interface MasonryGridProps<T extends MasonryGridItem> {
  /** Array of items to render in the grid */
  items: T[];
  /** Function to render each item */
  renderItem: (item: T, index: number) => React.ReactNode;
  /** 
   * Breakpoints for responsive column count
   * Keys are viewport widths, values are column counts
   * @default { 0: 1, 600: 2, 1200: 3 }
   */
  columnBreakpoints?: Record<number, number>;
  /** 
   * Gap between items in pixels
   * @default 16
   */
  gap?: number;
  /** 
   * Number of columns (overrides breakpoints if provided)
   */
  columnCount?: number;
  /**
   * Fixed width for each column in pixels
   * When set, columns will have this fixed width instead of flex: 1
   */
  columnWidth?: number;
  /** Additional CSS class name */
  className?: string;
  /** 
   * Unique ID for the layout group (for coordinated animations)
   * @default 'masonry-grid'
   */
  layoutId?: string;
  /**
   * Whether to animate item position changes
   * @default true
   */
  animateLayout?: boolean;
  /**
   * Animation duration in seconds
   * @default 0.3
   */
  animationDuration?: number;
  /**
   * Whether to enable virtualization for large lists (50+ items)
   * When enabled, only visible items are rendered for better performance
   * @default false
   */
  virtualize?: boolean;
  /**
   * Height of the virtualized container (required when virtualize is true)
   * @default '100vh'
   */
  virtualizedHeight?: string | number;
  /**
   * Threshold for auto-enabling virtualization
   * @default 50
   */
  virtualizationThreshold?: number;
}

/**
 * Animation variants for grid items
 */
const itemVariants = {
  hidden: { 
    opacity: 0, 
    scale: 0.9,
    y: 20 
  },
  visible: { 
    opacity: 1, 
    scale: 1,
    y: 0 
  },
  exit: { 
    opacity: 0, 
    scale: 0.9,
    y: -20 
  },
};



/**
 * MasonryGrid Component
 * 
 * A responsive masonry grid layout component that uses the column-bucket
 * algorithm to minimize vertical gaps between variable-height cards.
 * Includes Framer Motion layout animations for smooth position changes
 * when items are added or removed.
 * 
 * Requirements: 7.1, 7.3, 12.2
 * - Uses Masonry algorithm to minimize vertical gaps between variable-height cards
 * - Animates position changes using Framer Motion layout animations
 * - Supports virtualization for lists exceeding 50 items
 * 
 * @example
 * ```tsx
 * const items = [
 *   { id: '1', height: 200, title: 'Card 1' },
 *   { id: '2', height: 150, title: 'Card 2' },
 *   { id: '3', height: 300, title: 'Card 3' },
 * ];
 * 
 * <MasonryGrid
 *   items={items}
 *   renderItem={(item) => <Card>{item.title}</Card>}
 *   gap={16}
 * />
 * 
 * // With virtualization for large lists
 * <MasonryGrid
 *   items={largeItemArray}
 *   renderItem={(item) => <Card>{item.title}</Card>}
 *   virtualize
 *   virtualizedHeight="80vh"
 * />
 * ```
 */
export const MasonryGrid = <T extends MasonryGridItem>({
  items,
  renderItem,
  columnBreakpoints = DEFAULT_COLUMN_BREAKPOINTS,
  gap = 16,
  columnCount: columnCountOverride,
  className,
  layoutId = 'masonry-grid',
  animateLayout = true,
  animationDuration = 0.3,
  virtualize = false,
  virtualizedHeight = '100vh',
  virtualizationThreshold = VIRTUALIZATION_THRESHOLD,
  columnWidth,
}: MasonryGridProps<T>): React.ReactElement => {
  const parentRef = useRef<HTMLDivElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [containerWidth, setContainerWidth] = React.useState(0);

  // Measure container width for auto-fit columns
  React.useEffect(() => {
    if (!columnWidth || !containerRef.current) return;

    const resizeObserver = new ResizeObserver((entries) => {
      for (const entry of entries) {
        setContainerWidth(entry.contentRect.width);
      }
    });

    resizeObserver.observe(containerRef.current);
    // Initial measurement
    setContainerWidth(containerRef.current.clientWidth);

    return () => resizeObserver.disconnect();
  }, [columnWidth]);

  // Get responsive column count using the dedicated hook
  const { columnCount: breakpointColumnCount } = useResponsiveColumns({
    breakpoints: columnBreakpoints,
    overrideCount: columnCountOverride,
  });

  // Calculate column count: auto-fit based on container width if columnWidth is set
  const columnCount = useMemo(() => {
    if (columnWidth && containerWidth > 0) {
      // Calculate how many columns fit: (containerWidth + gap) / (columnWidth + gap)
      const fittingColumns = Math.floor((containerWidth + gap) / (columnWidth + gap));
      return Math.max(1, fittingColumns);
    }
    return breakpointColumnCount;
  }, [columnWidth, containerWidth, gap, breakpointColumnCount]);

  // Use the masonry hook to distribute items
  const { columns } = useMasonry(items, { columnCount, gap });

  // Determine if virtualization should be enabled
  const shouldVirtualize = useMemo(() => {
    return virtualize || items.length > virtualizationThreshold;
  }, [virtualize, items.length, virtualizationThreshold]);

  // Calculate row data for virtualization (each row contains items from all columns at the same index)
  const rowData = useMemo(() => {
    if (!shouldVirtualize) return [];
    
    // Find the maximum number of items in any column
    const maxItems = Math.max(...columns.map(col => col.items.length));
    const rows: { items: (T | null)[]; maxHeight: number }[] = [];
    
    for (let i = 0; i < maxItems; i++) {
      const rowItems = columns.map(col => (col.items[i] as T) || null);
      const maxHeight = Math.max(
        ...rowItems.map(item => item?.height ?? 200),
        200
      );
      rows.push({ items: rowItems, maxHeight });
    }
    
    return rows;
  }, [shouldVirtualize, columns]);

  // Create virtualizer for rows
  const rowVirtualizer = useVirtualizer({
    count: rowData.length,
    getScrollElement: () => parentRef.current,
    estimateSize: useCallback(
      (index: number) => (rowData[index]?.maxHeight ?? 200) + gap,
      [rowData, gap]
    ),
    overscan: 5,
    enabled: shouldVirtualize,
  });

  // Memoize the transition config
  const transition = useMemo(() => ({
    type: 'spring' as const,
    stiffness: 300,
    damping: 30,
    duration: animationDuration,
  }), [animationDuration]);

  // Render function for individual items with animation
  const renderAnimatedItem = useCallback((item: T, index: number) => {
    const content = renderItem(item, index);
    
    if (!animateLayout) {
      return (
        <div key={item.id} className={styles.item}>
          {content}
        </div>
      );
    }

    return (
      <motion.div
        key={item.id}
        layout
        layoutId={`${layoutId}-item-${item.id}`}
        variants={itemVariants}
        initial="hidden"
        animate="visible"
        exit="exit"
        transition={transition}
        className={styles.item}
      >
        {content}
      </motion.div>
    );
  }, [renderItem, animateLayout, layoutId, transition]);

  // Render virtualized grid
  if (shouldVirtualize) {
    const virtualRows = rowVirtualizer.getVirtualItems();
    
    return (
      <div
        ref={parentRef}
        className={clsx(styles.virtualizedContainer, className)}
        style={{ 
          height: typeof virtualizedHeight === 'number' ? `${virtualizedHeight}px` : virtualizedHeight,
          overflow: 'auto',
        }}
        data-testid="masonry-grid-virtualized"
        data-virtualized="true"
      >
        <div
          style={{
            height: `${rowVirtualizer.getTotalSize()}px`,
            width: '100%',
            position: 'relative',
          }}
        >
          {virtualRows.map((virtualRow) => {
            const row = rowData[virtualRow.index];
            return (
              <div
                key={virtualRow.key}
                className={styles.virtualRow}
                style={{
                  position: 'absolute',
                  top: 0,
                  left: 0,
                  width: '100%',
                  height: `${virtualRow.size}px`,
                  transform: `translateY(${virtualRow.start}px)`,
                  display: 'flex',
                  gap: `${gap}px`,
                }}
              >
                {row.items.map((item, colIndex) => (
                  <div
                    key={`col-${colIndex}`}
                    className={styles.virtualColumn}
                    style={{ flex: 1, minWidth: 0 }}
                  >
                    {item && renderItem(item, virtualRow.index * columnCount + colIndex)}
                  </div>
                ))}
              </div>
            );
          })}
        </div>
      </div>
    );
  }

  // Render non-virtualized grid (original implementation)
  return (
    <LayoutGroup id={layoutId}>
      <div 
        ref={containerRef}
        className={clsx(styles.grid, className)}
        style={{ gap: `${gap}px` }}
        data-testid="masonry-grid"
        data-virtualized="false"
      >
        <AnimatePresence mode="popLayout">
          {columns.map((column, columnIndex) => (
            <motion.div
              key={`column-${columnIndex}`}
              layout
              className={styles.column}
              style={{ 
                gap: `${gap}px`,
                ...(columnWidth ? { width: `${columnWidth}px`, flex: 'none' } : {})
              }}
            >
              <AnimatePresence mode="popLayout">
                {column.items.map((item, itemIndex) => 
                  renderAnimatedItem(item as T, itemIndex)
                )}
              </AnimatePresence>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>
    </LayoutGroup>
  );
};

MasonryGrid.displayName = 'MasonryGrid';

export default MasonryGrid;
