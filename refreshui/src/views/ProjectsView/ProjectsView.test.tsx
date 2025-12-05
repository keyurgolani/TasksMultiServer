import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor, fireEvent, act } from "@testing-library/react";
import { ProjectsView } from "./ProjectsView";
import { DataServiceProvider } from "../../context/DataServiceContext";
import type { IDataService, ProjectStats } from "../../services/types";
import type { Project } from "../../core/types/entities";

/**
 * ProjectsView Tests
 *
 * Requirements: 10.1
 * - Display all projects in a masonry grid with search and filter capabilities
 */

// Mock project data
const mockProjects: Project[] = [
  {
    id: "project-1",
    name: "Project Alpha",
    description: "First test project",
    createdAt: "2024-01-01T00:00:00Z",
    updatedAt: "2024-01-01T00:00:00Z",
  },
  {
    id: "project-2",
    name: "Project Beta",
    description: "Second test project",
    createdAt: "2024-01-02T00:00:00Z",
    updatedAt: "2024-01-02T00:00:00Z",
  },
  {
    id: "project-3",
    name: "Project Gamma",
    description: "Third test project with completed tasks",
    createdAt: "2024-01-03T00:00:00Z",
    updatedAt: "2024-01-03T00:00:00Z",
  },
];

// Mock project stats
const mockProjectStats: Record<string, ProjectStats> = {
  "project-1": {
    taskListCount: 2,
    totalTasks: 10,
    readyTasks: 3,
    completedTasks: 0,
    inProgressTasks: 2,
    blockedTasks: 1,
  },
  "project-2": {
    taskListCount: 1,
    totalTasks: 5,
    readyTasks: 1,
    completedTasks: 2,
    inProgressTasks: 1,
    blockedTasks: 0,
  },
  "project-3": {
    taskListCount: 3,
    totalTasks: 8,
    readyTasks: 0,
    completedTasks: 8,
    inProgressTasks: 0,
    blockedTasks: 0,
  },
};

// Create mock data service
const createMockDataService = (): IDataService => ({
  getProjects: vi.fn().mockResolvedValue(mockProjects),
  getProject: vi.fn().mockImplementation((id: string) => {
    const project = mockProjects.find((p) => p.id === id);
    return project
      ? Promise.resolve(project)
      : Promise.reject(new Error("Not found"));
  }),
  createProject: vi.fn(),
  updateProject: vi.fn(),
  deleteProject: vi.fn(),
  getProjectStats: vi.fn().mockImplementation((id: string) => {
    const stats = mockProjectStats[id];
    return stats
      ? Promise.resolve(stats)
      : Promise.resolve({
          taskListCount: 0,
          totalTasks: 0,
          readyTasks: 0,
          completedTasks: 0,
          inProgressTasks: 0,
          blockedTasks: 0,
        });
  }),
  getTaskLists: vi.fn().mockResolvedValue([]),
  getTaskList: vi.fn(),
  createTaskList: vi.fn(),
  updateTaskList: vi.fn(),
  deleteTaskList: vi.fn(),
  getTaskListStats: vi.fn(),
  getTasks: vi.fn().mockResolvedValue([]),
  getTask: vi.fn(),
  createTask: vi.fn(),
  updateTask: vi.fn(),
  deleteTask: vi.fn(),
  addNote: vi.fn(),
  addResearchNote: vi.fn(),
  addExecutionNote: vi.fn(),
  searchTasks: vi.fn().mockResolvedValue({ items: [], total: 0, count: 0, offset: 0 }),
  getReadyTasks: vi.fn().mockResolvedValue([]),
});

// Wrapper component with DataServiceProvider
const renderWithProvider = (
  ui: React.ReactElement,
  service: IDataService = createMockDataService()
) => {
  return render(
    <DataServiceProvider service={service}>{ui}</DataServiceProvider>
  );
};

describe("ProjectsView", () => {
  let mockService: IDataService;

  beforeEach(() => {
    mockService = createMockDataService();
    vi.clearAllMocks();
  });

  describe("rendering", () => {
    it("renders the projects view container", async () => {
      renderWithProvider(<ProjectsView />, mockService);

      await waitFor(() => {
        expect(screen.getByTestId("projects-view")).toBeInTheDocument();
      });
    });

    it("renders the page title", async () => {
      renderWithProvider(<ProjectsView />, mockService);

      await waitFor(() => {
        expect(screen.getByText("Projects")).toBeInTheDocument();
      });
    });

    it("renders the search bar", async () => {
      renderWithProvider(<ProjectsView />, mockService);

      await waitFor(() => {
        expect(
          screen.getByPlaceholderText("Search projects...")
        ).toBeInTheDocument();
      });
    });

    it("renders filter chips", async () => {
      renderWithProvider(<ProjectsView />, mockService);

      await waitFor(() => {
        expect(screen.getByText("All")).toBeInTheDocument();
        expect(screen.getByText("Not Started")).toBeInTheDocument();
        expect(screen.getByText("In Progress")).toBeInTheDocument();
        expect(screen.getByText("Completed")).toBeInTheDocument();
      });
    });
  });

  describe("data loading", () => {
    it("loads and displays projects", async () => {
      renderWithProvider(<ProjectsView />, mockService);

      await waitFor(() => {
        expect(screen.getByText("Project Alpha")).toBeInTheDocument();
        expect(screen.getByText("Project Beta")).toBeInTheDocument();
        expect(screen.getByText("Project Gamma")).toBeInTheDocument();
      });
    });

    it("displays project descriptions", async () => {
      renderWithProvider(<ProjectsView />, mockService);

      await waitFor(() => {
        expect(screen.getByText("First test project")).toBeInTheDocument();
        expect(screen.getByText("Second test project")).toBeInTheDocument();
      });
    });

    it("displays results count", async () => {
      renderWithProvider(<ProjectsView />, mockService);

      await waitFor(() => {
        expect(
          screen.getByText("Showing 3 of 3 projects")
        ).toBeInTheDocument();
      });
    });
  });

  describe("search functionality", () => {
    it("filters projects by search query", async () => {
      renderWithProvider(<ProjectsView />, mockService);

      // Wait for projects to load
      await waitFor(() => {
        expect(screen.getByText("Project Alpha")).toBeInTheDocument();
      });

      // Type in search
      const searchInput = screen.getByPlaceholderText("Search projects...");
      await act(async () => {
        fireEvent.change(searchInput, { target: { value: "Alpha" } });
      });

      // Wait for debounce and filter
      await waitFor(() => {
        expect(screen.getByText("Project Alpha")).toBeInTheDocument();
        expect(screen.queryByText("Project Beta")).not.toBeInTheDocument();
        expect(screen.queryByText("Project Gamma")).not.toBeInTheDocument();
      }, { timeout: 1000 });
    });

    it("shows empty state when no projects match search", async () => {
      renderWithProvider(<ProjectsView />, mockService);

      // Wait for projects to load
      await waitFor(() => {
        expect(screen.getByText("Project Alpha")).toBeInTheDocument();
      });

      // Type in search that matches nothing
      const searchInput = screen.getByPlaceholderText("Search projects...");
      await act(async () => {
        fireEvent.change(searchInput, { target: { value: "NonExistent" } });
      });

      // Wait for debounce and filter
      await waitFor(() => {
        expect(
          screen.getByText("No projects match your filters")
        ).toBeInTheDocument();
      }, { timeout: 1000 });
    });
  });

  describe("filter functionality", () => {
    it("filters projects by completion status", async () => {
      renderWithProvider(<ProjectsView />, mockService);

      // Wait for projects to load
      await waitFor(() => {
        expect(screen.getByText("Project Alpha")).toBeInTheDocument();
      });

      // Click on "Completed" filter
      const completedFilter = screen.getByRole("checkbox", {
        name: /Completed/i,
      });
      await act(async () => {
        fireEvent.click(completedFilter);
      });

      // Wait for filter to apply
      await waitFor(() => {
        // Project Gamma has 100% completion
        expect(screen.getByText("Project Gamma")).toBeInTheDocument();
        // Project Alpha has 0% completion
        expect(screen.queryByText("Project Alpha")).not.toBeInTheDocument();
      });
    });
  });

  describe("interactions", () => {
    it("calls onProjectClick when a project card is clicked", async () => {
      const onProjectClick = vi.fn();
      renderWithProvider(
        <ProjectsView onProjectClick={onProjectClick} />,
        mockService
      );

      // Wait for projects to load
      await waitFor(() => {
        expect(screen.getByText("Project Alpha")).toBeInTheDocument();
      });

      // Click on a project card
      const projectCard = screen.getByText("Project Alpha").closest("[data-testid='project-card']");
      if (projectCard) {
        fireEvent.click(projectCard);
      }

      expect(onProjectClick).toHaveBeenCalledWith(
        expect.objectContaining({ id: "project-1", name: "Project Alpha" })
      );
    });
  });

  describe("error handling", () => {
    it("displays error state when loading fails", async () => {
      const errorService = createMockDataService();
      vi.mocked(errorService.getProjects).mockRejectedValue(
        new Error("Network error")
      );

      renderWithProvider(<ProjectsView />, errorService);

      await waitFor(() => {
        expect(
          screen.getByText("Failed to load projects")
        ).toBeInTheDocument();
        expect(screen.getByText("Network error")).toBeInTheDocument();
      });
    });

    it("shows retry button on error", async () => {
      const errorService = createMockDataService();
      vi.mocked(errorService.getProjects).mockRejectedValue(
        new Error("Network error")
      );

      renderWithProvider(<ProjectsView />, errorService);

      await waitFor(() => {
        expect(screen.getByText("Try Again")).toBeInTheDocument();
      });
    });
  });

  describe("empty state", () => {
    it("displays empty state when no projects exist", async () => {
      const emptyService = createMockDataService();
      vi.mocked(emptyService.getProjects).mockResolvedValue([]);

      renderWithProvider(<ProjectsView />, emptyService);

      await waitFor(() => {
        expect(screen.getByTestId("projects-view-empty")).toBeInTheDocument();
        expect(screen.getByText("No projects yet")).toBeInTheDocument();
      });
    });
  });
});
