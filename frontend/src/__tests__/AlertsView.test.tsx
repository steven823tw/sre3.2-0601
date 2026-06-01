import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter } from "react-router-dom";
import { AlertsView } from "@/components/alerts/AlertsView";

function renderWithProviders(ui: React.ReactElement) {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>{ui}</MemoryRouter>
    </QueryClientProvider>,
  );
}

describe("AlertsView", () => {
  it("renders alerts heading", () => {
    renderWithProviders(<AlertsView />);
    expect(screen.getByText("Alerts")).toBeInTheDocument();
  });

  it("renders severity tabs", () => {
    renderWithProviders(<AlertsView />);
    expect(screen.getByText("All")).toBeInTheDocument();
    expect(screen.getByText("P0")).toBeInTheDocument();
    expect(screen.getByText("P1")).toBeInTheDocument();
  });

  it("renders search input", () => {
    renderWithProviders(<AlertsView />);
    expect(screen.getByLabelText("Search alerts")).toBeInTheDocument();
  });
});
