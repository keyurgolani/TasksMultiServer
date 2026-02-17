import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { Button, type ButtonVariant, type ButtonSize } from "./Button";

describe("Button", () => {
  const variants: ButtonVariant[] = ["primary", "secondary", "tertiary", "ghost", "destructive"];
  const sizes: ButtonSize[] = ["sm", "md", "lg"];

  it("renders with default props", () => {
    render(<Button>Click me</Button>);
    expect(screen.getByRole("button", { name: "Click me" })).toBeInTheDocument();
  });

  describe("variants", () => {
    variants.forEach((variant) => {
      it(`renders ${variant} variant without error`, () => {
        render(<Button variant={variant}>Button</Button>);
        const button = screen.getByRole("button", { name: "Button" });
        expect(button).toBeInTheDocument();
      });
    });
  });

  describe("sizes", () => {
    sizes.forEach((size) => {
      it(`renders ${size} size without error`, () => {
        render(<Button size={size}>Button</Button>);
        const button = screen.getByRole("button", { name: "Button" });
        expect(button).toBeInTheDocument();
      });
    });
  });

  it("handles click events", () => {
    const handleClick = vi.fn();
    render(<Button onClick={handleClick}>Click me</Button>);
    
    fireEvent.click(screen.getByRole("button"));
    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  it("renders with left icon", () => {
    render(<Button leftIcon={<span data-testid="left-icon">←</span>}>With Icon</Button>);
    expect(screen.getByTestId("left-icon")).toBeInTheDocument();
  });

  it("renders with right icon", () => {
    render(<Button rightIcon={<span data-testid="right-icon">→</span>}>With Icon</Button>);
    expect(screen.getByTestId("right-icon")).toBeInTheDocument();
  });

  it("shows loading state", () => {
    render(<Button loading>Loading</Button>);
    const button = screen.getByRole("button");
    expect(button).toHaveAttribute("aria-busy", "true");
    expect(button).toBeDisabled();
  });

  it("is disabled when disabled prop is true", () => {
    render(<Button disabled>Disabled</Button>);
    expect(screen.getByRole("button")).toBeDisabled();
  });

  it("applies custom className", () => {
    render(<Button className="custom-class">Custom</Button>);
    expect(screen.getByRole("button")).toHaveClass("custom-class");
  });
});
