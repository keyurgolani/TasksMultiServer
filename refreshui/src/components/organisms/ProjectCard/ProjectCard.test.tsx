import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { ProjectCard } from "./ProjectCard";
import type { Project } from "../../../core/types/entities";
import type { ProjectStats } from "../../../services/types";

// Helper functions copied from ProjectCard for testing
const calculateCompletionPercentage = (stats?: ProjectStats): number => {
  if (!stats || stats.totalTasks === 0) {
    return 0;
  }
  return Math.round((stats.completedTasks / stats.totalTasks) * 100);
};

const getProgressColor = (percentage: number): string => {
  if (percentage >= 100) return "var(--success)";
  if (percentage >= 75) return "var(--info)";
  if (percentage >= 50) return "var(--warning)";
  return "var(--primary)";
};

/**
 * ProjectCard Organism Tests
 *
 * Tests for the ProjectCard component ensuring it correctly displays
 * project information with task list count and completion statistics.
 *
 * Requirements: 5.2
 */

// Helper to create a mock project
const createMockProject = (overrides: Partial<Project> = {}): Project => ({
  id: "project-1",
  name: "Test Project",
  description: "Test project description",
  createdAt: "2024-01-01T00:00:00Z",
  updatedAt: "2024-01-01T00:00:00Z",
  ...overrides,
});

// Helper to create mock project stats
const createMockStats = (overrides: Partial<ProjectStats> = {}): ProjectStats => ({
  taskListCount: 3,
  totalTasks: 10,
  readyTasks: 2,
  completedTasks: 5,
  inProgressTasks: 2,
  blockedTasks: 1,
  ...overrides,
});

describe("ProjectCard", () => {
  describe("rendering", () => {
    it("renders project name", () => {
      const project = createMockProject({ name: "My Important Project" });
      render(<ProjectCard project={project} />);
      expect(screen.getByTestId("project-card-name")).toHaveTextContent(
        "My Important Project"
      );
    });

    it("renders project description when present", () => {
      const project = createMockProject({ description: "This is a description" });
      render(<ProjectCard project={project} />);
      expect(screen.getByTestId("project-card-description")).toHaveTextContent(
        "This is a description"
      );
    });

    it("does not render description when absent", () => {
      const project = createMockProject({ description: undefined });
      render(<ProjectCard project={project} />);
      expect(screen.queryByTestId("project-card-description")).not.toBeInTheDocument();
    });

    it("renders task list count when stats provided", () => {
      const project = createMockProject();
      const stats = createMockStats({ taskListCount: 5 });
      render(<ProjectCard project={project} stats={stats} />);
      expect(screen.getByTestId("project-card-tasklist-count")).toHaveTextContent("5");
    });

    it("renders total tasks when stats provided", () => {
      const project = createMockProject();
      const stats = createMockStats({ totalTasks: 15 });
      render(<ProjectCard project={project} stats={stats} />);
      expect(screen.getByTestId("project-card-total-tasks")).toHaveTextContent("15");
    });

    it("renders OverallProgress organism with completion stats", () => {
      const project = createMockProject();
      const stats = createMockStats({ completedTasks: 5, totalTasks: 10 });
      render(<ProjectCard project={project} stats={stats} />);
      // OverallProgress organism is now used instead of separate elements
      expect(screen.getByTestId("overall-progress")).toBeInTheDocument();
    });

    it("renders progress bar via OverallProgress", () => {
      const project = createMockProject();
      const stats = createMockStats();
      render(<ProjectCard project={project} stats={stats} />);
      // Progress bar is now rendered via OverallProgress organism
      expect(screen.getByTestId("overall-progress-bar")).toBeInTheDocument();
    });

    it("renders status breakdown via OverallProgress", () => {
      const project = createMockProject();
      const stats = createMockStats({
        inProgressTasks: 3,
        blockedTasks: 2,
        readyTasks: 4,
      });
      render(<ProjectCard project={project} stats={stats} />);
      // Status breakdown is now rendered via OverallProgress organism
      // The OverallProgress compact variant shows status indicators
      expect(screen.getByTestId("overall-progress")).toBeInTheDocument();
    });

    it("renders no stats message when stats not provided", () => {
      const project = createMockProject();
      render(<ProjectCard project={project} />);
      expect(screen.getByTestId("project-card-no-stats")).toBeInTheDocument();
      expect(screen.getByText("No task data available")).toBeInTheDocument();
    });
  });

  describe("interactions", () => {
    it("calls onClick when clicked", () => {
      const handleClick = vi.fn();
      const project = createMockProject();
      render(<ProjectCard project={project} onClick={handleClick} />);
      fireEvent.click(screen.getByTestId("project-card"));
      expect(handleClick).toHaveBeenCalledTimes(1);
    });
  });

  /**
   * Tests for edit/delete action buttons on hover
   * Requirements: 23.1
   * Property 47: Card Action Buttons Visibility
   */
  describe("action buttons", () => {
    it("does not show action buttons when not hovered", () => {
      const project = createMockProject();
      render(
        <ProjectCard
          project={project}
          onEdit={vi.fn()}
          onDelete={vi.fn()}
        />
      );
      expect(screen.queryByTestId("project-card-actions")).not.toBeInTheDocument();
    });

    it("shows action buttons on hover when handlers provided", () => {
      const project = createMockProject();
      render(
        <ProjectCard
          project={project}
          onEdit={vi.fn()}
          onDelete={vi.fn()}
        />
      );
      fireEvent.mouseEnter(screen.getByTestId("project-card"));
      expect(screen.getByTestId("project-card-actions")).toBeInTheDocument();
      expect(screen.getByTestId("project-card-edit-button")).toBeInTheDocument();
      expect(screen.getByTestId("project-card-delete-button")).toBeInTheDocument();
    });

    it("hides action buttons on mouse leave", () => {
      const project = createMockProject();
      render(
        <ProjectCard
          project={project}
          onEdit={vi.fn()}
          onDelete={vi.fn()}
        />
      );
      fireEvent.mouseEnter(screen.getByTestId("project-card"));
      expect(screen.getByTestId("project-card-actions")).toBeInTheDocument();
      fireEvent.mouseLeave(screen.getByTestId("project-card"));
      expect(screen.queryByTestId("project-card-actions")).not.toBeInTheDocument();
    });

    it("only shows edit button when only onEdit provided", () => {
      const project = createMockProject();
      render(<ProjectCard project={project} onEdit={vi.fn()} />);
      fireEvent.mouseEnter(screen.getByTestId("project-card"));
      expect(screen.getByTestId("project-card-edit-button")).toBeInTheDocument();
      expect(screen.queryByTestId("project-card-delete-button")).not.toBeInTheDocument();
    });

    it("only shows delete button when only onDelete provided", () => {
      const project = createMockProject();
      render(<ProjectCard project={project} onDelete={vi.fn()} />);
      fireEvent.mouseEnter(screen.getByTestId("project-card"));
      expect(screen.queryByTestId("project-card-edit-button")).not.toBeInTheDocument();
      expect(screen.getByTestId("project-card-delete-button")).toBeInTheDocument();
    });

    it("calls onEdit with project when edit button clicked", () => {
      const handleEdit = vi.fn();
      const project = createMockProject({ id: "test-project-id" });
      render(<ProjectCard project={project} onEdit={handleEdit} />);
      fireEvent.mouseEnter(screen.getByTestId("project-card"));
      fireEvent.click(screen.getByTestId("project-card-edit-button"));
      expect(handleEdit).toHaveBeenCalledTimes(1);
      expect(handleEdit).toHaveBeenCalledWith(project);
    });

    it("calls onDelete with project when delete button clicked", () => {
      const handleDelete = vi.fn();
      const project = createMockProject({ id: "test-project-id" });
      render(<ProjectCard project={project} onDelete={handleDelete} />);
      fireEvent.mouseEnter(screen.getByTestId("project-card"));
      fireEvent.click(screen.getByTestId("project-card-delete-button"));
      expect(handleDelete).toHaveBeenCalledTimes(1);
      expect(handleDelete).toHaveBeenCalledWith(project);
    });

    it("does not trigger onClick when edit button clicked", () => {
      const handleClick = vi.fn();
      const handleEdit = vi.fn();
      const project = createMockProject();
      render(
        <ProjectCard
          project={project}
          onClick={handleClick}
          onEdit={handleEdit}
        />
      );
      fireEvent.mouseEnter(screen.getByTestId("project-card"));
      fireEvent.click(screen.getByTestId("project-card-edit-button"));
      expect(handleEdit).toHaveBeenCalledTimes(1);
      expect(handleClick).not.toHaveBeenCalled();
    });

    it("does not trigger onClick when delete button clicked", () => {
      const handleClick = vi.fn();
      const handleDelete = vi.fn();
      const project = createMockProject();
      render(
        <ProjectCard
          project={project}
          onClick={handleClick}
          onDelete={handleDelete}
        />
      );
      fireEvent.mouseEnter(screen.getByTestId("project-card"));
      fireEvent.click(screen.getByTestId("project-card-delete-button"));
      expect(handleDelete).toHaveBeenCalledTimes(1);
      expect(handleClick).not.toHaveBeenCalled();
    });

    it("edit button has correct aria-label", () => {
      const project = createMockProject({ name: "My Project" });
      render(<ProjectCard project={project} onEdit={vi.fn()} />);
      fireEvent.mouseEnter(screen.getByTestId("project-card"));
      expect(screen.getByTestId("project-card-edit-button")).toHaveAttribute(
        "aria-label",
        "Edit project: My Project"
      );
    });

    it("delete button has correct aria-label", () => {
      const project = createMockProject({ name: "My Project" });
      render(<ProjectCard project={project} onDelete={vi.fn()} />);
      fireEvent.mouseEnter(screen.getByTestId("project-card"));
      expect(screen.getByTestId("project-card-delete-button")).toHaveAttribute(
        "aria-label",
        "Delete project: My Project"
      );
    });
  });

  describe("accessibility", () => {
    it("has correct aria-label", () => {
      const project = createMockProject({ name: "Accessible Project" });
      render(<ProjectCard project={project} />);
      expect(screen.getByRole("article")).toHaveAttribute(
        "aria-label",
        "Project: Accessible Project"
      );
    });

    it("progress bar has correct aria attributes", () => {
      const project = createMockProject();
      const stats = createMockStats({ completedTasks: 5, totalTasks: 10 });
      render(<ProjectCard project={project} stats={stats} />);
      const progressBar = screen.getByRole("progressbar");
      expect(progressBar).toHaveAttribute("aria-valuenow", "50");
      expect(progressBar).toHaveAttribute("aria-valuemin", "0");
      expect(progressBar).toHaveAttribute("aria-valuemax", "100");
    });
  });
});

describe("helper functions", () => {
  describe("calculateCompletionPercentage", () => {
    it("returns 0 when stats is undefined", () => {
      expect(calculateCompletionPercentage(undefined)).toBe(0);
    });

    it("returns 0 when totalTasks is 0", () => {
      const stats = createMockStats({ totalTasks: 0, completedTasks: 0 });
      expect(calculateCompletionPercentage(stats)).toBe(0);
    });

    it("calculates correct percentage", () => {
      const stats = createMockStats({ totalTasks: 10, completedTasks: 5 });
      expect(calculateCompletionPercentage(stats)).toBe(50);
    });

    it("rounds percentage to nearest integer", () => {
      const stats = createMockStats({ totalTasks: 3, completedTasks: 1 });
      expect(calculateCompletionPercentage(stats)).toBe(33);
    });

    it("returns 100 when all tasks completed", () => {
      const stats = createMockStats({ totalTasks: 10, completedTasks: 10 });
      expect(calculateCompletionPercentage(stats)).toBe(100);
    });
  });

  describe("getProgressColor", () => {
    it("returns success color for 100%", () => {
      expect(getProgressColor(100)).toBe("var(--success)");
    });

    it("returns info color for 75-99%", () => {
      expect(getProgressColor(75)).toBe("var(--info)");
      expect(getProgressColor(99)).toBe("var(--info)");
    });

    it("returns warning color for 50-74%", () => {
      expect(getProgressColor(50)).toBe("var(--warning)");
      expect(getProgressColor(74)).toBe("var(--warning)");
    });

    it("returns primary color for below 50%", () => {
      expect(getProgressColor(0)).toBe("var(--primary)");
      expect(getProgressColor(49)).toBe("var(--primary)");
    });
  });
});
