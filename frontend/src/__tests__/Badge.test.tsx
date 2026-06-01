import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { Badge } from "@/components/ui/Badge";

describe("Badge", () => {
  it("renders children", () => {
    render(<Badge>P0</Badge>);
    expect(screen.getByText("P0")).toBeInTheDocument();
  });
  it("applies severity styles", () => {
    render(<Badge severity="P0">Critical</Badge>);
    expect(screen.getByText("Critical").className).toContain("bg-red-500/15");
  });
});
