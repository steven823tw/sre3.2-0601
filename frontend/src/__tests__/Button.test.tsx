import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { Button } from "@/components/ui/Button";

describe("Button", () => {
  it("renders children", () => { render(<Button>Click</Button>); expect(screen.getByRole("button")).toHaveTextContent("Click"); });
  it("calls onClick", () => { const fn = vi.fn(); render(<Button onClick={fn}>C</Button>); fireEvent.click(screen.getByRole("button")); expect(fn).toHaveBeenCalledOnce(); });
  it("is disabled", () => { render(<Button disabled>D</Button>); expect(screen.getByRole("button")).toBeDisabled(); });
});
