import React, { useState, useEffect, useCallback, useMemo, useRef } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useDataService } from "../../context/DataServiceContext";
import { MasonryGrid } from "../../layouts/MasonryGrid";
import { TaskListCard, TaskListCardSkeleton } from "../../components/organisms/TaskListCard";
import { EditProjectModal } from "../../components/organisms/EditProjectModal";
import { DeleteConfirmationDialog } from "../../components/organisms/DeleteConfirmationDialog";
import { SearchFilterBar } from "../../components/molecules/SearchFilterBar";
import { SortFilterPopup, type SortOption, type FilterOption } from "../../components/organisms/SortFilterPopup";
import { OverallProgress, type StatusCounts } from "../../components/organisms/OverallProgress";
import { Typography } from "../../components/atoms/Typography";
import { Button } from "../../components/atoms/Button";
import { Icon } from "../../components/atoms/Icon";
import { filterTaskLists } from "../../utils/filtering";
import { sortTaskLists, type TaskListSortField, type SortDirection } from "../../utils/sorting";
import { cn } from "../../lib/utils";
import type { Project, TaskList } from "../../core/types/entities";
import type { ProjectStats, TaskListStats } from "../../services/types";

/**
 * SingleProjectView Component
 *
 * A view component for displaying a single project's details and its task lists.
 * Provides back navigation, search/filter, progress overview, and CRUD operations.
 *
 * Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7, 4.8
 * - 4.1: Display a back navigation button to return to the previous screen
 * - 4.2: Display SearchFilterBar with search and SortFilterButton controls
 * - 4.3: Display an OverallProgress component showing the project's completion statistics
 * - 4.4: Display all TaskListCard components belonging to that project
 * - 4.5: Display edit and delete buttons for the project
 * - 4.6: Navigate to /lists/{taskListId} on TaskListCard click
 * - 4.7: Open EditProjectModal on edit button click
 * - 4.8: Open DeleteConfirmationDialog on delete button click
 */

export interface SingleProjectViewProps {
  /** Project ID from route params (optional, can also use useParams) */
  projectId?: string;
  /** Additional CSS classes */
  className?: string;
}

/**
 * Sort options for task lists
 */
const TASKLIST_SORT_OPTIONS: SortOption[] = [
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


/** Extended task list type with stats for masonry grid */
interface TaskListWithStats extends TaskList {
  stats?: TaskListStats;
  height: number;
}

/**
 * Calculates estimated card height based on task list data
 */
const estimateCardHeight = (taskList: TaskList, stats?: TaskListStats): number => {
  let height = 120; // Base height for name
  if (taskList.description) height += 40;
  if (stats) height += 140; // Stats section
  return height;
};

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
 * Convert ProjectStats to StatusCounts for OverallProgress
 */
function convertToStatusCounts(stats: ProjectStats): StatusCounts {
  const notStarted = Math.max(
    0,
    stats.totalTasks - stats.completedTasks - stats.inProgressTasks - stats.blockedTasks
  );
  return {
    completed: stats.completedTasks,
    inProgress: stats.inProgressTasks,
    blocked: stats.blockedTasks,
    notStarted,
  };
}

/**
 * SingleProjectView component
 */
export const SingleProjectView: React.FC<SingleProjectViewProps> = ({
  projectId: propProjectId,
  className,
}) => {
  const navigate = useNavigate();
  const params = useParams<{ projectId: string }>();
  const { dataService } = useDataService();

  // Get project ID from props or route params
  const projectId = propProjectId || params.projectId;

  // State
  const [project, setProject] = useState<Project | null>(null);
  const [projectStats, setProjectStats] = useState<ProjectStats | null>(null);
  const [taskLists, setTaskLists] = useState<TaskList[]>([]);
  const [taskListStats, setTaskListStats] = useState<Map<string, TaskListStats>>(new Map());
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Search/filter state
  const [searchQuery, setSearchQuery] = useState("");
  const [sortFilterPopupOpen, setSortFilterPopupOpen] = useState(false);
  const [activeSortId, setActiveSortId] = useState("name-asc");
  const [activeFilters, setActiveFilters] = useState<string[]>([]);

  // Ref for SortFilterPopup anchor
  const sortFilterButtonRef = useRef<HTMLDivElement>(null);

  // Modal state
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);

  /**
   * Load project and its task lists
   */
  const loadProjectData = useCallback(async () => {
    if (!projectId) {
      setError("Project ID is required");
      setIsLoading(false);
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      // Load project
      const loadedProject = await dataService.getProject(projectId);
      setProject(loadedProject);

      // Load project stats
      const stats = await dataService.getProjectStats(projectId);
      setProjectStats(stats);

      // Load task lists for this project
      const loadedTaskLists = await dataService.getTaskLists(projectId);
      setTaskLists(loadedTaskLists);

      // Load stats for each task list
      const statsMap = new Map<string, TaskListStats>();
      await Promise.all(
        loadedTaskLists.map(async (taskList) => {
          try {
            const tlStats = await dataService.getTaskListStats(taskList.id);
            statsMap.set(taskList.id, tlStats);
          } catch {
            console.warn(`Failed to load stats for task list ${taskList.id}`);
          }
        })
      );
      setTaskListStats(statsMap);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load project");
    } finally {
      setIsLoading(false);
    }
  }, [dataService, projectId]);

  // Load project data on mount
  useEffect(() => {
    loadProjectData();
  }, [loadProjectData]);


  /**
   * Handle back navigation
   * Requirements: 4.1 - Display a back navigation button to return to the previous screen
   */
  const handleBackClick = useCallback(() => {
    navigate(-1);
  }, [navigate]);

  /**
   * Handle search query change
   * Requirements: 4.2 - SearchFilterBar with search controls
   */
  const handleSearchChange = useCallback((value: string) => {
    setSearchQuery(value);
  }, []);

  /**
   * Handle sort/filter popup open
   * Requirements: 4.2 - Wire up to SortFilterPopup
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
    setActiveSortId("name-asc");
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
    return activeSortId !== "name-asc" || activeFilters.length > 0;
  }, [activeSortId, activeFilters]);

  /**
   * Handle task list card click
   * Requirements: 4.6 - Navigate to /lists/{taskListId} on TaskListCard click
   */
  const handleTaskListClick = useCallback((taskList: TaskList) => {
    navigate(`/lists/${taskList.id}`);
  }, [navigate]);

  /**
   * Handle edit button click
   * Requirements: 4.7 - Open EditProjectModal on edit button click
   */
  const handleEditClick = useCallback(() => {
    setIsEditModalOpen(true);
  }, []);

  /**
   * Handle delete button click
   * Requirements: 4.8 - Open DeleteConfirmationDialog on delete button click
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
   * Handle edit modal success - reload project data
   */
  const handleEditSuccess = useCallback(() => {
    setIsEditModalOpen(false);
    loadProjectData();
  }, [loadProjectData]);

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
    if (!projectId) return;

    setIsDeleting(true);
    try {
      await dataService.deleteProject(projectId);
      setIsDeleteDialogOpen(false);
      navigate("/projects");
    } catch (err) {
      console.error("Failed to delete project:", err);
    } finally {
      setIsDeleting(false);
    }
  }, [projectId, dataService, navigate]);

  /**
   * Filter and sort task lists based on search query, filters, and sort option
   */
  const filteredTaskLists = useMemo(() => {
    let result = taskLists;

    // Apply search filter
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
    const { field, direction } = parseSortOption(activeSortId);
    result = sortTaskLists(result, field, direction);

    return result;
  }, [taskLists, searchQuery, activeFilters, activeSortId, taskListStats]);

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
   * Get status counts for OverallProgress
   * Requirements: 4.3 - Display OverallProgress showing project's completion statistics
   */
  const statusCounts = useMemo((): StatusCounts => {
    if (!projectStats) {
      return { completed: 0, inProgress: 0, blocked: 0, notStarted: 0 };
    }
    return convertToStatusCounts(projectStats);
  }, [projectStats]);


  /**
   * Render a task list card
   * Requirements: 4.4, 4.6, 18.3, 18.4
   * - Cards have min-height (160px) and max-height (320px) constraints
   * - Narrower column width (~280px) achieved via columnBreakpoints
   */
  const renderTaskListCard = useCallback(
    (taskList: TaskListWithStats) => (
      <div 
        className="min-h-[160px] max-h-[320px]"
        style={{ minHeight: '160px', maxHeight: '320px' }}
      >
        <TaskListCard
          taskList={taskList}
          stats={taskList.stats}
          onClick={() => handleTaskListClick(taskList)}
          spotlight
          tilt
        />
      </div>
    ),
    [handleTaskListClick]
  );

  /**
   * Render loading skeleton
   */
  const renderLoadingSkeleton = () => (
    <div
      className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4"
      data-testid="single-project-view-loading"
      aria-busy="true"
      aria-label="Loading project"
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
      data-testid="single-project-view-empty"
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
      data-testid="single-project-view-error"
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
        Failed to load project
      </Typography>
      <Typography variant="body-sm" color="muted" className="mb-4">
        {error}
      </Typography>
      <Button variant="primary" onClick={loadProjectData}>
        Try Again
      </Button>
    </div>
  );

  // Show error state
  if (error && !isLoading) {
    return (
      <div className={cn("flex flex-col gap-6", className)} data-testid="single-project-view">
        {renderErrorState()}
      </div>
    );
  }

  return (
    <div
      className={cn("flex flex-col gap-6", className)}
      data-testid="single-project-view"
    >
      {/* Header - Requirements: 4.1, 4.5, 14.1, 14.2, 14.3 */}
      <div className="flex flex-col gap-4">
        {/* Top row with back button and action buttons - 40px height, 12px gap */}
        <div className="flex items-center justify-between gap-3">
          {/* Back button and title - Requirements: 4.1, 14.1, 14.3 */}
          <div className="flex items-center gap-3 flex-1 min-w-0">
            <button
              onClick={handleBackClick}
              aria-label="Go back"
              data-testid="back-button"
              className="flex-shrink-0 w-10 h-10 flex items-center justify-center rounded-lg bg-[var(--bg-surface)] border border-[var(--border)] text-[var(--text-primary)] hover:bg-[var(--bg-surface-hover)] hover:border-[var(--primary)] hover:text-[var(--primary)] transition-all duration-200 shadow-sm"
            >
              <Icon name="ChevronLeft" size={20} />
            </button>
            {!isLoading && project && (
              <div className="flex items-center gap-2 flex-1 min-w-0">
                <Typography variant="h3" color="muted" className="text-lg md:text-xl font-medium flex-shrink-0">
                  Project:
                </Typography>
                <Typography variant="h3" color="primary" className="text-lg md:text-xl font-semibold truncate">
                  {project.name}
                </Typography>
              </div>
            )}
          </div>

          {/* Action buttons - Requirements: 4.5, 14.2, 14.3 */}
          {!isLoading && project && (
            <div className="flex items-center gap-3 flex-shrink-0">
              <Button
                variant="secondary"
                size="md"
                onClick={handleEditClick}
                leftIcon={<Icon name="Pencil" size="sm" />}
                data-testid="edit-project-button"
              >
                Edit
              </Button>
              <Button
                variant="destructive"
                size="md"
                onClick={handleDeleteClick}
                leftIcon={<Icon name="Trash2" size="sm" />}
                data-testid="delete-project-button"
              >
                Delete
              </Button>
            </div>
          )}
        </div>

        {/* Project description */}
        {!isLoading && project?.description && (
          <Typography variant="body" color="secondary" className="mt-1">
            {project.description}
          </Typography>
        )}

        {/* OverallProgress - Requirements: 4.3 */}
        {!isLoading && projectStats && (
          <OverallProgress
            statusCounts={statusCounts}
            data-testid="project-overall-progress"
          />
        )}

        {/* SearchFilterBar - Requirements: 4.2 */}
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

      {!isLoading && !error && taskListsWithStats.length === 0 && renderEmptyState()}

      {/* MasonryGrid - Requirements: 4.4, 4.9, 18.3, 18.4 */}
      {/* Use narrower columns (~280px) for showcase-style TaskListCards */}
      {!isLoading && !error && taskListsWithStats.length > 0 && (
        <MasonryGrid
          items={taskListsWithStats}
          renderItem={renderTaskListCard}
          gap={16}
          animateLayout
          layoutId="single-project-tasklists-masonry"
          columnBreakpoints={{ 0: 1, 560: 2, 840: 3, 1120: 4, 1400: 5, 1680: 6 }}
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

      {/* Edit Project Modal - Requirements: 4.7 */}
      {project && (
        <EditProjectModal
          isOpen={isEditModalOpen}
          project={project}
          onClose={handleEditModalClose}
          onSuccess={handleEditSuccess}
        />
      )}

      {/* Delete Confirmation Dialog - Requirements: 4.8 */}
      {project && (
        <DeleteConfirmationDialog
          isOpen={isDeleteDialogOpen}
          title="Delete Project"
          message="Are you sure you want to delete this project? This will also delete all task lists and tasks within it."
          itemName={project.name}
          onConfirm={handleDeleteConfirm}
          onCancel={handleDeleteDialogClose}
          isDestructive
          loading={isDeleting}
          cascadingDeletion={{
            taskListCount: projectStats?.taskListCount,
            taskCount: projectStats?.totalTasks,
          }}
        />
      )}
    </div>
  );
};

SingleProjectView.displayName = "SingleProjectView";

export default SingleProjectView;
