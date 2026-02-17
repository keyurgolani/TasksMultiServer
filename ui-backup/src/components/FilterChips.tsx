import React from 'react';
import { Status, Priority, SearchCriteria } from '../types';

interface FilterChipsProps {
  criteria: SearchCriteria;
  onRemoveFilter: (filterType: string, value?: string) => void;
}

const FilterChips: React.FC<FilterChipsProps> = ({ criteria, onRemoveFilter }) => {
  const hasFilters = 
    criteria.query || 
    (criteria.status && criteria.status.length > 0) ||
    (criteria.priority && criteria.priority.length > 0) ||
    (criteria.tags && criteria.tags.length > 0);

  if (!hasFilters) {
    return null;
  }

  return (
    <div style={{
      display: 'flex',
      flexWrap: 'wrap',
      gap: '0.5rem',
      marginBottom: '1rem',
      padding: '0.75rem',
      backgroundColor: '#f5f5f5',
      borderRadius: '4px',
    }}>
      <span style={{ fontSize: '0.875rem', fontWeight: 'bold', color: '#666', alignSelf: 'center' }}>
        Active Filters:
      </span>

      {/* Query Filter */}
      {criteria.query && (
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '0.5rem',
          padding: '0.25rem 0.75rem',
          backgroundColor: '#2196f3',
          color: 'white',
          borderRadius: '16px',
          fontSize: '0.875rem',
        }}>
          <span>🔍 "{criteria.query}"</span>
          <button
            onClick={() => onRemoveFilter('query')}
            style={{
              background: 'none',
              border: 'none',
              color: 'white',
              cursor: 'pointer',
              padding: '0',
              fontSize: '1rem',
              lineHeight: '1',
            }}
          >
            ✕
          </button>
        </div>
      )}

      {/* Status Filters */}
      {criteria.status && criteria.status.map((status) => (
        <div
          key={status}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
            padding: '0.25rem 0.75rem',
            backgroundColor: '#9c27b0',
            color: 'white',
            borderRadius: '16px',
            fontSize: '0.875rem',
          }}
        >
          <span>Status: {status.replace('_', ' ')}</span>
          <button
            onClick={() => onRemoveFilter('status', status)}
            style={{
              background: 'none',
              border: 'none',
              color: 'white',
              cursor: 'pointer',
              padding: '0',
              fontSize: '1rem',
              lineHeight: '1',
            }}
          >
            ✕
          </button>
        </div>
      ))}

      {/* Priority Filters */}
      {criteria.priority && criteria.priority.map((priority) => (
        <div
          key={priority}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
            padding: '0.25rem 0.75rem',
            backgroundColor: '#ff9800',
            color: 'white',
            borderRadius: '16px',
            fontSize: '0.875rem',
          }}
        >
          <span>Priority: {priority}</span>
          <button
            onClick={() => onRemoveFilter('priority', priority)}
            style={{
              background: 'none',
              border: 'none',
              color: 'white',
              cursor: 'pointer',
              padding: '0',
              fontSize: '1rem',
              lineHeight: '1',
            }}
          >
            ✕
          </button>
        </div>
      ))}

      {/* Tag Filters */}
      {criteria.tags && criteria.tags.map((tag) => (
        <div
          key={tag}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
            padding: '0.25rem 0.75rem',
            backgroundColor: '#4CAF50',
            color: 'white',
            borderRadius: '16px',
            fontSize: '0.875rem',
          }}
        >
          <span>🏷️ {tag}</span>
          <button
            onClick={() => onRemoveFilter('tag', tag)}
            style={{
              background: 'none',
              border: 'none',
              color: 'white',
              cursor: 'pointer',
              padding: '0',
              fontSize: '1rem',
              lineHeight: '1',
            }}
          >
            ✕
          </button>
        </div>
      ))}
    </div>
  );
};

export default FilterChips;
