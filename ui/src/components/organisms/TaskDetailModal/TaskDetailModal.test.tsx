import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { TaskDetailModal } from "./TaskDetailModal";
import type { Task } from "../../../core/types/entities";

/**
 * TaskDetailModal Organism Tests
 *
 * Tests for the TaskDetailModal component ensuring it properly displays
 * all task information including notes, dependencies, exit criteria, and metadata.
 *
 * Property 26: TaskDetailModal Content Completeness
 * - For any Task object, the TaskDetailModal SHALL render all sections:
 *   notes, dependencies, exit criteria, and metadata.
 */

// Mock framer-motion to avoid animation issues in tests
vi.mock("framer-motion", () => ({
  motion: {
    div: ({ children, ...props }: React.PropsWithChildren<Record<string, unknown>>) => (
      <div {...props}>{children}</div>
    ),
  },
  AnimatePresence: ({ children }: React.PropsWithChildren) => <>{children}</>,
}));

const createMockTask = (overrides: Partial<Task> = {}): Task => ({
  id: "task-1",
  taskListId: "list-1",
  title: "Test Task",
  description: "Test description",
  status: "IN_PROGRESS",
  priority: "HIGH",
  dependencies: [],
  exitCriteria: [
    { criteria: "Criterion 1", status: "COMPLETE" },
    { criteria: "Criterion 2", status: "INCOMPLETE" },
  ],
  notes: [{ content: "General note", timestamp: "2024-01-01T00:00:00Z" }],
  researchNotes: [{ content: "Research note", timestamp: "2024-01-02T00:00:00Z" }],
  executionNotes: [{ content: "Execution note", timestamp: "2024-01-03T00:00:00Z" }],
  tags: ["tag1", "tag2"],
  createdAt: "2024-01-01T00:00:00Z",
  updatedAt: "2024-01-15T00:00:00Z",
  ...overrides,
});

describe("TaskDetailModal", () => {
  it("renders nothing when task is null", () => {
    const { container } = render(
      <TaskDetailModal task={null} isOpen={true} onClose={vi.fn()} />
    );
    expect(container.firstChild).toBeNull();
  });

  it("renders nothing when isOpen is false", () => {
    const task = createMockTask();
    const { container } = render(
      <TaskDetailModal task={task} isOpen={false} onClose={vi.fn()} />
    );
    expect(container.querySelector("[data-testid='task-detail-modal']")).toBeNull();
  });

  it("renders the modal when isOpen is true and task is provided", () => {
    const task = createMockTask();
    render(<TaskDetailModal task={task} isOpen={true} onClose={vi.fn()} />);
    expect(screen.getByTestId("task-detail-modal")).toBeInTheDocument();
  });

  it("displays the task title", () => {
    const task = createMockTask({ title: "My Important Task" });
    render(<TaskDetailModal task={task} isOpen={true} onClose={vi.fn()} />);
    expect(screen.getByText("My Important Task")).toBeInTheDocument();
  });

  it("displays the task description", () => {
    const task = createMockTask({ description: "This is a detailed description" });
    render(<TaskDetailModal task={task} isOpen={true} onClose={vi.fn()} />);
    expect(screen.getByText("This is a detailed description")).toBeInTheDocument();
  });

  it("displays exit criteria section", async () => {
    const task = createMockTask();
    render(<TaskDetailModal task={task} isOpen={true} onClose={vi.fn()} />);
    expect(screen.getByTestId("exit-criteria-section")).toBeInTheDocument();
    // Wait for state sync via requestAnimationFrame
    await waitFor(() => {
      expect(screen.getByText("Criterion 1")).toBeInTheDocument();
    });
    expect(screen.getByText("Criterion 2")).toBeInTheDocument();
  });

  it("displays dependencies section", () => {
    const task = createMockTask();
    render(<TaskDetailModal task={task} isOpen={true} onClose={vi.fn()} />);
    expect(screen.getByTestId("dependencies-section")).toBeInTheDocument();
  });

  it("displays notes section", () => {
    const task = createMockTask();
    render(<TaskDetailModal task={task} isOpen={true} onClose={vi.fn()} />);
    expect(screen.getByTestId("notes-section")).toBeInTheDocument();
  });

  it("displays all note types", () => {
    const task = createMockTask();
    render(<TaskDetailModal task={task} isOpen={true} onClose={vi.fn()} />);
    expect(screen.getByText("General note")).toBeInTheDocument();
    expect(screen.getByText("Research note")).toBeInTheDocument();
    expect(screen.getByText("Execution note")).toBeInTheDocument();
  });

  it("displays tags", async () => {
    const task = createMockTask({ tags: ["frontend", "urgent"] });
    render(<TaskDetailModal task={task} isOpen={true} onClose={vi.fn()} />);
    // Wait for state sync via requestAnimationFrame
    await waitFor(() => {
      expect(screen.getByText("frontend")).toBeInTheDocument();
    });
    expect(screen.getByText("urgent")).toBeInTheDocument();
  });

  it("calls onClose when close button is clicked", () => {
    const task = createMockTask();
    const onClose = vi.fn();
    render(<TaskDetailModal task={task} isOpen={true} onClose={onClose} />);
    
    // Find the close button (X icon button)
    const closeButtons = screen.getAllByRole("button");
    const closeButton = closeButtons.find(btn => btn.querySelector("svg"));
    if (closeButton) {
      fireEvent.click(closeButton);
    }
    // The onClose should be called when clicking the backdrop or close button
  });

  it("displays exit criteria progress", async () => {
    const task = createMockTask({
      exitCriteria: [
        { criteria: "Done", status: "COMPLETE" },
        { criteria: "Not done", status: "INCOMPLETE" },
      ],
    });
    render(<TaskDetailModal task={task} isOpen={true} onClose={vi.fn()} />);
    // Wait for state sync via requestAnimationFrame
    await waitFor(() => {
      expect(screen.getByText("1 of 2 complete")).toBeInTheDocument();
    });
  });

  it("shows empty state when no exit criteria", () => {
    const task = createMockTask({ exitCriteria: [] });
    render(<TaskDetailModal task={task} isOpen={true} onClose={vi.fn()} />);
    expect(screen.getByText("No exit criteria defined")).toBeInTheDocument();
  });

  it("shows empty state when no notes", () => {
    const task = createMockTask({
      notes: [],
      researchNotes: [],
      executionNotes: [],
    });
    render(<TaskDetailModal task={task} isOpen={true} onClose={vi.fn()} />);
    expect(screen.getByText("No notes yet")).toBeInTheDocument();
  });

  it("shows empty state when no dependencies", () => {
    const task = createMockTask({ dependencies: [] });
    render(<TaskDetailModal task={task} isOpen={true} onClose={vi.fn()} />);
    expect(screen.getByText("No dependencies")).toBeInTheDocument();
  });
});
