import React, { useState, useEffect, useCallback, useMemo, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { useDataService } from "../../context/DataServiceContext";
import { TaskListGroup } from "../../components/organisms/TaskListGroup";
import { TaskCardSkeleton } from "../../components/organisms/TaskCard";
import { SearchFilterBar } from "../../components/molecules/SearchFilterBar";
import { SortFilterPopup, type SortOption, type FilterOption } from "../../components/organisms/SortFilterPopup";
import { OverallProgress, type StatusCounts } from "../../components/organisms/OverallProgress";
import { Typography } from "../../components/atoms/Typography";
import { filterTasks } from "../../utils/filtering";
import { sortTasks, type TaskSortField, type SortDirection } from "../../utils/sorting";
import { groupTasksByTaskList } from "../../utils/grouping";
import { calculateTaskStatistics } from "../../utils/statistics";
import { cn } from "../../lib/utils";
import type { TaskList, Task } from "../../core/types/entities";
import type { TaskListStats } from "../../services/types";
import type { GroupedItems } from "../../utils/grouping";

/**
 * TasksView Component
 *
 * A view component that displays all tasks grouped by their parent task lists
 * with search and filter capabilities using SearchFilterBar.
 *
 * Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6
 * - 7.1: Display SearchFilterBar with search input and SortFilterButton at top
 * - 7.2: Display OverallProgress component showing completion statistics for all tasks
 * - 7.3: Display TaskCard components grouped by task list using TaskListGroup in MasonryGrid
 * - 7.4: Filter TaskCard components based on search query
 * - 7.5: Navigate to /tasks/{taskId} on card click
 * - 7.6: Reorder or filter TaskCard components via SortFilterPopup
 */

export interface TasksViewProps {
  /** Callback when a task is clicked (optional, navigation is default) */
  onTaskClick?: (task: Task) => void;
  /** Additional CSS classes */
  className?: string;
}

/**
 * Sort options for tasks
 */
const TASK_SORT_OPTIONS: SortOption[] = [
  { id: "incompleteExitCriteria-desc", label: "Most incomplete criteria" },
  { id: "incompleteExitCriteria-asc", label: "Fewest incomplete criteria" },
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
 * Filter options for task status
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

/**
 * Parse sort option ID into field and direction
 */
function parseSortOption(sortId: string): { field: TaskSortField; direction: SortDirection } {
  const [field, direction] = sortId.split("-") as [TaskSortField, SortDirection];
  return { field, direction };
}

/**
 * Interface for task list group items with masonry layout support
 * Requirements: 7.3 - Outer MasonryGrid for task list groups
 */
interface TaskListGroupMasonryItem {
  id: string;
  height: number;
  group: GroupedItems<Task>;
  taskList: TaskList;
}

/**
 * Base height for a TaskListGroup header (compact styling)
 */
const TASK_LIST_GROUP_HEADER_HEIGHT = 48;

/**
 * Estimated height per task card row
 */
const TASK_CARD_HEIGHT = 180;

/**
 * Estimates the height of a TaskListGroup based on its tasks
 */
const estimateTaskListGroupHeight = (
  taskCount: number,
  columnsPerGroup: number = 2
): number => {
  // Calculate rows needed for tasks in masonry layout
  const rows = Math.ceil(taskCount / columnsPerGroup);
  // Header + rows of task cards + padding
  return TASK_LIST_GROUP_HEADER_HEIGHT + (rows * TASK_CARD_HEIGHT) + 40;
};

/**
 * TasksView component
 */
export const TasksView: React.FC<TasksViewProps> = ({
  onTaskClick,
  className,
}) => {
  const navigate = useNavigate();
  const { dataService } = useDataService();

  // State
  const [taskLists, setTaskLists] = useState<TaskList[]>([]);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [taskListStats, setTaskListStats] = useState<Map<string, TaskListStats>>(new Map());
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Search/filter state
  const [searchQuery, setSearchQuery] = useState("");
  const [sortFilterPopupOpen, setSortFilterPopupOpen] = useState(false);
  const [activeSortId, setActiveSortId] = useState("incompleteExitCriteria-desc");
  const [activeFilters, setActiveFilters] = useState<string[]>([]);
  
  // Ref for SortFilterPopup anchor
  const sortFilterButtonRef = useRef<HTMLDivElement>(null);

  /**
   * Load task lists, tasks, and their stats
   */
  const loadData = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      // Load task lists and all tasks in parallel
      const [loadedTaskLists, loadedTasks] = await Promise.all([
        dataService.getTaskLists(),
        dataService.getTasks(), // Get all tasks
      ]);
      
      setTaskLists(loadedTaskLists);
      setTasks(loadedTasks);

      // Load stats for task lists
      const taskListStatsMap = new Map<string, TaskListStats>();
      
      await Promise.all(
        loadedTaskLists.map(async (taskList) => {
          try {
            const stats = await dataService.getTaskListStats(taskList.id);
            taskListStatsMap.set(taskList.id, stats);
          } catch {
            console.warn(`Failed to load stats for task list ${taskList.id}`);
          }
        })
      );
      
      setTaskListStats(taskListStatsMap);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to load tasks"
      );
    } finally {
      setIsLoading(false);
    }
  }, [dataService]);

  // Load data on mount
  useEffect(() => {
    loadData();
  }, [loadData]);

  /**
   * Handle search query change
   * Requirements: 7.4 - Filter TaskCard components based on search query
   */
  const handleSearchChange = useCallback((value: string) => {
    setSearchQuery(value);
  }, []);

  /**
   * Handle sort/filter popup open
   * Requirements: 7.6 - Wire up to SortFilterPopup
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
    setActiveSortId("incompleteExitCriteria-desc");
    setActiveFilters([]);
    setSearchQuery("");
  }, []);

  /**
   * Handle sort option change
   * Requirements: 7.6 - Reorder TaskCard components via SortFilterPopup
   */
  const handleSortChange = useCallback((sortId: string) => {
    setActiveSortId(sortId);
  }, []);

  /**
   * Handle filter option change
   * Requirements: 7.6 - Filter TaskCard components via SortFilterPopup
   */
  const handleFilterChange = useCallback((filterIds: string[]) => {
    setActiveFilters(filterIds);
  }, []);

  /**
   * Check if any sort/filter is active (non-default)
   */
  const sortFilterActive = useMemo(() => {
    return activeSortId !== "incompleteExitCriteria-desc" || activeFilters.length > 0;
  }, [activeSortId, activeFilters]);

  /**
   * Handle task card click
   * Requirements: 7.5 - Navigate to /tasks/{taskId} on card click
   */
  const handleTaskClick = useCallback((taskId: string) => {
    const task = tasks.find((t) => t.id === taskId);
    if (onTaskClick && task) {
      onTaskClick(task);
    } else {
      navigate(`/tasks/${taskId}`);
    }
  }, [navigate, onTaskClick, tasks]);

  /**
   * Filter and sort tasks based on search query, filters, and sort option
   * Requirements: 7.4, 7.6
   */
  const filteredTasks = useMemo(() => {
    let result = tasks;

    // Apply search filter
    // Requirements: 7.4 - Filter TaskCard components based on search query
    if (searchQuery) {
      result = filterTasks(result, searchQuery);
    }

    // Apply status filters
    const statusFilters = activeFilters
      .filter((f) => f.startsWith("status-"))
      .map((f) => f.replace("status-", "").toUpperCase().replace(/-/g, "_"));

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
    // Requirements: 7.6 - Reorder TaskCard components via SortFilterPopup
    const { field, direction } = parseSortOption(activeSortId);
    
    // Handle custom incompleteExitCriteria sorting
    if (field === "incompleteExitCriteria") {
      result = [...result].sort((a, b) => {
        const incompleteA = a.exitCriteria?.filter(ec => ec.status === "INCOMPLETE").length ?? 0;
        const incompleteB = b.exitCriteria?.filter(ec => ec.status === "INCOMPLETE").length ?? 0;
        return direction === "desc" ? incompleteB - incompleteA : incompleteA - incompleteB;
      });
    } else {
      result = sortTasks(result, field as TaskSortField, direction);
    }

    return result;
  }, [tasks, searchQuery, activeFilters, activeSortId]);

  /**
   * Group filtered tasks by task list
   * Requirements: 7.3 - Display TaskCard components grouped by task list
   */
  const groupedTasks = useMemo(() => {
    return groupTasksByTaskList(filteredTasks, taskLists);
  }, [filteredTasks, taskLists]);

  /**
   * Calculate overall progress statistics for all tasks
   * Requirements: 7.2 - Display OverallProgress component
   */
  const overallStats = useMemo((): StatusCounts => {
    const stats = calculateTaskStatistics(tasks);
    return {
      completed: stats.completedTasks,
      inProgress: stats.inProgressTasks,
      blocked: stats.blockedTasks,
      notStarted: stats.notStartedTasks,
    };
  }, [tasks]);

  /**
   * Convert task list stats map to record for TaskListGroup
   */
  const taskListStatsRecord = useMemo(() => {
    const record: Record<string, TaskListStats> = {};
    taskListStats.forEach((stats, id) => {
      record[id] = stats;
    });
    return record;
  }, [taskListStats]);

  /**
   * Convert grouped tasks to masonry items for outer MasonryGrid
   * Requirements: 7.3 - Outer MasonryGrid for task list groups
   */
  const taskListGroupMasonryItems = useMemo((): TaskListGroupMasonryItem[] => {
    const items = groupedTasks.map((group) => {
      const taskList = taskLists.find((tl) => tl.id === group.groupId);
      if (!taskList) return null;
      
      return {
        id: group.groupId,
        height: estimateTaskListGroupHeight(group.items.length),
        group,
        taskList,
      };
    }).filter((item): item is TaskListGroupMasonryItem => item !== null);
    
    // Sort task list groups by ready tasks count (most ready tasks first)
    return items.sort((a, b) => {
      const readyA = taskListStats.get(a.id)?.readyTasks ?? 0;
      const readyB = taskListStats.get(b.id)?.readyTasks ?? 0;
      return readyB - readyA;
    });
  }, [groupedTasks, taskLists, taskListStats]);

  /**
   * Render a TaskListGroup item for the outer MasonryGrid
   * Requirements: 7.3, 7.8 - Nested masonry layout with parallax effect
   */
  const renderTaskListGroupItem = useCallback(
    (item: TaskListGroupMasonryItem) => (
      <TaskListGroup
        taskList={item.taskList}
        tasks={item.group.items}
        stats={taskListStatsRecord[item.group.groupId]}
        defaultExpanded={true}
        onTaskClick={handleTaskClick}
        taskLayout="masonry"
        enableCardTilt={true}
        enableCardSpotlight={true}
      />
    ),
    [taskListStatsRecord, handleTaskClick]
  );

  /**
   * Render loading skeleton
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
        onClick={loadData}
        className="px-4 py-2 bg-[var(--primary)] text-white rounded-lg hover:opacity-90 transition-opacity"
      >
        Try Again
      </button>
    </div>
  );

  return (
    <div
      className={cn("flex flex-col gap-6", className)}
      data-testid="tasks-view"
    >
      {/* Header */}
      {/* Requirements: 7.7 - Display a prominent page title that is clearly visible */}
      <div className="flex flex-col gap-4">
        <Typography variant="h1" color="primary" className="text-3xl md:text-4xl font-bold">
          Tasks
        </Typography>

        {/* SearchFilterBar - Requirements: 7.1 */}
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

      {/* OverallProgress - Requirements: 7.2 */}
      {!isLoading && !error && tasks.length > 0 && (
        <OverallProgress statusCounts={overallStats} />
      )}

      {/* Content */}
      {isLoading && renderLoadingSkeleton()}

      {error && !isLoading && renderErrorState()}

      {!isLoading && !error && filteredTasks.length === 0 && renderEmptyState()}

      {/* TaskListGroups with flexbox layout - Requirements: 7.3, 7.8, 7.9 */}
      {/* Groupings auto-size to fit content, flexbox distributes space evenly */}
      {!isLoading && !error && taskListGroupMasonryItems.length > 0 && (
        <div 
          className="flex flex-wrap justify-evenly gap-6"
          data-testid="task-list-groups-container"
        >
          {taskListGroupMasonryItems.map((item) => (
            <div key={item.id} className="flex-shrink-0">
              {renderTaskListGroupItem(item)}
            </div>
          ))}
        </div>
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

export default TasksView;
