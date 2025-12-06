import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { CreateTaskListModal } from "./CreateTaskListModal";
import { DataServiceProvider } from "../../../context/DataServiceContext";
import type { IDataService, Project } from "../../../services/types";

/**
 * CreateTaskListModal Tests
 *
 * Tests for the CreateTaskListModal organism component.
 * Validates form rendering, validation, and submission behavior.
 *
 * Requirements: 17.1, 17.2
 */

// Mock projects data
const mockProjects: Project[] = [
  {
    id: "project-1",
    name: "Project Alpha",
    description: "First project",
    createdAt: "2024-01-01T00:00:00Z",
    updatedAt: "2024-01-01T00:00:00Z",
  },
  {
    id: "project-2",
    name: "Project Beta",
    description: "Second project",
    createdAt: "2024-01-02T00:00:00Z",
    updatedAt: "2024-01-02T00:00:00Z",
  },
];

// Mock data service
const createMockDataService = (): IDataService => ({
  getProjects: vi.fn().mockResolvedValue(mockProjects),
  getProject: vi.fn().mockResolvedValue({ id: "1", name: "Test" }),
  createProject: vi.fn().mockResolvedValue({ id: "new-1", name: "New Project" }),
  updateProject: vi.fn().mockResolvedValue({}),
  deleteProject: vi.fn().mockResolvedValue(undefined),
  getProjectStats: vi.fn().mockResolvedValue({}),
  getTaskLists: vi.fn().mockResolvedValue([]),
  getTaskList: vi.fn().mockResolvedValue({}),
  createTaskList: vi.fn().mockResolvedValue({ id: "new-tl-1", name: "New Task List" }),
  updateTaskList: vi.fn().mockResolvedValue({}),
  deleteTaskList: vi.fn().mockResolvedValue(undefined),
  getTaskListStats: vi.fn().mockResolvedValue({}),
  getTasks: vi.fn().mockResolvedValue([]),
  getTask: vi.fn().mockResolvedValue({}),
  createTask: vi.fn().mockResolvedValue({}),
  updateTask: vi.fn().mockResolvedValue({}),
  deleteTask: vi.fn().mockResolvedValue(undefined),
  addNote: vi.fn().mockResolvedValue({}),
  addResearchNote: vi.fn().mockResolvedValue({}),
  addExecutionNote: vi.fn().mockResolvedValue({}),
  searchTasks: vi.fn().mockResolvedValue({ items: [], total: 0, count: 0, offset: 0 }),
  getReadyTasks: vi.fn().mockResolvedValue([]),
});

// Helper to render with provider
const renderWithProvider = (
  ui: React.ReactElement,
  mockService?: IDataService
) => {
  const service = mockService || createMockDataService();
  return {
    ...render(
      <DataServiceProvider service={service}>{ui}</DataServiceProvider>
    ),
    mockService: service,
  };
};

describe("CreateTaskListModal", () => {
  const defaultProps = {
    isOpen: true,
    onClose: vi.fn(),
    onSuccess: vi.fn(),
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe("Rendering", () => {
    it("renders when isOpen is true", async () => {
      renderWithProvider(<CreateTaskListModal {...defaultProps} />);
      expect(screen.getByTestId("create-task-list-modal")).toBeInTheDocument();
      expect(screen.getByRole("heading", { name: "Create Task List" })).toBeInTheDocument();
    });

    it("does not render when isOpen is false", () => {
      renderWithProvider(<CreateTaskListModal {...defaultProps} isOpen={false} />);
      expect(screen.queryByTestId("create-task-list-modal")).not.toBeInTheDocument();
    });

    it("renders form inputs", async () => {
      renderWithProvider(<CreateTaskListModal {...defaultProps} />);
      expect(screen.getByPlaceholderText(/enter task list name/i)).toBeInTheDocument();
      expect(screen.getByPlaceholderText(/enter task list description/i)).toBeInTheDocument();
    });

    it("renders project selection list", async () => {
      renderWithProvider(<CreateTaskListModal {...defaultProps} />);
      await waitFor(() => {
        // The component uses a searchable list pattern with radio items
        expect(screen.getByPlaceholderText(/search or type new project name/i)).toBeInTheDocument();
      });
    });

    it("renders action buttons", () => {
      renderWithProvider(<CreateTaskListModal {...defaultProps} />);
      expect(screen.getByRole("button", { name: /cancel/i })).toBeInTheDocument();
      expect(screen.getByRole("button", { name: /create task list/i })).toBeInTheDocument();
    });

    it("loads and displays projects in list", async () => {
      renderWithProvider(<CreateTaskListModal {...defaultProps} />);
      await waitFor(() => {
        // Projects are displayed as radio items in a searchable list
        expect(screen.getByRole("radio", { name: /Project Alpha/i })).toBeInTheDocument();
        expect(screen.getByRole("radio", { name: /Project Beta/i })).toBeInTheDocument();
      });
    });
  });

  describe("Form Validation", () => {
    it("shows error when submitting with empty name", async () => {
      renderWithProvider(<CreateTaskListModal {...defaultProps} />);
      
      // Wait for projects to load
      await waitFor(() => {
        expect(screen.getByRole("radio", { name: /Project Alpha/i })).toBeInTheDocument();
      });
      
      const submitButton = screen.getByRole("button", { name: /create task list/i });
      fireEvent.click(submitButton);
      
      await waitFor(() => {
        expect(screen.getByText(/task list name is required/i)).toBeInTheDocument();
      });
    });

    it("shows error when submitting with whitespace-only name", async () => {
      renderWithProvider(<CreateTaskListModal {...defaultProps} />);
      
      await waitFor(() => {
        expect(screen.getByRole("radio", { name: /Project Alpha/i })).toBeInTheDocument();
      });
      
      const nameInput = screen.getByPlaceholderText(/enter task list name/i);
      fireEvent.change(nameInput, { target: { value: "   " } });
      
      const submitButton = screen.getByRole("button", { name: /create task list/i });
      fireEvent.click(submitButton);
      
      await waitFor(() => {
        expect(screen.getByText(/task list name is required/i)).toBeInTheDocument();
      });
    });

    it("shows error when no project is selected", async () => {
      const mockService = createMockDataService();
      mockService.getProjects = vi.fn().mockResolvedValue(mockProjects);
      
      renderWithProvider(<CreateTaskListModal {...defaultProps} />, mockService);
      
      await waitFor(() => {
        expect(screen.getByRole("radio", { name: /Project Alpha/i })).toBeInTheDocument();
      });
      
      // Clear the auto-selected project by clicking the remove button on the chip
      const removeButton = screen.getByRole("button", { name: "" });
      // Find the chip remove button (X icon in the chip)
      const chipRemoveButtons = document.querySelectorAll('[class*="chipRemove"]');
      if (chipRemoveButtons.length > 0) {
        fireEvent.click(chipRemoveButtons[0]);
      }
      
      const nameInput = screen.getByPlaceholderText(/enter task list name/i);
      fireEvent.change(nameInput, { target: { value: "My Task List" } });
      
      const submitButton = screen.getByRole("button", { name: /create task list/i });
      fireEvent.click(submitButton);
      
      await waitFor(() => {
        expect(screen.getByText(/please select a project/i)).toBeInTheDocument();
      });
    });

    it("clears error when user starts typing", async () => {
      renderWithProvider(<CreateTaskListModal {...defaultProps} />);
      
      await waitFor(() => {
        expect(screen.getByRole("radio", { name: /Project Alpha/i })).toBeInTheDocument();
      });
      
      const submitButton = screen.getByRole("button", { name: /create task list/i });
      fireEvent.click(submitButton);
      
      await waitFor(() => {
        expect(screen.getByText(/task list name is required/i)).toBeInTheDocument();
      });
      
      const nameInput = screen.getByPlaceholderText(/enter task list name/i);
      fireEvent.change(nameInput, { target: { value: "T" } });
      
      expect(screen.queryByText(/task list name is required/i)).not.toBeInTheDocument();
    });
  });

  describe("Form Submission", () => {
    it("calls createTaskList with correct data on valid submission", async () => {
      const mockService = createMockDataService();
      renderWithProvider(<CreateTaskListModal {...defaultProps} />, mockService);
      
      await waitFor(() => {
        expect(screen.getByRole("radio", { name: /Project Alpha/i })).toBeInTheDocument();
      });
      
      const nameInput = screen.getByPlaceholderText(/enter task list name/i);
      const descInput = screen.getByPlaceholderText(/enter task list description/i);
      
      fireEvent.change(nameInput, { target: { value: "My New Task List" } });
      fireEvent.change(descInput, { target: { value: "Task list description" } });
      
      // Select Project Beta by clicking on it
      const projectBetaRadio = screen.getByRole("radio", { name: /Project Beta/i });
      fireEvent.click(projectBetaRadio);
      
      const submitButton = screen.getByRole("button", { name: /create task list/i });
      fireEvent.click(submitButton);
      
      await waitFor(() => {
        expect(mockService.createTaskList).toHaveBeenCalledWith({
          name: "My New Task List",
          projectId: "project-2",
          description: "Task list description",
        });
      });
    });

    it("calls onSuccess and onClose after successful creation", async () => {
      const onSuccess = vi.fn();
      const onClose = vi.fn();
      renderWithProvider(
        <CreateTaskListModal {...defaultProps} onSuccess={onSuccess} onClose={onClose} />
      );
      
      await waitFor(() => {
        expect(screen.getByRole("radio", { name: /Project Alpha/i })).toBeInTheDocument();
      });
      
      const nameInput = screen.getByPlaceholderText(/enter task list name/i);
      fireEvent.change(nameInput, { target: { value: "Test Task List" } });
      
      const submitButton = screen.getByRole("button", { name: /create task list/i });
      fireEvent.click(submitButton);
      
      await waitFor(() => {
        expect(onSuccess).toHaveBeenCalled();
        expect(onClose).toHaveBeenCalled();
      });
    });

    it("shows error message when creation fails", async () => {
      const mockService = createMockDataService();
      mockService.createTaskList = vi.fn().mockRejectedValue(new Error("Network error"));
      renderWithProvider(<CreateTaskListModal {...defaultProps} />, mockService);
      
      await waitFor(() => {
        expect(screen.getByRole("radio", { name: /Project Alpha/i })).toBeInTheDocument();
      });
      
      const nameInput = screen.getByPlaceholderText(/enter task list name/i);
      fireEvent.change(nameInput, { target: { value: "Test Task List" } });
      
      const submitButton = screen.getByRole("button", { name: /create task list/i });
      fireEvent.click(submitButton);
      
      await waitFor(() => {
        expect(screen.getByText(/network error/i)).toBeInTheDocument();
      });
    });

    it("trims whitespace from name before submission", async () => {
      const mockService = createMockDataService();
      renderWithProvider(<CreateTaskListModal {...defaultProps} />, mockService);
      
      await waitFor(() => {
        expect(screen.getByRole("radio", { name: /Project Alpha/i })).toBeInTheDocument();
      });
      
      const nameInput = screen.getByPlaceholderText(/enter task list name/i);
      fireEvent.change(nameInput, { target: { value: "  Trimmed Name  " } });
      
      const submitButton = screen.getByRole("button", { name: /create task list/i });
      fireEvent.click(submitButton);
      
      await waitFor(() => {
        expect(mockService.createTaskList).toHaveBeenCalledWith({
          name: "Trimmed Name",
          projectId: "project-1",
          description: undefined,
        });
      });
    });
  });

  describe("Modal Behavior", () => {
    it("calls onClose when cancel button is clicked", () => {
      const onClose = vi.fn();
      renderWithProvider(<CreateTaskListModal {...defaultProps} onClose={onClose} />);
      const cancelButton = screen.getByRole("button", { name: /cancel/i });
      fireEvent.click(cancelButton);
      expect(onClose).toHaveBeenCalled();
    });

    it("calls onClose when close icon is clicked", () => {
      const onClose = vi.fn();
      renderWithProvider(<CreateTaskListModal {...defaultProps} onClose={onClose} />);
      const closeButton = screen.getByRole("button", { name: /close modal/i });
      fireEvent.click(closeButton);
      expect(onClose).toHaveBeenCalled();
    });

    it("calls onClose when Escape key is pressed", () => {
      const onClose = vi.fn();
      renderWithProvider(<CreateTaskListModal {...defaultProps} onClose={onClose} />);
      fireEvent.keyDown(document, { key: "Escape" });
      expect(onClose).toHaveBeenCalled();
    });

    it("calls onClose when clicking outside the modal (on backdrop)", () => {
      const onClose = vi.fn();
      renderWithProvider(<CreateTaskListModal {...defaultProps} onClose={onClose} />);
      const modalOverlay = screen.getByTestId("create-task-list-modal");
      const backdrop = modalOverlay.querySelector("div[class*='backdrop']");
      expect(backdrop).toBeInTheDocument();
      fireEvent.click(backdrop!);
      expect(onClose).toHaveBeenCalled();
    });

    it("does not close when clicking inside the modal content", () => {
      const onClose = vi.fn();
      renderWithProvider(<CreateTaskListModal {...defaultProps} onClose={onClose} />);
      const nameInput = screen.getByPlaceholderText(/enter task list name/i);
      fireEvent.click(nameInput);
      expect(onClose).not.toHaveBeenCalled();
    });
  });

  describe("Default Project Selection", () => {
    it("uses defaultProjectId when provided", async () => {
      renderWithProvider(
        <CreateTaskListModal {...defaultProps} defaultProjectId="project-2" />
      );
      
      await waitFor(() => {
        // The radio for Project Beta should be checked
        const projectBetaRadio = screen.getByRole("radio", { name: /Project Beta/i });
        expect(projectBetaRadio).toHaveAttribute("aria-checked", "true");
        // And Project Alpha should not be checked
        const projectAlphaRadio = screen.getByRole("radio", { name: /Project Alpha/i });
        expect(projectAlphaRadio).toHaveAttribute("aria-checked", "false");
      });
    });

    it("auto-selects first project when no defaultProjectId provided", async () => {
      renderWithProvider(<CreateTaskListModal {...defaultProps} />);
      
      await waitFor(() => {
        // The radio for Project Alpha should be checked (first project auto-selected)
        const projectAlphaRadio = screen.getByRole("radio", { name: /Project Alpha/i });
        expect(projectAlphaRadio).toHaveAttribute("aria-checked", "true");
        // And Project Beta should not be checked
        const projectBetaRadio = screen.getByRole("radio", { name: /Project Beta/i });
        expect(projectBetaRadio).toHaveAttribute("aria-checked", "false");
      });
    });
  });
});
