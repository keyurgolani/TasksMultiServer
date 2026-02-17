import React, { useState, useEffect, useCallback, useMemo, useRef } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useDataService } from "../../context/DataServiceContext";
import { MasonryGrid } from "../../layouts/MasonryGrid";
import { TaskCard, TaskCardSkeleton } from "../../components/organisms/TaskCard";
import { EditTaskListModal } from "../../components/organisms/EditTaskListModal";
import { DeleteConfirmationDialog } from "../../components/organisms/DeleteConfirmationDialog";
import { SearchFilterBar } from "../../components/molecules/SearchFilterBar";
import { SortFilterPopup, type SortOption, type FilterOption } from "../../components/organisms/SortFilterPopup";
import { OverallProgress, type StatusCounts } from "../../components/organisms/OverallProgress";
import { Typography } from "../../components/atoms/Typography";
import { Button } from "../../components/atoms/Button";
import { Icon } from "../../components/atoms/Icon";
import { filterTasks } from "../../utils/filtering";
import { sortTasks, type TaskSortField, type SortDirection } from "../../utils/sorting";
import { cn } from "../../lib/utils";
import type { TaskList, Task, TaskStatus } from "../../core/types/entities";
import type { TaskListStats } from "../../services/types";

/**
 * SingleTaskListView Component
 *
 * A view component for displaying a single task list's details and its tasks.
 * Provides back navigation, search/filter, progress overview, and CRUD operations.
 *
 * Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7, 6.8
 * - 6.1: Display a back navigation button to return to the previous screen
 * - 6.2: Display SearchFilterBar with search and SortFilterButton controls
 * - 6.3: Display an OverallProgress component showing the task list's completion statistics
 * - 6.4: Display all TaskCard components belonging to that task list
 * - 6.5: Display edit and delete buttons for the task list
 * - 6.6: Navigate to /tasks/{taskId} on TaskCard click
 * - 6.7: Open EditTaskListModal on edit button click
 * - 6.8: Open DeleteConfirmationDialog on delete button click
 */

export interface SingleTaskListViewProps {
  /** Task List ID from route params (optional, can also use useParams) */
  taskListId?: string;
  /** Additional CSS classes */
  className?: string;
}

/**
 * Sort options for tasks
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
  { id: "updatedAt-desc", label: "Recently updated" },
  { id: "updatedAt-asc", label: "Least recently updated" },
];


/**
 * Filter options for task status and priority
 */
const TASK_FILTER_OPTIONS: FilterOption[] = [
  { id: "status-not-started", label: "Not Started", type: "checkbox", group: "Status" },
  { id: "status-in-progress", label: "In Progress", type: "checkbox", group: "Status" },
  { id: "status-blocked", label: "Blocked", type: "checkbox", group: "Status" },
  { id: "status-completed", label: "Completed", type: "checkbox", group: "Status" },
  { id: "priority-critical", label: "Critical", type: "checkbox", group: "Priority" },
  { id: "priority-high", label: "High", type: "checkbox", group: "Priority" },
  { id: "priority-medium", label: "Medium", type: "checkbox", group: "Priority" },
  { id: "priority-low", label: "Low", type: "checkbox", group: "Priority" },
  { id: "priority-trivial", label: "Trivial", type: "checkbox", group: "Priority" },
];

/** Extended task type with height for masonry grid */
interface TaskWithHeight extends Task {
  height: number;
}

/**
 * Calculates estimated card height based on task data
 */
const estimateCardHeight = (task: Task): number => {
  let height = 100; // Base height for title and status
  if (task.description) height += 40;
  if (task.exitCriteria && task.exitCriteria.length > 0) height += 50;
  if (task.tags && task.tags.length > 0) height += 30;
  if (task.dependencies && task.dependencies.length > 0) height += 25;
  return height;
};

/**
 * Parse sort option ID into field and direction
 */
function parseSortOption(sortId: string): { field: TaskSortField; direction: SortDirection } {
  const [field, direction] = sortId.split("-") as [TaskSortField, SortDirection];
  return { field, direction };
}

/**
 * Convert TaskListStats to StatusCounts for OverallProgress
 */
function convertToStatusCounts(stats: TaskListStats): StatusCounts {
  const notStarted = Math.max(
    0,
    stats.taskCount - stats.completedTasks - stats.inProgressTasks - stats.blockedTasks
  );
  return {
    completed: stats.completedTasks,
    inProgress: stats.inProgressTasks,
    blocked: stats.blockedTasks,
    notStarted,
  };
}

/**
 * Map filter ID to task status
 */
const STATUS_FILTER_MAP: Record<string, TaskStatus> = {
  "status-not-started": "NOT_STARTED",
  "status-in-progress": "IN_PROGRESS",
  "status-blocked": "BLOCKED",
  "status-completed": "COMPLETED",
};

/**
 * SingleTaskListView component
 */
export const SingleTaskListView: React.FC<SingleTaskListViewProps> = ({
  taskListId: propTaskListId,
  className,
}) => {
  const navigate = useNavigate();
  const params = useParams<{ taskListId: string }>();
  const { dataService } = useDataService();

  // Get task list ID from props or route params
  const taskListId = propTaskListId || params.taskListId;

  // State
  const [taskList, setTaskList] = useState<TaskList | null>(null);
  const [taskListStats, setTaskListStats] = useState<TaskListStats | null>(null);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Search/filter state
  const [searchQuery, setSearchQuery] = useState("");
  const [sortFilterPopupOpen, setSortFilterPopupOpen] = useState(false);
  const [activeSortId, setActiveSortId] = useState("priority-asc");
  const [activeFilters, setActiveFilters] = useState<string[]>([]);

  // Ref for SortFilterPopup anchor
  const sortFilterButtonRef = useRef<HTMLDivElement>(null);

  // Modal state
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);


  /**
   * Load task list and its tasks
   */
  const loadTaskListData = useCallback(async () => {
    if (!taskListId) {
      setError("Task List ID is required");
      setIsLoading(false);
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      // Load task list
      const loadedTaskList = await dataService.getTaskList(taskListId);
      setTaskList(loadedTaskList);

      // Load task list stats
      const stats = await dataService.getTaskListStats(taskListId);
      setTaskListStats(stats);

      // Load tasks for this task list
      const loadedTasks = await dataService.getTasks(taskListId);
      setTasks(loadedTasks);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load task list");
    } finally {
      setIsLoading(false);
    }
  }, [dataService, taskListId]);

  // Load task list data on mount
  useEffect(() => {
    loadTaskListData();
  }, [loadTaskListData]);

  /**
   * Handle back navigation
   * Requirements: 6.1 - Display a back navigation button to return to the previous screen
   */
  const handleBackClick = useCallback(() => {
    navigate(-1);
  }, [navigate]);

  /**
   * Handle search query change
   * Requirements: 6.2 - SearchFilterBar with search controls
   */
  const handleSearchChange = useCallback((value: string) => {
    setSearchQuery(value);
  }, []);

  /**
   * Handle sort/filter popup open
   * Requirements: 6.2 - Wire up to SortFilterPopup
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
   */
  const handleSortFilterReset = useCallback(() => {
    setActiveSortId("priority-asc");
    setActiveFilters([]);
    setSearchQuery("");
  }, []);

  /**
   * Handle sort option change
   */
  const handleSortChange = useCallback((sortId: string) => {
    setActiveSortId(sortId);
  }, []);

  /**
   * Handle filter option change
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
   * Handle task card click
   * Requirements: 6.6 - Navigate to /tasks/{taskId} on TaskCard click
   */
  const handleTaskClick = useCallback((task: Task) => {
    navigate(`/tasks/${task.id}`);
  }, [navigate]);

  /**
   * Handle edit button click
   * Requirements: 6.7 - Open EditTaskListModal on edit button click
   */
  const handleEditClick = useCallback(() => {
    setIsEditModalOpen(true);
  }, []);

  /**
   * Handle delete button click
   * Requirements: 6.8 - Open DeleteConfirmationDialog on delete button click
   */
  const handleDeleteClick = useCallback(() => {
    setIsDeleteDialogOpen(true);
  }, []);

  /**
   * Handle edit modal close
   */
  const handleEditModalClose = useCallback(() => {
    setIsEditModalOpen(false);
  }, []);

  /**
   * Handle edit modal success - reload task list data
   */
  const handleEditSuccess = useCallback(() => {
    setIsEditModalOpen(false);
    loadTaskListData();
  }, [loadTaskListData]);

  /**
   * Handle delete dialog close
   */
  const handleDeleteDialogClose = useCallback(() => {
    setIsDeleteDialogOpen(false);
  }, []);

  /**
   * Handle delete confirmation
   */
  const handleDeleteConfirm = useCallback(async () => {
    if (!taskListId) return;

    setIsDeleting(true);
    try {
      await dataService.deleteTaskList(taskListId);
      setIsDeleteDialogOpen(false);
      navigate("/lists");
    } catch (err) {
      console.error("Failed to delete task list:", err);
    } finally {
      setIsDeleting(false);
    }
  }, [taskListId, dataService, navigate]);


  /**
   * Filter and sort tasks based on search query, filters, and sort option
   */
  const filteredTasks = useMemo(() => {
    let result = tasks;

    // Apply search filter
    if (searchQuery) {
      result = filterTasks(result, searchQuery);
    }

    // Apply status filters
    const statusFilters = activeFilters
      .filter((f) => f.startsWith("status-"))
      .map((f) => STATUS_FILTER_MAP[f])
      .filter(Boolean);

    if (statusFilters.length > 0) {
      result = result.filter((task) => statusFilters.includes(task.status));
    }

    // Apply priority filters
    const priorityFilters = activeFilters
      .filter((f) => f.startsWith("priority-"))
      .map((f) => f.replace("priority-", "").toUpperCase());

    if (priorityFilters.length > 0) {
      result = result.filter((task) => priorityFilters.includes(task.priority));
    }

    // Apply sorting
    const { field, direction } = parseSortOption(activeSortId);
    result = sortTasks(result, field, direction);

    return result;
  }, [tasks, searchQuery, activeFilters, activeSortId]);

  /**
   * Prepare tasks for masonry grid with height
   */
  const tasksWithHeight: TaskWithHeight[] = useMemo(() => {
    return filteredTasks.map((task) => ({
      ...task,
      height: estimateCardHeight(task),
    }));
  }, [filteredTasks]);

  /**
   * Get status counts for OverallProgress
   * Requirements: 6.3 - Display OverallProgress showing task list's completion statistics
   */
  const statusCounts = useMemo((): StatusCounts => {
    if (!taskListStats) {
      return { completed: 0, inProgress: 0, blocked: 0, notStarted: 0 };
    }
    return convertToStatusCounts(taskListStats);
  }, [taskListStats]);

  /**
   * Render a task card
   * Requirements: 6.4, 6.6, 18.5, 18.6
   * - Cards have min-height (180px) and max-height (380px) constraints
   * - Narrower column width (~280px) achieved via columnBreakpoints
   */
  const renderTaskCard = useCallback(
    (task: TaskWithHeight) => (
      <div 
        className="min-h-[180px] max-h-[380px]"
        style={{ minHeight: '180px', maxHeight: '380px' }}
      >
        <TaskCard
          task={task}
          onClick={() => handleTaskClick(task)}
          spotlight
          tilt
        />
      </div>
    ),
    [handleTaskClick]
  );

  /**
   * Render loading skeleton
   */
  const renderLoadingSkeleton = () => (
    <div
      className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4"
      data-testid="single-task-list-view-loading"
      aria-busy="true"
      aria-label="Loading task list"
    >
      {Array.from({ length: 6 }).map((_, index) => (
        <TaskCardSkeleton key={index} />
      ))}
    </div>
  );

  /**
   * Render empty state
   */
  const renderEmptyState = () => (
    <div
      className="flex flex-col items-center justify-center py-16 text-center"
      data-testid="single-task-list-view-empty"
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
          d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4"
        />
      </svg>
      <Typography variant="h5" color="secondary" className="mb-2">
        {searchQuery || activeFilters.length > 0
          ? "No tasks match your filters"
          : "No tasks yet"}
      </Typography>
      <Typography variant="body-sm" color="muted">
        {searchQuery || activeFilters.length > 0
          ? "Try adjusting your search or filters"
          : "Create your first task to get started"}
      </Typography>
    </div>
  );

  /**
   * Render error state
   */
  const renderErrorState = () => (
    <div
      className="flex flex-col items-center justify-center py-16 text-center"
      data-testid="single-task-list-view-error"
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
        Failed to load task list
      </Typography>
      <Typography variant="body-sm" color="muted" className="mb-4">
        {error}
      </Typography>
      <Button variant="primary" onClick={loadTaskListData}>
        Try Again
      </Button>
    </div>
  );

  // Show error state
  if (error && !isLoading) {
    return (
      <div className={cn("flex flex-col gap-6", className)} data-testid="single-task-list-view">
        {renderErrorState()}
      </div>
    );
  }


  return (
    <div
      className={cn("flex flex-col gap-6", className)}
      data-testid="single-task-list-view"
    >
      {/* Header - Requirements: 6.1, 6.5, 14.1, 14.2, 14.3 */}
      <div className="flex flex-col gap-4">
        {/* Top row with back button and action buttons - 40px height, 12px gap */}
        <div className="flex items-center justify-between gap-3">
          {/* Back button and title - Requirements: 6.1, 14.1, 14.3 */}
          <div className="flex items-center gap-3 flex-1 min-w-0">
            <button
              onClick={handleBackClick}
              aria-label="Go back"
              data-testid="back-button"
              className="flex-shrink-0 w-10 h-10 flex items-center justify-center rounded-lg bg-[var(--bg-surface)] border border-[var(--border)] text-[var(--text-primary)] hover:bg-[var(--bg-surface-hover)] hover:border-[var(--primary)] hover:text-[var(--primary)] transition-all duration-200 shadow-sm"
            >
              <Icon name="ChevronLeft" size={20} />
            </button>
            {!isLoading && taskList && (
              <div className="flex items-center gap-2 flex-1 min-w-0">
                <Typography variant="h3" color="muted" className="text-lg md:text-xl font-medium flex-shrink-0">
                  Task List:
                </Typography>
                <Typography variant="h3" color="primary" className="text-lg md:text-xl font-semibold truncate">
                  {taskList.name}
                </Typography>
              </div>
            )}
          </div>

          {/* Action buttons - Requirements: 6.5, 14.2, 14.3 */}
          {!isLoading && taskList && (
            <div className="flex items-center gap-3 flex-shrink-0">
              <Button
                variant="secondary"
                size="md"
                onClick={handleEditClick}
                leftIcon={<Icon name="Pencil" size="sm" />}
                data-testid="edit-task-list-button"
              >
                Edit
              </Button>
              <Button
                variant="destructive"
                size="md"
                onClick={handleDeleteClick}
                leftIcon={<Icon name="Trash2" size="sm" />}
                data-testid="delete-task-list-button"
              >
                Delete
              </Button>
            </div>
          )}
        </div>

        {/* Task list description */}
        {!isLoading && taskList?.description && (
          <Typography variant="body" color="secondary" className="mt-1">
            {taskList.description}
          </Typography>
        )}

        {/* OverallProgress - Requirements: 6.3 */}
        {!isLoading && taskListStats && (
          <OverallProgress
            statusCounts={statusCounts}
            data-testid="task-list-overall-progress"
          />
        )}

        {/* SearchFilterBar - Requirements: 6.2 */}
        <div ref={sortFilterButtonRef} className="relative">
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
      </div>

      {/* Content */}
      {isLoading && renderLoadingSkeleton()}

      {!isLoading && !error && tasksWithHeight.length === 0 && renderEmptyState()}

      {/* MasonryGrid - Requirements: 6.4, 6.9, 18.5, 18.6 */}
      {/* Use narrower columns (~280px) for showcase-style TaskCards */}
      {!isLoading && !error && tasksWithHeight.length > 0 && (
        <MasonryGrid
          items={tasksWithHeight}
          renderItem={renderTaskCard}
          gap={16}
          animateLayout
          layoutId="single-task-list-tasks-masonry"
          columnBreakpoints={{ 0: 1, 560: 2, 840: 3, 1120: 4, 1400: 5, 1680: 6 }}
        />
      )}

      {/* Results count */}
      {!isLoading && !error && tasks.length > 0 && (
        <div className="text-center">
          <Typography variant="caption" color="muted">
            Showing {filteredTasks.length} of {tasks.length} tasks
          </Typography>
        </div>
      )}

      {/* Edit Task List Modal - Requirements: 6.7 */}
      {taskList && (
        <EditTaskListModal
          isOpen={isEditModalOpen}
          taskList={taskList}
          onClose={handleEditModalClose}
          onSuccess={handleEditSuccess}
        />
      )}

      {/* Delete Confirmation Dialog - Requirements: 6.8 */}
      {taskList && (
        <DeleteConfirmationDialog
          isOpen={isDeleteDialogOpen}
          title="Delete Task List"
          message="Are you sure you want to delete this task list? This will also delete all tasks within it."
          itemName={taskList.name}
          onConfirm={handleDeleteConfirm}
          onCancel={handleDeleteDialogClose}
          isDestructive
          loading={isDeleting}
          cascadingDeletion={{
            taskCount: taskListStats?.taskCount,
          }}
        />
      )}
    </div>
  );
};

SingleTaskListView.displayName = "SingleTaskListView";

export default SingleTaskListView;
