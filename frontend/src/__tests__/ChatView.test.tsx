import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter } from "react-router-dom";
import { ChatView } from "@/components/chat/ChatView";

function renderWithProviders(ui: React.ReactElement) {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>{ui}</MemoryRouter>
    </QueryClientProvider>,
  );
}

describe("ChatView", () => {
  it("renders welcome message and quick actions", () => {
    renderWithProviders(<ChatView />);
    expect(screen.getByText("SRE Engineer Assistant")).toBeInTheDocument();
    expect(screen.getByText("View Clusters")).toBeInTheDocument();
    expect(screen.getByText("View Alerts")).toBeInTheDocument();
  });

  it("renders message input", () => {
    renderWithProviders(<ChatView />);
    expect(screen.getByLabelText("Chat message input")).toBeInTheDocument();
  });

  it("renders send button", () => {
    renderWithProviders(<ChatView />);
    expect(screen.getByLabelText("Send message")).toBeInTheDocument();
  });

  it("allows typing in the input", async () => {
    const user = userEvent.setup();
    renderWithProviders(<ChatView />);
    const input = screen.getByLabelText("Chat message input");
    await user.type(input, "test message");
    expect(input).toHaveValue("test message");
  });
});
