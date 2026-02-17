import { useMemo } from 'react';

/**
 * Represents an item with a unique identifier and height for masonry distribution
 */
export interface MasonryItem {
  /** Unique identifier for the item */
  id: string;
  /** Height of the item in pixels (or relative units) */
  height: number;
}

/**
 * Represents a column in the masonry layout containing distributed items
 */
export interface MasonryColumn<T extends MasonryItem> {
  /** Items assigned to this column */
  items: T[];
  /** Total height of all items in this column */
  totalHeight: number;
}

/**
 * Return type for the useMasonry hook
 */
export interface UseMasonryReturn<T extends MasonryItem> {
  /** Array of columns with distributed items */
  columns: MasonryColumn<T>[];
  /** Maximum height among all columns */
  maxColumnHeight: number;
  /** Minimum height among all columns */
  minColumnHeight: number;
  /** Height difference between tallest and shortest columns */
  heightDifference: number;
}

/**
 * Options for configuring the useMasonry hook
 */
export interface UseMasonryOptions {
  /**
   * Number of columns to distribute items into
   * @default 3
   */
  columnCount?: number;
  /**
   * Gap between items in pixels (used for height calculations)
   * @default 16
   */
  gap?: number;
}

/**
 * Distribute items into columns using the column-bucket algorithm
 * 
 * This algorithm assigns each item to the column with the smallest total height,
 * which minimizes the height difference between columns.
 * 
 * @param items - Array of items with id and height properties
 * @param columnCount - Number of columns to distribute into
 * @param gap - Gap between items (added to height calculations)
 * @returns Array of columns with distributed items
 */
export const distributeItemsToColumns = <T extends MasonryItem>(
  items: T[],
  columnCount: number,
  gap: number = 0
): MasonryColumn<T>[] => {
  // Handle edge cases
  if (columnCount <= 0) {
    return [];
  }
  
  if (items.length === 0) {
    // Return empty columns
    return Array.from({ length: columnCount }, () => ({
      items: [],
      totalHeight: 0,
    }));
  }

  // Initialize columns
  const columns: MasonryColumn<T>[] = Array.from({ length: columnCount }, () => ({
    items: [],
    totalHeight: 0,
  }));

  // Distribute items to the shortest column
  for (const item of items) {
    // Find the column with the minimum total height
    let shortestColumnIndex = 0;
    let shortestHeight = columns[0].totalHeight;

    for (let i = 1; i < columns.length; i++) {
      if (columns[i].totalHeight < shortestHeight) {
        shortestHeight = columns[i].totalHeight;
        shortestColumnIndex = i;
      }
    }

    // Add item to the shortest column
    const column = columns[shortestColumnIndex];
    
    // Add gap if this isn't the first item in the column
    const gapToAdd = column.items.length > 0 ? gap : 0;
    
    column.items.push(item);
    column.totalHeight += item.height + gapToAdd;
  }

  return columns;
};

/**
 * Calculate the height statistics for a set of columns
 * 
 * @param columns - Array of masonry columns
 * @returns Object with max, min, and difference heights
 */
export const calculateColumnHeightStats = <T extends MasonryItem>(
  columns: MasonryColumn<T>[]
): { maxHeight: number; minHeight: number; heightDifference: number } => {
  if (columns.length === 0) {
    return { maxHeight: 0, minHeight: 0, heightDifference: 0 };
  }

  const heights = columns.map(col => col.totalHeight);
  const maxHeight = Math.max(...heights);
  const minHeight = Math.min(...heights);
  const heightDifference = maxHeight - minHeight;

  return { maxHeight, minHeight, heightDifference };
};

/**
 * useMasonry Hook
 * 
 * A hook for distributing items into columns using a column-bucket algorithm
 * that minimizes vertical gaps between variable-height cards.
 * 
 * The algorithm assigns each item to the column with the smallest total height,
 * which results in a balanced distribution that minimizes the height difference
 * between the tallest and shortest columns.
 * 
 * Requirements: 7.1
 * - Uses Masonry algorithm to minimize vertical gaps between variable-height cards
 * - Distributes items to minimize the height difference between columns
 * 
 * @example
 * ```tsx
 * const items = [
 *   { id: '1', height: 200, data: { title: 'Card 1' } },
 *   { id: '2', height: 150, data: { title: 'Card 2' } },
 *   { id: '3', height: 300, data: { title: 'Card 3' } },
 * ];
 * 
 * const { columns, heightDifference } = useMasonry(items, { columnCount: 2 });
 * 
 * return (
 *   <div style={{ display: 'flex', gap: '16px' }}>
 *     {columns.map((column, colIndex) => (
 *       <div key={colIndex} style={{ flex: 1 }}>
 *         {column.items.map(item => (
 *           <Card key={item.id} style={{ height: item.height }}>
 *             {item.data.title}
 *           </Card>
 *         ))}
 *       </div>
 *     ))}
 *   </div>
 * );
 * ```
 */
export const useMasonry = <T extends MasonryItem>(
  items: T[],
  options: UseMasonryOptions = {}
): UseMasonryReturn<T> => {
  const { columnCount = 3, gap = 16 } = options;

  // Memoize the column distribution to avoid recalculating on every render
  const result = useMemo(() => {
    const columns = distributeItemsToColumns(items, columnCount, gap);
    const { maxHeight, minHeight, heightDifference } = calculateColumnHeightStats(columns);

    return {
      columns,
      maxColumnHeight: maxHeight,
      minColumnHeight: minHeight,
      heightDifference,
    };
  }, [items, columnCount, gap]);

  return result;
};

export default useMasonry;
