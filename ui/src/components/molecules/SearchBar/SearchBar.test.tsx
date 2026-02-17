import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, fireEvent, act } from "@testing-library/react";
import { SearchBar } from "./SearchBar";

describe("SearchBar", () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("renders with default placeholder", () => {
    render(<SearchBar />);
    expect(screen.getByPlaceholderText("Search...")).toBeInTheDocument();
  });

  it("renders with custom placeholder", () => {
    render(<SearchBar placeholder="Find tasks..." />);
    expect(screen.getByPlaceholderText("Find tasks...")).toBeInTheDocument();
  });

  it("displays the search icon", () => {
    render(<SearchBar />);
    // The search icon should be present (rendered by Icon component)
    const input = screen.getByRole("searchbox");
    expect(input).toBeInTheDocument();
  });

  it("updates internal value immediately on input", () => {
    render(<SearchBar />);
    const input = screen.getByRole("searchbox");

    fireEvent.change(input, { target: { value: "test" } });

    expect(input).toHaveValue("test");
  });

  it("debounces onChange callback", () => {
    const onChange = vi.fn();
    render(<SearchBar onChange={onChange} debounceMs={300} />);
    const input = screen.getByRole("searchbox");

    fireEvent.change(input, { target: { value: "test" } });

    // onChange should not be called immediately
    expect(onChange).not.toHaveBeenCalled();

    // Fast-forward time by 300ms
    act(() => {
      vi.advanceTimersByTime(300);
    });

    // Now onChange should be called
    expect(onChange).toHaveBeenCalledWith("test");
    expect(onChange).toHaveBeenCalledTimes(1);
  });

  it("fires onImmediateChange without debounce", () => {
    const onImmediateChange = vi.fn();
    const onChange = vi.fn();
    render(
      <SearchBar
        onChange={onChange}
        onImmediateChange={onImmediateChange}
        debounceMs={300}
      />
    );
    const input = screen.getByRole("searchbox");

    fireEvent.change(input, { target: { value: "test" } });

    // onImmediateChange should be called immediately
    expect(onImmediateChange).toHaveBeenCalledWith("test");
    // onChange should not be called yet
    expect(onChange).not.toHaveBeenCalled();
  });

  it("shows clear button when input has value", () => {
    render(<SearchBar />);
    const input = screen.getByRole("searchbox");

    // Initially clear button is not rendered (only search icon is shown)
    expect(screen.queryByLabelText("Clear search")).not.toBeInTheDocument();

    fireEvent.change(input, { target: { value: "test" } });

    // Clear button should now be rendered and visible
    const clearButton = screen.getByLabelText("Clear search");
    expect(clearButton).toBeInTheDocument();
    expect(clearButton).toHaveAttribute("aria-hidden", "false");
    expect(clearButton).not.toBeDisabled();
  });

  it("clears input when clear button is clicked", () => {
    const onChange = vi.fn();
    const onClear = vi.fn();
    render(<SearchBar onChange={onChange} onClear={onClear} />);
    const input = screen.getByRole("searchbox");

    fireEvent.change(input, { target: { value: "test" } });
    expect(input).toHaveValue("test");

    const clearButton = screen.getByLabelText("Clear search");
    fireEvent.click(clearButton);

    expect(input).toHaveValue("");
    expect(onChange).toHaveBeenCalledWith("");
    expect(onClear).toHaveBeenCalled();
  });

  it("clears input on Escape key", () => {
    const onChange = vi.fn();
    render(<SearchBar onChange={onChange} />);
    const input = screen.getByRole("searchbox");

    fireEvent.change(input, { target: { value: "test" } });
    fireEvent.keyDown(input, { key: "Escape" });

    expect(input).toHaveValue("");
    expect(onChange).toHaveBeenCalledWith("");
  });

  it("respects controlled value prop", () => {
    const { rerender } = render(<SearchBar value="initial" />);
    const input = screen.getByRole("searchbox");

    expect(input).toHaveValue("initial");

    rerender(<SearchBar value="updated" />);
    expect(input).toHaveValue("updated");
  });

  it("can be disabled", () => {
    render(<SearchBar disabled />);
    const input = screen.getByRole("searchbox");

    expect(input).toBeDisabled();
  });

  it("does not show clear button when disabled", () => {
    render(<SearchBar value="test" disabled />);

    // Clear button should not be rendered when SearchBar is disabled (only search icon shown)
    expect(screen.queryByLabelText("Clear search")).not.toBeInTheDocument();
  });

  it("cancels pending debounce on rapid input changes", () => {
    const onChange = vi.fn();
    render(<SearchBar onChange={onChange} debounceMs={300} />);
    const input = screen.getByRole("searchbox");

    // Type multiple characters rapidly
    fireEvent.change(input, { target: { value: "t" } });
    act(() => {
      vi.advanceTimersByTime(100);
    });

    fireEvent.change(input, { target: { value: "te" } });
    act(() => {
      vi.advanceTimersByTime(100);
    });

    fireEvent.change(input, { target: { value: "tes" } });
    act(() => {
      vi.advanceTimersByTime(100);
    });

    fireEvent.change(input, { target: { value: "test" } });

    // onChange should not have been called yet
    expect(onChange).not.toHaveBeenCalled();

    // Wait for debounce
    act(() => {
      vi.advanceTimersByTime(300);
    });

    // Should only be called once with final value
    expect(onChange).toHaveBeenCalledTimes(1);
    expect(onChange).toHaveBeenCalledWith("test");
  });

  // Requirements 25.1, 25.2, 44.1, 44.2, 44.3: Icon transition tests
  describe("icon transitions (Requirements 25.1, 25.2, 25.4, 25.5, 44.1, 44.2, 44.3)", () => {
    it("shows exactly one search icon when empty (Requirement 44.2)", () => {
      render(<SearchBar />);

      // When empty: only search icon is rendered, clear button is not in DOM
      expect(screen.queryByLabelText("Clear search")).not.toBeInTheDocument();
    });

    it("shows exactly one X icon when has value (Requirement 44.1)", () => {
      render(<SearchBar />);
      const input = screen.getByRole("searchbox");

      // Type text
      fireEvent.change(input, { target: { value: "test" } });

      // When has value: only clear button is rendered
      const clearButton = screen.getByLabelText("Clear search");
      expect(clearButton).toBeInTheDocument();
      expect(clearButton).toHaveAttribute("aria-hidden", "false");
    });

    it("ensures only one icon is visible at any time (Requirement 44.3)", () => {
      render(<SearchBar />);
      const input = screen.getByRole("searchbox");

      // Initially: no clear button
      expect(screen.queryByLabelText("Clear search")).not.toBeInTheDocument();

      // Type text: clear button appears
      fireEvent.change(input, { target: { value: "test" } });
      expect(screen.getByLabelText("Clear search")).toBeInTheDocument();

      // Clear: clear button disappears
      fireEvent.click(screen.getByLabelText("Clear search"));
      expect(screen.queryByLabelText("Clear search")).not.toBeInTheDocument();
    });

    it("restores search icon after clearing (Requirement 25.4, 44.4)", () => {
      const onChange = vi.fn();
      render(<SearchBar onChange={onChange} />);
      const input = screen.getByRole("searchbox");

      // Type text
      fireEvent.change(input, { target: { value: "test" } });

      // Clear button should be visible
      const clearButton = screen.getByLabelText("Clear search");
      expect(clearButton).toBeInTheDocument();

      // Click clear
      fireEvent.click(clearButton);

      // Search icon should be restored (clear button no longer in DOM)
      expect(screen.queryByLabelText("Clear search")).not.toBeInTheDocument();
      expect(input).toHaveValue("");
    });

    it("applies transition styles for smooth animation (Requirement 25.5)", () => {
      render(<SearchBar />);
      const input = screen.getByRole("searchbox");

      // Type text to show clear button
      fireEvent.change(input, { target: { value: "test" } });

      // Check that the clear button has transition styles
      const clearButton = screen.getByLabelText("Clear search");
      const style = clearButton.getAttribute("style");
      expect(style).toContain("transition");
      expect(style).toContain("opacity");
      expect(style).toContain("animation-speed");
    });
  });
});
