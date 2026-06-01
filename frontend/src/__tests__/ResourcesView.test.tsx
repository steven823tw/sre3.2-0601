import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter } from "react-router-dom";
import { ResourcesView } from "@/components/resources/ResourcesView";

function renderWithProviders(ui: React.ReactElement) {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>{ui}</MemoryRouter>
    </QueryClientProvider>,
  );
}

describe("ResourcesView", () => {
  it("renders resources heading", () => {
    renderWithProviders(<ResourcesView />);
    expect(screen.getByText("Resources")).toBeInTheDocument();
  });

  it("renders type tabs", () => {
    renderWithProviders(<ResourcesView />);
    expect(screen.getByText("Virtual Machines")).toBeInTheDocument();
    expect(screen.getByText("Physical Hosts")).toBeInTheDocument();
    expect(screen.getByText("Storage")).toBeInTheDocument();
  });

  it("renders search input", () => {
    renderWithProviders(<ResourcesView />);
    expect(screen.getByLabelText("Search assets")).toBeInTheDocument();
  });
});
