import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { EmptyState } from "@/components/ui/EmptyState";
import { Server } from "lucide-react";

describe("EmptyState", () => {
  it("renders title", () => { render(<EmptyState icon={Server} title="No data" description="Empty" />); expect(screen.getByText("No data")).toBeInTheDocument(); });
  it("renders action", () => { const fn = vi.fn(); render(<EmptyState icon={Server} title="E" description="D" action={{ label: "Add", onClick: fn }} />); fireEvent.click(screen.getByText("Add")); expect(fn).toHaveBeenCalledOnce(); });
});
