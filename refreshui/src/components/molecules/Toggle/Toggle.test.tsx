import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { Toggle } from "./Toggle";

/**
 * Toggle Molecule Tests
 *
 * Tests for the Toggle component verifying:
 * - Rendering with different props
 * - State changes on click
 * - Accessibility attributes
 * - Disabled state behavior
 *
 * Requirements: 4.2
 */

describe("Toggle", () => {
  describe("rendering", () => {
    it("renders without crashing", () => {
      const onChange = vi.fn();
      render(<Toggle checked={false} onChange={onChange} />);
      expect(screen.getByRole("switch")).toBeInTheDocument();
    });

    it("renders with label when provided", () => {
      const onChange = vi.fn();
      render(<Toggle checked={false} onChange={onChange} label="Enable feature" />);
      expect(screen.getByText("Enable feature")).toBeInTheDocument();
    });

    it("renders in checked state", () => {
      const onChange = vi.fn();
      render(<Toggle checked={true} onChange={onChange} />);
      expect(screen.getByRole("switch")).toHaveAttribute("aria-checked", "true");
    });

    it("renders in unchecked state", () => {
      const onChange = vi.fn();
      render(<Toggle checked={false} onChange={onChange} />);
      expect(screen.getByRole("switch")).toHaveAttribute("aria-checked", "false");
    });
  });

  describe("state changes", () => {
    it("calls onChange with true when clicking unchecked toggle", () => {
      const onChange = vi.fn();
      render(<Toggle checked={false} onChange={onChange} />);
      
      fireEvent.click(screen.getByRole("switch"));
      
      expect(onChange).toHaveBeenCalledTimes(1);
      expect(onChange).toHaveBeenCalledWith(true);
    });

    it("calls onChange with false when clicking checked toggle", () => {
      const onChange = vi.fn();
      render(<Toggle checked={true} onChange={onChange} />);
      
      fireEvent.click(screen.getByRole("switch"));
      
      expect(onChange).toHaveBeenCalledTimes(1);
      expect(onChange).toHaveBeenCalledWith(false);
    });

    it("calls onChange when clicking the label", () => {
      const onChange = vi.fn();
      render(<Toggle checked={false} onChange={onChange} label="Toggle me" />);
      
      fireEvent.click(screen.getByText("Toggle me"));
      
      expect(onChange).toHaveBeenCalledTimes(1);
      expect(onChange).toHaveBeenCalledWith(true);
    });
  });

  describe("keyboard interaction", () => {
    it("toggles on Space key press", () => {
      const onChange = vi.fn();
      render(<Toggle checked={false} onChange={onChange} />);
      
      fireEvent.keyDown(screen.getByRole("switch"), { key: " " });
      
      expect(onChange).toHaveBeenCalledTimes(1);
      expect(onChange).toHaveBeenCalledWith(true);
    });

    it("toggles on Enter key press", () => {
      const onChange = vi.fn();
      render(<Toggle checked={false} onChange={onChange} />);
      
      fireEvent.keyDown(screen.getByRole("switch"), { key: "Enter" });
      
      expect(onChange).toHaveBeenCalledTimes(1);
      expect(onChange).toHaveBeenCalledWith(true);
    });
  });

  describe("disabled state", () => {
    it("does not call onChange when disabled and clicked", () => {
      const onChange = vi.fn();
      render(<Toggle checked={false} onChange={onChange} disabled />);
      
      fireEvent.click(screen.getByRole("switch"));
      
      expect(onChange).not.toHaveBeenCalled();
    });

    it("does not call onChange when disabled and key pressed", () => {
      const onChange = vi.fn();
      render(<Toggle checked={false} onChange={onChange} disabled />);
      
      fireEvent.keyDown(screen.getByRole("switch"), { key: " " });
      
      expect(onChange).not.toHaveBeenCalled();
    });

    it("has disabled attribute on the switch button", () => {
      const onChange = vi.fn();
      render(<Toggle checked={false} onChange={onChange} disabled />);
      
      expect(screen.getByRole("switch")).toBeDisabled();
    });
  });

  describe("sizes", () => {
    it("renders small size", () => {
      const onChange = vi.fn();
      render(<Toggle checked={false} onChange={onChange} size="sm" />);
      expect(screen.getByRole("switch")).toBeInTheDocument();
    });

    it("renders medium size (default)", () => {
      const onChange = vi.fn();
      render(<Toggle checked={false} onChange={onChange} size="md" />);
      expect(screen.getByRole("switch")).toBeInTheDocument();
    });

    it("renders large size", () => {
      const onChange = vi.fn();
      render(<Toggle checked={false} onChange={onChange} size="lg" />);
      expect(screen.getByRole("switch")).toBeInTheDocument();
    });
  });

  describe("accessibility", () => {
    it("has role switch", () => {
      const onChange = vi.fn();
      render(<Toggle checked={false} onChange={onChange} />);
      expect(screen.getByRole("switch")).toBeInTheDocument();
    });

    it("has aria-checked attribute", () => {
      const onChange = vi.fn();
      render(<Toggle checked={true} onChange={onChange} />);
      expect(screen.getByRole("switch")).toHaveAttribute("aria-checked", "true");
    });

    it("associates label with toggle via aria-labelledby", () => {
      const onChange = vi.fn();
      render(<Toggle checked={false} onChange={onChange} label="My toggle" id="test-toggle" />);
      
      const toggle = screen.getByRole("switch");
      expect(toggle).toHaveAttribute("aria-labelledby", "test-toggle-label");
    });
  });
});
