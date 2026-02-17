import React from "react";
import { cn } from "../../../lib/utils";
import { SearchBar } from "../SearchBar";
import type { SearchBarProps } from "../SearchBar";
import { SortFilterButton } from "../SortFilterButton";

/**
 * SearchFilterBar Composite Molecule Component
 *
 * A unified search and filter interface that combines SortFilterButton
 * on the left with SearchBar expanding to fill the remaining width on the right.
 *
 * Requirements: 28.1, 28.2, 28.3, 28.4, 28.5
 * - Displays SortFilterButton on the left and SearchBar on the right
 * - SearchBar expands to fill available width
 * - SortFilterButton maintains fixed width
 * - Applies consistent spacing using design tokens
 * - Forwards change events from child components
 */

export interface SearchFilterBarProps {
  /** Current search input value */
  searchValue: string;
  /** Callback fired when search value changes (after debounce) */
  onSearchChange: (value: string) => void;
  /** Whether any non-default sort or filter is currently active */
  sortFilterActive: boolean;
  /** Callback fired when the sort/filter button is clicked to open popup */
  onSortFilterOpen: () => void;
  /** Callback fired when the sort/filter reset (X) icon is clicked */
  onSortFilterReset: () => void;
  /** Placeholder text for the search input */
  searchPlaceholder?: string;
  /** Label text for the sort/filter button */
  sortFilterLabel?: string;
  /** Debounce delay in milliseconds for search (default: 300ms) */
  searchDebounceMs?: number;
  /** Whether the search bar is disabled */
  searchDisabled?: boolean;
  /** Whether the sort/filter button is disabled */
  sortFilterDisabled?: boolean;
  /** Additional CSS classes for the container */
  className?: string;
  /** Callback fired immediately on search input change (before debounce) */
  onSearchImmediateChange?: SearchBarProps["onImmediateChange"];
  /** Callback fired when the search clear button is clicked */
  onSearchClear?: SearchBarProps["onClear"];
}

/**
 * SearchFilterBar component
 *
 * Combines SortFilterButton and SearchBar into a unified toolbar.
 * The SortFilterButton has fixed width on the left, while SearchBar
 * expands to fill the remaining space on the right.
 */
export const SearchFilterBar: React.FC<SearchFilterBarProps> = ({
  searchValue,
  onSearchChange,
  sortFilterActive,
  onSortFilterOpen,
  onSortFilterReset,
  searchPlaceholder = "Search...",
  sortFilterLabel = "Sort & Filter",
  searchDebounceMs = 300,
  searchDisabled = false,
  sortFilterDisabled = false,
  className,
  onSearchImmediateChange,
  onSearchClear,
}) => {
  return (
    <div
      className={cn(
        // Layout: flex row with items centered
        "flex items-center",
        // Spacing: gap using design token (space-3 = 12px)
        "gap-[var(--space-3)]",
        // Full width container
        "w-full",
        className
      )}
    >
      {/* SortFilterButton - fixed width on left */}
      {/* Requirements: 28.1, 28.3 */}
      <SortFilterButton
        isActive={sortFilterActive}
        onOpenPopup={onSortFilterOpen}
        onReset={onSortFilterReset}
        label={sortFilterLabel}
        disabled={sortFilterDisabled}
        className="flex-shrink-0"
      />

      {/* SearchBar - expands to fill remaining width */}
      {/* Requirements: 28.1, 28.2 */}
      <SearchBar
        value={searchValue}
        onChange={onSearchChange}
        placeholder={searchPlaceholder}
        debounceMs={searchDebounceMs}
        disabled={searchDisabled}
        onImmediateChange={onSearchImmediateChange}
        onClear={onSearchClear}
        className="flex-1 min-w-0"
      />
    </div>
  );
};

SearchFilterBar.displayName = "SearchFilterBar";

export default SearchFilterBar;
