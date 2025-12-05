import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { FAB, type FABProps } from "./FAB";

/**
 * FAB Component Tests
 *
 * Tests for the Floating Action Button organism component.
 *
 * Requirements: 15.1, 15.2, 15.3
 * - 15.1: Display a floating button with a plus icon in the bottom-right corner
 * - 15.2: Expand to show action options (Create Project, Create Task List, Create Task)
 * - 15.3: Display labeled action buttons with appropriate icons when expanded
 */

describe("FAB", () => {
  const defaultProps: FABProps = {
    onAddProject: vi.fn(),
    onAddTaskList: vi.fn(),
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe("Requirement 15.1: Display floating button with plus icon", () => {
    it("renders the main FAB button", () => {
      render(<FAB {...defaultProps} />);

      const mainButton = screen.getByTestId("fab-main-button");
      expect(mainButton).toBeInTheDocument();
    });

    it("renders in collapsed state by default", () => {
      render(<FAB {...defaultProps} />);

      const actions = screen.queryByTestId("fab-actions");
      expect(actions).not.toBeInTheDocument();
    });

    it("has correct aria-label when collapsed", () => {
      render(<FAB {...defaultProps} />);

      const mainButton = screen.getByTestId("fab-main-button");
      expect(mainButton).toHaveAttribute("aria-label", "Open menu");
      expect(mainButton).toHaveAttribute("aria-expanded", "false");
    });
  });

  describe("Requirement 15.2: Expand to show action options", () => {
    it("expands when main button is clicked", async () => {
      render(<FAB {...defaultProps} />);

      const mainButton = screen.getByTestId("fab-main-button");
      fireEvent.click(mainButton);

      await waitFor(() => {
        const actions = screen.getByTestId("fab-actions");
        expect(actions).toBeInTheDocument();
      });
    });

    it("collapses when main button is clicked again", async () => {
      render(<FAB {...defaultProps} />);

      const mainButton = screen.getByTestId("fab-main-button");

      // Expand
      fireEvent.click(mainButton);
      await waitFor(() => {
        expect(screen.getByTestId("fab-actions")).toBeInTheDocument();
      });

      // Collapse
      fireEvent.click(mainButton);
      await waitFor(() => {
        expect(screen.queryByTestId("fab-actions")).not.toBeInTheDocument();
      });
    });

    it("updates aria-expanded when expanded", async () => {
      render(<FAB {...defaultProps} />);

      const mainButton = screen.getByTestId("fab-main-button");
      fireEvent.click(mainButton);

      await waitFor(() => {
        expect(mainButton).toHaveAttribute("aria-expanded", "true");
        expect(mainButton).toHaveAttribute("aria-label", "Close menu");
      });
    });

    it("shows backdrop when expanded", async () => {
      render(<FAB {...defaultProps} />);

      const mainButton = screen.getByTestId("fab-main-button");
      fireEvent.click(mainButton);

      await waitFor(() => {
        const backdrop = screen.getByTestId("fab-backdrop");
        expect(backdrop).toBeInTheDocument();
      });
    });

    it("shows project and task list action buttons when expanded", async () => {
      render(<FAB {...defaultProps} />);

      const mainButton = screen.getByTestId("fab-main-button");
      fireEvent.click(mainButton);

      await waitFor(() => {
        expect(screen.getByTestId("fab-action-project")).toBeInTheDocument();
        expect(screen.getByTestId("fab-action-taskList")).toBeInTheDocument();
      });
    });

    it("shows task action button when showTaskButton is true and onAddTask is provided", async () => {
      const onAddTask = vi.fn();
      render(<FAB {...defaultProps} onAddTask={onAddTask} showTaskButton={true} />);

      const mainButton = screen.getByTestId("fab-main-button");
      fireEvent.click(mainButton);

      await waitFor(() => {
        expect(screen.getByTestId("fab-action-task")).toBeInTheDocument();
      });
    });

    it("does not show task action button when showTaskButton is false", async () => {
      const onAddTask = vi.fn();
      render(<FAB {...defaultProps} onAddTask={onAddTask} showTaskButton={false} />);

      const mainButton = screen.getByTestId("fab-main-button");
      fireEvent.click(mainButton);

      await waitFor(() => {
        expect(screen.queryByTestId("fab-action-task")).not.toBeInTheDocument();
      });
    });
  });

  describe("Requirement 15.3: Display labeled action buttons with icons", () => {
    it("displays 'New Project' label on project action button", async () => {
      render(<FAB {...defaultProps} />);

      const mainButton = screen.getByTestId("fab-main-button");
      fireEvent.click(mainButton);

      await waitFor(() => {
        const projectButton = screen.getByTestId("fab-action-project");
        expect(projectButton).toHaveTextContent("New Project");
      });
    });

    it("displays 'New Task List' label on task list action button", async () => {
      render(<FAB {...defaultProps} />);

      const mainButton = screen.getByTestId("fab-main-button");
      fireEvent.click(mainButton);

      await waitFor(() => {
        const taskListButton = screen.getByTestId("fab-action-taskList");
        expect(taskListButton).toHaveTextContent("New Task List");
      });
    });

    it("displays 'New Task' label on task action button when shown", async () => {
      const onAddTask = vi.fn();
      render(<FAB {...defaultProps} onAddTask={onAddTask} showTaskButton={true} />);

      const mainButton = screen.getByTestId("fab-main-button");
      fireEvent.click(mainButton);

      await waitFor(() => {
        const taskButton = screen.getByTestId("fab-action-task");
        expect(taskButton).toHaveTextContent("New Task");
      });
    });

    it("calls onAddProject when project action is clicked", async () => {
      const onAddProject = vi.fn();
      render(<FAB {...defaultProps} onAddProject={onAddProject} />);

      const mainButton = screen.getByTestId("fab-main-button");
      fireEvent.click(mainButton);

      await waitFor(() => {
        const projectButton = screen.getByTestId("fab-action-project");
        fireEvent.click(projectButton);
      });

      expect(onAddProject).toHaveBeenCalledTimes(1);
    });

    it("calls onAddTaskList when task list action is clicked", async () => {
      const onAddTaskList = vi.fn();
      render(<FAB {...defaultProps} onAddTaskList={onAddTaskList} />);

      const mainButton = screen.getByTestId("fab-main-button");
      fireEvent.click(mainButton);

      await waitFor(() => {
        const taskListButton = screen.getByTestId("fab-action-taskList");
        fireEvent.click(taskListButton);
      });

      expect(onAddTaskList).toHaveBeenCalledTimes(1);
    });

    it("calls onAddTask when task action is clicked", async () => {
      const onAddTask = vi.fn();
      render(<FAB {...defaultProps} onAddTask={onAddTask} showTaskButton={true} />);

      const mainButton = screen.getByTestId("fab-main-button");
      fireEvent.click(mainButton);

      await waitFor(() => {
        const taskButton = screen.getByTestId("fab-action-task");
        fireEvent.click(taskButton);
      });

      expect(onAddTask).toHaveBeenCalledTimes(1);
    });

    it("collapses after action is clicked", async () => {
      render(<FAB {...defaultProps} />);

      const mainButton = screen.getByTestId("fab-main-button");
      fireEvent.click(mainButton);

      await waitFor(() => {
        const projectButton = screen.getByTestId("fab-action-project");
        fireEvent.click(projectButton);
      });

      await waitFor(() => {
        expect(screen.queryByTestId("fab-actions")).not.toBeInTheDocument();
      });
    });
  });

  describe("Requirement 15.4: Outside click detection to collapse FAB", () => {
    it("collapses when clicking outside the FAB container", async () => {
      render(
        <div>
          <div data-testid="outside-element">Outside Element</div>
          <FAB {...defaultProps} />
        </div>
      );

      const mainButton = screen.getByTestId("fab-main-button");
      
      // Expand the FAB
      fireEvent.click(mainButton);
      await waitFor(() => {
        expect(screen.getByTestId("fab-actions")).toBeInTheDocument();
      });

      // Click outside the FAB container
      const outsideElement = screen.getByTestId("outside-element");
      fireEvent.mouseDown(outsideElement);

      await waitFor(() => {
        expect(screen.queryByTestId("fab-actions")).not.toBeInTheDocument();
      });
    });

    it("collapses when clicking on the backdrop", async () => {
      render(<FAB {...defaultProps} />);

      const mainButton = screen.getByTestId("fab-main-button");
      
      // Expand the FAB
      fireEvent.click(mainButton);
      await waitFor(() => {
        expect(screen.getByTestId("fab-backdrop")).toBeInTheDocument();
      });

      // Click on the backdrop
      const backdrop = screen.getByTestId("fab-backdrop");
      fireEvent.click(backdrop);

      // Wait for the animation to complete and elements to be removed
      await waitFor(
        () => {
          expect(screen.queryByTestId("fab-actions")).not.toBeInTheDocument();
          expect(screen.queryByTestId("fab-backdrop")).not.toBeInTheDocument();
        },
        { timeout: 2000 }
      );
    });

    it("does not collapse when clicking inside the FAB container", async () => {
      render(<FAB {...defaultProps} />);

      const mainButton = screen.getByTestId("fab-main-button");
      
      // Expand the FAB
      fireEvent.click(mainButton);
      await waitFor(() => {
        expect(screen.getByTestId("fab-actions")).toBeInTheDocument();
      });

      // Click inside the FAB container (on the container itself)
      const fabContainer = screen.getByTestId("fab-container");
      fireEvent.mouseDown(fabContainer);

      // Should still be expanded
      expect(screen.getByTestId("fab-actions")).toBeInTheDocument();
    });

    it("removes event listener when FAB is collapsed", async () => {
      const removeEventListenerSpy = vi.spyOn(document, "removeEventListener");
      
      render(<FAB {...defaultProps} />);

      const mainButton = screen.getByTestId("fab-main-button");
      
      // Expand the FAB
      fireEvent.click(mainButton);
      await waitFor(() => {
        expect(screen.getByTestId("fab-actions")).toBeInTheDocument();
      });

      // Collapse the FAB
      fireEvent.click(mainButton);
      await waitFor(() => {
        expect(screen.queryByTestId("fab-actions")).not.toBeInTheDocument();
      });

      // Verify cleanup was called
      expect(removeEventListenerSpy).toHaveBeenCalledWith(
        "mousedown",
        expect.any(Function)
      );

      removeEventListenerSpy.mockRestore();
    });
  });

  describe("Disabled state", () => {
    it("does not expand when disabled", () => {
      render(<FAB {...defaultProps} disabled={true} />);

      const mainButton = screen.getByTestId("fab-main-button");
      fireEvent.click(mainButton);

      expect(screen.queryByTestId("fab-actions")).not.toBeInTheDocument();
    });

    it("has disabled attribute when disabled", () => {
      render(<FAB {...defaultProps} disabled={true} />);

      const mainButton = screen.getByTestId("fab-main-button");
      expect(mainButton).toBeDisabled();
    });
  });
});
