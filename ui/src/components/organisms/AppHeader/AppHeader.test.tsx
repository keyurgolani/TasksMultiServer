import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { ThemeProvider } from "../../../context/ThemeContext";
import { AppHeader } from "./AppHeader";

/**
 * Test wrapper that provides required contexts for AppHeader
 */
const TestWrapper: React.FC<{ children: React.ReactNode; initialRoute?: string }> = ({
  children,
  initialRoute = "/",
}) => (
  <MemoryRouter initialEntries={[initialRoute]}>
    <ThemeProvider>{children}</ThemeProvider>
  </MemoryRouter>
);

describe("AppHeader", () => {
  describe("Rendering", () => {
    it("renders with default props", () => {
      render(
        <TestWrapper>
          <AppHeader />
        </TestWrapper>
      );

      expect(screen.getByTestId("app-header")).toBeInTheDocument();
      expect(screen.getByTestId("app-header-branding")).toBeInTheDocument();
    });

    it("renders with custom title", () => {
      render(
        <TestWrapper>
          <AppHeader title="My App" />
        </TestWrapper>
      );

      expect(screen.getByTestId("app-header-title")).toHaveTextContent("My App");
    });

    it("renders logo icon when showLogo is true and logoVariant includes icon", () => {
      render(
        <TestWrapper>
          <AppHeader showLogo={true} logoVariant="icon" />
        </TestWrapper>
      );

      expect(screen.getByTestId("app-header-logo-icon")).toBeInTheDocument();
      expect(screen.queryByTestId("app-header-title")).not.toBeInTheDocument();
    });

    it("renders logo text when showLogo is true and logoVariant includes text", () => {
      render(
        <TestWrapper>
          <AppHeader showLogo={true} logoVariant="text" />
        </TestWrapper>
      );

      expect(screen.queryByTestId("app-header-logo-icon")).not.toBeInTheDocument();
      expect(screen.getByTestId("app-header-title")).toBeInTheDocument();
    });

    it("renders both icon and text when logoVariant is 'both'", () => {
      render(
        <TestWrapper>
          <AppHeader showLogo={true} logoVariant="both" />
        </TestWrapper>
      );

      expect(screen.getByTestId("app-header-logo-icon")).toBeInTheDocument();
      expect(screen.getByTestId("app-header-title")).toBeInTheDocument();
    });

    it("does not render logo when showLogo is false", () => {
      render(
        <TestWrapper>
          <AppHeader showLogo={false} />
        </TestWrapper>
      );

      expect(screen.queryByTestId("app-header-logo-icon")).not.toBeInTheDocument();
      expect(screen.queryByTestId("app-header-title")).not.toBeInTheDocument();
    });

    it("renders children content", () => {
      render(
        <TestWrapper>
          <AppHeader>
            <button>Action</button>
          </AppHeader>
        </TestWrapper>
      );

      expect(screen.getByTestId("app-header-content")).toBeInTheDocument();
      expect(screen.getByRole("button", { name: "Action" })).toBeInTheDocument();
    });

    it("does not render content container when no children", () => {
      render(
        <TestWrapper>
          <AppHeader />
        </TestWrapper>
      );

      expect(screen.queryByTestId("app-header-content")).not.toBeInTheDocument();
    });
  });

  describe("Navigation", () => {
    it("renders navigation links by default", () => {
      render(
        <TestWrapper>
          <AppHeader />
        </TestWrapper>
      );

      expect(screen.getByTestId("app-header-navigation")).toBeInTheDocument();
      expect(screen.getByTestId("app-header-nav-dashboard")).toBeInTheDocument();
      expect(screen.getByTestId("app-header-nav-projects")).toBeInTheDocument();
      expect(screen.getByTestId("app-header-nav-lists")).toBeInTheDocument();
      expect(screen.getByTestId("app-header-nav-tasks")).toBeInTheDocument();
    });

    it("does not render navigation when showNavigation is false", () => {
      render(
        <TestWrapper>
          <AppHeader showNavigation={false} />
        </TestWrapper>
      );

      expect(screen.queryByTestId("app-header-navigation")).not.toBeInTheDocument();
    });

    it("highlights Dashboard link when on root route", () => {
      render(
        <TestWrapper initialRoute="/">
          <AppHeader />
        </TestWrapper>
      );

      const dashboardLink = screen.getByTestId("app-header-nav-dashboard");
      expect(dashboardLink).toHaveAttribute("aria-current", "page");
      expect(dashboardLink).toHaveClass("bg-[var(--primary)]");
    });

    it("highlights Projects link when on /projects route", () => {
      render(
        <TestWrapper initialRoute="/projects">
          <AppHeader />
        </TestWrapper>
      );

      const projectsLink = screen.getByTestId("app-header-nav-projects");
      expect(projectsLink).toHaveAttribute("aria-current", "page");
      expect(projectsLink).toHaveClass("bg-[var(--primary)]");
    });

    it("highlights Lists link when on /lists route", () => {
      render(
        <TestWrapper initialRoute="/lists">
          <AppHeader />
        </TestWrapper>
      );

      const listsLink = screen.getByTestId("app-header-nav-lists");
      expect(listsLink).toHaveAttribute("aria-current", "page");
      expect(listsLink).toHaveClass("bg-[var(--primary)]");
    });

    it("highlights Tasks link when on /tasks route", () => {
      render(
        <TestWrapper initialRoute="/tasks">
          <AppHeader />
        </TestWrapper>
      );

      const tasksLink = screen.getByTestId("app-header-nav-tasks");
      expect(tasksLink).toHaveAttribute("aria-current", "page");
      expect(tasksLink).toHaveClass("bg-[var(--primary)]");
    });

    it("highlights Projects link when on nested project route", () => {
      render(
        <TestWrapper initialRoute="/projects/123">
          <AppHeader />
        </TestWrapper>
      );

      const projectsLink = screen.getByTestId("app-header-nav-projects");
      expect(projectsLink).toHaveAttribute("aria-current", "page");
    });
  });

  describe("Customization", () => {
    it("renders customization button by default", () => {
      render(
        <TestWrapper>
          <AppHeader />
        </TestWrapper>
      );

      expect(screen.getByTestId("customization-button")).toBeInTheDocument();
    });

    it("does not render customization button when showCustomization is false", () => {
      render(
        <TestWrapper>
          <AppHeader showCustomization={false} />
        </TestWrapper>
      );

      expect(screen.queryByTestId("customization-button")).not.toBeInTheDocument();
    });
  });

  describe("Accessibility", () => {
    it("has banner role", () => {
      render(
        <TestWrapper>
          <AppHeader />
        </TestWrapper>
      );

      expect(screen.getByRole("banner")).toBeInTheDocument();
    });

    it("has aria-label for accessibility", () => {
      render(
        <TestWrapper>
          <AppHeader />
        </TestWrapper>
      );

      expect(screen.getByLabelText("Application header")).toBeInTheDocument();
    });

    it("has navigation landmark with label", () => {
      render(
        <TestWrapper>
          <AppHeader />
        </TestWrapper>
      );

      expect(screen.getByRole("navigation", { name: "Main navigation" })).toBeInTheDocument();
    });
  });

  describe("Styling", () => {
    it("applies glassmorphism classes", () => {
      render(
        <TestWrapper>
          <AppHeader />
        </TestWrapper>
      );

      const header = screen.getByTestId("app-header");
      expect(header).toHaveClass("bg-[var(--glass-bg)]");
      expect(header).toHaveClass("backdrop-blur-[var(--glass-blur)]");
    });

    it("applies sticky positioning by default", () => {
      render(
        <TestWrapper>
          <AppHeader />
        </TestWrapper>
      );

      const header = screen.getByTestId("app-header");
      expect(header).toHaveClass("sticky");
      expect(header).toHaveClass("top-0");
    });

    it("does not apply sticky positioning when sticky is false", () => {
      render(
        <TestWrapper>
          <AppHeader sticky={false} />
        </TestWrapper>
      );

      const header = screen.getByTestId("app-header");
      expect(header).not.toHaveClass("sticky");
    });

    it("applies custom className", () => {
      render(
        <TestWrapper>
          <AppHeader className="custom-class" />
        </TestWrapper>
      );

      const header = screen.getByTestId("app-header");
      expect(header).toHaveClass("custom-class");
    });
  });

  describe("Logo Variants", () => {
    it("uses custom logoText when provided", () => {
      render(
        <TestWrapper>
          <AppHeader title="App Title" logoText="Custom Logo" />
        </TestWrapper>
      );

      expect(screen.getByTestId("app-header-title")).toHaveTextContent("Custom Logo");
    });

    it("falls back to title when logoText is not provided", () => {
      render(
        <TestWrapper>
          <AppHeader title="App Title" />
        </TestWrapper>
      );

      expect(screen.getByTestId("app-header-title")).toHaveTextContent("App Title");
    });
  });
});
