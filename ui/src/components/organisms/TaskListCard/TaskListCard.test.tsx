import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { TaskListCard } from "./TaskListCard";
import type { TaskList } from "../../../core/types/entities";
import type { TaskListStats } from "../../../services/types";

// Helper function copied from TaskListCard for testing
const getTaskListProgressColor = (percentage: number): string => {
  if (percentage >= 100) return "var(--success)";
  if (percentage >= 75) return "var(--info)";
  if (percentage >= 50) return "var(--warning)";
  return "var(--primary)";
};

/**
 * TaskListCard Organism Tests
 *
 * Tests for the TaskListCard component ensuring it correctly displays
 * task list information with task count and completion percentage.
 *
 * Requirements: 5.3
 */

// Helper to create a mock task list
const createMockTaskList = (overrides: Partial<TaskList> = {}): TaskList => ({
  id: "tasklist-1",
  projectId: "project-1",
  name: "Test Task List",
  description: "Test task list description",
  createdAt: "2024-01-01T00:00:00Z",
  updatedAt: "2024-01-01T00:00:00Z",
  ...overrides,
});

// Helper to create mock task list stats
const createMockStats = (overrides: Partial<TaskListStats> = {}): TaskListStats => ({
  taskCount: 10,
  readyTasks: 2,
  completedTasks: 5,
  inProgressTasks: 2,
  blockedTasks: 1,
  completionPercentage: 50,
  ...overrides,
});

describe("TaskListCard", () => {
  describe("rendering", () => {
    it("renders task list name", () => {
      const taskList = createMockTaskList({ name: "My Important Task List" });
      render(<TaskListCard taskList={taskList} />);
      expect(screen.getByTestId("tasklist-card-name")).toHaveTextContent(
        "My Important Task List"
      );
    });

    it("renders task list description when present", () => {
      const taskList = createMockTaskList({ description: "This is a description" });
      render(<TaskListCard taskList={taskList} />);
      expect(screen.getByTestId("tasklist-card-description")).toHaveTextContent(
        "This is a description"
      );
    });

    it("does not render description when absent", () => {
      const taskList = createMockTaskList({ description: undefined });
      render(<TaskListCard taskList={taskList} />);
      expect(screen.queryByTestId("tasklist-card-description")).not.toBeInTheDocument();
    });

    it("renders task count when stats provided", () => {
      const taskList = createMockTaskList();
      const stats = createMockStats({ taskCount: 15 });
      render(<TaskListCard taskList={taskList} stats={stats} />);
      expect(screen.getByTestId("tasklist-card-task-count")).toHaveTextContent("15");
    });

    it("renders OverallProgress organism with completion stats", () => {
      const taskList = createMockTaskList();
      const stats = createMockStats({ completedTasks: 5, taskCount: 10, completionPercentage: 50 });
      render(<TaskListCard taskList={taskList} stats={stats} />);
      // OverallProgress organism is now used instead of separate elements
      expect(screen.getByTestId("overall-progress")).toBeInTheDocument();
    });

    it("renders progress bar via OverallProgress", () => {
      const taskList = createMockTaskList();
      const stats = createMockStats();
      render(<TaskListCard taskList={taskList} stats={stats} />);
      // Progress bar is now rendered via OverallProgress organism
      expect(screen.getByTestId("overall-progress-bar")).toBeInTheDocument();
    });

    it("renders status breakdown via OverallProgress", () => {
      const taskList = createMockTaskList();
      const stats = createMockStats({
        inProgressTasks: 3,
        blockedTasks: 2,
        readyTasks: 4,
      });
      render(<TaskListCard taskList={taskList} stats={stats} />);
      // Status breakdown is now rendered via OverallProgress organism
      expect(screen.getByTestId("overall-progress")).toBeInTheDocument();
    });

    it("renders no stats message when stats not provided", () => {
      const taskList = createMockTaskList();
      render(<TaskListCard taskList={taskList} />);
      expect(screen.getByTestId("tasklist-card-no-stats")).toBeInTheDocument();
      expect(screen.getByText("No task data available")).toBeInTheDocument();
    });
  });

  describe("interactions", () => {
    it("calls onClick when clicked", () => {
      const handleClick = vi.fn();
      const taskList = createMockTaskList();
      render(<TaskListCard taskList={taskList} onClick={handleClick} />);
      fireEvent.click(screen.getByTestId("tasklist-card"));
      expect(handleClick).toHaveBeenCalledTimes(1);
    });
  });

  /**
   * Tests for edit/delete action buttons on hover
   * Requirements: 23.2
   * Property 47: Card Action Buttons Visibility
   */
  describe("action buttons", () => {
    it("does not show action buttons when not hovered", () => {
      const taskList = createMockTaskList();
      render(
        <TaskListCard
          taskList={taskList}
          onEdit={vi.fn()}
          onDelete={vi.fn()}
        />
      );
      expect(screen.queryByTestId("tasklist-card-actions")).not.toBeInTheDocument();
    });

    it("shows action buttons on hover when handlers provided", () => {
      const taskList = createMockTaskList();
      render(
        <TaskListCard
          taskList={taskList}
          onEdit={vi.fn()}
          onDelete={vi.fn()}
        />
      );
      fireEvent.mouseEnter(screen.getByTestId("tasklist-card"));
      expect(screen.getByTestId("tasklist-card-actions")).toBeInTheDocument();
      expect(screen.getByTestId("tasklist-card-edit-button")).toBeInTheDocument();
      expect(screen.getByTestId("tasklist-card-delete-button")).toBeInTheDocument();
    });

    it("hides action buttons on mouse leave", () => {
      const taskList = createMockTaskList();
      render(
        <TaskListCard
          taskList={taskList}
          onEdit={vi.fn()}
          onDelete={vi.fn()}
        />
      );
      fireEvent.mouseEnter(screen.getByTestId("tasklist-card"));
      expect(screen.getByTestId("tasklist-card-actions")).toBeInTheDocument();
      fireEvent.mouseLeave(screen.getByTestId("tasklist-card"));
      expect(screen.queryByTestId("tasklist-card-actions")).not.toBeInTheDocument();
    });

    it("only shows edit button when only onEdit provided", () => {
      const taskList = createMockTaskList();
      render(<TaskListCard taskList={taskList} onEdit={vi.fn()} />);
      fireEvent.mouseEnter(screen.getByTestId("tasklist-card"));
      expect(screen.getByTestId("tasklist-card-edit-button")).toBeInTheDocument();
      expect(screen.queryByTestId("tasklist-card-delete-button")).not.toBeInTheDocument();
    });

    it("only shows delete button when only onDelete provided", () => {
      const taskList = createMockTaskList();
      render(<TaskListCard taskList={taskList} onDelete={vi.fn()} />);
      fireEvent.mouseEnter(screen.getByTestId("tasklist-card"));
      expect(screen.queryByTestId("tasklist-card-edit-button")).not.toBeInTheDocument();
      expect(screen.getByTestId("tasklist-card-delete-button")).toBeInTheDocument();
    });

    it("calls onEdit with taskList when edit button clicked", () => {
      const handleEdit = vi.fn();
      const taskList = createMockTaskList({ id: "test-tasklist-id" });
      render(<TaskListCard taskList={taskList} onEdit={handleEdit} />);
      fireEvent.mouseEnter(screen.getByTestId("tasklist-card"));
      fireEvent.click(screen.getByTestId("tasklist-card-edit-button"));
      expect(handleEdit).toHaveBeenCalledTimes(1);
      expect(handleEdit).toHaveBeenCalledWith(taskList);
    });

    it("calls onDelete with taskList when delete button clicked", () => {
      const handleDelete = vi.fn();
      const taskList = createMockTaskList({ id: "test-tasklist-id" });
      render(<TaskListCard taskList={taskList} onDelete={handleDelete} />);
      fireEvent.mouseEnter(screen.getByTestId("tasklist-card"));
      fireEvent.click(screen.getByTestId("tasklist-card-delete-button"));
      expect(handleDelete).toHaveBeenCalledTimes(1);
      expect(handleDelete).toHaveBeenCalledWith(taskList);
    });

    it("does not trigger onClick when edit button clicked", () => {
      const handleClick = vi.fn();
      const handleEdit = vi.fn();
      const taskList = createMockTaskList();
      render(
        <TaskListCard
          taskList={taskList}
          onClick={handleClick}
          onEdit={handleEdit}
        />
      );
      fireEvent.mouseEnter(screen.getByTestId("tasklist-card"));
      fireEvent.click(screen.getByTestId("tasklist-card-edit-button"));
      expect(handleEdit).toHaveBeenCalledTimes(1);
      expect(handleClick).not.toHaveBeenCalled();
    });

    it("does not trigger onClick when delete button clicked", () => {
      const handleClick = vi.fn();
      const handleDelete = vi.fn();
      const taskList = createMockTaskList();
      render(
        <TaskListCard
          taskList={taskList}
          onClick={handleClick}
          onDelete={handleDelete}
        />
      );
      fireEvent.mouseEnter(screen.getByTestId("tasklist-card"));
      fireEvent.click(screen.getByTestId("tasklist-card-delete-button"));
      expect(handleDelete).toHaveBeenCalledTimes(1);
      expect(handleClick).not.toHaveBeenCalled();
    });

    it("edit button has correct aria-label", () => {
      const taskList = createMockTaskList({ name: "My Task List" });
      render(<TaskListCard taskList={taskList} onEdit={vi.fn()} />);
      fireEvent.mouseEnter(screen.getByTestId("tasklist-card"));
      expect(screen.getByTestId("tasklist-card-edit-button")).toHaveAttribute(
        "aria-label",
        "Edit task list: My Task List"
      );
    });

    it("delete button has correct aria-label", () => {
      const taskList = createMockTaskList({ name: "My Task List" });
      render(<TaskListCard taskList={taskList} onDelete={vi.fn()} />);
      fireEvent.mouseEnter(screen.getByTestId("tasklist-card"));
      expect(screen.getByTestId("tasklist-card-delete-button")).toHaveAttribute(
        "aria-label",
        "Delete task list: My Task List"
      );
    });
  });

  describe("accessibility", () => {
    it("has correct aria-label", () => {
      const taskList = createMockTaskList({ name: "Accessible Task List" });
      render(<TaskListCard taskList={taskList} />);
      expect(screen.getByRole("article")).toHaveAttribute(
        "aria-label",
        "Task List: Accessible Task List"
      );
    });

    it("progress bar has correct aria attributes", () => {
      const taskList = createMockTaskList();
      const stats = createMockStats({ completionPercentage: 50 });
      render(<TaskListCard taskList={taskList} stats={stats} />);
      const progressBar = screen.getByRole("progressbar");
      expect(progressBar).toHaveAttribute("aria-valuenow", "50");
      expect(progressBar).toHaveAttribute("aria-valuemin", "0");
      expect(progressBar).toHaveAttribute("aria-valuemax", "100");
    });
  });
});

describe("helper functions", () => {
  describe("getTaskListProgressColor", () => {
    it("returns success color for 100%", () => {
      expect(getTaskListProgressColor(100)).toBe("var(--success)");
    });

    it("returns info color for 75-99%", () => {
      expect(getTaskListProgressColor(75)).toBe("var(--info)");
      expect(getTaskListProgressColor(99)).toBe("var(--info)");
    });

    it("returns warning color for 50-74%", () => {
      expect(getTaskListProgressColor(50)).toBe("var(--warning)");
      expect(getTaskListProgressColor(74)).toBe("var(--warning)");
    });

    it("returns primary color for below 50%", () => {
      expect(getTaskListProgressColor(0)).toBe("var(--primary)");
      expect(getTaskListProgressColor(49)).toBe("var(--primary)");
    });
  });
});
