import './index.css';
import { lazy, Suspense, useState, useCallback } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';

import { ToastProvider } from './context/ToastContext';
import { ThemeProvider } from './context/ThemeContext';
import { DataServiceProvider } from './context/DataServiceContext';
import { ThemeSynchronizer } from './core/engine';
import { MainLayout } from './layouts';
import { 
  FAB,
  AppHeader,
  CreateProjectModal,
  CreateTaskListModal,
  CreateTaskModal 
} from './components/organisms';

// Lazy load view components for code splitting
// Requirements: 1.1, 3.1, 4.1, 5.1, 6.1, 7.1, 8.1
const DashboardView = lazy(() => import('./views/DashboardView'));
const ShowcasePage = lazy(() => import('./pages/ShowcasePage').then(m => ({ default: m.ShowcasePage })));
const ProjectsView = lazy(() => import('./views/ProjectsView'));
const SingleProjectView = lazy(() => import('./views/SingleProjectView'));
const TaskListsView = lazy(() => import('./views/TaskListsView'));
const SingleTaskListView = lazy(() => import('./views/SingleTaskListView'));
const TasksView = lazy(() => import('./views/TasksView'));
const SingleTaskView = lazy(() => import('./views/SingleTaskView'));

/**
 * AppContent Component
 * 
 * Inner component that handles FAB state and modals.
 * Separated to allow hooks to be used within the provider context.
 * 
 * Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 9.6
 */
function AppContent() {
  // Modal state
  const [isCreateProjectModalOpen, setIsCreateProjectModalOpen] = useState(false);
  const [isCreateTaskListModalOpen, setIsCreateTaskListModalOpen] = useState(false);
  const [isCreateTaskModalOpen, setIsCreateTaskModalOpen] = useState(false);

  // FAB handlers
  const handleAddProject = useCallback(() => {
    setIsCreateProjectModalOpen(true);
  }, []);

  const handleAddTaskList = useCallback(() => {
    setIsCreateTaskListModalOpen(true);
  }, []);

  const handleAddTask = useCallback(() => {
    setIsCreateTaskModalOpen(true);
  }, []);

  // Modal close handlers
  const handleCloseProjectModal = useCallback(() => {
    setIsCreateProjectModalOpen(false);
  }, []);

  const handleCloseTaskListModal = useCallback(() => {
    setIsCreateTaskListModalOpen(false);
  }, []);

  const handleCloseTaskModal = useCallback(() => {
    setIsCreateTaskModalOpen(false);
  }, []);

  // Success handlers - refresh data after creation
  const handleProjectSuccess = useCallback(() => {
    // Data will be refreshed by the views that need it
    setIsCreateProjectModalOpen(false);
  }, []);

  const handleTaskListSuccess = useCallback(() => {
    // Data will be refreshed by the views that need it
    setIsCreateTaskListModalOpen(false);
  }, []);

  const handleTaskSuccess = useCallback(() => {
    // Data will be refreshed by the views that need it
    setIsCreateTaskModalOpen(false);
  }, []);

  // FAB component with handlers wired up
  // Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 9.6
  const fabComponent = (
    <FAB
      onAddProject={handleAddProject}
      onAddTaskList={handleAddTaskList}
      onAddTask={handleAddTask}
      showTaskButton={true}
    />
  );

  return (
    <>
      <MainLayout 
        showHeader={true} 
        header={<AppHeader title="Task Manager" showLogo={true} logoVariant="both" />}
        fab={fabComponent}
      >
        <Suspense fallback={
          <div className="flex items-center justify-center min-h-screen">
            <div className="text-[var(--text-muted)]">Loading...</div>
          </div>
        }>
          <Routes>
            {/* Dashboard - Requirements: 1.1 */}
            <Route path="/" element={<DashboardView />} />
            
            {/* Projects - Requirements: 3.1, 4.1 */}
            <Route path="/projects" element={<ProjectsView />} />
            <Route path="/projects/:projectId" element={<SingleProjectView />} />
            
            {/* Task Lists - Requirements: 5.1, 6.1 */}
            <Route path="/lists" element={<TaskListsView />} />
            <Route path="/lists/:taskListId" element={<SingleTaskListView />} />
            
            {/* Tasks - Requirements: 7.1, 8.1 */}
            <Route path="/tasks" element={<TasksView />} />
            <Route path="/tasks/:taskId" element={<SingleTaskView />} />
            
            {/* Design System Showcase */}
            <Route path="/showcase" element={<ShowcasePage />} />
          </Routes>
        </Suspense>
      </MainLayout>

      {/* Create Project Modal - Requirements: 9.3 */}
      <CreateProjectModal
        isOpen={isCreateProjectModalOpen}
        onClose={handleCloseProjectModal}
        onSuccess={handleProjectSuccess}
      />

      {/* Create Task List Modal - Requirements: 9.4 */}
      <CreateTaskListModal
        isOpen={isCreateTaskListModalOpen}
        onClose={handleCloseTaskListModal}
        onSuccess={handleTaskListSuccess}
      />

      {/* Create Task Modal - Requirements: 9.5 */}
      <CreateTaskModal
        isOpen={isCreateTaskModalOpen}
        taskListId=""
        onClose={handleCloseTaskModal}
        onSuccess={handleTaskSuccess}
      />
    </>
  );
}

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
 * - FAB: Floating action button for quick create actions (Requirements: 9.1-9.6)
 * 
 * Routes:
 * - /                    : DashboardView (main view) - Requirements: 1.1
 * - /projects            : ProjectsView (projects grid) - Requirements: 3.1
 * - /projects/:projectId : SingleProjectView (project details) - Requirements: 4.1
 * - /lists               : TaskListsView (task lists grouped by project) - Requirements: 5.1
 * - /lists/:taskListId   : SingleTaskListView (task list details) - Requirements: 6.1
 * - /tasks               : TasksView (tasks grouped by task list) - Requirements: 7.1
 * - /tasks/:taskId       : SingleTaskView (task details) - Requirements: 8.1
 * - /showcase            : ShowcasePage (design system showcase)
 * 
 * Requirements: 1.1, 3.1, 4.1, 5.1, 6.1, 7.1, 8.1, 9.1, 9.2, 9.3, 9.4, 9.5, 9.6, 10.1, 10.2, 10.3, 11.4
 */
function App() {
  return (
    <ThemeProvider>
      <ThemeSynchronizer>
        <ToastProvider>
          <DataServiceProvider>
            <BrowserRouter>
              <AppContent />
            </BrowserRouter>
          </DataServiceProvider>
        </ToastProvider>
      </ThemeSynchronizer>
    </ThemeProvider>
  );
}

export default App;
