import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { AlertFilters } from "@/components/alerts/AlertFilters";

function renderWithProviders(ui: React.ReactElement) {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>,
  );
}

describe("AlertFilters", () => {
  it("renders search input", () => {
    renderWithProviders(<AlertFilters />);
    expect(screen.getByLabelText("Search alerts")).toBeInTheDocument();
  });

  it("renders status filter", () => {
    renderWithProviders(<AlertFilters />);
    expect(screen.getByLabelText("Filter by status")).toBeInTheDocument();
  });
});
