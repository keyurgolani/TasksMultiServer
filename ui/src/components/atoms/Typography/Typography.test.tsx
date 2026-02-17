import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import {
  Typography,
  variantElementMap,
  type TypographyVariant,
  type TypographyColor,
} from "./Typography";

describe("Typography", () => {
  const variants: TypographyVariant[] = [
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "body",
    "body-sm",
    "body-lg",
    "caption",
    "label",
  ];

  const colors: TypographyColor[] = [
    "primary",
    "secondary",
    "muted",
    "inherit",
    "success",
    "warning",
    "error",
    "info",
  ];

  it("renders with default props", () => {
    render(<Typography>Hello World</Typography>);
    expect(screen.getByText("Hello World")).toBeInTheDocument();
  });

  describe("variants render correct semantic elements", () => {
    /**
     * Property 7: Typography Element Mapping
     * For any Typography variant, the component SHALL render
     * the semantically correct HTML element.
     */
    variants.forEach((variant) => {
      it(`renders ${variant} variant with correct element`, () => {
        const testId = `typography-${variant}`;
        render(
          <Typography variant={variant} data-testid={testId}>
            Test Content
          </Typography>
        );

        const element = screen.getByTestId(testId);
        const expectedTag = variantElementMap[variant].toString().toLowerCase();
        expect(element.tagName.toLowerCase()).toBe(expectedTag);
      });
    });
  });

  describe("colors", () => {
    colors.forEach((color) => {
      it(`renders ${color} color without error`, () => {
        render(
          <Typography color={color} data-testid={`color-${color}`}>
            Colored Text
          </Typography>
        );
        expect(screen.getByTestId(`color-${color}`)).toBeInTheDocument();
      });
    });
  });

  describe("heading variants", () => {
    const headings: TypographyVariant[] = ["h1", "h2", "h3", "h4", "h5", "h6"];

    headings.forEach((heading) => {
      it(`${heading} renders as heading element`, () => {
        render(<Typography variant={heading}>Heading</Typography>);
        const element = screen.getByRole("heading", { level: parseInt(heading.slice(1)) });
        expect(element).toBeInTheDocument();
      });
    });
  });

  it("renders with truncate prop", () => {
    render(
      <Typography truncate data-testid="truncated">
        This is a very long text that should be truncated
      </Typography>
    );
    const element = screen.getByTestId("truncated");
    expect(element).toHaveClass("overflow-hidden");
    expect(element).toHaveClass("text-ellipsis");
    expect(element).toHaveClass("whitespace-nowrap");
  });

  it("renders with custom 'as' prop", () => {
    render(
      <Typography as="div" data-testid="custom-element">
        Custom Element
      </Typography>
    );
    const element = screen.getByTestId("custom-element");
    expect(element.tagName.toLowerCase()).toBe("div");
  });

  it("applies custom className", () => {
    render(
      <Typography className="custom-class" data-testid="custom-class">
        Custom Class
      </Typography>
    );
    expect(screen.getByTestId("custom-class")).toHaveClass("custom-class");
  });

  it("passes through additional HTML attributes", () => {
    render(
      <Typography id="test-id" aria-label="Test label">
        With Attributes
      </Typography>
    );
    const element = screen.getByText("With Attributes");
    expect(element).toHaveAttribute("id", "test-id");
    expect(element).toHaveAttribute("aria-label", "Test label");
  });

  it("label variant renders as label element", () => {
    render(<Typography variant="label">Label Text</Typography>);
    const element = screen.getByText("Label Text");
    expect(element.tagName.toLowerCase()).toBe("label");
  });

  it("caption variant renders as span element", () => {
    render(
      <Typography variant="caption" data-testid="caption">
        Caption Text
      </Typography>
    );
    const element = screen.getByTestId("caption");
    expect(element.tagName.toLowerCase()).toBe("span");
  });
});
