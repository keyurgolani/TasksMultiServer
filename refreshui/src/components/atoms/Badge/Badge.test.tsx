import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { Badge, type BadgeVariant, type BadgeSize } from "./Badge";

describe("Badge", () => {
  const variants: BadgeVariant[] = ["success", "warning", "error", "info", "neutral"];
  const sizes: BadgeSize[] = ["sm", "md"];

  it("renders with default props", () => {
    render(<Badge>Status</Badge>);
    expect(screen.getByText("Status")).toBeInTheDocument();
  });

  describe("variants", () => {
    variants.forEach((variant) => {
      it(`renders ${variant} variant without error`, () => {
        render(<Badge variant={variant}>Badge</Badge>);
        const badge = screen.getByText("Badge");
        expect(badge).toBeInTheDocument();
      });
    });
  });

  describe("sizes", () => {
    sizes.forEach((size) => {
      it(`renders ${size} size without error`, () => {
        render(<Badge size={size}>Badge</Badge>);
        const badge = screen.getByText("Badge");
        expect(badge).toBeInTheDocument();
      });
    });
  });

  it("applies custom className", () => {
    render(<Badge className="custom-class">Custom</Badge>);
    expect(screen.getByText("Custom")).toHaveClass("custom-class");
  });

  it("forwards ref correctly", () => {
    const ref = { current: null as HTMLSpanElement | null };
    render(<Badge ref={ref}>Ref Test</Badge>);
    expect(ref.current).toBeInstanceOf(HTMLSpanElement);
  });

  it("passes through additional HTML attributes", () => {
    render(<Badge data-testid="test-badge" title="Test Title">Attrs</Badge>);
    const badge = screen.getByTestId("test-badge");
    expect(badge).toHaveAttribute("title", "Test Title");
  });
});
