# Task Manager UI

A modern React-based user interface for the Task Manager application.

## Development

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Run tests
npm test

# Build for production
npm run build
```

## Environment Variables

- `VITE_USE_MOCK_DATA` - Set to "false" to use the REST API, "true" for mock data (default: "true")
- `VITE_API_BASE_URL` - Base URL for the REST API (default: "http://localhost:8000")

## Docker

The UI can be built and run as a Docker container:

```bash
docker build -t task-manager-ui .
docker run -p 3000:80 task-manager-ui
```
