import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { Input, type InputType, type InputState } from "./Input";

describe("Input", () => {
  const types: InputType[] = ["text", "search", "password"];
  const states: InputState[] = ["default", "focus", "error", "disabled"];

  it("renders with default props", () => {
    render(<Input placeholder="Enter text" />);
    expect(screen.getByPlaceholderText("Enter text")).toBeInTheDocument();
  });

  describe("types", () => {
    types.forEach((type) => {
      it(`renders ${type} type without error`, () => {
        render(<Input type={type} placeholder={`${type} input`} />);
        const input = screen.getByPlaceholderText(`${type} input`);
        expect(input).toBeInTheDocument();
        expect(input).toHaveAttribute("type", type);
      });
    });
  });

  describe("states", () => {
    states.forEach((state) => {
      it(`renders ${state} state without error`, () => {
        render(<Input state={state} placeholder="Test input" />);
        const input = screen.getByPlaceholderText("Test input");
        expect(input).toBeInTheDocument();
      });
    });

    it("applies error state with aria-invalid", () => {
      render(<Input state="error" placeholder="Error input" />);
      const input = screen.getByPlaceholderText("Error input");
      expect(input).toHaveAttribute("aria-invalid", "true");
    });

    it("is disabled when state is disabled", () => {
      render(<Input state="disabled" placeholder="Disabled input" />);
      expect(screen.getByPlaceholderText("Disabled input")).toBeDisabled();
    });

    it("is disabled when disabled prop is true", () => {
      render(<Input disabled placeholder="Disabled input" />);
      expect(screen.getByPlaceholderText("Disabled input")).toBeDisabled();
    });
  });

  it("handles change events", () => {
    const handleChange = vi.fn();
    render(<Input onChange={handleChange} placeholder="Test input" />);

    fireEvent.change(screen.getByPlaceholderText("Test input"), {
      target: { value: "test value" },
    });
    expect(handleChange).toHaveBeenCalledTimes(1);
  });

  it("renders with left icon", () => {
    render(
      <Input
        leftIcon={<span data-testid="left-icon">🔍</span>}
        placeholder="With icon"
      />
    );
    expect(screen.getByTestId("left-icon")).toBeInTheDocument();
  });

  it("renders with right icon", () => {
    render(
      <Input
        rightIcon={<span data-testid="right-icon">✓</span>}
        placeholder="With icon"
      />
    );
    expect(screen.getByTestId("right-icon")).toBeInTheDocument();
  });

  it("renders with both icons", () => {
    render(
      <Input
        leftIcon={<span data-testid="left-icon">🔍</span>}
        rightIcon={<span data-testid="right-icon">✓</span>}
        placeholder="With icons"
      />
    );
    expect(screen.getByTestId("left-icon")).toBeInTheDocument();
    expect(screen.getByTestId("right-icon")).toBeInTheDocument();
  });

  it("renders with label", () => {
    render(<Input label="Email" placeholder="Enter email" />);
    expect(screen.getByText("Email")).toBeInTheDocument();
  });

  it("renders error message when in error state", () => {
    render(
      <Input
        state="error"
        errorMessage="This field is required"
        placeholder="Error input"
      />
    );
    expect(screen.getByText("This field is required")).toBeInTheDocument();
    expect(screen.getByRole("alert")).toBeInTheDocument();
  });

  it("does not render error message when not in error state", () => {
    render(
      <Input
        state="default"
        errorMessage="This field is required"
        placeholder="Default input"
      />
    );
    expect(
      screen.queryByText("This field is required")
    ).not.toBeInTheDocument();
  });

  it("applies custom className", () => {
    render(<Input className="custom-class" placeholder="Custom input" />);
    expect(screen.getByPlaceholderText("Custom input")).toHaveClass(
      "custom-class"
    );
  });
});
