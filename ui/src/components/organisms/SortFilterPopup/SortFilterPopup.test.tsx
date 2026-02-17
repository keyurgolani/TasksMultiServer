import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { SortFilterPopup } from "./SortFilterPopup";
import type { SortOption, FilterOption } from "./SortFilterPopup";

/**
 * SortFilterPopup Tests
 *
 * Tests for the SortFilterPopup organism component.
 * Validates requirements: 26.6, 26.7, 27.1, 27.2, 27.3, 27.4, 27.5
 */

const mockSortOptions: SortOption[] = [
  { id: "name-asc", label: "Name (A-Z)" },
  { id: "name-desc", label: "Name (Z-A)" },
  { id: "date-newest", label: "Newest First" },
  { id: "date-oldest", label: "Oldest First" },
];

const mockFilterOptions: FilterOption[] = [
  { id: "status-completed", label: "Completed", type: "checkbox", group: "Status" },
  { id: "status-in-progress", label: "In Progress", type: "checkbox", group: "Status" },
  { id: "status-blocked", label: "Blocked", type: "checkbox", group: "Status" },
  { id: "priority-high", label: "High Priority", type: "checkbox", group: "Priority" },
  { id: "priority-medium", label: "Medium Priority", type: "checkbox", group: "Priority" },
];

describe("SortFilterPopup", () => {
  const defaultProps = {
    isOpen: true,
    onClose: vi.fn(),
    sortOptions: mockSortOptions,
    filterOptions: mockFilterOptions,
    activeSortId: "name-asc",
    activeFilters: [] as string[],
    onSortChange: vi.fn(),
    onFilterChange: vi.fn(),
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe("Requirement 27.1: Display sort options and filter criteria", () => {
    it("renders sort section with all sort options", () => {
      render(<SortFilterPopup {...defaultProps} />);

      expect(screen.getByTestId("sort-section")).toBeInTheDocument();
      expect(screen.getByText("Sort By")).toBeInTheDocument();

      mockSortOptions.forEach((option) => {
        expect(screen.getByTestId(`sort-option-${option.id}`)).toBeInTheDocument();
        expect(screen.getByText(option.label)).toBeInTheDocument();
      });
    });

    it("renders filter section with all filter options", () => {
      render(<SortFilterPopup {...defaultProps} />);

      expect(screen.getByTestId("filter-section")).toBeInTheDocument();
      expect(screen.getByText("Filter")).toBeInTheDocument();

      mockFilterOptions.forEach((option) => {
        expect(screen.getByTestId(`filter-option-${option.id}`)).toBeInTheDocument();
        expect(screen.getByText(option.label)).toBeInTheDocument();
      });
    });

    it("does not render when isOpen is false", () => {
      render(<SortFilterPopup {...defaultProps} isOpen={false} />);

      expect(screen.queryByTestId("sort-filter-popup")).not.toBeInTheDocument();
    });
  });

  describe("Requirement 27.2: Sort option selection and change event", () => {
    it("calls onSortChange when a sort option is clicked", () => {
      render(<SortFilterPopup {...defaultProps} />);

      fireEvent.click(screen.getByTestId("sort-option-date-newest"));

      expect(defaultProps.onSortChange).toHaveBeenCalledWith("date-newest");
    });

    it("highlights the active sort option", () => {
      render(<SortFilterPopup {...defaultProps} activeSortId="date-newest" />);

      const activeOption = screen.getByTestId("sort-option-date-newest");
      expect(activeOption).toHaveAttribute("aria-pressed", "true");
    });
  });

  describe("Requirement 27.3: Filter criteria selection and change event", () => {
    it("calls onFilterChange when a filter option is clicked", () => {
      render(<SortFilterPopup {...defaultProps} />);

      fireEvent.click(screen.getByTestId("filter-option-status-completed"));

      expect(defaultProps.onFilterChange).toHaveBeenCalledWith(["status-completed"]);
    });

    it("toggles filter selection for checkbox type", () => {
      render(
        <SortFilterPopup
          {...defaultProps}
          activeFilters={["status-completed"]}
        />
      );

      // Click to deselect
      fireEvent.click(screen.getByTestId("filter-option-status-completed"));

      expect(defaultProps.onFilterChange).toHaveBeenCalledWith([]);
    });

    it("allows multiple checkbox selections", () => {
      render(
        <SortFilterPopup
          {...defaultProps}
          activeFilters={["status-completed"]}
        />
      );

      fireEvent.click(screen.getByTestId("filter-option-status-in-progress"));

      expect(defaultProps.onFilterChange).toHaveBeenCalledWith([
        "status-completed",
        "status-in-progress",
      ]);
    });
  });

  describe("Requirement 27.5: Popup persistence for multiple selections", () => {
    it("does not close popup when sort option is selected", () => {
      render(<SortFilterPopup {...defaultProps} />);

      fireEvent.click(screen.getByTestId("sort-option-date-newest"));

      expect(defaultProps.onClose).not.toHaveBeenCalled();
      expect(screen.getByTestId("sort-filter-popup")).toBeInTheDocument();
    });

    it("does not close popup when filter option is selected", () => {
      render(<SortFilterPopup {...defaultProps} />);

      fireEvent.click(screen.getByTestId("filter-option-status-completed"));

      expect(defaultProps.onClose).not.toHaveBeenCalled();
      expect(screen.getByTestId("sort-filter-popup")).toBeInTheDocument();
    });
  });

  describe("Requirement 26.6: Outside click detection to close popup", () => {
    it("calls onClose when clicking outside the popup", () => {
      render(
        <div>
          <div data-testid="outside-element">Outside</div>
          <SortFilterPopup {...defaultProps} />
        </div>
      );

      fireEvent.mouseDown(screen.getByTestId("outside-element"));

      expect(defaultProps.onClose).toHaveBeenCalled();
    });

    it("does not close when clicking inside the popup", () => {
      render(<SortFilterPopup {...defaultProps} />);

      fireEvent.mouseDown(screen.getByTestId("sort-filter-popup"));

      expect(defaultProps.onClose).not.toHaveBeenCalled();
    });
  });

  describe("Keyboard navigation", () => {
    it("closes popup when Escape key is pressed", () => {
      render(<SortFilterPopup {...defaultProps} />);

      fireEvent.keyDown(document, { key: "Escape" });

      expect(defaultProps.onClose).toHaveBeenCalled();
    });
  });

  describe("Accessibility", () => {
    it("has proper ARIA attributes", () => {
      render(<SortFilterPopup {...defaultProps} />);

      const popup = screen.getByTestId("sort-filter-popup");
      expect(popup).toHaveAttribute("role", "dialog");
      expect(popup).toHaveAttribute("aria-label", "Sort and filter options");
    });

    it("sort options have aria-pressed attribute", () => {
      render(<SortFilterPopup {...defaultProps} />);

      const activeOption = screen.getByTestId("sort-option-name-asc");
      const inactiveOption = screen.getByTestId("sort-option-date-newest");

      expect(activeOption).toHaveAttribute("aria-pressed", "true");
      expect(inactiveOption).toHaveAttribute("aria-pressed", "false");
    });
  });
});
