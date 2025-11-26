import React from 'react';

export interface FormErrorProps {
  message: string;
  field?: string;
}

const FormError: React.FC<FormErrorProps> = ({ message, field }) => {
  return (
    <div
      style={{
        padding: '0.75rem',
        backgroundColor: '#f8d7da',
        color: '#721c24',
        border: '1px solid #f5c6cb',
        borderRadius: '4px',
        marginBottom: '1rem',
        fontSize: '0.875rem',
      }}
    >
      <strong>⚠️ Error{field ? ` in ${field}` : ''}:</strong> {message}
    </div>
  );
};

export default FormError;
