import React, { useState, useEffect, useCallback, useMemo, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { useDataService } from "../../context/DataServiceContext";
import { ProjectGroup } from "../../components/organisms/ProjectGroup";
import { TaskListCardSkeleton } from "../../components/organisms/TaskListCard";
import { EditTaskListModal } from "../../components/organisms/EditTaskListModal";
import { DeleteConfirmationDialog } from "../../components/organisms/DeleteConfirmationDialog";
import { SearchFilterBar } from "../../components/molecules/SearchFilterBar";
import { SortFilterPopup, type SortOption, type FilterOption } from "../../components/organisms/SortFilterPopup";
import { Typography } from "../../components/atoms/Typography";
import { filterTaskLists } from "../../utils/filtering";
import { sortTaskLists, type TaskListSortField, type SortDirection } from "../../utils/sorting";
import { groupTaskListsByProject } from "../../utils/grouping";
import { cn } from "../../lib/utils";
import type { Project, TaskList } from "../../core/types/entities";
import type { ProjectStats, TaskListStats } from "../../services/types";
import type { GroupedItems } from "../../utils/grouping";

/**
 * TaskListsView Component
 *
 * A view component that displays all task lists grouped by their parent projects
 * with search and filter capabilities using SearchFilterBar.
 *
 * Requirements: 5.1, 5.2, 5.3, 5.4, 5.5
 * - 5.1: Display SearchFilterBar with search input and SortFilterButton at top
 * - 5.2: Display TaskListCard components grouped by project using ProjectGroup
 * - 5.3: Filter TaskListCard components based on search query
 * - 5.4: Navigate to /lists/{taskListId} on card click
 * - 5.5: Reorder or filter TaskListCard components via SortFilterPopup
 */

export interface TaskListsViewProps {
  /** Callback when a task list is clicked (optional, navigation is default) */
  onTaskListClick?: (taskList: TaskList) => void;
  /** Additional CSS classes */
  className?: string;
}


/**
 * Sort options for task lists
 */
const TASKLIST_SORT_OPTIONS: SortOption[] = [
  { id: "readyTasks-desc", label: "Most ready tasks" },
  { id: "readyTasks-asc", label: "Fewest ready tasks" },
  { id: "name-asc", label: "Name (A-Z)" },
  { id: "name-desc", label: "Name (Z-A)" },
  { id: "createdAt-desc", label: "Newest first" },
  { id: "createdAt-asc", label: "Oldest first" },
  { id: "updatedAt-desc", label: "Recently updated" },
  { id: "updatedAt-asc", label: "Least recently updated" },
];

/**
 * Filter options for task list completion status
 */
const TASKLIST_FILTER_OPTIONS: FilterOption[] = [
  { id: "status-not-started", label: "Not Started", type: "checkbox", group: "Status" },
  { id: "status-in-progress", label: "In Progress", type: "checkbox", group: "Status" },
  { id: "status-completed", label: "Completed", type: "checkbox", group: "Status" },
];

/**
 * Determines completion status category based on stats
 */
const getCompletionStatus = (stats?: TaskListStats): string => {
  if (!stats || stats.taskCount === 0) return "not-started";
  const percentage = stats.completionPercentage;
  if (percentage >= 100) return "completed";
  if (percentage > 0) return "in-progress";
  return "not-started";
};

/**
 * Parse sort option ID into field and direction
 */
function parseSortOption(sortId: string): { field: TaskListSortField; direction: SortDirection } {
  const [field, direction] = sortId.split("-") as [TaskListSortField, SortDirection];
  return { field, direction };
}

/**
 * Interface for project group items with masonry layout support
 * Requirements: 5.2 - Outer MasonryGrid for ProjectGroups
 */
interface ProjectGroupMasonryItem {
  id: string;
  height: number;
  group: GroupedItems<TaskList>;
  project: Project;
}

/**
 * Base height for a ProjectGroup header (compact styling)
 */
const PROJECT_GROUP_HEADER_HEIGHT = 48;

/**
 * Estimated height per task list card row
 */
const TASK_LIST_CARD_HEIGHT = 200;

/**
 * Estimates the height of a ProjectGroup based on its task lists
 */
const estimateProjectGroupHeight = (
  taskListCount: number,
  columnsPerGroup: number = 2
): number => {
  // Calculate rows needed for task lists in masonry layout
  const rows = Math.ceil(taskListCount / columnsPerGroup);
  // Header + rows of task list cards + padding
  return PROJECT_GROUP_HEADER_HEIGHT + (rows * TASK_LIST_CARD_HEIGHT) + 40;
};

/**
 * TaskListsView component
 */
export const TaskListsView: React.FC<TaskListsViewProps> = ({
  onTaskListClick,
  className,
}) => {
  const navigate = useNavigate();
  const { dataService } = useDataService();

  // State
  const [projects, setProjects] = useState<Project[]>([]);
  const [taskLists, setTaskLists] = useState<TaskList[]>([]);
  const [projectStats, setProjectStats] = useState<Map<string, ProjectStats>>(new Map());
  const [taskListStats, setTaskListStats] = useState<Map<string, TaskListStats>>(new Map());
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Search/filter state
  const [searchQuery, setSearchQuery] = useState("");
  const [sortFilterPopupOpen, setSortFilterPopupOpen] = useState(false);
  const [activeSortId, setActiveSortId] = useState("readyTasks-desc");
  const [activeFilters, setActiveFilters] = useState<string[]>([]);
  
  // Ref for SortFilterPopup anchor
  const sortFilterButtonRef = useRef<HTMLDivElement>(null);

  // Edit/Delete modal state
  const [editingTaskList, setEditingTaskList] = useState<TaskList | null>(null);
  const [deletingTaskList, setDeletingTaskList] = useState<TaskList | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);


  /**
   * Load projects, task lists, and their stats
   */
  const loadData = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      // Load projects and task lists in parallel
      const [loadedProjects, loadedTaskLists] = await Promise.all([
        dataService.getProjects(),
        dataService.getTaskLists(),
      ]);
      
      setProjects(loadedProjects);
      setTaskLists(loadedTaskLists);

      // Load stats for projects and task lists
      const projectStatsMap = new Map<string, ProjectStats>();
      const taskListStatsMap = new Map<string, TaskListStats>();
      
      await Promise.all([
        // Load project stats
        ...loadedProjects.map(async (project) => {
          try {
            const stats = await dataService.getProjectStats(project.id);
            projectStatsMap.set(project.id, stats);
          } catch {
            console.warn(`Failed to load stats for project ${project.id}`);
          }
        }),
        // Load task list stats
        ...loadedTaskLists.map(async (taskList) => {
          try {
            const stats = await dataService.getTaskListStats(taskList.id);
            taskListStatsMap.set(taskList.id, stats);
          } catch {
            console.warn(`Failed to load stats for task list ${taskList.id}`);
          }
        }),
      ]);
      
      setProjectStats(projectStatsMap);
      setTaskListStats(taskListStatsMap);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to load task lists"
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
   * Requirements: 5.3 - Filter TaskListCard components based on search query
   */
  const handleSearchChange = useCallback((value: string) => {
    setSearchQuery(value);
  }, []);

  /**
   * Handle sort/filter popup open
   * Requirements: 5.5 - Wire up to SortFilterPopup
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
    setActiveSortId("readyTasks-desc");
    setActiveFilters([]);
    setSearchQuery("");
  }, []);

  /**
   * Handle sort option change
   * Requirements: 5.5 - Reorder TaskListCard components via SortFilterPopup
   */
  const handleSortChange = useCallback((sortId: string) => {
    setActiveSortId(sortId);
  }, []);

  /**
   * Handle filter option change
   * Requirements: 5.5 - Filter TaskListCard components via SortFilterPopup
   */
  const handleFilterChange = useCallback((filterIds: string[]) => {
    setActiveFilters(filterIds);
  }, []);

  /**
   * Check if any sort/filter is active (non-default)
   */
  const sortFilterActive = useMemo(() => {
    return activeSortId !== "readyTasks-desc" || activeFilters.length > 0;
  }, [activeSortId, activeFilters]);

  /**
   * Handle task list card click
   * Requirements: 5.4 - Navigate to /lists/{taskListId} on card click
   */
  const handleTaskListClick = useCallback((taskListId: string) => {
    const taskList = taskLists.find((tl) => tl.id === taskListId);
    if (onTaskListClick && taskList) {
      onTaskListClick(taskList);
    } else {
      navigate(`/lists/${taskListId}`);
    }
  }, [navigate, onTaskListClick, taskLists]);

  /**
   * Handle edit action on a task list
   */
  const handleEditTaskList = useCallback((taskList: TaskList) => {
    setEditingTaskList(taskList);
  }, []);

  /**
   * Handle delete action on a task list
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
   * Handle edit modal success - reload data to reflect changes
   */
  const handleEditSuccess = useCallback(() => {
    setEditingTaskList(null);
    loadData();
  }, [loadData]);

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
      loadData();
    } catch (err) {
      console.error("Failed to delete task list:", err);
      // Keep dialog open on error so user can retry or cancel
    } finally {
      setIsDeleting(false);
    }
  }, [deletingTaskList, dataService, loadData]);


  /**
   * Filter and sort task lists based on search query, filters, and sort option
   * Requirements: 5.3, 5.5
   */
  const filteredTaskLists = useMemo(() => {
    let result = taskLists;

    // Apply search filter
    // Requirements: 5.3 - Filter TaskListCard components based on search query
    if (searchQuery) {
      result = filterTaskLists(result, searchQuery);
    }

    // Apply status filters
    if (activeFilters.length > 0) {
      const statusFilters = activeFilters
        .filter((f) => f.startsWith("status-"))
        .map((f) => f.replace("status-", ""));

      if (statusFilters.length > 0) {
        result = result.filter((taskList) => {
          const stats = taskListStats.get(taskList.id);
          const status = getCompletionStatus(stats);
          return statusFilters.includes(status);
        });
      }
    }

    // Apply sorting
    // Requirements: 5.5 - Reorder TaskListCard components via SortFilterPopup
    const { field, direction } = parseSortOption(activeSortId);
    
    // Handle custom readyTasks sorting
    if (field === "readyTasks") {
      result = [...result].sort((a, b) => {
        const readyA = taskListStats.get(a.id)?.readyTasks ?? 0;
        const readyB = taskListStats.get(b.id)?.readyTasks ?? 0;
        return direction === "desc" ? readyB - readyA : readyA - readyB;
      });
    } else {
      result = sortTaskLists(result, field as TaskListSortField, direction);
    }

    return result;
  }, [taskLists, searchQuery, activeFilters, activeSortId, taskListStats]);

  /**
   * Group filtered task lists by project
   * Requirements: 5.2 - Display TaskListCard components grouped by project
   */
  const groupedTaskLists = useMemo(() => {
    return groupTaskListsByProject(filteredTaskLists, projects);
  }, [filteredTaskLists, projects]);

  /**
   * Convert grouped task lists to masonry items for outer MasonryGrid
   * Requirements: 5.2 - Outer MasonryGrid for ProjectGroups
   */
  const projectGroupMasonryItems = useMemo((): ProjectGroupMasonryItem[] => {
    const items = groupedTaskLists.map((group) => {
      const project = projects.find((p) => p.id === group.groupId);
      if (!project) return null;
      
      return {
        id: group.groupId,
        height: estimateProjectGroupHeight(group.items.length),
        group,
        project,
      };
    }).filter((item): item is ProjectGroupMasonryItem => item !== null);
    
    // Sort project groups by task list count (most lists first)
    return items.sort((a, b) => b.group.items.length - a.group.items.length);
  }, [groupedTaskLists, projects]);

  /**
   * Convert task list stats map to record for ProjectGroup
   */
  const taskListStatsRecord = useMemo(() => {
    const record: Record<string, TaskListStats> = {};
    taskListStats.forEach((stats, id) => {
      record[id] = stats;
    });
    return record;
  }, [taskListStats]);

  /**
   * Render a ProjectGroup item for the outer MasonryGrid
   * Requirements: 5.2, 5.7 - Nested masonry layout with parallax effect
   */
  const renderProjectGroupItem = useCallback(
    (item: ProjectGroupMasonryItem) => (
      <ProjectGroup
        project={item.project}
        taskLists={item.group.items}
        stats={projectStats.get(item.group.groupId)}
        taskListStats={taskListStatsRecord}
        defaultExpanded={true}
        onTaskListClick={handleTaskListClick}
        onTaskListEdit={handleEditTaskList}
        onTaskListDelete={handleDeleteTaskList}
        taskListLayout="masonry"
        enableCardTilt={true}
        enableCardSpotlight={true}
      />
    ),
    [projectStats, taskListStatsRecord, handleTaskListClick, handleEditTaskList, handleDeleteTaskList]
  );

  /**
   * Render loading skeleton
   */
  const renderLoadingSkeleton = () => (
    <div 
      className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4"
      data-testid="tasklists-view-loading"
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
      data-testid="tasklists-view-empty"
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
        {searchQuery || activeFilters.length > 0
          ? "No task lists match your filters"
          : "No task lists yet"}
      </Typography>
      <Typography variant="body-sm" color="muted">
        {searchQuery || activeFilters.length > 0
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
      data-testid="tasklists-view-error"
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
      data-testid="tasklists-view"
    >
      {/* Header */}
      {/* Requirements: 5.6 - Display a prominent page title that is clearly visible */}
      <div className="flex flex-col gap-4">
        <Typography variant="h1" color="primary" className="text-3xl md:text-4xl font-bold">
          Task Lists
        </Typography>

        {/* SearchFilterBar - Requirements: 5.1 */}
        <div ref={sortFilterButtonRef} className="relative">
          <SearchFilterBar
            searchValue={searchQuery}
            onSearchChange={handleSearchChange}
            sortFilterActive={sortFilterActive}
            onSortFilterOpen={handleSortFilterOpen}
            onSortFilterReset={handleSortFilterReset}
            searchPlaceholder="Search task lists..."
            sortFilterLabel="Sort & Filter"
          />
          <SortFilterPopup
            isOpen={sortFilterPopupOpen}
            onClose={handleSortFilterClose}
            sortOptions={TASKLIST_SORT_OPTIONS}
            filterOptions={TASKLIST_FILTER_OPTIONS}
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

      {error && !isLoading && renderErrorState()}

      {!isLoading && !error && filteredTaskLists.length === 0 && renderEmptyState()}

      {/* ProjectGroups with flexbox layout - Requirements: 5.2, 5.7, 5.8 */}
      {/* Groupings auto-size to fit content, flexbox distributes space evenly */}
      {!isLoading && !error && projectGroupMasonryItems.length > 0 && (
        <div 
          className="flex flex-wrap justify-evenly gap-6"
          data-testid="project-groups-container"
        >
          {projectGroupMasonryItems.map((item) => (
            <div key={item.id} className="flex-shrink-0">
              {renderProjectGroupItem(item)}
            </div>
          ))}
        </div>
      )}

      {/* Results count */}
      {!isLoading && !error && taskLists.length > 0 && (
        <div className="text-center">
          <Typography variant="caption" color="muted">
            Showing {filteredTaskLists.length} of {taskLists.length} task lists
          </Typography>
        </div>
      )}

      {/* Edit Task List Modal */}
      {editingTaskList && (
        <EditTaskListModal
          isOpen={!!editingTaskList}
          taskList={editingTaskList}
          onClose={handleEditModalClose}
          onSuccess={handleEditSuccess}
        />
      )}

      {/* Delete Confirmation Dialog */}
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

TaskListsView.displayName = "TaskListsView";

export default TaskListsView;
