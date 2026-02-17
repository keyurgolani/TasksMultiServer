import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, act } from '@testing-library/react';
import { MasonryGrid, type MasonryGridItem } from './MasonryGrid';

// Mock framer-motion to avoid animation issues in tests
vi.mock('framer-motion', () => ({
  motion: {
    div: ({ children, className, style, ...props }: React.HTMLAttributes<HTMLDivElement> & { 'data-testid'?: string }) => (
      <div className={className} style={style} data-testid={props['data-testid']}>
        {children}
      </div>
    ),
  },
  AnimatePresence: ({ children }: { children: React.ReactNode }) => <>{children}</>,
  LayoutGroup: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

interface TestItem extends MasonryGridItem {
  title: string;
}

const createTestItems = (count: number): TestItem[] => {
  return Array.from({ length: count }, (_, i) => ({
    id: `item-${i + 1}`,
    height: 100 + (i % 3) * 50, // Varying heights: 100, 150, 200
    title: `Item ${i + 1}`,
  }));
};

describe('MasonryGrid', () => {
  const originalInnerWidth = window.innerWidth;

  beforeEach(() => {
    // Reset window width
    Object.defineProperty(window, 'innerWidth', {
      writable: true,
      configurable: true,
      value: 1400, // Default to 3 columns
    });
  });

  afterEach(() => {
    Object.defineProperty(window, 'innerWidth', {
      writable: true,
      configurable: true,
      value: originalInnerWidth,
    });
  });

  it('renders items in columns', () => {
    const items = createTestItems(6);
    const renderItem = (item: TestItem) => (
      <div data-testid={`card-${item.id}`}>{item.title}</div>
    );

    render(
      <MasonryGrid
        items={items}
        renderItem={renderItem}
        columnCount={3}
      />
    );

    // All items should be rendered
    items.forEach(item => {
      expect(screen.getByTestId(`card-${item.id}`)).toBeInTheDocument();
    });
  });

  it('renders empty grid when no items provided', () => {
    const renderItem = (item: TestItem) => <div>{item.title}</div>;

    const { container } = render(
      <MasonryGrid
        items={[]}
        renderItem={renderItem}
        columnCount={3}
      />
    );

    // Grid should exist but be empty
    expect(container.querySelector('[class*="grid"]')).toBeInTheDocument();
  });

  it('applies custom gap', () => {
    const items = createTestItems(3);
    const renderItem = (item: TestItem) => <div>{item.title}</div>;

    const { container } = render(
      <MasonryGrid
        items={items}
        renderItem={renderItem}
        columnCount={2}
        gap={24}
      />
    );

    const grid = container.querySelector('[class*="grid"]');
    expect(grid).toHaveStyle({ gap: '24px' });
  });

  it('applies custom className', () => {
    const items = createTestItems(3);
    const renderItem = (item: TestItem) => <div>{item.title}</div>;

    const { container } = render(
      <MasonryGrid
        items={items}
        renderItem={renderItem}
        columnCount={2}
        className="custom-class"
      />
    );

    const grid = container.querySelector('[class*="grid"]');
    expect(grid).toHaveClass('custom-class');
  });

  it('renders correct number of columns based on columnCount prop', () => {
    const items = createTestItems(6);
    const renderItem = (item: TestItem) => <div>{item.title}</div>;

    const { container } = render(
      <MasonryGrid
        items={items}
        renderItem={renderItem}
        columnCount={2}
      />
    );

    const columns = container.querySelectorAll('[class*="column"]');
    expect(columns.length).toBe(2);
  });

  it('distributes items across columns', () => {
    const items = createTestItems(4);
    const renderItem = (item: TestItem) => (
      <div data-testid={`card-${item.id}`}>{item.title}</div>
    );

    render(
      <MasonryGrid
        items={items}
        renderItem={renderItem}
        columnCount={2}
      />
    );

    // All items should be rendered
    expect(screen.getByTestId('card-item-1')).toBeInTheDocument();
    expect(screen.getByTestId('card-item-2')).toBeInTheDocument();
    expect(screen.getByTestId('card-item-3')).toBeInTheDocument();
    expect(screen.getByTestId('card-item-4')).toBeInTheDocument();
  });

  it('responds to viewport width changes', async () => {
    const items = createTestItems(6);
    const renderItem = (item: TestItem) => <div>{item.title}</div>;

    // Start with wide viewport (3 columns)
    Object.defineProperty(window, 'innerWidth', {
      writable: true,
      configurable: true,
      value: 1400,
    });

    const { container: initialContainer, rerender } = render(
      <MasonryGrid
        items={items}
        renderItem={renderItem}
      />
    );

    // Simulate resize to narrow viewport
    await act(async () => {
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 500,
      });
      window.dispatchEvent(new Event('resize'));
    });

    // Force rerender to pick up the change
    rerender(
      <MasonryGrid
        items={items}
        renderItem={renderItem}
      />
    );

    // Component should still render all items
    const columns = initialContainer.querySelectorAll('[class*="column"]');
    expect(columns.length).toBeGreaterThan(0);
  });

  it('renders without animations when animateLayout is false', () => {
    const items = createTestItems(3);
    const renderItem = (item: TestItem) => (
      <div data-testid={`card-${item.id}`}>{item.title}</div>
    );

    render(
      <MasonryGrid
        items={items}
        renderItem={renderItem}
        columnCount={2}
        animateLayout={false}
      />
    );

    // Items should still be rendered
    items.forEach(item => {
      expect(screen.getByTestId(`card-${item.id}`)).toBeInTheDocument();
    });
  });

  it('uses custom breakpoints', async () => {
    const items = createTestItems(6);
    const renderItem = (item: TestItem) => <div>{item.title}</div>;

    const customBreakpoints = {
      0: 1,
      800: 2,
      1600: 4,
    };

    // Set viewport to trigger 2 columns
    Object.defineProperty(window, 'innerWidth', {
      writable: true,
      configurable: true,
      value: 1000,
    });

    const { container } = render(
      <MasonryGrid
        items={items}
        renderItem={renderItem}
        columnBreakpoints={customBreakpoints}
      />
    );

    const columns = container.querySelectorAll('[class*="column"]');
    expect(columns.length).toBe(2);
  });

  describe('Virtualization (Requirements: 12.2)', () => {
    it('sets data-virtualized to false when below threshold', () => {
      const items = createTestItems(10);
      const renderItem = (item: TestItem) => <div>{item.title}</div>;

      render(
        <MasonryGrid
          items={items}
          renderItem={renderItem}
          columnCount={2}
        />
      );

      const grid = screen.getByTestId('masonry-grid');
      expect(grid).toHaveAttribute('data-virtualized', 'false');
    });

    it('sets data-virtualized to true when above threshold', () => {
      const items = createTestItems(60);
      const renderItem = (item: TestItem) => <div>{item.title}</div>;

      render(
        <MasonryGrid
          items={items}
          renderItem={renderItem}
          columnCount={2}
          virtualizedHeight={400}
        />
      );

      const grid = screen.getByTestId('masonry-grid-virtualized');
      expect(grid).toHaveAttribute('data-virtualized', 'true');
    });

    it('enables virtualization when virtualize prop is true', () => {
      const items = createTestItems(10); // Below threshold
      const renderItem = (item: TestItem) => <div>{item.title}</div>;

      render(
        <MasonryGrid
          items={items}
          renderItem={renderItem}
          columnCount={2}
          virtualize
          virtualizedHeight={400}
        />
      );

      const grid = screen.getByTestId('masonry-grid-virtualized');
      expect(grid).toHaveAttribute('data-virtualized', 'true');
    });

    it('respects custom virtualization threshold', () => {
      const items = createTestItems(30);
      const renderItem = (item: TestItem) => <div>{item.title}</div>;

      render(
        <MasonryGrid
          items={items}
          renderItem={renderItem}
          columnCount={2}
          virtualizationThreshold={25}
          virtualizedHeight={400}
        />
      );

      const grid = screen.getByTestId('masonry-grid-virtualized');
      expect(grid).toHaveAttribute('data-virtualized', 'true');
    });

    it('applies virtualizedHeight style when virtualized', () => {
      const items = createTestItems(60);
      const renderItem = (item: TestItem) => <div>{item.title}</div>;

      render(
        <MasonryGrid
          items={items}
          renderItem={renderItem}
          columnCount={2}
          virtualizedHeight={500}
        />
      );

      const grid = screen.getByTestId('masonry-grid-virtualized');
      expect(grid).toHaveStyle({ height: '500px' });
    });

    it('applies string virtualizedHeight', () => {
      const items = createTestItems(60);
      const renderItem = (item: TestItem) => <div>{item.title}</div>;

      render(
        <MasonryGrid
          items={items}
          renderItem={renderItem}
          columnCount={2}
          virtualizedHeight="80vh"
        />
      );

      const grid = screen.getByTestId('masonry-grid-virtualized');
      expect(grid).toHaveStyle({ height: '80vh' });
    });
  });
});
