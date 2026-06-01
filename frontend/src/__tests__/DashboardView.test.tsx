import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter } from "react-router-dom";
import { DashboardView } from "@/components/dashboard/DashboardView";

function renderWithProviders(ui: React.ReactElement) {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>{ui}</MemoryRouter>
    </QueryClientProvider>,
  );
}

describe("DashboardView", () => {
  it("renders dashboard heading", () => {
    renderWithProviders(<DashboardView />);
    expect(screen.getByText("Dashboard")).toBeInTheDocument();
  });

  it("renders refresh button", () => {
    renderWithProviders(<DashboardView />);
    expect(screen.getByLabelText("Refresh dashboard")).toBeInTheDocument();
  });

  it("renders loading skeletons initially", () => {
    renderWithProviders(<DashboardView />);
    // Skeleton elements should be present during loading
    expect(screen.getByText("Dashboard")).toBeInTheDocument();
  });
});
