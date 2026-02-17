/**
 * VirtualizedList Component Tests
 *
 * Tests for the virtualized list component.
 * Requirements: 12.2 - Maintain smooth scrolling by using virtualization for lists exceeding 50 items
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { VirtualizedList, type VirtualizedListItem } from './VirtualizedList';

// Mock ResizeObserver
class ResizeObserverMock {
  observe = vi.fn();
  unobserve = vi.fn();
  disconnect = vi.fn();
}

(globalThis as unknown as { ResizeObserver: typeof ResizeObserver }).ResizeObserver = ResizeObserverMock as unknown as typeof ResizeObserver;

// Helper to create test items
const createTestItems = (count: number): VirtualizedListItem[] => {
  return Array.from({ length: count }, (_, i) => ({
    id: `item-${i}`,
    height: 100 + (i % 3) * 50, // Variable heights: 100, 150, 200
  }));
};

describe('VirtualizedList', () => {
  describe('Non-virtualized rendering (below threshold)', () => {
    it('renders all items when count is below threshold', () => {
      const items = createTestItems(10);
      
      render(
        <VirtualizedList
          items={items}
          renderItem={(item) => <div data-testid={`item-${item.id}`}>{item.id}</div>}
        />
      );

      // All items should be rendered
      items.forEach((item) => {
        expect(screen.getByTestId(`item-${item.id}`)).toBeInTheDocument();
      });
    });

    it('sets data-virtualized to false when below threshold', () => {
      const items = createTestItems(10);
      
      render(
        <VirtualizedList
          items={items}
          renderItem={(item) => <div>{item.id}</div>}
          data-testid="test-list"
        />
      );

      const list = screen.getByTestId('test-list');
      expect(list).toHaveAttribute('data-virtualized', 'false');
    });

    it('renders with custom gap', () => {
      const items = createTestItems(5);
      
      render(
        <VirtualizedList
          items={items}
          renderItem={(item) => <div>{item.id}</div>}
          gap={24}
        />
      );

      // Component should render without errors
      expect(screen.getByTestId('virtualized-list')).toBeInTheDocument();
    });
  });

  describe('Virtualized rendering (above threshold)', () => {
    it('sets data-virtualized to true when above threshold', () => {
      const items = createTestItems(60);
      
      render(
        <VirtualizedList
          items={items}
          renderItem={(item) => <div>{item.id}</div>}
          data-testid="test-list"
          height={400}
        />
      );

      const list = screen.getByTestId('test-list');
      expect(list).toHaveAttribute('data-virtualized', 'true');
    });

    it('enables virtualization when forceVirtualization is true', () => {
      const items = createTestItems(10); // Below threshold
      
      render(
        <VirtualizedList
          items={items}
          renderItem={(item) => <div>{item.id}</div>}
          forceVirtualization
          data-testid="test-list"
          height={400}
        />
      );

      const list = screen.getByTestId('test-list');
      expect(list).toHaveAttribute('data-virtualized', 'true');
    });

    it('respects custom threshold', () => {
      const items = createTestItems(30);
      
      render(
        <VirtualizedList
          items={items}
          renderItem={(item) => <div>{item.id}</div>}
          threshold={25} // Lower threshold
          data-testid="test-list"
          height={400}
        />
      );

      const list = screen.getByTestId('test-list');
      expect(list).toHaveAttribute('data-virtualized', 'true');
    });
  });

  describe('Props and configuration', () => {
    it('applies custom className', () => {
      const items = createTestItems(5);
      
      render(
        <VirtualizedList
          items={items}
          renderItem={(item) => <div>{item.id}</div>}
          className="custom-class"
          data-testid="test-list"
        />
      );

      const list = screen.getByTestId('test-list');
      expect(list).toHaveClass('custom-class');
    });

    it('applies custom height', () => {
      const items = createTestItems(60);
      
      render(
        <VirtualizedList
          items={items}
          renderItem={(item) => <div>{item.id}</div>}
          height={500}
          data-testid="test-list"
        />
      );

      const list = screen.getByTestId('test-list');
      expect(list).toHaveStyle({ height: '500px' });
    });

    it('applies string height', () => {
      const items = createTestItems(60);
      
      render(
        <VirtualizedList
          items={items}
          renderItem={(item) => <div>{item.id}</div>}
          height="80vh"
          data-testid="test-list"
        />
      );

      const list = screen.getByTestId('test-list');
      expect(list).toHaveStyle({ height: '80vh' });
    });

    it('renders empty list without errors', () => {
      const emptyItems: VirtualizedListItem[] = [];
      render(
        <VirtualizedList
          items={emptyItems}
          renderItem={(item) => <div>{item.id}</div>}
          data-testid="test-list"
        />
      );

      expect(screen.getByTestId('test-list')).toBeInTheDocument();
    });
  });

  describe('Render function', () => {
    it('passes correct item and index to renderItem', () => {
      const items = createTestItems(5);
      const renderItem = vi.fn((item: VirtualizedListItem, index: number) => (
        <div data-testid={`item-${index}`}>{item.id}</div>
      ));
      
      render(
        <VirtualizedList
          items={items}
          renderItem={renderItem}
        />
      );

      // renderItem should be called for each item
      expect(renderItem).toHaveBeenCalledTimes(5);
      
      // Verify first and last calls with matching objects
      expect(renderItem).toHaveBeenNthCalledWith(1, expect.objectContaining({ id: items[0].id }), 0);
      expect(renderItem).toHaveBeenNthCalledWith(5, expect.objectContaining({ id: items[4].id }), 4);
    });
  });
});
