import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { ViewSelector, type ViewOption } from "./ViewSelector";

describe("ViewSelector", () => {
  const mockOnViewChange = vi.fn();

  beforeEach(() => {
    mockOnViewChange.mockClear();
  });

  describe("Rendering", () => {
    it("renders all default view options", () => {
      render(
        <ViewSelector
          currentView="dashboard"
          onViewChange={mockOnViewChange}
        />
      );

      expect(screen.getByTestId("view-selector")).toBeInTheDocument();
      expect(screen.getByTestId("view-selector-option-dashboard")).toBeInTheDocument();
      expect(screen.getByTestId("view-selector-option-projects")).toBeInTheDocument();
      expect(screen.getByTestId("view-selector-option-taskLists")).toBeInTheDocument();
      expect(screen.getByTestId("view-selector-option-tasks")).toBeInTheDocument();
    });

    it("renders custom view options when provided", () => {
      const customViews: ViewOption[] = [
        { id: "projects", label: "My Projects", icon: "Folder" },
        { id: "tasks", label: "My Tasks", icon: "CheckSquare" },
      ];

      render(
        <ViewSelector
          currentView="projects"
          onViewChange={mockOnViewChange}
          views={customViews}
        />
      );

      expect(screen.getByText("My Projects")).toBeInTheDocument();
      expect(screen.getByText("My Tasks")).toBeInTheDocument();
      expect(screen.queryByText("Dashboard")).not.toBeInTheDocument();
    });

    it("renders labels when showLabels is true", () => {
      render(
        <ViewSelector
          currentView="dashboard"
          onViewChange={mockOnViewChange}
          showLabels={true}
        />
      );

      expect(screen.getByText("Dashboard")).toBeInTheDocument();
      expect(screen.getByText("Projects")).toBeInTheDocument();
    });

    it("hides labels when showLabels is false", () => {
      render(
        <ViewSelector
          currentView="dashboard"
          onViewChange={mockOnViewChange}
          showLabels={false}
        />
      );

      expect(screen.queryByText("Dashboard")).not.toBeInTheDocument();
      expect(screen.queryByText("Projects")).not.toBeInTheDocument();
    });
  });

  describe("Active State Highlighting (Property 30)", () => {
    it("highlights the current view option", () => {
      render(
        <ViewSelector
          currentView="projects"
          onViewChange={mockOnViewChange}
        />
      );

      const projectsButton = screen.getByTestId("view-selector-option-projects");
      const dashboardButton = screen.getByTestId("view-selector-option-dashboard");

      expect(projectsButton).toHaveAttribute("data-active", "true");
      expect(projectsButton).toHaveAttribute("aria-selected", "true");
      expect(dashboardButton).toHaveAttribute("data-active", "false");
      expect(dashboardButton).toHaveAttribute("aria-selected", "false");
    });

    it("updates active state when currentView changes", () => {
      const { rerender } = render(
        <ViewSelector
          currentView="dashboard"
          onViewChange={mockOnViewChange}
        />
      );

      expect(screen.getByTestId("view-selector-option-dashboard")).toHaveAttribute("data-active", "true");
      expect(screen.getByTestId("view-selector-option-tasks")).toHaveAttribute("data-active", "false");

      rerender(
        <ViewSelector
          currentView="tasks"
          onViewChange={mockOnViewChange}
        />
      );

      expect(screen.getByTestId("view-selector-option-dashboard")).toHaveAttribute("data-active", "false");
      expect(screen.getByTestId("view-selector-option-tasks")).toHaveAttribute("data-active", "true");
    });
  });

  describe("View Change Event (Property 31)", () => {
    it("emits onViewChange when clicking a different view", () => {
      render(
        <ViewSelector
          currentView="dashboard"
          onViewChange={mockOnViewChange}
        />
      );

      fireEvent.click(screen.getByTestId("view-selector-option-projects"));

      expect(mockOnViewChange).toHaveBeenCalledTimes(1);
      expect(mockOnViewChange).toHaveBeenCalledWith("projects");
    });

    it("does not emit onViewChange when clicking the current view", () => {
      render(
        <ViewSelector
          currentView="dashboard"
          onViewChange={mockOnViewChange}
        />
      );

      fireEvent.click(screen.getByTestId("view-selector-option-dashboard"));

      expect(mockOnViewChange).not.toHaveBeenCalled();
    });

    it("emits correct view ID for each option", () => {
      render(
        <ViewSelector
          currentView="dashboard"
          onViewChange={mockOnViewChange}
        />
      );

      fireEvent.click(screen.getByTestId("view-selector-option-projects"));
      expect(mockOnViewChange).toHaveBeenLastCalledWith("projects");

      fireEvent.click(screen.getByTestId("view-selector-option-taskLists"));
      expect(mockOnViewChange).toHaveBeenLastCalledWith("taskLists");

      fireEvent.click(screen.getByTestId("view-selector-option-tasks"));
      expect(mockOnViewChange).toHaveBeenLastCalledWith("tasks");
    });
  });

  describe("Accessibility", () => {
    it("has correct ARIA attributes", () => {
      render(
        <ViewSelector
          currentView="projects"
          onViewChange={mockOnViewChange}
        />
      );

      const container = screen.getByTestId("view-selector");
      expect(container).toHaveAttribute("role", "tablist");
      expect(container).toHaveAttribute("aria-label", "View selector");

      const buttons = screen.getAllByRole("tab");
      expect(buttons).toHaveLength(4);
    });

    it("sets correct tabIndex for keyboard navigation", () => {
      render(
        <ViewSelector
          currentView="projects"
          onViewChange={mockOnViewChange}
        />
      );

      const activeButton = screen.getByTestId("view-selector-option-projects");
      const inactiveButton = screen.getByTestId("view-selector-option-dashboard");

      expect(activeButton).toHaveAttribute("tabIndex", "0");
      expect(inactiveButton).toHaveAttribute("tabIndex", "-1");
    });
  });

  describe("Size Variants", () => {
    it("renders with small size", () => {
      render(
        <ViewSelector
          currentView="dashboard"
          onViewChange={mockOnViewChange}
          size="sm"
        />
      );

      expect(screen.getByTestId("view-selector")).toBeInTheDocument();
    });

    it("renders with medium size (default)", () => {
      render(
        <ViewSelector
          currentView="dashboard"
          onViewChange={mockOnViewChange}
          size="md"
        />
      );

      expect(screen.getByTestId("view-selector")).toBeInTheDocument();
    });

    it("renders with large size", () => {
      render(
        <ViewSelector
          currentView="dashboard"
          onViewChange={mockOnViewChange}
          size="lg"
        />
      );

      expect(screen.getByTestId("view-selector")).toBeInTheDocument();
    });
  });

  describe("Glass Effect", () => {
    it("applies glassmorphism by default", () => {
      render(
        <ViewSelector
          currentView="dashboard"
          onViewChange={mockOnViewChange}
        />
      );

      const container = screen.getByTestId("view-selector");
      expect(container.className).toContain("backdrop-blur");
    });

    it("does not apply glassmorphism when glass is false", () => {
      render(
        <ViewSelector
          currentView="dashboard"
          onViewChange={mockOnViewChange}
          glass={false}
        />
      );

      const container = screen.getByTestId("view-selector");
      expect(container.className).not.toContain("backdrop-blur");
    });
  });
});
