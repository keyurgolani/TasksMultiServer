import React, { useState, useEffect, useCallback, useMemo, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { useDataService } from "../../context/DataServiceContext";
import { ProjectCard, ProjectCardSkeleton } from "../../components/organisms/ProjectCard";
import { TaskListCard, TaskListCardSkeleton } from "../../components/organisms/TaskListCard";
import { TaskCard, TaskCardSkeleton } from "../../components/organisms/TaskCard";
import { SearchFilterBar } from "../../components/molecules/SearchFilterBar";
import { SortFilterPopup, type SortOption, type FilterOption } from "../../components/organisms/SortFilterPopup";
import { MasonryGrid } from "../../layouts/MasonryGrid";
import { Typography } from "../../components/atoms/Typography";
import { Icon } from "../../components/atoms/Icon";
import { Badge } from "../../components/atoms/Badge";
import { getReadyTasks } from "../../utils/readyTasks";
import { filterTasks } from "../../utils/filtering";
import { sortTasks, sortTasksByPriorityDescending, type TaskSortField, type SortDirection } from "../../utils/sorting";
import { cn } from "../../lib/utils";
import type { Project, TaskList, Task, TaskStatus, TaskPriority } from "../../core/types/entities";
import type { ProjectStats, TaskListStats } from "../../services/types";
import styles from "./DashboardView.module.css";

/**
 * Default height for task cards in masonry grid
 */
const DEFAULT_TASK_CARD_HEIGHT = 240;

/**
 * Sort options for tasks in the dashboard
 */
const TASK_SORT_OPTIONS: SortOption[] = [
  { id: "title-asc", label: "Title (A-Z)" },
  { id: "title-desc", label: "Title (Z-A)" },
  { id: "priority-asc", label: "Priority (High first)" },
  { id: "priority-desc", label: "Priority (Low first)" },
  { id: "status-asc", label: "Status (Active first)" },
  { id: "status-desc", label: "Status (Completed first)" },
  { id: "createdAt-desc", label: "Newest first" },
  { id: "createdAt-asc", label: "Oldest first" },
];

/**
 * Filter options for tasks in the dashboard
 */
const TASK_FILTER_OPTIONS: FilterOption[] = [
  // Status filters
  { id: "status-NOT_STARTED", label: "Not Started", type: "checkbox", group: "Status" },
  { id: "status-IN_PROGRESS", label: "In Progress", type: "checkbox", group: "Status" },
  { id: "status-BLOCKED", label: "Blocked", type: "checkbox", group: "Status" },
  { id: "status-COMPLETED", label: "Completed", type: "checkbox", group: "Status" },
  // Priority filters
  { id: "priority-CRITICAL", label: "Critical", type: "checkbox", group: "Priority" },
  { id: "priority-HIGH", label: "High", type: "checkbox", group: "Priority" },
  { id: "priority-MEDIUM", label: "Medium", type: "checkbox", group: "Priority" },
  { id: "priority-LOW", label: "Low", type: "checkbox", group: "Priority" },
  { id: "priority-TRIVIAL", label: "Trivial", type: "checkbox", group: "Priority" },
];

/**
 * Parse sort option ID into field and direction
 */
function parseSortOption(sortId: string): { field: TaskSortField; direction: SortDirection } {
  const [field, direction] = sortId.split("-") as [TaskSortField, SortDirection];
  return { field, direction };
}

/**
 * Filter tasks by status and priority based on active filters
 */
function filterTasksByStatusAndPriority(
  tasks: Task[],
  activeFilters: string[]
): Task[] {
  if (activeFilters.length === 0) {
    return tasks;
  }

  const statusFilters = activeFilters
    .filter((f) => f.startsWith("status-"))
    .map((f) => f.replace("status-", "") as TaskStatus);

  const priorityFilters = activeFilters
    .filter((f) => f.startsWith("priority-"))
    .map((f) => f.replace("priority-", "") as TaskPriority);

  return tasks.filter((task) => {
    const statusMatch = statusFilters.length === 0 || statusFilters.includes(task.status);
    const priorityMatch = priorityFilters.length === 0 || priorityFilters.includes(task.priority);
    return statusMatch && priorityMatch;
  });
}

/**
 * DashboardView Component
 *
 * Main dashboard view displaying:
 * - Horizontal scrollable row of ProjectCards at top
 * - Horizontal scrollable row of TaskListCards below projects
 * - Left sidebar for ready tasks
 * - Main content area with SearchFilterBar and TaskCards
 *
 * Requirements: 1.1, 1.4, 1.5
 */

export interface DashboardViewProps {
  /** Callback when a task is clicked */
  onTaskClick?: (task: Task) => void;
  /** Additional CSS classes */
  className?: string;
}

export const DashboardView: React.FC<DashboardViewProps> = ({
  onTaskClick,
  className,
}) => {
  const { dataService } = useDataService();
  const navigate = useNavigate();

  // Data state
  const [projects, setProjects] = useState<Project[]>([]);
  const [projectStats, setProjectStats] = useState<Map<string, ProjectStats>>(new Map());
  const [taskLists, setTaskLists] = useState<TaskList[]>([]);
  const [taskListStats, setTaskListStats] = useState<Map<string, TaskListStats>>(new Map());
  const [tasks, setTasks] = useState<Task[]>([]);
  const [allTasks, setAllTasks] = useState<Task[]>([]);

  // Selection state
  const [selectedProjectId, setSelectedProjectId] = useState<string | null>(null);
  const [selectedTaskListId, setSelectedTaskListId] = useState<string | null>(null);

  // Search/filter state
  const [searchQuery, setSearchQuery] = useState("");
  const [sortFilterPopupOpen, setSortFilterPopupOpen] = useState(false);
  const [activeSortId, setActiveSortId] = useState("priority-asc");
  const [activeFilters, setActiveFilters] = useState<string[]>([]);
  
  // Ref for SortFilterPopup anchor
  const sortFilterButtonRef = useRef<HTMLDivElement>(null);

  // Loading state
  const [isLoadingProjects, setIsLoadingProjects] = useState(true);
  const [isLoadingTaskLists, setIsLoadingTaskLists] = useState(false);
  const [isLoadingTasks, setIsLoadingTasks] = useState(false);

  // Error state
  const [error, setError] = useState<string | null>(null);


  /**
   * Load all projects and their stats
   * Requirements: 1.1 - Display horizontal scrollable row of ProjectCards
   * Requirements: 1.6, 16.1 - Auto-select first project in sorted list on load
   */
  const loadProjects = useCallback(async () => {
    setIsLoadingProjects(true);
    setError(null);

    try {
      const loadedProjects = await dataService.getProjects();
      setProjects(loadedProjects);

      // Load stats for each project
      const statsMap = new Map<string, ProjectStats>();
      await Promise.all(
        loadedProjects.map(async (project) => {
          try {
            const stats = await dataService.getProjectStats(project.id);
            statsMap.set(project.id, stats);
          } catch {
            console.warn(`Failed to load stats for project ${project.id}`);
          }
        })
      );
      setProjectStats(statsMap);

      // Auto-select first project in sorted list (by ready task count descending)
      // Requirements: 1.6, 16.1, 16.3 - Auto-select first project on load
      if (loadedProjects.length > 0) {
        // Sort projects by ready task count descending to find the first one
        const sortedByReadyTasks = [...loadedProjects].sort((a, b) => {
          const readyA = statsMap.get(a.id)?.readyTasks ?? 0;
          const readyB = statsMap.get(b.id)?.readyTasks ?? 0;
          return readyB - readyA;
        });
        // Always set the first sorted project on initial load
        setSelectedProjectId((currentId) => {
          // Only auto-select if no project is currently selected
          if (!currentId) {
            return sortedByReadyTasks[0].id;
          }
          return currentId;
        });
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load projects");
    } finally {
      setIsLoadingProjects(false);
    }
  }, [dataService]);

  /**
   * Load task lists for the selected project
   * Requirements: 1.2 - Filter task lists based on selected project
   * Requirements: 1.6, 16.2 - Auto-select first task list in sorted list on load
   */
  const loadTaskLists = useCallback(async (projectId: string) => {
    setIsLoadingTaskLists(true);

    try {
      const loadedTaskLists = await dataService.getTaskLists(projectId);
      setTaskLists(loadedTaskLists);

      // Load stats for each task list
      const statsMap = new Map<string, TaskListStats>();
      await Promise.all(
        loadedTaskLists.map(async (taskList) => {
          try {
            const stats = await dataService.getTaskListStats(taskList.id);
            statsMap.set(taskList.id, stats);
          } catch {
            console.warn(`Failed to load stats for task list ${taskList.id}`);
          }
        })
      );
      setTaskListStats(statsMap);

      // Auto-select first task list in sorted list (by ready task count descending)
      // Requirements: 1.6, 16.2, 16.4 - Auto-select first task list on load
      if (loadedTaskLists.length > 0) {
        // Sort task lists by ready task count descending to find the first one
        const sortedByReadyTasks = [...loadedTaskLists].sort((a, b) => {
          const readyA = statsMap.get(a.id)?.readyTasks ?? 0;
          const readyB = statsMap.get(b.id)?.readyTasks ?? 0;
          return readyB - readyA;
        });
        
        setSelectedTaskListId((currentId) => {
          // Check if current selection is valid for this project
          const currentSelectionValid = loadedTaskLists.some(
            (tl) => tl.id === currentId
          );
          // If no valid selection, auto-select first sorted task list
          if (!currentSelectionValid) {
            return sortedByReadyTasks[0].id;
          }
          return currentId;
        });
      } else {
        setSelectedTaskListId(null);
      }
    } catch (err) {
      console.error("Failed to load task lists:", err);
    } finally {
      setIsLoadingTaskLists(false);
    }
  }, [dataService]);

  /**
   * Load tasks for the selected task list
   * Requirements: 1.3 - Update main content area to show tasks from selected task list
   */
  const loadTasks = useCallback(async (taskListId: string) => {
    setIsLoadingTasks(true);

    try {
      const loadedTasks = await dataService.getTasks(taskListId);
      setTasks(loadedTasks);

      // Also load all tasks for ready task calculation
      const allLoadedTasks = await dataService.getTasks();
      setAllTasks(allLoadedTasks);
    } catch (err) {
      console.error("Failed to load tasks:", err);
    } finally {
      setIsLoadingTasks(false);
    }
  }, [dataService]);

  // Load projects on mount
  useEffect(() => {
    loadProjects();
  }, [loadProjects]);

  // Load task lists when project selection changes
  useEffect(() => {
    if (selectedProjectId) {
      loadTaskLists(selectedProjectId);
    } else {
      setTaskLists([]);
      setTaskListStats(new Map());
      setSelectedTaskListId(null);
    }
  }, [selectedProjectId, loadTaskLists]);

  // Load tasks when task list selection changes
  useEffect(() => {
    if (selectedTaskListId) {
      loadTasks(selectedTaskListId);
    } else {
      setTasks([]);
    }
  }, [selectedTaskListId, loadTasks]);

  /**
   * Handle project selection
   * Requirements: 1.2 - Highlight ProjectCard and filter task lists
   */
  const handleProjectSelect = useCallback((project: Project) => {
    setSelectedProjectId(project.id);
  }, []);

  /**
   * Handle task list selection
   * Requirements: 1.3 - Highlight TaskListCard and update main content
   */
  const handleTaskListSelect = useCallback((taskList: TaskList) => {
    setSelectedTaskListId(taskList.id);
  }, []);

  /**
   * Handle search query change
   * Requirements: 1.5 - SearchFilterBar in main content area
   */
  const handleSearchChange = useCallback((value: string) => {
    setSearchQuery(value);
  }, []);

  /**
   * Handle task card click - navigate to task detail page
   * Requirements: 1.10 - Navigate to /tasks/{taskId} on TaskCard click
   */
  const handleTaskClick = useCallback((task: Task) => {
    navigate(`/tasks/${task.id}`);
    onTaskClick?.(task);
  }, [navigate, onTaskClick]);

  /**
   * Handle sort/filter popup open
   * Requirements: 1.5 - Wire up to SortFilterPopup
   */
  const handleSortFilterOpen = useCallback(() => {
    setSortFilterPopupOpen((prev) => !prev);
  }, []);

  /**
   * Handle sort/filter popup close
   */
  const handleSortFilterClose = useCallback(() => {
    setSortFilterPopupOpen(false);
  }, []);

  /**
   * Handle sort/filter reset
   * Requirements: 1.5 - Reset sort and filter options
   */
  const handleSortFilterReset = useCallback(() => {
    setActiveSortId("priority-asc");
    setActiveFilters([]);
    setSearchQuery("");
  }, []);

  /**
   * Handle sort option change
   * Requirements: 1.5 - Apply sort options to tasks
   */
  const handleSortChange = useCallback((sortId: string) => {
    setActiveSortId(sortId);
  }, []);

  /**
   * Handle filter option change
   * Requirements: 1.5 - Apply filter options to tasks
   */
  const handleFilterChange = useCallback((filterIds: string[]) => {
    setActiveFilters(filterIds);
  }, []);

  /**
   * Check if any sort/filter is active (non-default)
   */
  const sortFilterActive = useMemo(() => {
    return activeSortId !== "priority-asc" || activeFilters.length > 0;
  }, [activeSortId, activeFilters]);


  /**
   * Filter and sort tasks based on search query, filters, and sort option
   * Requirements: 1.5 - Search and sort/filter controls for tasks
   */
  const filteredTasks = useMemo(() => {
    let result = tasks;

    // Apply search filter
    if (searchQuery) {
      result = filterTasks(result, searchQuery);
    }

    // Apply status and priority filters
    if (activeFilters.length > 0) {
      result = filterTasksByStatusAndPriority(result, activeFilters);
    }

    // Apply sorting
    const { field, direction } = parseSortOption(activeSortId);
    result = sortTasks(result, field, direction);

    return result;
  }, [tasks, searchQuery, activeFilters, activeSortId]);

  /**
   * Get ready tasks for the sidebar, sorted by priority
   * Requirements: 1.4 - Display ready tasks in left sidebar
   * Requirements: 1.14 - Sort ready tasks by priority (CRITICAL > HIGH > MEDIUM > LOW > TRIVIAL)
   */
  const readyTasks = useMemo(() => {
    const ready = getReadyTasks(tasks, allTasks);
    return sortTasksByPriorityDescending(ready);
  }, [tasks, allTasks]);

  /**
   * Sort projects by ready task count in descending order
   * Requirements: 1.7 - Projects with more ready tasks should appear first
   */
  const sortedProjects = useMemo(() => {
    return [...projects].sort((a, b) => {
      const statsA = projectStats.get(a.id);
      const statsB = projectStats.get(b.id);
      const readyA = statsA?.readyTasks ?? 0;
      const readyB = statsB?.readyTasks ?? 0;
      return readyB - readyA; // Descending order
    });
  }, [projects, projectStats]);

  /**
   * Sort task lists by ready task count in descending order
   * Requirements: 1.8 - Task lists with more ready tasks should appear first
   */
  const sortedTaskLists = useMemo(() => {
    return [...taskLists].sort((a, b) => {
      const statsA = taskListStats.get(a.id);
      const statsB = taskListStats.get(b.id);
      const readyA = statsA?.readyTasks ?? 0;
      const readyB = statsB?.readyTasks ?? 0;
      return readyB - readyA; // Descending order
    });
  }, [taskLists, taskListStats]);

  /**
   * Render loading skeleton for project row
   * Uses minimal variant to match the compact ProjectCard display
   */
  const renderProjectsLoading = () => (
    <div className={styles.loadingRow} data-testid="projects-loading">
      {Array.from({ length: 4 }).map((_, index) => (
        <div key={index} className={cn(styles.cardWrapper, styles.minimalCardWrapper)}>
          <ProjectCardSkeleton variant="minimal" />
        </div>
      ))}
    </div>
  );

  /**
   * Render loading skeleton for task list row
   * Uses minimal variant to match the compact TaskListCard display
   */
  const renderTaskListsLoading = () => (
    <div className={styles.loadingRow} data-testid="tasklists-loading">
      {Array.from({ length: 4 }).map((_, index) => (
        <div key={index} className={cn(styles.cardWrapper, styles.minimalCardWrapper)}>
          <TaskListCardSkeleton variant="minimal" />
        </div>
      ))}
    </div>
  );

  /**
   * Render loading skeleton for tasks grid
   */
  const renderTasksLoading = () => (
    <div className={styles.tasksGrid} data-testid="tasks-loading">
      {Array.from({ length: 6 }).map((_, index) => (
        <TaskCardSkeleton key={index} />
      ))}
    </div>
  );

  /**
   * Render empty state for a section (full size, used in main content areas)
   */
  const renderEmptyState = (message: string, subMessage?: string) => (
    <div className={styles.emptyState}>
      <svg
        className={styles.emptyIcon}
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
        aria-hidden="true"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={1.5}
          d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4"
        />
      </svg>
      <Typography variant="h5" color="secondary" className="mb-2">
        {message}
      </Typography>
      {subMessage && (
        <Typography variant="body-sm" color="muted">
          {subMessage}
        </Typography>
      )}
    </div>
  );

  /**
   * Render constrained placeholder for scroll row empty states
   * Requirements: 22.1, 22.2, 22.3
   * - Fixed height matching TaskListCard minimal variant (~56px)
   * - Prevents layout shift when content loads
   * - Centered text with muted color
   */
  const renderConstrainedPlaceholder = (message: string) => (
    <div className={styles.scrollRow}>
      <div 
        className={styles.constrainedPlaceholder}
        data-testid="constrained-placeholder"
      >
        <Typography variant="body-sm" color="muted">
          {message}
        </Typography>
      </div>
    </div>
  );

  /**
   * Render error state
   */
  const renderErrorState = () => (
    <div className={styles.emptyState} data-testid="dashboard-error">
      <svg
        className={styles.emptyIcon}
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
        aria-hidden="true"
        style={{ color: "var(--error)" }}
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={1.5}
          d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
        />
      </svg>
      <Typography variant="h5" color="secondary" className="mb-2">
        Failed to load dashboard
      </Typography>
      <Typography variant="body-sm" color="muted" className="mb-4">
        {error}
      </Typography>
      <button
        onClick={loadProjects}
        className="px-4 py-2 bg-[var(--primary)] text-white rounded-lg hover:opacity-90 transition-opacity"
      >
        Try Again
      </button>
    </div>
  );

  if (error && !isLoadingProjects) {
    return (
      <div className={cn(styles.dashboard, className)} data-testid="dashboard-view">
        {renderErrorState()}
      </div>
    );
  }

  return (
    <div className={cn(styles.dashboard, className)} data-testid="dashboard-view">
      {/* Projects Row - Requirements: 1.1 */}
      <section aria-label="Projects">
        <div className={styles.sectionHeader}>
          <Typography variant="h5" color="primary">
            Projects
          </Typography>
          <Typography variant="caption" color="muted">
            {projects.length} {projects.length === 1 ? "project" : "projects"}
          </Typography>
        </div>
        {isLoadingProjects ? (
          renderProjectsLoading()
        ) : sortedProjects.length === 0 ? (
          /* Requirements: 22.1, 22.3 - Constrained placeholder matching ProjectCard height */
          renderConstrainedPlaceholder("No projects yet")
        ) : (
          <div className={styles.scrollRow} data-testid="projects-row">
            {sortedProjects.map((project) => (
              <div
                key={project.id}
                className={cn(
                  styles.cardWrapper,
                  styles.minimalCardWrapper,
                  selectedProjectId === project.id && styles.selected
                )}
              >
                <ProjectCard
                  project={project}
                  stats={projectStats.get(project.id)}
                  variant="minimal"
                  onClick={() => handleProjectSelect(project)}
                />
              </div>
            ))}
          </div>
        )}
      </section>


      {/* Task Lists Row - Requirements: 1.2 */}
      <section aria-label="Task Lists">
        <div className={styles.sectionHeader}>
          <Typography variant="h5" color="primary">
            Task Lists
          </Typography>
          <Typography variant="caption" color="muted">
            {taskLists.length} {taskLists.length === 1 ? "list" : "lists"}
          </Typography>
        </div>
        {isLoadingTaskLists ? (
          renderTaskListsLoading()
        ) : !selectedProjectId ? (
          /* Requirements: 22.1, 22.3 - Constrained placeholder matching TaskListCard height */
          renderConstrainedPlaceholder("Select a project")
        ) : sortedTaskLists.length === 0 ? (
          /* Requirements: 22.1, 22.3 - Constrained placeholder matching TaskListCard height */
          renderConstrainedPlaceholder("No task lists")
        ) : (
          <div className={styles.scrollRow} data-testid="tasklists-row">
            {sortedTaskLists.map((taskList) => (
              <div
                key={taskList.id}
                className={cn(
                  styles.cardWrapper,
                  styles.minimalCardWrapper,
                  selectedTaskListId === taskList.id && styles.selected
                )}
              >
                <TaskListCard
                  taskList={taskList}
                  stats={taskListStats.get(taskList.id)}
                  variant="minimal"
                  onClick={() => handleTaskListSelect(taskList)}
                />
              </div>
            ))}
          </div>
        )}
      </section>

      {/* Main Content Area - Requirements: 1.4, 1.5 */}
      <div className={styles.mainContent}>
        {/* Ready Tasks Sidebar - Requirements: 1.4 */}
        <aside className={styles.sidebar} aria-label="Ready Tasks">
          <div className={styles.sidebarHeader}>
            <Icon name="Zap" size="sm" className="text-[var(--warning)]" />
            <Typography variant="h6" color="primary">
              Ready Tasks
            </Typography>
            <Badge variant="info" size="sm">
              {readyTasks.length}
            </Badge>
          </div>
          <div className={styles.sidebarContent} data-testid="ready-tasks-sidebar">
            {isLoadingTasks ? (
              Array.from({ length: 3 }).map((_, index) => (
                <TaskCardSkeleton key={index} />
              ))
            ) : readyTasks.length === 0 ? (
              <div className={styles.emptyState}>
                <Typography variant="body-sm" color="muted">
                  No ready tasks
                </Typography>
              </div>
            ) : (
              readyTasks.map((task) => {
                // Find the task list name for this task
                const taskList = taskLists.find((tl) => tl.id === task.taskListId);
                return (
                  <TaskCard
                    key={task.id}
                    task={task}
                    variant="ready"
                    taskListName={taskList?.name}
                    onClick={() => handleTaskClick(task)}
                    spotlight
                    tilt={false}
                  />
                );
              })
            )}
          </div>
        </aside>

        {/* Tasks Content Area - Requirements: 1.5 */}
        <main className={styles.tasksContent} aria-label="Tasks">
          <div className={styles.tasksHeader} ref={sortFilterButtonRef}>
            <SearchFilterBar
              searchValue={searchQuery}
              onSearchChange={handleSearchChange}
              sortFilterActive={sortFilterActive}
              onSortFilterOpen={handleSortFilterOpen}
              onSortFilterReset={handleSortFilterReset}
              searchPlaceholder="Search tasks..."
              sortFilterLabel="Sort & Filter"
            />
            <SortFilterPopup
              isOpen={sortFilterPopupOpen}
              onClose={handleSortFilterClose}
              sortOptions={TASK_SORT_OPTIONS}
              filterOptions={TASK_FILTER_OPTIONS}
              activeSortId={activeSortId}
              activeFilters={activeFilters}
              onSortChange={handleSortChange}
              onFilterChange={handleFilterChange}
              anchorElement={sortFilterButtonRef.current}
            />
          </div>
          {isLoadingTasks ? (
            renderTasksLoading()
          ) : !selectedTaskListId ? (
            renderEmptyState("Select a task list", "Choose a task list to see its tasks")
          ) : filteredTasks.length === 0 ? (
            searchQuery ? (
              renderEmptyState("No matching tasks", "Try adjusting your search query")
            ) : (
              renderEmptyState("No tasks", "This task list has no tasks yet")
            )
          ) : (
            <div className={styles.tasksGridContainer} data-testid="tasks-grid">
              <MasonryGrid
                items={filteredTasks.map((task) => ({
                  ...task,
                  height: DEFAULT_TASK_CARD_HEIGHT,
                }))}
                renderItem={(task) => (
                  <TaskCard
                    task={task}
                    onClick={() => handleTaskClick(task)}
                    spotlight
                    tilt
                    className={styles.taskCardWrapper}
                  />
                )}
                columnBreakpoints={{ 0: 2, 600: 3, 900: 4, 1200: 5 }}
                gap={12}
                animateLayout
              />
            </div>
          )}
        </main>
      </div>
    </div>
  );
};

DashboardView.displayName = "DashboardView";

export default DashboardView;
