import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { CreateProjectModal } from "./CreateProjectModal";
import { DataServiceProvider } from "../../../context/DataServiceContext";
import type { IDataService } from "../../../services/types";

/**
 * CreateProjectModal Tests
 *
 * Tests for the CreateProjectModal organism component.
 * Validates form rendering, validation, and submission behavior.
 *
 * Requirements: 16.1, 16.2
 */

// Mock data service
const createMockDataService = (): IDataService => ({
  getProjects: vi.fn().mockResolvedValue([]),
  getProject: vi.fn().mockResolvedValue({ id: "1", name: "Test" }),
  createProject: vi.fn().mockResolvedValue({ id: "new-1", name: "New Project" }),
  updateProject: vi.fn().mockResolvedValue({}),
  deleteProject: vi.fn().mockResolvedValue(undefined),
  getProjectStats: vi.fn().mockResolvedValue({}),
  getTaskLists: vi.fn().mockResolvedValue([]),
  getTaskList: vi.fn().mockResolvedValue({}),
  createTaskList: vi.fn().mockResolvedValue({}),
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

describe("CreateProjectModal", () => {
  const defaultProps = {
    isOpen: true,
    onClose: vi.fn(),
    onSuccess: vi.fn(),
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe("Rendering", () => {
    it("renders when isOpen is true", () => {
      renderWithProvider(<CreateProjectModal {...defaultProps} />);
      expect(screen.getByTestId("create-project-modal")).toBeInTheDocument();
      // Check for the header title (h5 element)
      expect(screen.getByRole("heading", { name: "Create Project" })).toBeInTheDocument();
    });

    it("does not render when isOpen is false", () => {
      renderWithProvider(<CreateProjectModal {...defaultProps} isOpen={false} />);
      expect(screen.queryByTestId("create-project-modal")).not.toBeInTheDocument();
    });

    it("renders form inputs", () => {
      renderWithProvider(<CreateProjectModal {...defaultProps} />);
      expect(screen.getByPlaceholderText(/enter project name/i)).toBeInTheDocument();
      expect(screen.getByPlaceholderText(/enter project description/i)).toBeInTheDocument();
    });

    it("renders action buttons", () => {
      renderWithProvider(<CreateProjectModal {...defaultProps} />);
      expect(screen.getByRole("button", { name: /cancel/i })).toBeInTheDocument();
      expect(screen.getByRole("button", { name: /create project/i })).toBeInTheDocument();
    });
  });

  describe("Form Validation", () => {
    it("shows error when submitting with empty name", async () => {
      renderWithProvider(<CreateProjectModal {...defaultProps} />);
      const submitButton = screen.getByRole("button", { name: /create project/i });
      fireEvent.click(submitButton);
      await waitFor(() => {
        expect(screen.getByText(/project name is required/i)).toBeInTheDocument();
      });
    });

    it("shows error when submitting with whitespace-only name", async () => {
      renderWithProvider(<CreateProjectModal {...defaultProps} />);
      const nameInput = screen.getByPlaceholderText(/enter project name/i);
      fireEvent.change(nameInput, { target: { value: "   " } });
      const submitButton = screen.getByRole("button", { name: /create project/i });
      fireEvent.click(submitButton);
      await waitFor(() => {
        expect(screen.getByText(/project name is required/i)).toBeInTheDocument();
      });
    });

    it("clears error when user starts typing", async () => {
      renderWithProvider(<CreateProjectModal {...defaultProps} />);
      const submitButton = screen.getByRole("button", { name: /create project/i });
      fireEvent.click(submitButton);
      await waitFor(() => {
        expect(screen.getByText(/project name is required/i)).toBeInTheDocument();
      });
      const nameInput = screen.getByPlaceholderText(/enter project name/i);
      fireEvent.change(nameInput, { target: { value: "T" } });
      expect(screen.queryByText(/project name is required/i)).not.toBeInTheDocument();
    });
  });

  describe("Form Submission", () => {
    it("calls createProject with correct data on valid submission", async () => {
      const mockService = createMockDataService();
      renderWithProvider(<CreateProjectModal {...defaultProps} />, mockService);
      const nameInput = screen.getByPlaceholderText(/enter project name/i);
      const descInput = screen.getByPlaceholderText(/enter project description/i);
      fireEvent.change(nameInput, { target: { value: "My New Project" } });
      fireEvent.change(descInput, { target: { value: "Project description" } });
      const submitButton = screen.getByRole("button", { name: /create project/i });
      fireEvent.click(submitButton);
      await waitFor(() => {
        expect(mockService.createProject).toHaveBeenCalledWith({
          name: "My New Project",
          description: "Project description",
        });
      });
    });

    it("calls onSuccess and onClose after successful creation", async () => {
      const onSuccess = vi.fn();
      const onClose = vi.fn();
      renderWithProvider(
        <CreateProjectModal {...defaultProps} onSuccess={onSuccess} onClose={onClose} />
      );
      const nameInput = screen.getByPlaceholderText(/enter project name/i);
      fireEvent.change(nameInput, { target: { value: "Test Project" } });
      const submitButton = screen.getByRole("button", { name: /create project/i });
      fireEvent.click(submitButton);
      await waitFor(() => {
        expect(onSuccess).toHaveBeenCalled();
        expect(onClose).toHaveBeenCalled();
      });
    });

    it("shows error message when creation fails", async () => {
      const mockService = createMockDataService();
      mockService.createProject = vi.fn().mockRejectedValue(new Error("Network error"));
      renderWithProvider(<CreateProjectModal {...defaultProps} />, mockService);
      const nameInput = screen.getByPlaceholderText(/enter project name/i);
      fireEvent.change(nameInput, { target: { value: "Test Project" } });
      const submitButton = screen.getByRole("button", { name: /create project/i });
      fireEvent.click(submitButton);
      await waitFor(() => {
        expect(screen.getByText(/network error/i)).toBeInTheDocument();
      });
    });

    it("trims whitespace from name before submission", async () => {
      const mockService = createMockDataService();
      renderWithProvider(<CreateProjectModal {...defaultProps} />, mockService);
      const nameInput = screen.getByPlaceholderText(/enter project name/i);
      fireEvent.change(nameInput, { target: { value: "  Trimmed Name  " } });
      const submitButton = screen.getByRole("button", { name: /create project/i });
      fireEvent.click(submitButton);
      await waitFor(() => {
        expect(mockService.createProject).toHaveBeenCalledWith({
          name: "Trimmed Name",
          description: undefined,
        });
      });
    });
  });

  describe("Modal Behavior", () => {
    it("calls onClose when cancel button is clicked", () => {
      const onClose = vi.fn();
      renderWithProvider(<CreateProjectModal {...defaultProps} onClose={onClose} />);
      const cancelButton = screen.getByRole("button", { name: /cancel/i });
      fireEvent.click(cancelButton);
      expect(onClose).toHaveBeenCalled();
    });

    it("calls onClose when close icon is clicked", () => {
      const onClose = vi.fn();
      renderWithProvider(<CreateProjectModal {...defaultProps} onClose={onClose} />);
      const closeButton = screen.getByRole("button", { name: /close modal/i });
      fireEvent.click(closeButton);
      expect(onClose).toHaveBeenCalled();
    });

    it("calls onClose when Escape key is pressed", () => {
      const onClose = vi.fn();
      renderWithProvider(<CreateProjectModal {...defaultProps} onClose={onClose} />);
      fireEvent.keyDown(document, { key: "Escape" });
      expect(onClose).toHaveBeenCalled();
    });

    it("calls onClose when clicking outside the modal (on backdrop)", () => {
      const onClose = vi.fn();
      renderWithProvider(<CreateProjectModal {...defaultProps} onClose={onClose} />);
      // The backdrop is the element with the blur effect that covers the screen
      // It's a motion.div inside the modal overlay with backdrop-filter styling
      const modalOverlay = screen.getByTestId("create-project-modal");
      // The backdrop is the first child div with absolute positioning
      const backdrop = modalOverlay.querySelector("div[class*='backdrop']");
      expect(backdrop).toBeInTheDocument();
      fireEvent.click(backdrop!);
      expect(onClose).toHaveBeenCalled();
    });

    it("does not close when clicking inside the modal content", () => {
      const onClose = vi.fn();
      renderWithProvider(<CreateProjectModal {...defaultProps} onClose={onClose} />);
      // Click on the form content area
      const nameInput = screen.getByPlaceholderText(/enter project name/i);
      fireEvent.click(nameInput);
      expect(onClose).not.toHaveBeenCalled();
    });
  });
});
