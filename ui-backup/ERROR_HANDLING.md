# UI Error Handling Implementation

This document describes the error handling implementation for the Task Management System UI.

## Overview

The UI implements comprehensive error handling that categorizes errors into different types and displays them appropriately based on their severity and context.

## Error Types

The system categorizes errors into the following types (defined in `src/utils/errorHandler.ts`):

1. **VALIDATION** - Input validation errors (HTTP 400)

   - Displayed as form errors inline with forms
   - Example: "Task cannot be created with empty exit criteria list"

2. **BUSINESS_LOGIC** - Business rule violations (HTTP 409)

   - Displayed as notifications
   - Example: "Cannot delete default project"

3. **STORAGE** - Database/storage errors (HTTP 500+)

   - Displayed as both notifications and global error banner
   - Example: "Storage error: Database connection failed"

4. **NOT_FOUND** - Resource not found (HTTP 404)

   - Displayed as notifications
   - Example: "Not found: Project with ID xyz does not exist"

5. **NETWORK** - Network connectivity issues

   - Displayed as both notifications and global error banner
   - Example: "Network error: Unable to reach the server"

6. **UNKNOWN** - Unexpected errors
   - Displayed as notifications
   - Example: "An unexpected error occurred"

## Error Display Components

### 1. Global Error Banner (Layout.tsx)

Located at the top of the page, displays critical errors (storage and network errors) that affect the entire application.

- Red background with dismiss button
- Persists until user dismisses
- Used for critical errors that need immediate attention

### 2. Notification Toasts (Notification.tsx)

Floating notifications in the top-right corner that auto-dismiss after 5 seconds.

- Color-coded by error type
- Icon-based visual indicators
- Stacked when multiple notifications appear
- Used for all error types

### 3. Form Errors (FormError.tsx)

Inline error messages displayed within forms.

- Appears directly above form fields
- Shows field-specific validation errors
- Used exclusively for validation errors (HTTP 400)

## Error Flow

1. **API Call** → Error occurs in backend
2. **API Client** → Axios interceptor logs error details
3. **Context Layer** → `withErrorHandling` wrapper catches error
4. **Error Parser** → `parseApiError` categorizes error by HTTP status
5. **Error Formatter** → `formatErrorMessage` creates user-friendly message
6. **Display** → Error shown via appropriate component(s):
   - Validation errors → Form error + notification
   - Business logic errors → Notification
   - Storage/Network errors → Global banner + notification

## Usage in Components

### Adding Error Handling to Forms

```typescript
import { useApp } from "../context/AppContext";
import FormError from "../components/FormError";

const MyComponent = () => {
  const { formError, clearFormError, createProject } = useApp();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    clearFormError(); // Clear previous errors

    try {
      await createProject({ name: "New Project" });
      // Success handling
    } catch (error) {
      // Error automatically handled by context
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      {formError && (
        <FormError message={formError.message} field={formError.field} />
      )}
      {/* Form fields */}
    </form>
  );
};
```

### Showing Success Notifications

```typescript
const { addNotification } = useApp();

// After successful operation
addNotification("Project created successfully!", "success");
```

## Error Message Examples

### Validation Error (400)

```
⚠️ Error in name: Project name cannot be empty
```

### Business Logic Error (409)

```
❌ Operation failed: Cannot delete default project "Chore"
```

### Storage Error (500)

```
💾 Storage error: Failed to connect to database
```

### Network Error

```
🌐 Network error: Unable to reach the server
```

## Testing Error Handling

To test error handling:

1. **Validation Errors**: Try submitting forms with invalid data
2. **Business Logic Errors**: Try deleting default projects or resetting non-repeatable task lists
3. **Network Errors**: Stop the backend server and try any operation
4. **Storage Errors**: Simulate database failures (requires backend configuration)

## Implementation Files

- `ui/src/utils/errorHandler.ts` - Error parsing and formatting utilities
- `ui/src/components/Notification.tsx` - Toast notification component
- `ui/src/components/FormError.tsx` - Inline form error component
- `ui/src/components/Layout.tsx` - Global error banner
- `ui/src/context/AppContext.tsx` - Error handling logic and state management
- `ui/src/api/client.ts` - Axios interceptor for error logging

## Requirements Validation

This implementation satisfies Requirement 13.5:

> WHEN a user performs an invalid operation via React UI THEN the React UI SHALL display appropriate error messages

The implementation provides:

- ✅ Display validation errors in forms (FormError component)
- ✅ Display business logic errors as notifications (Notification component)
- ✅ Display storage errors as error messages (Global banner + notifications)
