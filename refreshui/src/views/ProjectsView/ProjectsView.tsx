import React, { useState, useEffect, useCallback, useMemo } from "react";
import { useDataService } from "../../context/DataServiceContext";
import { MasonryGrid } from "../../layouts/MasonryGrid";
import { ProjectCard, ProjectCardSkeleton } from "../../components/organisms/ProjectCard";
import { EditProjectModal } from "../../components/organisms/EditProjectModal";
import { DeleteConfirmationDialog } from "../../components/organisms/DeleteConfirmationDialog";
import { SearchBar } from "../../components/molecules/SearchBar";
import { FilterChips } from "../../components/molecules/FilterChips";
import { Typography } from "../../components/atoms/Typography";
import { cn } from "../../lib/utils";
import type { Project } from "../../core/types/entities";
import type { ProjectStats } from "../../services/types";

/**
 * ProjectsView Component
 *
 * A view component that displays all projects in a masonry grid layout
 * with search and filter capabilities.
 *
 * Requirements: 10.1
 * - Display all projects in a masonry grid
 * - Search capability for filtering projects by name/description
 * - Filter capabilities for project status
 */

export interface ProjectsViewProps {
  /** Callback when a project is clicked */
  onProjectClick?: (project: Project) => void;
  /** Additional CSS classes */
  className?: string;
}

/** Filter options for project completion status */
const COMPLETION_FILTER_OPTIONS = [
  { id: "all", label: "All" },
  { id: "not-started", label: "Not Started" },
  { id: "in-progress", label: "In Progress" },
  { id: "completed", label: "Completed" },
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
 * ProjectsView component
 */
export const ProjectsView: React.FC<ProjectsViewProps> = ({
  onProjectClick,
  className,
}) => {
  const { dataService } = useDataService();

  // State
  const [projects, setProjects] = useState<Project[]>([]);
  const [projectStats, setProjectStats] = useState<Map<string, ProjectStats>>(
    new Map()
  );
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedFilters, setSelectedFilters] = useState<string[]>(["all"]);

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
   * Handle edit action on a project
   * Requirements: 23.3 - Open the corresponding edit modal when edit button is clicked
   */
  const handleEditProject = useCallback((project: Project) => {
    setEditingProject(project);
  }, []);

  /**
   * Handle delete action on a project
   * Requirements: 23.4 - Open the corresponding confirmation dialog when delete button is clicked
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
   * Filter projects based on search query and filters
   */
  const filteredProjects = useMemo(() => {
    return projects.filter((project) => {
      // Search filter
      if (searchQuery) {
        const query = searchQuery.toLowerCase();
        const matchesName = project.name.toLowerCase().includes(query);
        const matchesDescription = project.description
          ?.toLowerCase()
          .includes(query);
        if (!matchesName && !matchesDescription) {
          return false;
        }
      }

      // Completion status filter
      if (!selectedFilters.includes("all")) {
        const stats = projectStats.get(project.id);
        const status = getCompletionStatus(stats);
        if (!selectedFilters.includes(status)) {
          return false;
        }
      }

      return true;
    });
  }, [projects, searchQuery, selectedFilters, projectStats]);

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
   * Requirements: 23.3, 23.4 - Wire up edit and delete handlers to card actions
   */
  const renderProjectCard = useCallback(
    (project: ProjectWithStats) => (
      <ProjectCard
        project={project}
        stats={project.stats}
        onClick={() => onProjectClick?.(project)}
        onEdit={handleEditProject}
        onDelete={handleDeleteProject}
        spotlight
        tilt
      />
    ),
    [onProjectClick, handleEditProject, handleDeleteProject]
  );

  /**
   * Render loading skeleton
   * Requirements: 10.5 - Display skeleton placeholders matching expected content layout
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
        {searchQuery || !selectedFilters.includes("all")
          ? "No projects match your filters"
          : "No projects yet"}
      </Typography>
      <Typography variant="body-sm" color="muted">
        {searchQuery || !selectedFilters.includes("all")
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
      <div className="flex flex-col gap-4">
        <Typography variant="h3" color="primary">
          Projects
        </Typography>

        {/* Search and Filters */}
        <div className="flex flex-col sm:flex-row gap-4">
          <div className="flex-1 max-w-md">
            <SearchBar
              placeholder="Search projects..."
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

      {/* Content */}
      {isLoading && renderLoadingSkeleton()}

      {error && !isLoading && renderErrorState()}

      {!isLoading && !error && projectsWithStats.length === 0 && renderEmptyState()}

      {!isLoading && !error && projectsWithStats.length > 0 && (
        <MasonryGrid
          items={projectsWithStats}
          renderItem={renderProjectCard}
          gap={16}
          animateLayout
          layoutId="projects-masonry"
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

      {/* Edit Project Modal - Requirements: 23.3 */}
      {editingProject && (
        <EditProjectModal
          isOpen={!!editingProject}
          project={editingProject}
          onClose={handleEditModalClose}
          onSuccess={handleEditSuccess}
        />
      )}

      {/* Delete Confirmation Dialog - Requirements: 23.4 */}
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
