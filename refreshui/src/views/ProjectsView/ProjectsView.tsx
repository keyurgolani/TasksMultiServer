import React, { useState, useEffect, useCallback, useMemo, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { useDataService } from "../../context/DataServiceContext";
import { MasonryGrid } from "../../layouts/MasonryGrid";
import { ProjectCard, ProjectCardSkeleton } from "../../components/organisms/ProjectCard";
import { EditProjectModal } from "../../components/organisms/EditProjectModal";
import { DeleteConfirmationDialog } from "../../components/organisms/DeleteConfirmationDialog";
import { SearchFilterBar } from "../../components/molecules/SearchFilterBar";
import { SortFilterPopup, type SortOption, type FilterOption } from "../../components/organisms/SortFilterPopup";
import { Typography } from "../../components/atoms/Typography";
import { filterProjects } from "../../utils/filtering";
import { sortProjects, type ProjectSortField, type SortDirection } from "../../utils/sorting";
import { cn } from "../../lib/utils";
import type { Project } from "../../core/types/entities";
import type { ProjectStats } from "../../services/types";

/**
 * ProjectsView Component
 *
 * A view component that displays all projects in a masonry grid layout
 * with search and filter capabilities using SearchFilterBar.
 *
 * Requirements: 3.1, 3.2, 3.3, 3.4, 3.5
 * - 3.1: Display SearchFilterBar with search input and SortFilterButton at top
 * - 3.2: Display all ProjectCard components in a MasonryGrid layout
 * - 3.3: Filter ProjectCard components based on search query
 * - 3.4: Navigate to /projects/{projectId} on card click
 * - 3.5: Reorder or filter ProjectCard components via SortFilterPopup
 */

export interface ProjectsViewProps {
  /** Callback when a project is clicked (optional, navigation is default) */
  onProjectClick?: (project: Project) => void;
  /** Additional CSS classes */
  className?: string;
}

/**
 * Sort options for projects
 */
const PROJECT_SORT_OPTIONS: SortOption[] = [
  { id: "taskListCount-desc", label: "Most lists" },
  { id: "taskListCount-asc", label: "Fewest lists" },
  { id: "name-asc", label: "Name (A-Z)" },
  { id: "name-desc", label: "Name (Z-A)" },
  { id: "createdAt-desc", label: "Newest first" },
  { id: "createdAt-asc", label: "Oldest first" },
  { id: "updatedAt-desc", label: "Recently updated" },
  { id: "updatedAt-asc", label: "Least recently updated" },
];

/**
 * Filter options for project completion status
 */
const PROJECT_FILTER_OPTIONS: FilterOption[] = [
  { id: "status-not-started", label: "Not Started", type: "checkbox", group: "Status" },
  { id: "status-in-progress", label: "In Progress", type: "checkbox", group: "Status" },
  { id: "status-completed", label: "Completed", type: "checkbox", group: "Status" },
];

/** Extended project type with stats for masonry grid */
interface ProjectWithStats extends Project {
  stats?: ProjectStats;
  height: number;
}

/**
 * Calculates estimated card height based on project data
 */
const estimateCardHeight = (project: Project, stats?: ProjectStats): number => {
  let height = 120; // Base height for name
  if (project.description) height += 40;
  if (stats) height += 140; // Stats section
  return height;
};

/**
 * Determines completion status category based on stats
 */
const getCompletionStatus = (stats?: ProjectStats): string => {
  if (!stats || stats.totalTasks === 0) return "not-started";
  const percentage = (stats.completedTasks / stats.totalTasks) * 100;
  if (percentage >= 100) return "completed";
  if (percentage > 0) return "in-progress";
  return "not-started";
};

/**
 * Parse sort option ID into field and direction
 */
function parseSortOption(sortId: string): { field: ProjectSortField; direction: SortDirection } {
  const [field, direction] = sortId.split("-") as [ProjectSortField, SortDirection];
  return { field, direction };
}

/**
 * ProjectsView component
 */
export const ProjectsView: React.FC<ProjectsViewProps> = ({
  onProjectClick,
  className,
}) => {
  const navigate = useNavigate();
  const { dataService } = useDataService();

  // State
  const [projects, setProjects] = useState<Project[]>([]);
  const [projectStats, setProjectStats] = useState<Map<string, ProjectStats>>(
    new Map()
  );
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Search/filter state
  const [searchQuery, setSearchQuery] = useState("");
  const [sortFilterPopupOpen, setSortFilterPopupOpen] = useState(false);
  const [activeSortId, setActiveSortId] = useState("taskListCount-desc");
  const [activeFilters, setActiveFilters] = useState<string[]>([]);
  
  // Ref for SortFilterPopup anchor
  const sortFilterButtonRef = useRef<HTMLDivElement>(null);

  // Edit/Delete modal state
  const [editingProject, setEditingProject] = useState<Project | null>(null);
  const [deletingProject, setDeletingProject] = useState<Project | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);

  /**
   * Load projects and their stats
   */
  const loadProjects = useCallback(async () => {
    setIsLoading(true);
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
            // Stats loading failure is non-critical
            console.warn(`Failed to load stats for project ${project.id}`);
          }
        })
      );
      setProjectStats(statsMap);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to load projects"
      );
    } finally {
      setIsLoading(false);
    }
  }, [dataService]);

  // Load projects on mount
  useEffect(() => {
    loadProjects();
  }, [loadProjects]);

  /**
   * Handle search query change
   * Requirements: 3.3 - Filter ProjectCard components based on search query
   */
  const handleSearchChange = useCallback((value: string) => {
    setSearchQuery(value);
  }, []);

  /**
   * Handle sort/filter popup open
   * Requirements: 3.5 - Wire up to SortFilterPopup
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
    setActiveSortId("taskListCount-desc");
    setActiveFilters([]);
    setSearchQuery("");
  }, []);

  /**
   * Handle sort option change
   * Requirements: 3.5 - Reorder ProjectCard components via SortFilterPopup
   */
  const handleSortChange = useCallback((sortId: string) => {
    setActiveSortId(sortId);
  }, []);

  /**
   * Handle filter option change
   * Requirements: 3.5 - Filter ProjectCard components via SortFilterPopup
   */
  const handleFilterChange = useCallback((filterIds: string[]) => {
    setActiveFilters(filterIds);
  }, []);

  /**
   * Check if any sort/filter is active (non-default)
   */
  const sortFilterActive = useMemo(() => {
    return activeSortId !== "taskListCount-desc" || activeFilters.length > 0;
  }, [activeSortId, activeFilters]);

  /**
   * Handle project card click
   * Requirements: 3.4 - Navigate to /projects/{projectId} on card click
   */
  const handleProjectCardClick = useCallback((project: Project) => {
    if (onProjectClick) {
      onProjectClick(project);
    } else {
      navigate(`/projects/${project.id}`);
    }
  }, [navigate, onProjectClick]);

  /**
   * Handle edit action on a project
   */
  const handleEditProject = useCallback((project: Project) => {
    setEditingProject(project);
  }, []);

  /**
   * Handle delete action on a project
   */
  const handleDeleteProject = useCallback((project: Project) => {
    setDeletingProject(project);
  }, []);

  /**
   * Handle edit modal close
   */
  const handleEditModalClose = useCallback(() => {
    setEditingProject(null);
  }, []);

  /**
   * Handle edit modal success - reload projects to reflect changes
   */
  const handleEditSuccess = useCallback(() => {
    setEditingProject(null);
    loadProjects();
  }, [loadProjects]);

  /**
   * Handle delete confirmation dialog close
   */
  const handleDeleteDialogClose = useCallback(() => {
    setDeletingProject(null);
  }, []);

  /**
   * Handle delete confirmation - delete the project and reload
   */
  const handleDeleteConfirm = useCallback(async () => {
    if (!deletingProject) return;

    setIsDeleting(true);
    try {
      await dataService.deleteProject(deletingProject.id);
      setDeletingProject(null);
      loadProjects();
    } catch (err) {
      console.error("Failed to delete project:", err);
      // Keep dialog open on error so user can retry or cancel
    } finally {
      setIsDeleting(false);
    }
  }, [deletingProject, dataService, loadProjects]);

  /**
   * Filter and sort projects based on search query, filters, and sort option
   * Requirements: 3.3, 3.5
   */
  const filteredProjects = useMemo(() => {
    let result = projects;

    // Apply search filter
    // Requirements: 3.3 - Filter ProjectCard components based on search query
    if (searchQuery) {
      result = filterProjects(result, searchQuery);
    }

    // Apply status filters
    if (activeFilters.length > 0) {
      const statusFilters = activeFilters
        .filter((f) => f.startsWith("status-"))
        .map((f) => f.replace("status-", ""));

      if (statusFilters.length > 0) {
        result = result.filter((project) => {
          const stats = projectStats.get(project.id);
          const status = getCompletionStatus(stats);
          return statusFilters.includes(status);
        });
      }
    }

    // Apply sorting
    // Requirements: 3.5 - Reorder ProjectCard components via SortFilterPopup
    const { field, direction } = parseSortOption(activeSortId);
    
    // Handle custom taskListCount sorting
    if (field === "taskListCount") {
      result = [...result].sort((a, b) => {
        const countA = projectStats.get(a.id)?.taskListCount ?? 0;
        const countB = projectStats.get(b.id)?.taskListCount ?? 0;
        return direction === "desc" ? countB - countA : countA - countB;
      });
    } else {
      result = sortProjects(result, field as ProjectSortField, direction);
    }

    return result;
  }, [projects, searchQuery, activeFilters, activeSortId, projectStats]);

  /**
   * Prepare projects for masonry grid with stats and height
   */
  const projectsWithStats: ProjectWithStats[] = useMemo(() => {
    return filteredProjects.map((project) => {
      const stats = projectStats.get(project.id);
      return {
        ...project,
        stats,
        height: estimateCardHeight(project, stats),
      };
    });
  }, [filteredProjects, projectStats]);

  /**
   * Render a project card
   * Requirements: 3.2, 3.4, 3.7, 18.1, 18.2
   * - Use showcase-style ProjectCards with tilt effect for parallax
   * - Cards have min-height (180px) and max-height (350px) constraints
   * - Narrower column width (~280px) achieved via columnBreakpoints
   */
  const renderProjectCard = useCallback(
    (project: ProjectWithStats) => (
      <div 
        className="min-h-[180px] max-h-[350px]"
        style={{ minHeight: '180px', maxHeight: '350px' }}
      >
        <ProjectCard
          project={project}
          stats={project.stats}
          onClick={() => handleProjectCardClick(project)}
          onEdit={handleEditProject}
          onDelete={handleDeleteProject}
          spotlight
          tilt
        />
      </div>
    ),
    [handleProjectCardClick, handleEditProject, handleDeleteProject]
  );

  /**
   * Render loading skeleton
   */
  const renderLoadingSkeleton = () => (
    <div 
      className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4"
      data-testid="projects-view-loading"
      aria-busy="true"
      aria-label="Loading projects"
    >
      {Array.from({ length: 6 }).map((_, index) => (
        <ProjectCardSkeleton key={index} />
      ))}
    </div>
  );

  /**
   * Render empty state
   */
  const renderEmptyState = () => (
    <div
      className="flex flex-col items-center justify-center py-16 text-center"
      data-testid="projects-view-empty"
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
        {searchQuery || activeFilters.length > 0
          ? "No projects match your filters"
          : "No projects yet"}
      </Typography>
      <Typography variant="body-sm" color="muted">
        {searchQuery || activeFilters.length > 0
          ? "Try adjusting your search or filters"
          : "Create your first project to get started"}
      </Typography>
    </div>
  );

  /**
   * Render error state
   */
  const renderErrorState = () => (
    <div
      className="flex flex-col items-center justify-center py-16 text-center"
      data-testid="projects-view-error"
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
        Failed to load projects
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

  return (
    <div
      className={cn("flex flex-col gap-6", className)}
      data-testid="projects-view"
    >
      {/* Header */}
      {/* Requirements: 3.6 - Display a prominent page title that is clearly visible */}
      <div className="flex flex-col gap-4">
        <Typography variant="h1" color="primary" className="text-3xl md:text-4xl font-bold">
          Projects
        </Typography>

        {/* SearchFilterBar - Requirements: 3.1 */}
        <div ref={sortFilterButtonRef} className="relative">
          <SearchFilterBar
            searchValue={searchQuery}
            onSearchChange={handleSearchChange}
            sortFilterActive={sortFilterActive}
            onSortFilterOpen={handleSortFilterOpen}
            onSortFilterReset={handleSortFilterReset}
            searchPlaceholder="Search projects..."
            sortFilterLabel="Sort & Filter"
          />
          <SortFilterPopup
            isOpen={sortFilterPopupOpen}
            onClose={handleSortFilterClose}
            sortOptions={PROJECT_SORT_OPTIONS}
            filterOptions={PROJECT_FILTER_OPTIONS}
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

      {!isLoading && !error && projectsWithStats.length === 0 && renderEmptyState()}

      {/* MasonryGrid - Requirements: 3.2, 3.7, 18.1, 18.2 */}
      {/* Use narrower columns (~280px) for showcase-style cards with parallax effect */}
      {!isLoading && !error && projectsWithStats.length > 0 && (
        <MasonryGrid
          items={projectsWithStats}
          renderItem={renderProjectCard}
          gap={16}
          animateLayout
          layoutId="projects-masonry"
          columnBreakpoints={{ 0: 1, 560: 2, 840: 3, 1120: 4, 1400: 5, 1680: 6 }}
        />
      )}

      {/* Results count */}
      {!isLoading && !error && projects.length > 0 && (
        <div className="text-center">
          <Typography variant="caption" color="muted">
            Showing {filteredProjects.length} of {projects.length} projects
          </Typography>
        </div>
      )}

      {/* Edit Project Modal */}
      {editingProject && (
        <EditProjectModal
          isOpen={!!editingProject}
          project={editingProject}
          onClose={handleEditModalClose}
          onSuccess={handleEditSuccess}
        />
      )}

      {/* Delete Confirmation Dialog */}
      {deletingProject && (
        <DeleteConfirmationDialog
          isOpen={!!deletingProject}
          title="Delete Project"
          message="Are you sure you want to delete this project? This will also delete all task lists and tasks within it."
          itemName={deletingProject.name}
          onConfirm={handleDeleteConfirm}
          onCancel={handleDeleteDialogClose}
          isDestructive
          loading={isDeleting}
        />
      )}
    </div>
  );
};

ProjectsView.displayName = "ProjectsView";

export default ProjectsView;
