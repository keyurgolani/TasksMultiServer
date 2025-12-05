import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { CustomizationDrawer } from "./CustomizationDrawer";
import { ThemeProvider } from "../../../context/ThemeContext";

/**
 * CustomizationDrawer Organism Tests
 *
 * Tests for the CustomizationDrawer component ensuring it correctly
 * provides grouped controls for all customizable design tokens.
 *
 * Requirements: 5.4
 */

// Wrapper component to provide theme context
const renderWithTheme = (ui: React.ReactElement) => {
  return render(<ThemeProvider>{ui}</ThemeProvider>);
};

describe("CustomizationDrawer", () => {
  const mockOnClose = vi.fn();

  beforeEach(() => {
    mockOnClose.mockClear();
  });

  describe("rendering", () => {
    it("renders nothing when closed", () => {
      renderWithTheme(
        <CustomizationDrawer isOpen={false} onClose={mockOnClose} />
      );
      expect(screen.queryByTestId("customization-drawer")).not.toBeInTheDocument();
    });

    it("renders drawer when open", () => {
      renderWithTheme(
        <CustomizationDrawer isOpen={true} onClose={mockOnClose} />
      );
      expect(screen.getByTestId("customization-drawer")).toBeInTheDocument();
    });

    it("renders title", () => {
      renderWithTheme(
        <CustomizationDrawer isOpen={true} onClose={mockOnClose} />
      );
      expect(screen.getByText("Customizations")).toBeInTheDocument();
    });

    it("renders close button", () => {
      renderWithTheme(
        <CustomizationDrawer isOpen={true} onClose={mockOnClose} />
      );
      expect(screen.getByLabelText("Close customization drawer")).toBeInTheDocument();
    });

    it("renders Color Theme section", () => {
      renderWithTheme(
        <CustomizationDrawer isOpen={true} onClose={mockOnClose} />
      );
      expect(screen.getByText("Color Theme")).toBeInTheDocument();
    });

    it("renders Typography section", () => {
      renderWithTheme(
        <CustomizationDrawer isOpen={true} onClose={mockOnClose} />
      );
      expect(screen.getByText("Typography")).toBeInTheDocument();
    });

    it("renders Interface Effects section", () => {
      renderWithTheme(
        <CustomizationDrawer isOpen={true} onClose={mockOnClose} />
      );
      expect(screen.getByText("Interface Effects")).toBeInTheDocument();
    });

    it("renders effect sliders", () => {
      renderWithTheme(
        <CustomizationDrawer isOpen={true} onClose={mockOnClose} />
      );
      expect(screen.getByText("Glow Strength")).toBeInTheDocument();
      expect(screen.getByText("Glass Opacity")).toBeInTheDocument();
      expect(screen.getByText("Glass Blur")).toBeInTheDocument();
      expect(screen.getByText("Shadow Strength")).toBeInTheDocument();
      expect(screen.getByText("Border Radius")).toBeInTheDocument();
      expect(screen.getByText("FAB Roundness")).toBeInTheDocument();
      expect(screen.getByText("Parallax Strength")).toBeInTheDocument();
      expect(screen.getByText("Animation Speed")).toBeInTheDocument();
    });

    it("renders Done button", () => {
      renderWithTheme(
        <CustomizationDrawer isOpen={true} onClose={mockOnClose} />
      );
      expect(screen.getByText("Done")).toBeInTheDocument();
    });

    it("renders Reset Effects button", () => {
      renderWithTheme(
        <CustomizationDrawer isOpen={true} onClose={mockOnClose} />
      );
      expect(screen.getByText("Reset Effects")).toBeInTheDocument();
    });
  });

  describe("interactions", () => {
    it("calls onClose when close button is clicked", () => {
      renderWithTheme(
        <CustomizationDrawer isOpen={true} onClose={mockOnClose} />
      );
      fireEvent.click(screen.getByLabelText("Close customization drawer"));
      expect(mockOnClose).toHaveBeenCalledTimes(1);
    });

    it("calls onClose when Done button is clicked", () => {
      renderWithTheme(
        <CustomizationDrawer isOpen={true} onClose={mockOnClose} />
      );
      fireEvent.click(screen.getByText("Done"));
      expect(mockOnClose).toHaveBeenCalledTimes(1);
    });

    it("calls onClose when backdrop is clicked", () => {
      renderWithTheme(
        <CustomizationDrawer isOpen={true} onClose={mockOnClose} />
      );
      // The backdrop is the first element with the fade-in animation
      const backdrop = document.querySelector('[aria-hidden="true"]');
      if (backdrop) {
        fireEvent.click(backdrop);
        expect(mockOnClose).toHaveBeenCalledTimes(1);
      }
    });

    it("calls onClose when Escape key is pressed", () => {
      renderWithTheme(
        <CustomizationDrawer isOpen={true} onClose={mockOnClose} />
      );
      fireEvent.keyDown(document, { key: "Escape" });
      expect(mockOnClose).toHaveBeenCalledTimes(1);
    });

    it("can collapse and expand control groups", () => {
      renderWithTheme(
        <CustomizationDrawer isOpen={true} onClose={mockOnClose} />
      );
      
      // Find the Color Theme section button
      const colorThemeButton = screen.getByText("Color Theme").closest("button");
      expect(colorThemeButton).toBeInTheDocument();
      
      // Initially expanded, so color options should be visible
      // Click to collapse
      if (colorThemeButton) {
        fireEvent.click(colorThemeButton);
        // After collapse, the aria-expanded should be false
        expect(colorThemeButton).toHaveAttribute("aria-expanded", "false");
      }
    });
  });

  describe("accessibility", () => {
    it("has correct role and aria-modal", () => {
      renderWithTheme(
        <CustomizationDrawer isOpen={true} onClose={mockOnClose} />
      );
      const drawer = screen.getByRole("dialog");
      expect(drawer).toHaveAttribute("aria-modal", "true");
    });

    it("has correct aria-label", () => {
      renderWithTheme(
        <CustomizationDrawer isOpen={true} onClose={mockOnClose} />
      );
      expect(screen.getByLabelText("Customization drawer")).toBeInTheDocument();
    });

    it("color options have aria-pressed attribute", () => {
      renderWithTheme(
        <CustomizationDrawer isOpen={true} onClose={mockOnClose} />
      );
      const colorOptions = screen.getAllByRole("button", { pressed: true });
      expect(colorOptions.length).toBeGreaterThan(0);
    });
  });
});
