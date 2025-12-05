import React, { useState, useEffect, useCallback, useMemo } from "react";
import { useDataService } from "../../context/DataServiceContext";
import { MasonryGrid } from "../../layouts/MasonryGrid";
import { TaskListCard, TaskListCardSkeleton } from "../../components/organisms/TaskListCard";
import { EditTaskListModal } from "../../components/organisms/EditTaskListModal";
import { DeleteConfirmationDialog } from "../../components/organisms/DeleteConfirmationDialog";
import { SearchBar } from "../../components/molecules/SearchBar";
import { FilterChips } from "../../components/molecules/FilterChips";
import { Typography } from "../../components/atoms/Typography";
import { cn } from "../../lib/utils";
import type { TaskList, Project } from "../../core/types/entities";
import type { TaskListStats } from "../../services/types";

/**
 * TaskListView Component
 *
 * A view component that displays task lists for a selected project
 * with completion statistics in a masonry grid layout.
 *
 * Requirements: 10.2
 * - Display task lists for a selected project with completion statistics
 */

export interface TaskListViewProps {
  /** The project to display task lists for */
  project?: Project;
  /** Project ID to load task lists for (alternative to project prop) */
  projectId?: string;
  /** Callback when a task list is clicked */
  onTaskListClick?: (taskList: TaskList) => void;
  /** Callback to navigate back to projects */
  onBackClick?: () => void;
  /** Additional CSS classes */
  className?: string;
}

/** Filter options for task list completion status */
const COMPLETION_FILTER_OPTIONS = [
  { id: "all", label: "All" },
  { id: "not-started", label: "Not Started" },
  { id: "in-progress", label: "In Progress" },
  { id: "completed", label: "Completed" },
];

/** Extended task list type with stats for masonry grid */
interface TaskListWithStats extends TaskList {
  stats?: TaskListStats;
  height: number;
}

/**
 * Calculates estimated card height based on task list data
 */
const estimateCardHeight = (taskList: TaskList, stats?: TaskListStats): number => {
  let height = 100; // Base height for name
  if (taskList.description) height += 40;
  if (stats) height += 160; // Stats section with progress bar and breakdown
  return height;
};

/**
 * Determines completion status category based on stats
 */
const getCompletionStatus = (stats?: TaskListStats): string => {
  if (!stats || stats.taskCount === 0) return "not-started";
  if (stats.completionPercentage >= 100) return "completed";
  if (stats.completionPercentage > 0) return "in-progress";
  return "not-started";
};


/**
 * TaskListView component
 */
export const TaskListView: React.FC<TaskListViewProps> = ({
  project: projectProp,
  projectId: projectIdProp,
  onTaskListClick,
  onBackClick,
  className,
}) => {
  const { dataService } = useDataService();

  // State
  const [project, setProject] = useState<Project | null>(projectProp ?? null);
  const [taskLists, setTaskLists] = useState<TaskList[]>([]);
  const [taskListStats, setTaskListStats] = useState<Map<string, TaskListStats>>(
    new Map()
  );
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedFilters, setSelectedFilters] = useState<string[]>(["all"]);

  // Edit/Delete modal state
  const [editingTaskList, setEditingTaskList] = useState<TaskList | null>(null);
  const [deletingTaskList, setDeletingTaskList] = useState<TaskList | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);

  // Determine the project ID to use
  const projectId = projectProp?.id ?? projectIdProp;

  /**
   * Load project if only projectId is provided
   */
  const loadProject = useCallback(async () => {
    if (projectProp) {
      setProject(projectProp);
      return;
    }

    if (!projectIdProp) {
      setError("No project specified");
      setIsLoading(false);
      return;
    }

    try {
      const loadedProject = await dataService.getProject(projectIdProp);
      setProject(loadedProject);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to load project"
      );
    }
  }, [dataService, projectProp, projectIdProp]);

  /**
   * Load task lists and their stats
   */
  const loadTaskLists = useCallback(async () => {
    if (!projectId) return;

    setIsLoading(true);
    setError(null);

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
            // Stats loading failure is non-critical
            console.warn(`Failed to load stats for task list ${taskList.id}`);
          }
        })
      );
      setTaskListStats(statsMap);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to load task lists"
      );
    } finally {
      setIsLoading(false);
    }
  }, [dataService, projectId]);

  // Load project on mount if needed
  useEffect(() => {
    loadProject();
  }, [loadProject]);

  // Load task lists when project is available
  useEffect(() => {
    if (projectId) {
      loadTaskLists();
    }
  }, [projectId, loadTaskLists]);

  /**
   * Handle search query change
   */
  const handleSearchChange = useCallback((value: string) => {
    setSearchQuery(value);
  }, []);

  /**
   * Handle filter selection change
   */
  const handleFilterChange = useCallback((selected: string[]) => {
    // If "all" is selected, clear other filters
    if (selected.includes("all") && !selectedFilters.includes("all")) {
      setSelectedFilters(["all"]);
    } else if (selected.length === 0) {
      // If nothing selected, default to "all"
      setSelectedFilters(["all"]);
    } else {
      // Remove "all" if other filters are selected
      setSelectedFilters(selected.filter((id) => id !== "all"));
    }
  }, [selectedFilters]);

  /**
   * Handle edit action on a task list
   * Requirements: 23.3 - Open the corresponding edit modal when edit button is clicked
   */
  const handleEditTaskList = useCallback((taskList: TaskList) => {
    setEditingTaskList(taskList);
  }, []);

  /**
   * Handle delete action on a task list
   * Requirements: 23.4 - Open the corresponding confirmation dialog when delete button is clicked
   */
  const handleDeleteTaskList = useCallback((taskList: TaskList) => {
    setDeletingTaskList(taskList);
  }, []);

  /**
   * Handle edit modal close
   */
  const handleEditModalClose = useCallback(() => {
    setEditingTaskList(null);
  }, []);

  /**
   * Handle edit modal success - reload task lists to reflect changes
   */
  const handleEditSuccess = useCallback(() => {
    setEditingTaskList(null);
    loadTaskLists();
  }, [loadTaskLists]);

  /**
   * Handle delete confirmation dialog close
   */
  const handleDeleteDialogClose = useCallback(() => {
    setDeletingTaskList(null);
  }, []);

  /**
   * Handle delete confirmation - delete the task list and reload
   */
  const handleDeleteConfirm = useCallback(async () => {
    if (!deletingTaskList) return;

    setIsDeleting(true);
    try {
      await dataService.deleteTaskList(deletingTaskList.id);
      setDeletingTaskList(null);
      loadTaskLists();
    } catch (err) {
      console.error("Failed to delete task list:", err);
      // Keep dialog open on error so user can retry or cancel
    } finally {
      setIsDeleting(false);
    }
  }, [deletingTaskList, dataService, loadTaskLists]);

  /**
   * Filter task lists based on search query and filters
   */
  const filteredTaskLists = useMemo(() => {
    return taskLists.filter((taskList) => {
      // Search filter
      if (searchQuery) {
        const query = searchQuery.toLowerCase();
        const matchesName = taskList.name.toLowerCase().includes(query);
        const matchesDescription = taskList.description
          ?.toLowerCase()
          .includes(query);
        if (!matchesName && !matchesDescription) {
          return false;
        }
      }

      // Completion status filter
      if (!selectedFilters.includes("all")) {
        const stats = taskListStats.get(taskList.id);
        const status = getCompletionStatus(stats);
        if (!selectedFilters.includes(status)) {
          return false;
        }
      }

      return true;
    });
  }, [taskLists, searchQuery, selectedFilters, taskListStats]);

  /**
   * Prepare task lists for masonry grid with stats and height
   */
  const taskListsWithStats: TaskListWithStats[] = useMemo(() => {
    return filteredTaskLists.map((taskList) => {
      const stats = taskListStats.get(taskList.id);
      return {
        ...taskList,
        stats,
        height: estimateCardHeight(taskList, stats),
      };
    });
  }, [filteredTaskLists, taskListStats]);

  /**
   * Render a task list card
   * Requirements: 23.3, 23.4 - Wire up edit and delete handlers to card actions
   */
  const renderTaskListCard = useCallback(
    (taskList: TaskListWithStats) => (
      <TaskListCard
        taskList={taskList}
        stats={taskList.stats}
        onClick={() => onTaskListClick?.(taskList)}
        onEdit={handleEditTaskList}
        onDelete={handleDeleteTaskList}
        spotlight
        tilt
      />
    ),
    [onTaskListClick, handleEditTaskList, handleDeleteTaskList]
  );

  /**
   * Render loading skeleton
   * Requirements: 10.5 - Display skeleton placeholders matching expected content layout
   */
  const renderLoadingSkeleton = () => (
    <div 
      className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4"
      data-testid="tasklist-view-loading"
      aria-busy="true"
      aria-label="Loading task lists"
    >
      {Array.from({ length: 6 }).map((_, index) => (
        <TaskListCardSkeleton key={index} />
      ))}
    </div>
  );

  /**
   * Render empty state
   */
  const renderEmptyState = () => (
    <div
      className="flex flex-col items-center justify-center py-16 text-center"
      data-testid="tasklist-view-empty"
    >
      <svg
        className="w-16 h-16 text-[var(--text-muted)] mb-4"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
        aria-hidden="true"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={1.5}
          d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"
        />
      </svg>
      <Typography variant="h5" color="secondary" className="mb-2">
        {searchQuery || !selectedFilters.includes("all")
          ? "No task lists match your filters"
          : "No task lists yet"}
      </Typography>
      <Typography variant="body-sm" color="muted">
        {searchQuery || !selectedFilters.includes("all")
          ? "Try adjusting your search or filters"
          : "Create your first task list to get started"}
      </Typography>
    </div>
  );

  /**
   * Render error state
   */
  const renderErrorState = () => (
    <div
      className="flex flex-col items-center justify-center py-16 text-center"
      data-testid="tasklist-view-error"
    >
      <svg
        className="w-16 h-16 text-[var(--error)] mb-4"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
        aria-hidden="true"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={1.5}
          d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
        />
      </svg>
      <Typography variant="h5" color="secondary" className="mb-2">
        Failed to load task lists
      </Typography>
      <Typography variant="body-sm" color="muted" className="mb-4">
        {error}
      </Typography>
      <button
        onClick={loadTaskLists}
        className="px-4 py-2 bg-[var(--primary)] text-white rounded-lg hover:opacity-90 transition-opacity"
      >
        Try Again
      </button>
    </div>
  );

  /**
   * Render no project state
   */
  const renderNoProjectState = () => (
    <div
      className="flex flex-col items-center justify-center py-16 text-center"
      data-testid="tasklist-view-no-project"
    >
      <svg
        className="w-16 h-16 text-[var(--text-muted)] mb-4"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
        aria-hidden="true"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={1.5}
          d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z"
        />
      </svg>
      <Typography variant="h5" color="secondary" className="mb-2">
        No project selected
      </Typography>
      <Typography variant="body-sm" color="muted" className="mb-4">
        Select a project to view its task lists
      </Typography>
      {onBackClick && (
        <button
          onClick={onBackClick}
          className="px-4 py-2 bg-[var(--primary)] text-white rounded-lg hover:opacity-90 transition-opacity"
        >
          Go to Projects
        </button>
      )}
    </div>
  );

  // Show no project state if no project is specified
  if (!projectId && !isLoading) {
    return (
      <div className={cn("flex flex-col gap-6", className)} data-testid="tasklist-view">
        {renderNoProjectState()}
      </div>
    );
  }

  return (
    <div
      className={cn("flex flex-col gap-6", className)}
      data-testid="tasklist-view"
    >
      {/* Header */}
      <div className="flex flex-col gap-4">
        <div className="flex items-center gap-4">
          {onBackClick && (
            <button
              onClick={onBackClick}
              className="p-2 rounded-lg hover:bg-[var(--bg-muted)] transition-colors"
              aria-label="Back to projects"
            >
              <svg
                className="w-5 h-5 text-[var(--text-secondary)]"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M15 19l-7-7 7-7"
                />
              </svg>
            </button>
          )}
          <div>
            <Typography variant="h3" color="primary">
              {project?.name ?? "Task Lists"}
            </Typography>
            {project?.description && (
              <Typography variant="body-sm" color="muted" className="mt-1">
                {project.description}
              </Typography>
            )}
          </div>
        </div>

        {/* Search and Filters */}
        <div className="flex flex-col sm:flex-row gap-4">
          <div className="flex-1 max-w-md">
            <SearchBar
              placeholder="Search task lists..."
              value={searchQuery}
              onChange={handleSearchChange}
              debounceMs={300}
            />
          </div>
          <FilterChips
            options={COMPLETION_FILTER_OPTIONS}
            selected={selectedFilters}
            onChange={handleFilterChange}
            multiSelect
            aria-label="Filter by completion status"
          />
        </div>
      </div>

      {/* Completion Statistics Summary */}
      {!isLoading && !error && taskLists.length > 0 && (
        <CompletionStatsSummary
          taskLists={taskLists}
          taskListStats={taskListStats}
        />
      )}

      {/* Content */}
      {isLoading && renderLoadingSkeleton()}

      {error && !isLoading && renderErrorState()}

      {!isLoading && !error && taskListsWithStats.length === 0 && renderEmptyState()}

      {!isLoading && !error && taskListsWithStats.length > 0 && (
        <MasonryGrid
          items={taskListsWithStats}
          renderItem={renderTaskListCard}
          gap={16}
          animateLayout
          layoutId="tasklists-masonry"
        />
      )}

      {/* Results count */}
      {!isLoading && !error && taskLists.length > 0 && (
        <div className="text-center">
          <Typography variant="caption" color="muted">
            Showing {filteredTaskLists.length} of {taskLists.length} task lists
          </Typography>
        </div>
      )}

      {/* Edit Task List Modal - Requirements: 23.3 */}
      {editingTaskList && (
        <EditTaskListModal
          isOpen={!!editingTaskList}
          taskList={editingTaskList}
          onClose={handleEditModalClose}
          onSuccess={handleEditSuccess}
        />
      )}

      {/* Delete Confirmation Dialog - Requirements: 23.4 */}
      {deletingTaskList && (
        <DeleteConfirmationDialog
          isOpen={!!deletingTaskList}
          title="Delete Task List"
          message="Are you sure you want to delete this task list? This will also delete all tasks within it."
          itemName={deletingTaskList.name}
          onConfirm={handleDeleteConfirm}
          onCancel={handleDeleteDialogClose}
          isDestructive
          loading={isDeleting}
        />
      )}
    </div>
  );
};

TaskListView.displayName = "TaskListView";


/**
 * CompletionStatsSummary Component
 *
 * Displays aggregated completion statistics for all task lists
 */
interface CompletionStatsSummaryProps {
  taskLists: TaskList[];
  taskListStats: Map<string, TaskListStats>;
}

const CompletionStatsSummary: React.FC<CompletionStatsSummaryProps> = ({
  taskLists,
  taskListStats,
}) => {
  // Calculate aggregated stats
  const aggregatedStats = useMemo(() => {
    let totalTasks = 0;
    let completedTasks = 0;
    let inProgressTasks = 0;
    let blockedTasks = 0;
    let readyTasks = 0;

    taskLists.forEach((taskList) => {
      const stats = taskListStats.get(taskList.id);
      if (stats) {
        totalTasks += stats.taskCount;
        completedTasks += stats.completedTasks;
        inProgressTasks += stats.inProgressTasks;
        blockedTasks += stats.blockedTasks;
        readyTasks += stats.readyTasks;
      }
    });

    const completionPercentage =
      totalTasks > 0 ? Math.round((completedTasks / totalTasks) * 100) : 0;

    return {
      totalTasks,
      completedTasks,
      inProgressTasks,
      blockedTasks,
      readyTasks,
      completionPercentage,
      taskListCount: taskLists.length,
    };
  }, [taskLists, taskListStats]);

  return (
    <div
      className="p-4 rounded-lg bg-[var(--bg-surface)] border border-[var(--border-default)]"
      data-testid="completion-stats-summary"
    >
      <div className="flex flex-wrap items-center justify-between gap-4">
        {/* Overall Progress */}
        <div className="flex items-center gap-4">
          <div className="relative w-16 h-16">
            <svg className="w-16 h-16 transform -rotate-90" viewBox="0 0 36 36">
              <path
                className="text-[var(--bg-muted)]"
                stroke="currentColor"
                strokeWidth="3"
                fill="none"
                d="M18 2.0845
                  a 15.9155 15.9155 0 0 1 0 31.831
                  a 15.9155 15.9155 0 0 1 0 -31.831"
              />
              <path
                className="text-[var(--primary)]"
                stroke="currentColor"
                strokeWidth="3"
                strokeLinecap="round"
                fill="none"
                strokeDasharray={`${aggregatedStats.completionPercentage}, 100`}
                d="M18 2.0845
                  a 15.9155 15.9155 0 0 1 0 31.831
                  a 15.9155 15.9155 0 0 1 0 -31.831"
              />
            </svg>
            <div className="absolute inset-0 flex items-center justify-center">
              <Typography variant="body-sm" color="primary" className="font-bold">
                {aggregatedStats.completionPercentage}%
              </Typography>
            </div>
          </div>
          <div>
            <Typography variant="h6" color="primary">
              Overall Progress
            </Typography>
            <Typography variant="caption" color="muted">
              {aggregatedStats.completedTasks} of {aggregatedStats.totalTasks} tasks completed
            </Typography>
          </div>
        </div>

        {/* Stats Breakdown */}
        <div className="flex flex-wrap gap-6">
          <div className="text-center">
            <Typography variant="h5" color="primary">
              {aggregatedStats.taskListCount}
            </Typography>
            <Typography variant="caption" color="muted">
              Task Lists
            </Typography>
          </div>
          <div className="text-center">
            <Typography variant="h5" className="text-[var(--success)]">
              {aggregatedStats.completedTasks}
            </Typography>
            <Typography variant="caption" color="muted">
              Completed
            </Typography>
          </div>
          <div className="text-center">
            <Typography variant="h5" className="text-[var(--warning)]">
              {aggregatedStats.inProgressTasks}
            </Typography>
            <Typography variant="caption" color="muted">
              In Progress
            </Typography>
          </div>
          <div className="text-center">
            <Typography variant="h5" className="text-[var(--error)]">
              {aggregatedStats.blockedTasks}
            </Typography>
            <Typography variant="caption" color="muted">
              Blocked
            </Typography>
          </div>
          <div className="text-center">
            <Typography variant="h5" className="text-[var(--info)]">
              {aggregatedStats.readyTasks}
            </Typography>
            <Typography variant="caption" color="muted">
              Ready
            </Typography>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TaskListView;
