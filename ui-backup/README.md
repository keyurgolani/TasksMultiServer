# Task Manager UI

React-based web interface for the Task Management System.

## Setup

### Prerequisites

- Node.js 18+
- npm or yarn

### Installation

```bash
npm install
```

### Configuration

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

Edit `.env` to set the API base URL:

```
VITE_API_BASE_URL=http://localhost:8000
```

### Development

Start the development server:

```bash
npm run dev
```

The UI will be available at `http://localhost:3000`.

### Build

Build for production:

```bash
npm run build
```

Preview production build:

```bash
npm run preview
```

## Architecture

### Technology Stack

- **React 18** - UI framework
- **TypeScript** - Type safety
- **Vite** - Build tool and dev server
- **React Router** - Client-side routing
- **Axios** - HTTP client
- **React Context** - State management

### Project Structure

```
ui/
├── src/
│   ├── api/              # API client and service layer
│   │   ├── client.ts     # Axios instance with interceptors
│   │   └── services.ts   # API service functions
│   ├── components/       # Reusable UI components
│   │   └── Layout.tsx    # Main layout with header/footer
│   ├── context/          # React Context for state management
│   │   └── AppContext.tsx # Global app state and actions
│   ├── pages/            # Page components (routes)
│   │   ├── ProjectsPage.tsx
│   │   ├── TaskListsPage.tsx
│   │   ├── TasksPage.tsx
│   │   └── TaskDetailPage.tsx
│   ├── types/            # TypeScript type definitions
│   │   └── index.ts      # Entity types and enums
│   ├── App.tsx           # Root component with routing
│   ├── main.tsx          # Application entry point
│   ├── index.css         # Global styles
│   └── vite-env.d.ts     # Vite environment types
├── index.html            # HTML template
├── package.json          # Dependencies and scripts
├── tsconfig.json         # TypeScript configuration
├── vite.config.ts        # Vite configuration
└── .env.example          # Environment variables template
```

### State Management

The application uses React Context API for global state management:

- **AppContext**: Provides global state and actions for projects, task lists, and tasks
- **useApp hook**: Custom hook to access context in components

### API Integration

- **API Client**: Configured Axios instance with interceptors for error handling
- **Service Layer**: Organized API calls by entity (projects, task lists, tasks)
- **Type Safety**: Full TypeScript types for all API requests and responses

### Routing

Routes are defined in `App.tsx`:

- `/` - Projects list
- `/projects/:projectId/task-lists` - Task lists for a project
- `/task-lists/:taskListId/tasks` - Tasks for a task list
- `/tasks/:taskId` - Task detail view

## Features Implemented

### Task 15.1 - React Application Setup

- ✅ React project with TypeScript
- ✅ API client configured with Axios
- ✅ React Router for navigation
- ✅ React Context for state management
- ✅ Type definitions for all entities
- ✅ Basic layout with header, footer, and error handling
- ✅ Placeholder pages for all routes

## Next Steps

The following tasks will implement the actual UI components:

- **15.2** - ProjectList component
- **15.3** - TaskListView component
- **15.4** - TaskView component
- **15.5** - TaskDetail component
- **15.6** - ReadyTasksPanel component
- **15.7** - DependencyGraph component
- **15.8** - Error handling UI
- **15.9** - End-to-end tests

## Development Notes

- All components use TypeScript with strict type checking
- No `any` types allowed
- API calls go through the centralized service layer
- Error handling is managed at the context level
- Loading states are tracked in the global context
