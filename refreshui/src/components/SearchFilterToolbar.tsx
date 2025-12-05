import React from 'react';
import { Search, Filter } from 'lucide-react';
import { Input, Button } from './ui';
import styles from './SearchFilterToolbar.module.css';

interface SearchFilterToolbarProps {
  searchQuery: string;
  onSearchChange: (value: string) => void;
  onClearSearch: () => void;
  isFilterOpen: boolean;
  setIsFilterOpen: (isOpen: boolean) => void;
  isFilterActive: boolean;
  onReset?: () => void;
  filterButtonRef: React.RefObject<HTMLButtonElement>;
  children?: React.ReactNode; // For the Popover component
  placeholder?: string;
  className?: string;
}

export const SearchFilterToolbar: React.FC<SearchFilterToolbarProps> = ({
  searchQuery,
  onSearchChange,
  onClearSearch,
  isFilterOpen,
  setIsFilterOpen,
  isFilterActive,
  onReset,
  filterButtonRef,
  children,
  placeholder = "Search...",
  className
}) => {
  return (
    <div className={`${styles.toolbar} ${className || ''}`}>
      <div className={styles.searchContainer}>
        <Input
          icon={<Search size={16} />}
          placeholder={placeholder}
          value={searchQuery}
          onChange={(e) => onSearchChange(e.target.value)}
          onClear={onClearSearch}
        />
      </div>
      <div className={styles.filterContainer}>
        <Button
          ref={filterButtonRef}
          variant={isFilterActive ? "primary" : "secondary"}
          icon={<Filter size={16} />}
          onClick={() => setIsFilterOpen(!isFilterOpen)}
          className={styles.filterButton}
        >
          Sort & Filter
          {isFilterActive && onReset && (
            <span 
              className={styles.resetIcon} 
              onClick={(e) => {
                e.stopPropagation();
                onReset();
              }}
            >
              ×
            </span>
          )}
        </Button>
        {children}
      </div>
    </div>
  );
};
