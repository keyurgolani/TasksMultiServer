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
  filterButtonRef: React.RefObject<HTMLButtonElement>;
  children?: React.ReactNode; // For the Popover component
  placeholder?: string;
}

export const SearchFilterToolbar: React.FC<SearchFilterToolbarProps> = ({
  searchQuery,
  onSearchChange,
  onClearSearch,
  isFilterOpen,
  setIsFilterOpen,
  isFilterActive,
  filterButtonRef,
  children,
  placeholder = "Search..."
}) => {
  return (
    <div className={styles.toolbar}>
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
        >
          Filter
        </Button>
        {children}
      </div>
    </div>
  );
};
