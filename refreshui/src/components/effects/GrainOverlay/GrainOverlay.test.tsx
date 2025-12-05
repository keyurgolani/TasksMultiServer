import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { GrainOverlay } from "./GrainOverlay";

describe("GrainOverlay", () => {
  it("renders when enabled (default)", () => {
    render(<GrainOverlay />);
    const overlay = screen.getByTestId("grain-overlay");
    expect(overlay).toBeInTheDocument();
  });

  it("does not render when disabled", () => {
    render(<GrainOverlay enabled={false} />);
    const overlay = screen.queryByTestId("grain-overlay");
    expect(overlay).not.toBeInTheDocument();
  });

  it("applies grain-overlay class", () => {
    render(<GrainOverlay />);
    const overlay = screen.getByTestId("grain-overlay");
    expect(overlay).toHaveClass("grain-overlay");
  });

  it("applies custom opacity when provided", () => {
    render(<GrainOverlay opacity={0.1} />);
    const overlay = screen.getByTestId("grain-overlay");
    expect(overlay).toHaveStyle({ opacity: "0.1" });
  });

  it("does not apply inline opacity when not provided", () => {
    render(<GrainOverlay />);
    const overlay = screen.getByTestId("grain-overlay");
    // When opacity is not provided, style should not have opacity set
    expect(overlay.style.opacity).toBe("");
  });

  it("applies additional className", () => {
    render(<GrainOverlay className="custom-class" />);
    const overlay = screen.getByTestId("grain-overlay");
    expect(overlay).toHaveClass("grain-overlay");
    expect(overlay).toHaveClass("custom-class");
  });

  it("has aria-hidden attribute for accessibility", () => {
    render(<GrainOverlay />);
    const overlay = screen.getByTestId("grain-overlay");
    expect(overlay).toHaveAttribute("aria-hidden", "true");
  });

  it("accepts opacity value of 0", () => {
    render(<GrainOverlay opacity={0} />);
    const overlay = screen.getByTestId("grain-overlay");
    expect(overlay).toHaveStyle({ opacity: "0" });
  });

  it("accepts opacity value of 1", () => {
    render(<GrainOverlay opacity={1} />);
    const overlay = screen.getByTestId("grain-overlay");
    expect(overlay).toHaveStyle({ opacity: "1" });
  });
});
