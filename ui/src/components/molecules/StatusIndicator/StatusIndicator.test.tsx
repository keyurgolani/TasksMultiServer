import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { StatusIndicator, type StatusType } from "./StatusIndicator";

/**
 * StatusIndicator Molecule Tests
 *
 * Tests for the StatusIndicator component that displays a colored dot
 * with optional pulse animation for active states.
 *
 * Requirements: 4.5
 */

describe("StatusIndicator", () => {
  describe("rendering", () => {
    it("renders without crashing", () => {
      render(<StatusIndicator status="not_started" />);
      expect(screen.getByRole("status")).toBeInTheDocument();
    });

    it("renders with correct aria-label for status", () => {
      render(<StatusIndicator status="in_progress" />);
      expect(screen.getByRole("status")).toHaveAttribute(
        "aria-label",
        "Status: in progress"
      );
    });

    it("renders with data-status attribute", () => {
      render(<StatusIndicator status="completed" />);
      expect(screen.getByRole("status")).toHaveAttribute(
        "data-status",
        "completed"
      );
    });
  });

  describe("status variants", () => {
    const statuses: StatusType[] = [
      "not_started",
      "in_progress",
      "completed",
      "blocked",
    ];

    statuses.forEach((status) => {
      it(`renders ${status} status without error`, () => {
        render(<StatusIndicator status={status} />);
        expect(screen.getByRole("status")).toBeInTheDocument();
        expect(screen.getByRole("status")).toHaveAttribute(
          "data-status",
          status
        );
      });
    });
  });

  describe("sizes", () => {
    it("renders small size", () => {
      render(<StatusIndicator status="not_started" size="sm" />);
      const indicator = screen.getByRole("status");
      expect(indicator).toHaveClass("w-2", "h-2");
    });

    it("renders medium size (default)", () => {
      render(<StatusIndicator status="not_started" />);
      const indicator = screen.getByRole("status");
      expect(indicator).toHaveClass("w-3", "h-3");
    });

    it("renders large size", () => {
      render(<StatusIndicator status="not_started" size="lg" />);
      const indicator = screen.getByRole("status");
      expect(indicator).toHaveClass("w-4", "h-4");
    });
  });

  describe("pulse animation", () => {
    it("does not show pulse animation by default", () => {
      render(<StatusIndicator status="in_progress" />);
      const indicator = screen.getByRole("status");
      expect(indicator).toHaveAttribute("data-pulse", "false");
      // Should not have the ping animation child
      expect(indicator.querySelector(".animate-ping")).toBeNull();
    });

    it("shows pulse animation for in_progress when pulse is enabled", () => {
      render(<StatusIndicator status="in_progress" pulse />);
      const indicator = screen.getByRole("status");
      expect(indicator).toHaveAttribute("data-pulse", "true");
      // Should have the ping animation child
      expect(indicator.querySelector(".animate-ping")).toBeInTheDocument();
    });

    it("shows pulse animation for blocked when pulse is enabled", () => {
      render(<StatusIndicator status="blocked" pulse />);
      const indicator = screen.getByRole("status");
      expect(indicator).toHaveAttribute("data-pulse", "true");
      expect(indicator.querySelector(".animate-ping")).toBeInTheDocument();
    });

    it("does not show pulse animation for not_started even when pulse is enabled", () => {
      render(<StatusIndicator status="not_started" pulse />);
      const indicator = screen.getByRole("status");
      expect(indicator).toHaveAttribute("data-pulse", "false");
      expect(indicator.querySelector(".animate-ping")).toBeNull();
    });

    it("does not show pulse animation for completed even when pulse is enabled", () => {
      render(<StatusIndicator status="completed" pulse />);
      const indicator = screen.getByRole("status");
      expect(indicator).toHaveAttribute("data-pulse", "false");
      expect(indicator.querySelector(".animate-ping")).toBeNull();
    });
  });

  describe("custom className", () => {
    it("applies custom className", () => {
      render(
        <StatusIndicator status="not_started" className="custom-class" />
      );
      expect(screen.getByRole("status")).toHaveClass("custom-class");
    });
  });
});
