import React, { useState, KeyboardEvent } from 'react';

interface TagInputProps {
  tags: string[];
  onChange: (tags: string[]) => void;
  maxTags?: number;
  maxLength?: number;
  placeholder?: string;
  disabled?: boolean;
}

const TagInput: React.FC<TagInputProps> = ({
  tags,
  onChange,
  maxTags = 10,
  maxLength = 50,
  placeholder = 'Add a tag...',
  disabled = false,
}) => {
  const [inputValue, setInputValue] = useState('');
  const [error, setError] = useState('');

  const validateTag = (tag: string): string | null => {
    if (!tag.trim()) {
      return 'Tag cannot be empty';
    }
    if (tag.length > maxLength) {
      return `Tag cannot exceed ${maxLength} characters`;
    }
    if (tags.includes(tag)) {
      return 'Tag already exists';
    }
    if (tags.length >= maxTags) {
      return `Maximum ${maxTags} tags allowed`;
    }
    // Validate characters (unicode letters, numbers, emoji, hyphens, underscores)
    const validPattern = /^[\p{L}\p{N}\p{Emoji}_-]+$/u;
    if (!validPattern.test(tag)) {
      return 'Tag can only contain letters, numbers, emoji, hyphens, and underscores';
    }
    return null;
  };

  const handleAddTag = () => {
    const trimmedTag = inputValue.trim();
    if (!trimmedTag) return;

    const validationError = validateTag(trimmedTag);
    if (validationError) {
      setError(validationError);
      return;
    }

    onChange([...tags, trimmedTag]);
    setInputValue('');
    setError('');
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleAddTag();
    } else if (e.key === 'Backspace' && !inputValue && tags.length > 0) {
      // Remove last tag on backspace if input is empty
      onChange(tags.slice(0, -1));
    }
  };

  const handleRemoveTag = (tagToRemove: string) => {
    onChange(tags.filter((tag) => tag !== tagToRemove));
  };

  return (
    <div>
      <div
        style={{
          display: 'flex',
          flexWrap: 'wrap',
          gap: '0.5rem',
          padding: '0.5rem',
          border: '1px solid #ccc',
          borderRadius: '4px',
          backgroundColor: disabled ? '#f5f5f5' : 'white',
          minHeight: '42px',
          alignItems: 'center',
        }}
      >
        {tags.map((tag) => (
          <span
            key={tag}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '0.25rem',
              padding: '0.25rem 0.5rem',
              backgroundColor: '#61dafb',
              color: '#282c34',
              borderRadius: '4px',
              fontSize: '0.875rem',
              fontWeight: '500',
            }}
          >
            {tag}
            {!disabled && (
              <button
                type="button"
                onClick={() => handleRemoveTag(tag)}
                style={{
                  background: 'none',
                  border: 'none',
                  color: '#282c34',
                  cursor: 'pointer',
                  padding: '0',
                  marginLeft: '0.25rem',
                  fontSize: '1rem',
                  lineHeight: '1',
                  fontWeight: 'bold',
                }}
                aria-label={`Remove tag ${tag}`}
              >
                ×
              </button>
            )}
          </span>
        ))}
        {!disabled && (
          <input
            type="text"
            value={inputValue}
            onChange={(e) => {
              setInputValue(e.target.value);
              setError('');
            }}
            onKeyDown={handleKeyDown}
            placeholder={tags.length === 0 ? placeholder : ''}
            disabled={disabled || tags.length >= maxTags}
            style={{
              flex: 1,
              minWidth: '120px',
              border: 'none',
              outline: 'none',
              fontSize: '1rem',
              padding: '0.25rem',
              backgroundColor: 'transparent',
            }}
          />
        )}
      </div>
      {error && (
        <div style={{ color: '#f44336', fontSize: '0.875rem', marginTop: '0.25rem' }}>
          {error}
        </div>
      )}
      {!disabled && tags.length < maxTags && (
        <div style={{ fontSize: '0.75rem', color: '#666', marginTop: '0.25rem' }}>
          Press Enter to add tag. {tags.length}/{maxTags} tags used.
        </div>
      )}
    </div>
  );
};

export default TagInput;
