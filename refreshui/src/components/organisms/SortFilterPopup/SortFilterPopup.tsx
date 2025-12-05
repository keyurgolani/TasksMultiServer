import React, { useCallback, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Check } from "lucide-react";
import { cn } from "../../../lib/utils";
import { Icon } from "../../atoms/Icon";
import { Typography } from "../../atoms/Typography";
import styles from "./SortFilterPopup.module.css";

/**
 * SortFilterPopup Organism Component
 *
 * A popup component for configuring sort and filter options.
 * Displays sort options and filter criteria with glassmorphism styling.
 * Uses a two-column layout with sort options on the left and filter options on the right.
 * Supports outside click detection and toggle close behavior.
 *
 * Requirements: 26.6, 26.7, 27.1, 27.2, 27.3, 27.4, 27.5, 49.1, 49.2, 49.3, 49.4, 49.5
 * - 26.6: Close popup when user clicks outside
 * - 26.7: Close popup when button is clicked again (toggle)
 * - 27.1: Display sort options and filter criteria
 * - 27.2: Update active sort and emit change event on selection
 * - 27.3: Update active filters and emit change event on selection
 * - 27.4: Apply glassmorphism effect and position relative to button
 * - 27.5: Maintain popup open for multiple selections
 * - 49.1: Display a wider popup with two-column layout
 * - 49.2: Display sort options in the left column
 * - 49.3: Display filter options in the right column
 * - 49.4: Maintain glassmorphism effect and design system styling
 * - 49.5: Gracefully collapse to single-column layout on narrow viewports
 *
 * Property 55: SortFilterPopup Outside Click Close
 * - For any open SortFilterPopup, clicking outside the popup SHALL close it.
 *
 * Property 56: SortFilterPopup Toggle Close
 * - For any open SortFilterPopup, clicking the SortFilterButton again SHALL close the popup.
 *
 * Property 57: SortFilterPopup Selection Persistence
 * - For any SortFilterPopup selection change, the popup SHALL remain open to allow multiple selections.
 */

export interface SortOption {
  /** Unique identifier for the sort option */
  id: string;
  /** Display label for the sort option */
  label: string;
  /** Optional icon to display */
  icon?: React.ReactNode;
}

export interface FilterOption {
  /** Unique identifier for the filter option */
  id: string;
  /** Display label for the filter option */
  label: string;
  /** Type of filter control */
  type: "checkbox" | "radio";
  /** Optional group name for organizing filters */
  group?: string;
}

export interface SortFilterPopupProps {
  /** Whether the popup is open */
  isOpen: boolean;
  /** Callback fired when the popup should close */
  onClose: () => void;
  /** Available sort options */
  sortOptions: SortOption[];
  /** Available filter options */
  filterOptions: FilterOption[];
  /** Currently active sort option ID */
  activeSortId: string;
  /** Currently active filter option IDs */
  activeFilters: string[];
  /** Callback fired when sort selection changes - Requirements: 27.2 */
  onSortChange: (sortId: string) => void;
  /** Callback fired when filter selection changes - Requirements: 27.3 */
  onFilterChange: (filterIds: string[]) => void;
  /** Optional anchor element for positioning */
  anchorElement?: HTMLElement | null;
  /** Additional CSS classes */
  className?: string;
}

/**
 * SortFilterPopup component for configuring sort and filter options
 */
export const SortFilterPopup: React.FC<SortFilterPopupProps> = ({
  isOpen,
  onClose,
  sortOptions,
  filterOptions,
  activeSortId,
  activeFilters,
  onSortChange,
  onFilterChange,
  anchorElement,
  className,
}) => {
  const popupRef = useRef<HTMLDivElement>(null);

  /**
   * Handle sort option selection
   * Requirements: 27.2 - Update active sort and emit change event
   * Property 57: Popup remains open for multiple selections
   */
  const handleSortSelect = useCallback(
    (sortId: string) => {
      onSortChange(sortId);
      // Popup stays open - Requirements: 27.5
    },
    [onSortChange]
  );

  /**
   * Handle filter option toggle
   * Requirements: 27.3 - Update active filters and emit change event
   * Property 57: Popup remains open for multiple selections
   */
  const handleFilterToggle = useCallback(
    (filterId: string, filterType: "checkbox" | "radio", group?: string) => {
      let newFilters: string[];

      if (filterType === "radio" && group) {
        // For radio buttons in a group, replace any existing selection in that group
        const groupFilters = filterOptions
          .filter((f) => f.group === group)
          .map((f) => f.id);
        newFilters = activeFilters.filter((id) => !groupFilters.includes(id));
        newFilters.push(filterId);
      } else if (filterType === "checkbox") {
        // For checkboxes, toggle the selection
        if (activeFilters.includes(filterId)) {
          newFilters = activeFilters.filter((id) => id !== filterId);
        } else {
          newFilters = [...activeFilters, filterId];
        }
      } else {
        // Default radio behavior without group
        newFilters = [filterId];
      }

      onFilterChange(newFilters);
      // Popup stays open - Requirements: 27.5
    },
    [activeFilters, filterOptions, onFilterChange]
  );

  /**
   * Handle outside click detection
   * Requirements: 26.6 - Close popup when user clicks outside
   * Property 55: SortFilterPopup Outside Click Close
   */
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      const target = event.target as Node;

      // Check if click is outside popup
      if (popupRef.current && !popupRef.current.contains(target)) {
        // Also check if click is on the anchor element (handled by toggle)
        if (anchorElement && anchorElement.contains(target)) {
          // Let the button handle the toggle - Requirements: 26.7
          return;
        }
        onClose();
      }
    };

    if (isOpen) {
      // Use mousedown for immediate response
      document.addEventListener("mousedown", handleClickOutside);
    }

    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [isOpen, onClose, anchorElement]);

  // Handle escape key
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape" && isOpen) {
        onClose();
      }
    };
    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, onClose]);

  // Group filter options by their group property
  const groupedFilters = filterOptions.reduce<Record<string, FilterOption[]>>(
    (acc, filter) => {
      const group = filter.group || "Other";
      if (!acc[group]) {
        acc[group] = [];
      }
      acc[group].push(filter);
      return acc;
    },
    {}
  );

  // Determine if we should use two-column layout
  const hasBothSections = sortOptions.length > 0 && filterOptions.length > 0;

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          ref={popupRef}
          className={cn(styles.popup, className)}
          initial={{ opacity: 0, y: -8, scale: 0.95 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          exit={{ opacity: 0, y: -8, scale: 0.95 }}
          transition={{ type: "spring", damping: 25, stiffness: 400 }}
          role="dialog"
          aria-modal="false"
          aria-label="Sort and filter options"
          data-testid="sort-filter-popup"
        >
          {/* Two-column layout container - Requirements: 49.1, 49.2, 49.3 */}
          <div className={hasBothSections ? styles.columnsContainer : undefined}>
            {/* Sort Section (Left Column) - Requirements: 27.1, 27.2, 49.2 */}
            {sortOptions.length > 0 && (
              <div
                className={cn(
                  styles.section,
                  hasBothSections && styles.leftColumn
                )}
                data-testid="sort-section"
              >
                <Typography
                  variant="label"
                  color="muted"
                  className={styles.sectionTitle}
                >
                  Sort By
                </Typography>
                <div className={styles.optionsList}>
                  {sortOptions.map((option) => (
                    <button
                      key={option.id}
                      type="button"
                      className={cn(
                        styles.option,
                        activeSortId === option.id && styles.optionActive
                      )}
                      onClick={() => handleSortSelect(option.id)}
                      aria-pressed={activeSortId === option.id}
                      data-testid={`sort-option-${option.id}`}
                    >
                      {option.icon && (
                        <span className={styles.optionIcon}>{option.icon}</span>
                      )}
                      <span className={styles.optionLabel}>{option.label}</span>
                      {activeSortId === option.id && (
                        <Check size={16} className={styles.checkIcon} />
                      )}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* Filter Section (Right Column) - Requirements: 27.1, 27.3, 49.3 */}
            {filterOptions.length > 0 && (
              <div
                className={cn(
                  styles.section,
                  hasBothSections && styles.rightColumn
                )}
                data-testid="filter-section"
              >
                <Typography
                  variant="label"
                  color="muted"
                  className={styles.sectionTitle}
                >
                  Filter
                </Typography>

                {Object.entries(groupedFilters).map(([group, filters]) => (
                  <div key={group} className={styles.filterGroup}>
                    {Object.keys(groupedFilters).length > 1 && (
                      <Typography
                        variant="caption"
                        color="muted"
                        className={styles.groupTitle}
                      >
                        {group}
                      </Typography>
                    )}
                    <div className={styles.optionsList}>
                      {filters.map((filter) => (
                        <button
                          key={filter.id}
                          type="button"
                          className={cn(
                            styles.option,
                            activeFilters.includes(filter.id) && styles.optionActive
                          )}
                          onClick={() =>
                            handleFilterToggle(filter.id, filter.type, filter.group)
                          }
                          aria-pressed={activeFilters.includes(filter.id)}
                          data-testid={`filter-option-${filter.id}`}
                        >
                          <span className={styles.checkbox}>
                            {filter.type === "checkbox" ? (
                              <Icon
                                name={
                                  activeFilters.includes(filter.id)
                                    ? "CheckSquare"
                                    : "Square"
                                }
                                size="sm"
                              />
                            ) : (
                              <Icon
                                name={
                                  activeFilters.includes(filter.id)
                                    ? "CircleDot"
                                    : "Circle"
                                }
                                size="sm"
                              />
                            )}
                          </span>
                          <span className={styles.optionLabel}>{filter.label}</span>
                        </button>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
};

SortFilterPopup.displayName = "SortFilterPopup";

export default SortFilterPopup;
