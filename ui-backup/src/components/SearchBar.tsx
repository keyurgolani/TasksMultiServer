import React, { useState } from 'react';
import { Status, Priority, SearchCriteria } from '../types';

interface SearchBarProps {
  onSearch: (criteria: SearchCriteria) => void;
  availableTags: string[];
  projectName?: string;
}

const SearchBar: React.FC<SearchBarProps> = ({ onSearch, availableTags, projectName }) => {
  const [query, setQuery] = useState('');
  const [selectedStatuses, setSelectedStatuses] = useState<Status[]>([]);
  const [selectedPriorities, setSelectedPriorities] = useState<Priority[]>([]);
  const [selectedTags, setSelectedTags] = useState<string[]>([]);
  const [showFilters, setShowFilters] = useState(false);
  const [sortBy, setSortBy] = useState<'relevance' | 'created_at' | 'updated_at' | 'priority'>('relevance');

  const handleSearch = () => {
    const criteria: SearchCriteria = {
      query: query.trim() || undefined,
      status: selectedStatuses.length > 0 ? selectedStatuses : undefined,
      priority: selectedPriorities.length > 0 ? selectedPriorities : undefined,
      tags: selectedTags.length > 0 ? selectedTags : undefined,
      project_name: projectName,
      sort_by: sortBy,
      limit: 50,
      offset: 0,
    };
    onSearch(criteria);
  };

  const handleClear = () => {
    setQuery('');
    setSelectedStatuses([]);
    setSelectedPriorities([]);
    setSelectedTags([]);
    setSortBy('relevance');
    onSearch({});
  };

  const toggleStatus = (status: Status) => {
    setSelectedStatuses((prev) =>
      prev.includes(status) ? prev.filter((s) => s !== status) : [...prev, status]
    );
  };

  const togglePriority = (priority: Priority) => {
    setSelectedPriorities((prev) =>
      prev.includes(priority) ? prev.filter((p) => p !== priority) : [...prev, priority]
    );
  };

  const toggleTag = (tag: string) => {
    setSelectedTags((prev) =>
      prev.includes(tag) ? prev.filter((t) => t !== tag) : [...prev, tag]
    );
  };

  const hasActiveFilters = query || selectedStatuses.length > 0 || selectedPriorities.length > 0 || selectedTags.length > 0;

  return (
    <div style={{
      padding: '1rem',
      backgroundColor: '#f9f9f9',
      border: '1px solid #ddd',
      borderRadius: '8px',
      marginBottom: '1.5rem',
    }}>
      {/* Search Input */}
      <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1rem' }}>
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
          placeholder="Search tasks by title or description..."
          style={{
            flex: 1,
            padding: '0.75rem',
            border: '1px solid #ccc',
            borderRadius: '4px',
            fontSize: '1rem',
          }}
        />
        <button
          onClick={handleSearch}
          style={{
            padding: '0.75rem 1.5rem',
            backgroundColor: '#2196f3',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer',
            fontWeight: 'bold',
          }}
        >
          🔍 Search
        </button>
        <button
          onClick={() => setShowFilters(!showFilters)}
          style={{
            padding: '0.75rem 1.5rem',
            backgroundColor: showFilters ? '#4CAF50' : '#757575',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer',
            fontWeight: 'bold',
          }}
        >
          {showFilters ? '✓ Filters' : '⚙️ Filters'}
        </button>
        {hasActiveFilters && (
          <button
            onClick={handleClear}
            style={{
              padding: '0.75rem 1.5rem',
              backgroundColor: '#f44336',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer',
              fontWeight: 'bold',
            }}
          >
            ✕ Clear
          </button>
        )}
      </div>

      {/* Filter Options */}
      {showFilters && (
        <div style={{
          padding: '1rem',
          backgroundColor: 'white',
          border: '1px solid #ddd',
          borderRadius: '4px',
        }}>
          {/* Status Filter */}
          <div style={{ marginBottom: '1rem' }}>
            <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 'bold', fontSize: '0.875rem' }}>
              Status
            </label>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
              {Object.values(Status).map((status) => (
                <button
                  key={status}
                  onClick={() => toggleStatus(status)}
                  style={{
                    padding: '0.5rem 1rem',
                    backgroundColor: selectedStatuses.includes(status) ? '#2196f3' : '#e0e0e0',
                    color: selectedStatuses.includes(status) ? 'white' : '#333',
                    border: 'none',
                    borderRadius: '4px',
                    cursor: 'pointer',
                    fontSize: '0.875rem',
                  }}
                >
                  {selectedStatuses.includes(status) && '✓ '}
                  {status.replace('_', ' ')}
                </button>
              ))}
            </div>
          </div>

          {/* Priority Filter */}
          <div style={{ marginBottom: '1rem' }}>
            <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 'bold', fontSize: '0.875rem' }}>
              Priority
            </label>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
              {Object.values(Priority).map((priority) => (
                <button
                  key={priority}
                  onClick={() => togglePriority(priority)}
                  style={{
                    padding: '0.5rem 1rem',
                    backgroundColor: selectedPriorities.includes(priority) ? '#ff9800' : '#e0e0e0',
                    color: selectedPriorities.includes(priority) ? 'white' : '#333',
                    border: 'none',
                    borderRadius: '4px',
                    cursor: 'pointer',
                    fontSize: '0.875rem',
                  }}
                >
                  {selectedPriorities.includes(priority) && '✓ '}
                  {priority}
                </button>
              ))}
            </div>
          </div>

          {/* Tags Filter */}
          {availableTags.length > 0 && (
            <div style={{ marginBottom: '1rem' }}>
              <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 'bold', fontSize: '0.875rem' }}>
                Tags
              </label>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
                {availableTags.map((tag) => (
                  <button
                    key={tag}
                    onClick={() => toggleTag(tag)}
                    style={{
                      padding: '0.5rem 1rem',
                      backgroundColor: selectedTags.includes(tag) ? '#4CAF50' : '#e0e0e0',
                      color: selectedTags.includes(tag) ? 'white' : '#333',
                      border: 'none',
                      borderRadius: '4px',
                      cursor: 'pointer',
                      fontSize: '0.875rem',
                    }}
                  >
                    {selectedTags.includes(tag) && '✓ '}
                    🏷️ {tag}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Sort By */}
          <div>
            <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 'bold', fontSize: '0.875rem' }}>
              Sort By
            </label>
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value as any)}
              style={{
                padding: '0.5rem',
                border: '1px solid #ccc',
                borderRadius: '4px',
                fontSize: '0.875rem',
              }}
            >
              <option value="relevance">Relevance</option>
              <option value="created_at">Created Date</option>
              <option value="updated_at">Updated Date</option>
              <option value="priority">Priority</option>
            </select>
          </div>
        </div>
      )}
    </div>
  );
};

export default SearchBar;
