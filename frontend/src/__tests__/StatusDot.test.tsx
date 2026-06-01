import { render } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { StatusDot } from "@/components/ui/StatusDot";

describe("StatusDot", () => {
  it("renders with aria-label", () => { const { getByLabelText } = render(<StatusDot status="online" />); expect(getByLabelText("Status: online")).toBeInTheDocument(); });
  it("applies correct color", () => { const { getByLabelText } = render(<StatusDot status="online" />); expect(getByLabelText("Status: online").className).toContain("bg-success"); });
  it("pulses for running", () => { const { getByLabelText } = render(<StatusDot status="running" />); expect(getByLabelText("Status: running").className).toContain("animate-pulse"); });
});
