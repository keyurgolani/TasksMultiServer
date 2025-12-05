import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { AppHeader } from "./AppHeader";

describe("AppHeader", () => {
  describe("Rendering", () => {
    it("renders with default props", () => {
      render(<AppHeader />);
      
      expect(screen.getByTestId("app-header")).toBeInTheDocument();
      expect(screen.getByTestId("app-header-branding")).toBeInTheDocument();
    });

    it("renders with custom title", () => {
      render(<AppHeader title="My App" />);
      
      expect(screen.getByTestId("app-header-title")).toHaveTextContent("My App");
    });

    it("renders logo icon when showLogo is true and logoVariant includes icon", () => {
      render(<AppHeader showLogo={true} logoVariant="icon" />);
      
      expect(screen.getByTestId("app-header-logo-icon")).toBeInTheDocument();
      expect(screen.queryByTestId("app-header-title")).not.toBeInTheDocument();
    });

    it("renders logo text when showLogo is true and logoVariant includes text", () => {
      render(<AppHeader showLogo={true} logoVariant="text" />);
      
      expect(screen.queryByTestId("app-header-logo-icon")).not.toBeInTheDocument();
      expect(screen.getByTestId("app-header-title")).toBeInTheDocument();
    });

    it("renders both icon and text when logoVariant is 'both'", () => {
      render(<AppHeader showLogo={true} logoVariant="both" />);
      
      expect(screen.getByTestId("app-header-logo-icon")).toBeInTheDocument();
      expect(screen.getByTestId("app-header-title")).toBeInTheDocument();
    });

    it("does not render logo when showLogo is false", () => {
      render(<AppHeader showLogo={false} />);
      
      expect(screen.queryByTestId("app-header-logo-icon")).not.toBeInTheDocument();
      expect(screen.queryByTestId("app-header-title")).not.toBeInTheDocument();
    });

    it("renders children content", () => {
      render(
        <AppHeader>
          <button>Action</button>
        </AppHeader>
      );
      
      expect(screen.getByTestId("app-header-content")).toBeInTheDocument();
      expect(screen.getByRole("button", { name: "Action" })).toBeInTheDocument();
    });

    it("does not render content container when no children", () => {
      render(<AppHeader />);
      
      expect(screen.queryByTestId("app-header-content")).not.toBeInTheDocument();
    });
  });

  describe("Accessibility", () => {
    it("has banner role", () => {
      render(<AppHeader />);
      
      expect(screen.getByRole("banner")).toBeInTheDocument();
    });

    it("has aria-label for accessibility", () => {
      render(<AppHeader />);
      
      expect(screen.getByLabelText("Application header")).toBeInTheDocument();
    });
  });

  describe("Styling", () => {
    it("applies glassmorphism classes", () => {
      render(<AppHeader />);
      
      const header = screen.getByTestId("app-header");
      expect(header).toHaveClass("bg-[var(--glass-bg)]");
      expect(header).toHaveClass("backdrop-blur-[var(--glass-blur)]");
    });

    it("applies sticky positioning by default", () => {
      render(<AppHeader />);
      
      const header = screen.getByTestId("app-header");
      expect(header).toHaveClass("sticky");
      expect(header).toHaveClass("top-0");
    });

    it("does not apply sticky positioning when sticky is false", () => {
      render(<AppHeader sticky={false} />);
      
      const header = screen.getByTestId("app-header");
      expect(header).not.toHaveClass("sticky");
    });

    it("applies custom className", () => {
      render(<AppHeader className="custom-class" />);
      
      const header = screen.getByTestId("app-header");
      expect(header).toHaveClass("custom-class");
    });
  });

  describe("Logo Variants", () => {
    it("uses custom logoText when provided", () => {
      render(<AppHeader title="App Title" logoText="Custom Logo" />);
      
      expect(screen.getByTestId("app-header-title")).toHaveTextContent("Custom Logo");
    });

    it("falls back to title when logoText is not provided", () => {
      render(<AppHeader title="App Title" />);
      
      expect(screen.getByTestId("app-header-title")).toHaveTextContent("App Title");
    });
  });
});
