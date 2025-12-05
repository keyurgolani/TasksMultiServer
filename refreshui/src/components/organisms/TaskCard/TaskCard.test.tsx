import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { TaskCard } from "./TaskCard";
import type { Task, TaskStatus, TaskPriority, ExitCriterion } from "../../../core/types/entities";
import type { StatusType } from "../../molecules/StatusIndicator";
import type { BadgeVariant } from "../../atoms/Badge";

// Helper functions copied from TaskCard for testing
const mapTaskStatusToIndicator = (status: TaskStatus): StatusType => {
  const statusMap: Record<TaskStatus, StatusType> = {
    NOT_STARTED: "not_started",
    IN_PROGRESS: "in_progress",
    COMPLETED: "completed",
    BLOCKED: "blocked",
  };
  return statusMap[status];
};

const mapPriorityToVariant = (priority: TaskPriority): BadgeVariant => {
  const priorityMap: Record<TaskPriority, BadgeVariant> = {
    CRITICAL: "error",
    HIGH: "warning",
    MEDIUM: "info",
    LOW: "neutral",
    TRIVIAL: "neutral",
  };
  return priorityMap[priority];
};

const formatPriority = (priority: TaskPriority): string => {
  return priority.charAt(0) + priority.slice(1).toLowerCase();
};

const formatStatus = (status: TaskStatus): string => {
  return status.replace(/_/g, " ").toLowerCase().replace(/\b\w/g, (c) => c.toUpperCase());
};

const calculateExitCriteriaProgress = (
  exitCriteria: ExitCriterion[]
): { completed: number; total: number; percentage: number } => {
  if (!exitCriteria || exitCriteria.length === 0) {
    return { completed: 0, total: 0, percentage: 0 };
  }
  const completed = exitCriteria.filter((ec) => ec.status === "COMPLETE").length;
  const total = exitCriteria.length;
  const percentage = Math.round((completed / total) * 100);
  return { completed, total, percentage };
};

/**
 * TaskCard Organism Tests
 *
 * Tests for the TaskCard component ensuring it correctly displays
 * task information with status, priority, and progress.
 *
 * Requirements: 5.1
 */

// Helper to create a mock task
const createMockTask = (overrides: Partial<Task> = {}): Task => ({
  id: "task-1",
  taskListId: "list-1",
  title: "Test Task Title",
  description: "Test task description",
  status: "NOT_STARTED",
  priority: "MEDIUM",
  dependencies: [],
  exitCriteria: [],
  notes: [],
  researchNotes: [],
  executionNotes: [],
  tags: [],
  createdAt: "2024-01-01T00:00:00Z",
  updatedAt: "2024-01-01T00:00:00Z",
  ...overrides,
});

describe("TaskCard", () => {
  describe("rendering", () => {
    it("renders task title", () => {
      const task = createMockTask({ title: "My Important Task" });
      render(<TaskCard task={task} />);
      expect(screen.getByTestId("task-card-title")).toHaveTextContent("My Important Task");
    });

    it("renders task description when present", () => {
      const task = createMockTask({ description: "This is a description" });
      render(<TaskCard task={task} />);
      expect(screen.getByTestId("task-card-description")).toHaveTextContent("This is a description");
    });

    it("does not render description when absent", () => {
      const task = createMockTask({ description: undefined });
      render(<TaskCard task={task} />);
      expect(screen.queryByTestId("task-card-description")).not.toBeInTheDocument();
    });

    it("renders status indicator", () => {
      const task = createMockTask({ status: "IN_PROGRESS" });
      render(<TaskCard task={task} />);
      expect(screen.getByRole("status")).toBeInTheDocument();
    });

    it("renders priority badge", () => {
      const task = createMockTask({ priority: "HIGH" });
      render(<TaskCard task={task} />);
      expect(screen.getByText("High")).toBeInTheDocument();
    });

    it("renders exit criteria progress when present", () => {
      const task = createMockTask({
        exitCriteria: [
          { criteria: "Criterion 1", status: "COMPLETE" },
          { criteria: "Criterion 2", status: "INCOMPLETE" },
        ],
      });
      render(<TaskCard task={task} />);
      expect(screen.getByTestId("task-card-progress")).toBeInTheDocument();
      expect(screen.getByText("1/2")).toBeInTheDocument();
    });

    it("does not render exit criteria progress when empty", () => {
      const task = createMockTask({ exitCriteria: [] });
      render(<TaskCard task={task} />);
      expect(screen.queryByTestId("task-card-progress")).not.toBeInTheDocument();
    });

    it("renders tags when present", () => {
      const task = createMockTask({ tags: ["tag1", "tag2"] });
      render(<TaskCard task={task} />);
      expect(screen.getByTestId("task-card-tags")).toBeInTheDocument();
      expect(screen.getByText("tag1")).toBeInTheDocument();
      expect(screen.getByText("tag2")).toBeInTheDocument();
    });

    it("limits displayed tags to 3 with overflow indicator", () => {
      const task = createMockTask({ tags: ["tag1", "tag2", "tag3", "tag4", "tag5"] });
      render(<TaskCard task={task} />);
      expect(screen.getByText("tag1")).toBeInTheDocument();
      expect(screen.getByText("tag2")).toBeInTheDocument();
      expect(screen.getByText("tag3")).toBeInTheDocument();
      expect(screen.queryByText("tag4")).not.toBeInTheDocument();
      expect(screen.getByText("+2")).toBeInTheDocument();
    });

    it("renders dependencies indicator when present", () => {
      const task = createMockTask({
        dependencies: [{ taskId: "dep-1", taskListId: "list-1" }],
      });
      render(<TaskCard task={task} />);
      expect(screen.getByTestId("task-card-dependencies")).toBeInTheDocument();
      expect(screen.getByText("1 dependency")).toBeInTheDocument();
    });

    it("renders notes indicator when notes present", () => {
      const task = createMockTask({
        notes: [{ content: "Note 1", timestamp: "2024-01-01T00:00:00Z" }],
      });
      render(<TaskCard task={task} />);
      expect(screen.getByTestId("task-card-notes")).toBeInTheDocument();
      expect(screen.getByText("1 notes")).toBeInTheDocument();
    });
  });

  describe("interactions", () => {
    it("calls onClick when clicked", () => {
      const handleClick = vi.fn();
      const task = createMockTask();
      render(<TaskCard task={task} onClick={handleClick} />);
      fireEvent.click(screen.getByTestId("task-card"));
      expect(handleClick).toHaveBeenCalledTimes(1);
    });
  });

  describe("accessibility", () => {
    it("has correct aria-label", () => {
      const task = createMockTask({ title: "Accessible Task" });
      render(<TaskCard task={task} />);
      expect(screen.getByRole("article")).toHaveAttribute(
        "aria-label",
        "Task: Accessible Task"
      );
    });

    it("progress bar has correct aria attributes", () => {
      const task = createMockTask({
        exitCriteria: [
          { criteria: "Criterion 1", status: "COMPLETE" },
          { criteria: "Criterion 2", status: "INCOMPLETE" },
        ],
      });
      render(<TaskCard task={task} />);
      const progressBar = screen.getByRole("progressbar");
      expect(progressBar).toHaveAttribute("aria-valuenow", "50");
      expect(progressBar).toHaveAttribute("aria-valuemin", "0");
      expect(progressBar).toHaveAttribute("aria-valuemax", "100");
    });
  });
});

describe("helper functions", () => {
  describe("mapTaskStatusToIndicator", () => {
    it("maps NOT_STARTED to not_started", () => {
      expect(mapTaskStatusToIndicator("NOT_STARTED")).toBe("not_started");
    });

    it("maps IN_PROGRESS to in_progress", () => {
      expect(mapTaskStatusToIndicator("IN_PROGRESS")).toBe("in_progress");
    });

    it("maps COMPLETED to completed", () => {
      expect(mapTaskStatusToIndicator("COMPLETED")).toBe("completed");
    });

    it("maps BLOCKED to blocked", () => {
      expect(mapTaskStatusToIndicator("BLOCKED")).toBe("blocked");
    });
  });

  describe("mapPriorityToVariant", () => {
    it("maps CRITICAL to error", () => {
      expect(mapPriorityToVariant("CRITICAL")).toBe("error");
    });

    it("maps HIGH to warning", () => {
      expect(mapPriorityToVariant("HIGH")).toBe("warning");
    });

    it("maps MEDIUM to info", () => {
      expect(mapPriorityToVariant("MEDIUM")).toBe("info");
    });

    it("maps LOW to neutral", () => {
      expect(mapPriorityToVariant("LOW")).toBe("neutral");
    });

    it("maps TRIVIAL to neutral", () => {
      expect(mapPriorityToVariant("TRIVIAL")).toBe("neutral");
    });
  });

  describe("formatPriority", () => {
    it("formats CRITICAL as Critical", () => {
      expect(formatPriority("CRITICAL")).toBe("Critical");
    });

    it("formats HIGH as High", () => {
      expect(formatPriority("HIGH")).toBe("High");
    });

    it("formats MEDIUM as Medium", () => {
      expect(formatPriority("MEDIUM")).toBe("Medium");
    });
  });

  describe("formatStatus", () => {
    it("formats NOT_STARTED as Not Started", () => {
      expect(formatStatus("NOT_STARTED")).toBe("Not Started");
    });

    it("formats IN_PROGRESS as In Progress", () => {
      expect(formatStatus("IN_PROGRESS")).toBe("In Progress");
    });

    it("formats COMPLETED as Completed", () => {
      expect(formatStatus("COMPLETED")).toBe("Completed");
    });

    it("formats BLOCKED as Blocked", () => {
      expect(formatStatus("BLOCKED")).toBe("Blocked");
    });
  });

  describe("calculateExitCriteriaProgress", () => {
    it("returns zeros for empty array", () => {
      const result = calculateExitCriteriaProgress([]);
      expect(result).toEqual({ completed: 0, total: 0, percentage: 0 });
    });

    it("calculates correct progress", () => {
      const exitCriteria = [
        { criteria: "A", status: "COMPLETE" as const },
        { criteria: "B", status: "INCOMPLETE" as const },
        { criteria: "C", status: "COMPLETE" as const },
        { criteria: "D", status: "INCOMPLETE" as const },
      ];
      const result = calculateExitCriteriaProgress(exitCriteria);
      expect(result).toEqual({ completed: 2, total: 4, percentage: 50 });
    });

    it("handles all complete", () => {
      const exitCriteria = [
        { criteria: "A", status: "COMPLETE" as const },
        { criteria: "B", status: "COMPLETE" as const },
      ];
      const result = calculateExitCriteriaProgress(exitCriteria);
      expect(result).toEqual({ completed: 2, total: 2, percentage: 100 });
    });

    it("handles none complete", () => {
      const exitCriteria = [
        { criteria: "A", status: "INCOMPLETE" as const },
        { criteria: "B", status: "INCOMPLETE" as const },
      ];
      const result = calculateExitCriteriaProgress(exitCriteria);
      expect(result).toEqual({ completed: 0, total: 2, percentage: 0 });
    });
  });
});
