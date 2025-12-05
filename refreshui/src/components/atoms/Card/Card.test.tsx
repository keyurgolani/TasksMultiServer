import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { Card, type CardVariant, type CardPadding } from "./Card";

describe("Card", () => {
  const variants: CardVariant[] = ["glass", "solid", "outline"];
  const paddings: CardPadding[] = ["none", "sm", "md", "lg"];

  it("renders with default props", () => {
    render(<Card>Card content</Card>);
    expect(screen.getByText("Card content")).toBeInTheDocument();
  });

  describe("variants", () => {
    variants.forEach((variant) => {
      it(`renders ${variant} variant without error`, () => {
        render(<Card variant={variant}>Card content</Card>);
        expect(screen.getByText("Card content")).toBeInTheDocument();
      });
    });
  });

  describe("padding sizes", () => {
    paddings.forEach((padding) => {
      it(`renders ${padding} padding without error`, () => {
        render(<Card padding={padding}>Card content</Card>);
        expect(screen.getByText("Card content")).toBeInTheDocument();
      });
    });
  });

  it("applies custom className", () => {
    const { container } = render(<Card className="custom-class">Card content</Card>);
    const card = container.firstChild;
    expect(card).toHaveClass("custom-class");
  });

  it("applies custom style", () => {
    const { container } = render(<Card style={{ maxWidth: "500px" }}>Card content</Card>);
    const card = container.firstChild;
    expect(card).toHaveStyle({ maxWidth: "500px" });
  });

  describe("spotlight effect", () => {
    it("renders spotlight overlay when spotlight is enabled", () => {
      const { container } = render(<Card spotlight>Card content</Card>);
      // Spotlight overlay should be present
      const overlay = container.querySelector('[aria-hidden="true"]');
      expect(overlay).toBeInTheDocument();
    });

    it("does not render spotlight overlay when spotlight is disabled", () => {
      const { container } = render(<Card spotlight={false}>Card content</Card>);
      const overlay = container.querySelector('[aria-hidden="true"]');
      expect(overlay).not.toBeInTheDocument();
    });
  });

  describe("tilt effect", () => {
    it("applies cursor-pointer class when tilt is enabled", () => {
      const { container } = render(<Card tilt>Card content</Card>);
      const card = container.firstChild;
      expect(card).toHaveClass("cursor-pointer");
    });

    it("does not apply cursor-pointer class when tilt is disabled", () => {
      const { container } = render(<Card tilt={false}>Card content</Card>);
      const card = container.firstChild;
      expect(card).not.toHaveClass("cursor-pointer");
    });
  });

  describe("mouse interactions", () => {
    it("calls external onMouseMove handler", () => {
      const handleMouseMove = vi.fn();
      const { container } = render(
        <Card spotlight onMouseMove={handleMouseMove}>
          Card content
        </Card>
      );
      
      fireEvent.mouseMove(container.firstChild as Element);
      expect(handleMouseMove).toHaveBeenCalled();
    });

    it("calls external onMouseLeave handler", () => {
      const handleMouseLeave = vi.fn();
      const { container } = render(
        <Card spotlight onMouseLeave={handleMouseLeave}>
          Card content
        </Card>
      );
      
      fireEvent.mouseLeave(container.firstChild as Element);
      expect(handleMouseLeave).toHaveBeenCalled();
    });
  });

  it("forwards ref correctly", () => {
    const ref = vi.fn();
    render(<Card ref={ref}>Card content</Card>);
    expect(ref).toHaveBeenCalled();
  });
});
