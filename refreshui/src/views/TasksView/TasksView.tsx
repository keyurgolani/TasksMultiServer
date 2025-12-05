import React, { useState, useEffect, useCallback, useMemo } from "react";
import { useDataService } from "../../context/DataServiceContext";
import { MasonryGrid } from "../../layouts/MasonryGrid";
import { TaskCard, TaskCardSkeleton } from "../../components/organisms/TaskCard";
import { SearchBar } from "../../components/molecules/SearchBar";
import { FilterChips } from "../../components/molecules/FilterChips";
import { Typography } from "../../components/atoms/Typography";
import { cn } from "../../lib/utils";
import type { Task, TaskList } from "../../core/types/entities";

/**
 * TasksView Component
 *
 * A view component that displays tasks with filtering by status, priority,
 * and search query in a masonry grid layout.
 *
 * Requirements: 10.3
 * - Display tasks with filtering by status, priority, and search query
 */

export interface TasksViewProps {
  /** Optional task list to filter tasks by */
  taskList?: TaskList;
  /** Task list ID to load tasks for (alternative to taskList prop) */
  taskListId?: string;
  /** Callback when a task is clicked */
  onTaskClick?: (task: Task) => void;
  /** Callback to navigate back */
  onBackClick?: () => void;
  /** Additional CSS classes */
  className?: string;
}

/** Filter options for task status */
const STATUS_FILTER_OPTIONS = [
  { id: "all", label: "All" },
  { id: "NOT_STARTED", label: "Not Started" },
  { id: "IN_PROGRESS", label: "In Progress" },
  { id: "COMPLETED", label: "Completed" },
  { id: "BLOCKED", label: "Blocked" },
];

/** Filter options for task priority */
const PRIORITY_FILTER_OPTIONS = [
  { id: "all", label: "All" },
  { id: "CRITICAL", label: "Critical" },
  { id: "HIGH", label: "High" },
  { id: "MEDIUM", label: "Medium" },
  { id: "LOW", label: "Low" },
  { id: "TRIVIAL", label: "Trivial" },
];

/** Extended task type with height for masonry grid */
interface TaskWithHeight extends Task {
  height: number;
  [key: string]: unknown;
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
  if (task.notes?.length > 0 || task.researchNotes?.length > 0 || task.executionNotes?.length > 0) {
    height += 25;
  }
  return height;
};

/**
 * Filters tasks based on search query, status filters, and priority filters
 */
const filterTasks = (
  tasks: Task[],
  searchQuery: string,
  statusFilters: string[],
  priorityFilters: string[]
): Task[] => {
  return tasks.filter((task) => {
    // Search filter - matches title or description
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      const matchesTitle = task.title.toLowerCase().includes(query);
      const matchesDescription = task.description?.toLowerCase().includes(query);
      if (!matchesTitle && !matchesDescription) {
        return false;
      }
    }

    // Status filter
    if (!statusFilters.includes("all")) {
      if (!statusFilters.includes(task.status)) {
        return false;
      }
    }

    // Priority filter
    if (!priorityFilters.includes("all")) {
      if (!priorityFilters.includes(task.priority)) {
        return false;
      }
    }

    return true;
  });
};

/**
 * TasksView component
 */
export const TasksView: React.FC<TasksViewProps> = ({
  taskList: taskListProp,
  taskListId: taskListIdProp,
  onTaskClick,
  onBackClick,
  className,
}) => {
  const { dataService } = useDataService();

  // State
  const [taskList, setTaskList] = useState<TaskList | null>(taskListProp ?? null);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilters, setStatusFilters] = useState<string[]>(["all"]);
  const [priorityFilters, setPriorityFilters] = useState<string[]>(["all"]);

  // Determine the task list ID to use
  const taskListId = taskListProp?.id ?? taskListIdProp;

  /**
   * Load task list if only taskListId is provided
   */
  const loadTaskList = useCallback(async () => {
    if (taskListProp) {
      setTaskList(taskListProp);
      return;
    }

    if (!taskListIdProp) {
      // No task list specified - load all tasks
      return;
    }

    try {
      const loadedTaskList = await dataService.getTaskList(taskListIdProp);
      setTaskList(loadedTaskList);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to load task list"
      );
    }
  }, [dataService, taskListProp, taskListIdProp]);

  /**
   * Load tasks
   */
  const loadTasks = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const loadedTasks = await dataService.getTasks(taskListId);
      setTasks(loadedTasks);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to load tasks"
      );
    } finally {
      setIsLoading(false);
    }
  }, [dataService, taskListId]);

  // Load task list on mount if needed
  useEffect(() => {
    loadTaskList();
  }, [loadTaskList]);

  // Load tasks when component mounts or taskListId changes
  useEffect(() => {
    loadTasks();
  }, [loadTasks]);

  /**
   * Handle search query change
   */
  const handleSearchChange = useCallback((value: string) => {
    setSearchQuery(value);
  }, []);

  /**
   * Handle status filter selection change
   */
  const handleStatusFilterChange = useCallback((selected: string[]) => {
    // If "all" is selected, clear other filters
    if (selected.includes("all") && !statusFilters.includes("all")) {
      setStatusFilters(["all"]);
    } else if (selected.length === 0) {
      // If nothing selected, default to "all"
      setStatusFilters(["all"]);
    } else {
      // Remove "all" if other filters are selected
      setStatusFilters(selected.filter((id) => id !== "all"));
    }
  }, [statusFilters]);

  /**
   * Handle priority filter selection change
   */
  const handlePriorityFilterChange = useCallback((selected: string[]) => {
    // If "all" is selected, clear other filters
    if (selected.includes("all") && !priorityFilters.includes("all")) {
      setPriorityFilters(["all"]);
    } else if (selected.length === 0) {
      // If nothing selected, default to "all"
      setPriorityFilters(["all"]);
    } else {
      // Remove "all" if other filters are selected
      setPriorityFilters(selected.filter((id) => id !== "all"));
    }
  }, [priorityFilters]);

  /**
   * Filter tasks based on search query and filters
   */
  const filteredTasks = useMemo(() => {
    return filterTasks(tasks, searchQuery, statusFilters, priorityFilters);
  }, [tasks, searchQuery, statusFilters, priorityFilters]);

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
   * Render a task card
   */
  const renderTaskCard = useCallback(
    (task: TaskWithHeight) => (
      <TaskCard
        task={task}
        onClick={() => onTaskClick?.(task)}
        spotlight
        tilt
      />
    ),
    [onTaskClick]
  );

  /**
   * Render loading skeleton
   * Requirements: 10.5 - Display skeleton placeholders matching expected content layout
   */
  const renderLoadingSkeleton = () => (
    <div 
      className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4"
      data-testid="tasks-view-loading"
      aria-busy="true"
      aria-label="Loading tasks"
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
      data-testid="tasks-view-empty"
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
        {searchQuery || !statusFilters.includes("all") || !priorityFilters.includes("all")
          ? "No tasks match your filters"
          : "No tasks yet"}
      </Typography>
      <Typography variant="body-sm" color="muted">
        {searchQuery || !statusFilters.includes("all") || !priorityFilters.includes("all")
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
      data-testid="tasks-view-error"
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
        Failed to load tasks
      </Typography>
      <Typography variant="body-sm" color="muted" className="mb-4">
        {error}
      </Typography>
      <button
        onClick={loadTasks}
        className="px-4 py-2 bg-[var(--primary)] text-white rounded-lg hover:opacity-90 transition-opacity"
      >
        Try Again
      </button>
    </div>
  );

  /**
   * Calculate task statistics for display
   */
  const taskStats = useMemo(() => {
    const stats = {
      total: tasks.length,
      notStarted: 0,
      inProgress: 0,
      completed: 0,
      blocked: 0,
    };

    tasks.forEach((task) => {
      switch (task.status) {
        case "NOT_STARTED":
          stats.notStarted++;
          break;
        case "IN_PROGRESS":
          stats.inProgress++;
          break;
        case "COMPLETED":
          stats.completed++;
          break;
        case "BLOCKED":
          stats.blocked++;
          break;
      }
    });

    return stats;
  }, [tasks]);

  return (
    <div
      className={cn("flex flex-col gap-6", className)}
      data-testid="tasks-view"
    >
      {/* Header */}
      <div className="flex flex-col gap-4">
        <div className="flex items-center gap-4">
          {onBackClick && (
            <button
              onClick={onBackClick}
              className="p-2 rounded-lg hover:bg-[var(--bg-muted)] transition-colors"
              aria-label="Go back"
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
              {taskList?.name ?? "Tasks"}
            </Typography>
            {taskList?.description && (
              <Typography variant="body-sm" color="muted" className="mt-1">
                {taskList.description}
              </Typography>
            )}
          </div>
        </div>

        {/* Search */}
        <div className="flex-1 max-w-md">
          <SearchBar
            placeholder="Search tasks..."
            value={searchQuery}
            onChange={handleSearchChange}
            debounceMs={300}
          />
        </div>

        {/* Filters */}
        <div className="flex flex-col sm:flex-row gap-4">
          <div className="flex flex-col gap-2">
            <Typography variant="caption" color="muted">
              Status
            </Typography>
            <FilterChips
              options={STATUS_FILTER_OPTIONS}
              selected={statusFilters}
              onChange={handleStatusFilterChange}
              multiSelect
              size="sm"
              aria-label="Filter by status"
            />
          </div>
          <div className="flex flex-col gap-2">
            <Typography variant="caption" color="muted">
              Priority
            </Typography>
            <FilterChips
              options={PRIORITY_FILTER_OPTIONS}
              selected={priorityFilters}
              onChange={handlePriorityFilterChange}
              multiSelect
              size="sm"
              aria-label="Filter by priority"
            />
          </div>
        </div>
      </div>

      {/* Task Statistics Summary */}
      {!isLoading && !error && tasks.length > 0 && (
        <TaskStatsSummary stats={taskStats} />
      )}

      {/* Content */}
      {isLoading && renderLoadingSkeleton()}

      {error && !isLoading && renderErrorState()}

      {!isLoading && !error && tasksWithHeight.length === 0 && renderEmptyState()}

      {!isLoading && !error && tasksWithHeight.length > 0 && (
        <MasonryGrid
          items={tasksWithHeight}
          renderItem={renderTaskCard}
          gap={16}
          animateLayout
          layoutId="tasks-masonry"
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
    </div>
  );
};

TasksView.displayName = "TasksView";

/**
 * TaskStatsSummary Component
 *
 * Displays task statistics summary
 */
interface TaskStatsSummaryProps {
  stats: {
    total: number;
    notStarted: number;
    inProgress: number;
    completed: number;
    blocked: number;
  };
}

const TaskStatsSummary: React.FC<TaskStatsSummaryProps> = ({ stats }) => {
  const completionPercentage =
    stats.total > 0 ? Math.round((stats.completed / stats.total) * 100) : 0;

  return (
    <div
      className="p-4 rounded-lg bg-[var(--bg-surface)] border border-[var(--border-default)]"
      data-testid="task-stats-summary"
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
                strokeDasharray={`${completionPercentage}, 100`}
                d="M18 2.0845
                  a 15.9155 15.9155 0 0 1 0 31.831
                  a 15.9155 15.9155 0 0 1 0 -31.831"
              />
            </svg>
            <div className="absolute inset-0 flex items-center justify-center">
              <Typography variant="body-sm" color="primary" className="font-bold">
                {completionPercentage}%
              </Typography>
            </div>
          </div>
          <div>
            <Typography variant="h6" color="primary">
              Overall Progress
            </Typography>
            <Typography variant="caption" color="muted">
              {stats.completed} of {stats.total} tasks completed
            </Typography>
          </div>
        </div>

        {/* Stats Breakdown */}
        <div className="flex flex-wrap gap-6">
          <div className="text-center">
            <Typography variant="h5" color="primary">
              {stats.total}
            </Typography>
            <Typography variant="caption" color="muted">
              Total
            </Typography>
          </div>
          <div className="text-center">
            <Typography variant="h5" className="text-[var(--text-muted)]">
              {stats.notStarted}
            </Typography>
            <Typography variant="caption" color="muted">
              Not Started
            </Typography>
          </div>
          <div className="text-center">
            <Typography variant="h5" className="text-[var(--warning)]">
              {stats.inProgress}
            </Typography>
            <Typography variant="caption" color="muted">
              In Progress
            </Typography>
          </div>
          <div className="text-center">
            <Typography variant="h5" className="text-[var(--success)]">
              {stats.completed}
            </Typography>
            <Typography variant="caption" color="muted">
              Completed
            </Typography>
          </div>
          <div className="text-center">
            <Typography variant="h5" className="text-[var(--error)]">
              {stats.blocked}
            </Typography>
            <Typography variant="caption" color="muted">
              Blocked
            </Typography>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TasksView;
