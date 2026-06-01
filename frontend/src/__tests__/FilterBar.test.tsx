import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { FilterBar } from "@/components/resources/FilterBar";

describe("FilterBar", () => {
  it("renders search input", () => {
    render(<FilterBar />);
    expect(screen.getByLabelText("Search assets")).toBeInTheDocument();
  });

  it("renders platform filter", () => {
    render(<FilterBar />);
    expect(screen.getByLabelText("Filter by platform")).toBeInTheDocument();
  });

  it("renders status filter", () => {
    render(<FilterBar />);
    expect(screen.getByLabelText("Filter by status")).toBeInTheDocument();
  });

  it("updates search", () => {
    render(<FilterBar />);
    const input = screen.getByLabelText("Search assets");
    fireEvent.change(input, { target: { value: "web" } });
    expect(input).toHaveValue("web");
  });
});
