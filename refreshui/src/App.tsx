import './index.css';
import { lazy, Suspense } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';

import { ToastProvider } from './context/ToastContext';
import { ThemeProvider } from './context/ThemeContext';
import { DataServiceProvider } from './context/DataServiceContext';
import { ThemeSynchronizer } from './core/engine';
import { MainLayout } from './layouts';

// Lazy load page components for code splitting
const Dashboard = lazy(() => import('./pages/Dashboard').then(m => ({ default: m.Dashboard })));
const ShowcasePage = lazy(() => import('./pages/ShowcasePage').then(m => ({ default: m.ShowcasePage })));
const ProjectsPage = lazy(() => import('./pages/ProjectsPage').then(m => ({ default: m.ProjectsPage })));
const TasksPage = lazy(() => import('./pages/TasksPage').then(m => ({ default: m.TasksPage })));

/**
 * App Component
 * 
 * Main application component that configures routing and providers.
 * 
 * The component hierarchy is:
 * - ThemeProvider: Provides theme context for legacy components
 * - ThemeSynchronizer: Syncs Zustand theme store to CSS variables (Requirements: 1.2, 2.2, 11.4)
 * - ToastProvider: Provides toast notification context
 * - DataServiceProvider: Provides data service for CRUD operations (Requirements: 8.1)
 * - BrowserRouter: Handles client-side routing
 * - MainLayout: Provides consistent layout structure (Requirements: 7.4)
 * 
 * Routes:
 * - / : Dashboard (main view)
 * - /showcase : Design system showcase page
 * - /projects : Projects view with masonry grid
 * - /tasks : Tasks view with filtering
 * 
 * Requirements: 7.4, 8.1, 9.6, 10.1, 10.2, 10.3, 11.4
 */
function App() {
  return (
    <ThemeProvider>
      <ThemeSynchronizer>
        <ToastProvider>
          <DataServiceProvider>
            <BrowserRouter>
              <MainLayout showHeader={false}>
                <Suspense fallback={
                  <div className="flex items-center justify-center min-h-screen">
                    <div className="text-[var(--text-muted)]">Loading...</div>
                  </div>
                }>
                  <Routes>
                    <Route path="/" element={<Dashboard />} />
                    <Route path="/showcase" element={<ShowcasePage />} />
                    <Route path="/projects" element={<ProjectsPage />} />
                    <Route path="/projects/:projectId" element={<ProjectsPage />} />
                    <Route path="/tasks" element={<TasksPage />} />
                    <Route path="/tasks/:taskListId" element={<TasksPage />} />
                  </Routes>
                </Suspense>
              </MainLayout>
            </BrowserRouter>
          </DataServiceProvider>
        </ToastProvider>
      </ThemeSynchronizer>
    </ThemeProvider>
  );
}

export default App;
