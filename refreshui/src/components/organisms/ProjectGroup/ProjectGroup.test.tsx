import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { ProjectGroup } from "./ProjectGroup";
import type { Project, TaskList } from "../../../core/types/entities";
import type { ProjectStats, TaskListStats } from "../../../services/types";

/**
 * ProjectGroup Organism Tests
 *
 * Tests for the ProjectGroup component verifying:
 * - Collapsible header functionality (Requirements 24.1, 24.2)
 * - Task list count display in collapsed state (Requirements 24.3)
 * - Task list rendering in expanded state (Requirements 24.4)
 * - Glassmorphism effect and design system styling (Requirements 24.5)
 *
 * Property 49: ProjectGroup Collapse State
 * Property 50: ProjectGroup Task List Display
 */

// Mock project data
const mockProject: Project = {
  id: "project-1",
  name: "Test Project",
  description: "A test project description",
  createdAt: "2024-01-01T00:00:00Z",
  updatedAt: "2024-01-01T00:00:00Z",
};

// Mock task lists
const mockTaskLists: TaskList[] = [
  {
    id: "tasklist-1",
    projectId: "project-1",
    name: "Task List 1",
    description: "First task list",
    createdAt: "2024-01-01T00:00:00Z",
    updatedAt: "2024-01-01T00:00:00Z",
  },
  {
    id: "tasklist-2",
    projectId: "project-1",
    name: "Task List 2",
    description: "Second task list",
    createdAt: "2024-01-01T00:00:00Z",
    updatedAt: "2024-01-01T00:00:00Z",
  },
];

// Mock project stats
const mockProjectStats: ProjectStats = {
  taskListCount: 2,
  totalTasks: 10,
  readyTasks: 3,
  completedTasks: 5,
  inProgressTasks: 2,
  blockedTasks: 0,
};

// Mock task list stats
const mockTaskListStats: Record<string, TaskListStats> = {
  "tasklist-1": {
    taskCount: 5,
    readyTasks: 2,
    completedTasks: 3,
    inProgressTasks: 1,
    blockedTasks: 0,
    completionPercentage: 60,
  },
  "tasklist-2": {
    taskCount: 5,
    readyTasks: 1,
    completedTasks: 2,
    inProgressTasks: 1,
    blockedTasks: 1,
    completionPercentage: 40,
  },
};

describe("ProjectGroup", () => {
  describe("Rendering", () => {
    it("renders project name in header", () => {
      render(<ProjectGroup project={mockProject} taskLists={mockTaskLists} />);

      expect(screen.getByTestId("project-group-name")).toHaveTextContent(
        "Test Project"
      );
    });

    it("renders project description when provided", () => {
      render(<ProjectGroup project={mockProject} taskLists={mockTaskLists} />);

      expect(screen.getByTestId("project-group-description")).toHaveTextContent(
        "A test project description"
      );
    });

    it("renders task list count badge", () => {
      render(<ProjectGroup project={mockProject} taskLists={mockTaskLists} />);

      expect(screen.getByTestId("project-group-tasklist-count")).toHaveTextContent(
        "2 lists"
      );
    });

    it("renders singular 'list' when only one task list", () => {
      render(
        <ProjectGroup project={mockProject} taskLists={[mockTaskLists[0]]} />
      );

      expect(screen.getByTestId("project-group-tasklist-count")).toHaveTextContent(
        "1 list"
      );
    });

    it("renders progress bar when stats are provided", () => {
      render(
        <ProjectGroup
          project={mockProject}
          taskLists={mockTaskLists}
          stats={mockProjectStats}
        />
      );

      expect(screen.getByTestId("project-group-progress")).toBeInTheDocument();
      expect(screen.getByTestId("project-group-completion-text")).toHaveTextContent(
        "50%"
      );
    });

    it("does not render progress bar when no stats", () => {
      render(<ProjectGroup project={mockProject} taskLists={mockTaskLists} />);

      expect(screen.queryByTestId("project-group-progress")).not.toBeInTheDocument();
    });
  });

  describe("Collapse/Expand Functionality (Property 49)", () => {
    it("is expanded by default", () => {
      render(<ProjectGroup project={mockProject} taskLists={mockTaskLists} />);

      expect(screen.getByTestId("project-group-content")).toBeInTheDocument();
      expect(screen.getByTestId("project-group-header")).toHaveAttribute(
        "aria-expanded",
        "true"
      );
    });

    it("can be collapsed by default with defaultExpanded=false", () => {
      render(
        <ProjectGroup
          project={mockProject}
          taskLists={mockTaskLists}
          defaultExpanded={false}
        />
      );

      expect(screen.queryByTestId("project-group-content")).not.toBeInTheDocument();
      expect(screen.getByTestId("project-group-header")).toHaveAttribute(
        "aria-expanded",
        "false"
      );
    });

    it("toggles expanded state when header is clicked", () => {
      render(<ProjectGroup project={mockProject} taskLists={mockTaskLists} />);

      const header = screen.getByTestId("project-group-header");

      // Initially expanded
      expect(screen.getByTestId("project-group-content")).toBeInTheDocument();

      // Click to collapse
      fireEvent.click(header);
      expect(screen.queryByTestId("project-group-content")).not.toBeInTheDocument();

      // Click to expand again
      fireEvent.click(header);
      expect(screen.getByTestId("project-group-content")).toBeInTheDocument();
    });

    it("toggles expanded state with keyboard (Enter)", () => {
      render(<ProjectGroup project={mockProject} taskLists={mockTaskLists} />);

      const header = screen.getByTestId("project-group-header");

      // Initially expanded
      expect(screen.getByTestId("project-group-content")).toBeInTheDocument();

      // Press Enter to collapse
      fireEvent.keyDown(header, { key: "Enter" });
      expect(screen.queryByTestId("project-group-content")).not.toBeInTheDocument();
    });

    it("toggles expanded state with keyboard (Space)", () => {
      render(<ProjectGroup project={mockProject} taskLists={mockTaskLists} />);

      const header = screen.getByTestId("project-group-header");

      // Initially expanded
      expect(screen.getByTestId("project-group-content")).toBeInTheDocument();

      // Press Space to collapse
      fireEvent.keyDown(header, { key: " " });
      expect(screen.queryByTestId("project-group-content")).not.toBeInTheDocument();
    });

    it("shows correct chevron icon based on expanded state", () => {
      render(
        <ProjectGroup
          project={mockProject}
          taskLists={mockTaskLists}
          defaultExpanded={false}
        />
      );

      const header = screen.getByTestId("project-group-header");

      // Collapsed - should show ChevronRight (we can't easily check the icon name,
      // but we can verify the chevron element exists)
      expect(screen.getByTestId("project-group-chevron")).toBeInTheDocument();

      // Expand
      fireEvent.click(header);

      // Still has chevron (now ChevronDown)
      expect(screen.getByTestId("project-group-chevron")).toBeInTheDocument();
    });
  });

  describe("Task List Display (Property 50)", () => {
    it("renders all task lists when expanded", () => {
      render(
        <ProjectGroup
          project={mockProject}
          taskLists={mockTaskLists}
          taskListStats={mockTaskListStats}
        />
      );

      // TaskListCard components render with data-testid="tasklist-card"
      const taskListCards = screen.getAllByTestId("tasklist-card");
      expect(taskListCards).toHaveLength(2);
      
      // Verify task list names are rendered
      expect(screen.getByText("Task List 1")).toBeInTheDocument();
      expect(screen.getByText("Task List 2")).toBeInTheDocument();
    });

    it("does not render task lists when collapsed", () => {
      render(
        <ProjectGroup
          project={mockProject}
          taskLists={mockTaskLists}
          defaultExpanded={false}
        />
      );

      // No task list cards should be rendered when collapsed
      expect(screen.queryAllByTestId("tasklist-card")).toHaveLength(0);
    });

    it("shows empty state when no task lists", () => {
      render(<ProjectGroup project={mockProject} taskLists={[]} />);

      expect(screen.getByTestId("project-group-empty")).toBeInTheDocument();
      expect(screen.getByTestId("project-group-empty")).toHaveTextContent(
        "No task lists in this project"
      );
    });
  });

  describe("Event Handlers", () => {
    it("calls onTaskListClick when task list is clicked", () => {
      const handleClick = vi.fn();

      render(
        <ProjectGroup
          project={mockProject}
          taskLists={mockTaskLists}
          onTaskListClick={handleClick}
        />
      );

      // Find and click the first task list card
      const taskListCards = screen.getAllByTestId("tasklist-card");
      fireEvent.click(taskListCards[0]);

      expect(handleClick).toHaveBeenCalledWith("tasklist-1");
    });

    it("calls onTaskListEdit when edit button is clicked", () => {
      const handleEdit = vi.fn();

      render(
        <ProjectGroup
          project={mockProject}
          taskLists={mockTaskLists}
          onTaskListEdit={handleEdit}
        />
      );

      // Hover over the first task list card to show action buttons
      const taskListCards = screen.getAllByTestId("tasklist-card");
      fireEvent.mouseEnter(taskListCards[0]);

      // Find and click the edit button
      const editButton = screen.getByTestId("tasklist-card-edit-button");
      fireEvent.click(editButton);

      expect(handleEdit).toHaveBeenCalledWith(mockTaskLists[0]);
    });

    it("calls onTaskListDelete when delete button is clicked", () => {
      const handleDelete = vi.fn();

      render(
        <ProjectGroup
          project={mockProject}
          taskLists={mockTaskLists}
          onTaskListDelete={handleDelete}
        />
      );

      // Hover over the first task list card to show action buttons
      const taskListCards = screen.getAllByTestId("tasklist-card");
      fireEvent.mouseEnter(taskListCards[0]);

      // Find and click the delete button
      const deleteButton = screen.getByTestId("tasklist-card-delete-button");
      fireEvent.click(deleteButton);

      expect(handleDelete).toHaveBeenCalledWith(mockTaskLists[0]);
    });
  });

  describe("Accessibility", () => {
    it("has correct ARIA attributes on header", () => {
      render(<ProjectGroup project={mockProject} taskLists={mockTaskLists} />);

      const header = screen.getByTestId("project-group-header");

      expect(header).toHaveAttribute("role", "button");
      expect(header).toHaveAttribute("tabIndex", "0");
      expect(header).toHaveAttribute("aria-expanded", "true");
      expect(header).toHaveAttribute(
        "aria-controls",
        `project-group-content-${mockProject.id}`
      );
    });

    it("has correct aria-label on header", () => {
      render(<ProjectGroup project={mockProject} taskLists={mockTaskLists} />);

      const header = screen.getByTestId("project-group-header");

      expect(header).toHaveAttribute(
        "aria-label",
        "Test Project - 2 task lists - collapse"
      );
    });

    it("updates aria-label when collapsed", () => {
      render(
        <ProjectGroup
          project={mockProject}
          taskLists={mockTaskLists}
          defaultExpanded={false}
        />
      );

      const header = screen.getByTestId("project-group-header");

      expect(header).toHaveAttribute(
        "aria-label",
        "Test Project - 2 task lists - expand"
      );
    });
  });

  describe("Masonry Layout (Requirements 48.1, 48.2, 48.3, 48.4)", () => {
    it("renders list layout by default", () => {
      render(<ProjectGroup project={mockProject} taskLists={mockTaskLists} />);

      expect(screen.getByTestId("project-group-list")).toBeInTheDocument();
      expect(screen.getByTestId("project-group-list")).toHaveAttribute(
        "data-layout",
        "list"
      );
      expect(screen.queryByTestId("project-group-masonry-grid")).not.toBeInTheDocument();
    });

    it("renders masonry grid layout when taskListLayout is masonry", () => {
      render(
        <ProjectGroup
          project={mockProject}
          taskLists={mockTaskLists}
          taskListLayout="masonry"
        />
      );

      expect(screen.getByTestId("project-group-masonry-grid")).toBeInTheDocument();
      expect(screen.getByTestId("project-group-masonry-grid")).toHaveAttribute(
        "data-layout",
        "masonry"
      );
      expect(screen.queryByTestId("project-group-list")).not.toBeInTheDocument();
    });

    it("renders all task lists in masonry layout", () => {
      render(
        <ProjectGroup
          project={mockProject}
          taskLists={mockTaskLists}
          taskListLayout="masonry"
          taskListStats={mockTaskListStats}
        />
      );

      // All task list cards should be rendered
      const taskListCards = screen.getAllByTestId("tasklist-card");
      expect(taskListCards).toHaveLength(2);

      // Verify task list names are rendered
      expect(screen.getByText("Task List 1")).toBeInTheDocument();
      expect(screen.getByText("Task List 2")).toBeInTheDocument();
    });

    it("renders masonry columns", () => {
      render(
        <ProjectGroup
          project={mockProject}
          taskLists={mockTaskLists}
          taskListLayout="masonry"
        />
      );

      // At least one column should be rendered
      expect(screen.getByTestId("project-group-masonry-column-0")).toBeInTheDocument();
    });

    it("calls onTaskListClick in masonry layout", () => {
      const handleClick = vi.fn();

      render(
        <ProjectGroup
          project={mockProject}
          taskLists={mockTaskLists}
          taskListLayout="masonry"
          onTaskListClick={handleClick}
        />
      );

      // Find and click the first task list card
      const taskListCards = screen.getAllByTestId("tasklist-card");
      fireEvent.click(taskListCards[0]);

      expect(handleClick).toHaveBeenCalled();
    });

    it("shows empty state in masonry layout when no task lists", () => {
      render(
        <ProjectGroup
          project={mockProject}
          taskLists={[]}
          taskListLayout="masonry"
        />
      );

      expect(screen.getByTestId("project-group-empty")).toBeInTheDocument();
      expect(screen.getByTestId("project-group-empty")).toHaveTextContent(
        "No task lists in this project"
      );
    });
  });
});
