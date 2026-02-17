import React from 'react';

interface TagFilterProps {
  availableTags: string[];
  selectedTags: string[];
  onTagSelect: (tag: string) => void;
  onTagDeselect: (tag: string) => void;
  onClearAll: () => void;
}

const TagFilter: React.FC<TagFilterProps> = ({
  availableTags,
  selectedTags,
  onTagSelect,
  onTagDeselect,
  onClearAll,
}) => {
  const isSelected = (tag: string) => selectedTags.includes(tag);

  const handleTagClick = (tag: string) => {
    if (isSelected(tag)) {
      onTagDeselect(tag);
    } else {
      onTagSelect(tag);
    }
  };

  if (availableTags.length === 0) {
    return null;
  }

  return (
    <div style={{ marginBottom: '1rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
        <label style={{ fontWeight: 'bold', fontSize: '0.875rem' }}>
          Filter by Tags:
        </label>
        {selectedTags.length > 0 && (
          <button
            onClick={onClearAll}
            style={{
              padding: '0.25rem 0.5rem',
              backgroundColor: '#f44336',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer',
              fontSize: '0.75rem',
            }}
          >
            Clear All
          </button>
        )}
      </div>
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
        {availableTags.map((tag) => (
          <button
            key={tag}
            onClick={() => handleTagClick(tag)}
            style={{
              padding: '0.25rem 0.75rem',
              backgroundColor: isSelected(tag) ? '#61dafb' : '#e0e0e0',
              color: isSelected(tag) ? '#282c34' : '#666',
              border: isSelected(tag) ? '2px solid #282c34' : '2px solid transparent',
              borderRadius: '16px',
              cursor: 'pointer',
              fontSize: '0.875rem',
              fontWeight: isSelected(tag) ? '600' : '400',
              transition: 'all 0.2s',
            }}
          >
            {tag}
            {isSelected(tag) && ' ✓'}
          </button>
        ))}
      </div>
      {selectedTags.length > 0 && (
        <div style={{ fontSize: '0.75rem', color: '#666', marginTop: '0.5rem' }}>
          Filtering by {selectedTags.length} tag{selectedTags.length !== 1 ? 's' : ''}
        </div>
      )}
    </div>
  );
};

export default TagFilter;
