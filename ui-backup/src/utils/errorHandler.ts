// Error types based on HTTP status codes and error responses
export enum ErrorType {
  VALIDATION = 'validation',
  BUSINESS_LOGIC = 'business_logic',
  STORAGE = 'storage',
  NOT_FOUND = 'not_found',
  NETWORK = 'network',
  UNKNOWN = 'unknown',
}

export interface ErrorDetails {
  type: ErrorType;
  message: string;
  field?: string;
  details?: Record<string, unknown>;
}

// Parse error from API response
export function parseApiError(error: unknown): ErrorDetails {
  // Handle axios errors
  if (error && typeof error === 'object' && 'response' in error) {
    const axiosError = error as {
      response?: {
        status: number;
        data?: {
          error?: {
            code?: string;
            message?: string;
            details?: Record<string, unknown>;
          };
          detail?: string;
          message?: string;
        };
      };
      request?: unknown;
      message?: string;
    };

    if (axiosError.response) {
      const { status, data } = axiosError.response;
      
      // Extract error message
      let message = 'An error occurred';
      let field: string | undefined;
      let details: Record<string, unknown> | undefined;

      if (data?.error) {
        message = data.error.message || message;
        details = data.error.details;
        if (details?.field && typeof details.field === 'string') {
          field = details.field;
        }
      } else if (data?.detail) {
        message = data.detail;
      } else if (data?.message) {
        message = data.message;
      }

      // Categorize by status code
      if (status === 400) {
        return {
          type: ErrorType.VALIDATION,
          message,
          field,
          details,
        };
      } else if (status === 404) {
        return {
          type: ErrorType.NOT_FOUND,
          message,
          details,
        };
      } else if (status === 409) {
        return {
          type: ErrorType.BUSINESS_LOGIC,
          message,
          details,
        };
      } else if (status >= 500) {
        return {
          type: ErrorType.STORAGE,
          message: message || 'Server error occurred',
          details,
        };
      }

      return {
        type: ErrorType.UNKNOWN,
        message,
        details,
      };
    } else if (axiosError.request) {
      // Request made but no response
      return {
        type: ErrorType.NETWORK,
        message: 'Network error: Unable to reach the server',
      };
    }
  }

  // Handle generic errors
  if (error instanceof Error) {
    return {
      type: ErrorType.UNKNOWN,
      message: error.message,
    };
  }

  return {
    type: ErrorType.UNKNOWN,
    message: 'An unexpected error occurred',
  };
}

// Format error message for display
export function formatErrorMessage(errorDetails: ErrorDetails): string {
  const { type, message, field } = errorDetails;

  switch (type) {
    case ErrorType.VALIDATION:
      return field ? `Validation error in ${field}: ${message}` : `Validation error: ${message}`;
    case ErrorType.BUSINESS_LOGIC:
      return `Operation failed: ${message}`;
    case ErrorType.STORAGE:
      return `Storage error: ${message}`;
    case ErrorType.NOT_FOUND:
      return `Not found: ${message}`;
    case ErrorType.NETWORK:
      return message;
    default:
      return message;
  }
}
