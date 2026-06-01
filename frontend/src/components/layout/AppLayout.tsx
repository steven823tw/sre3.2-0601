import { Outlet, useNavigate } from "react-router-dom";
import { Sidebar } from "./Sidebar";
import { Header } from "./Header";
import { StatusBar } from "./StatusBar";
import { ToastContainer } from "@/components/ui/Toast";
import { CommandPalette } from "@/components/ui/CommandPalette";
import { useKeyboard } from "@/hooks/useKeyboard";
import { useUIStore } from "@/stores/uiStore";

export function AppLayout() {
  useKeyboard();
  const navigate = useNavigate();
  const { activeModal, closeModal } = useUIStore();

  return (
    <div className="flex h-screen overflow-hidden bg-bg-primary">
      <Sidebar />
      <div className="flex flex-1 flex-col overflow-hidden">
        <Header />
        <main className="flex-1 overflow-auto p-4">
          <Outlet />
        </main>
        <StatusBar />
      </div>
      <ToastContainer />
      <CommandPalette
        isOpen={activeModal === "search"}
        onClose={closeModal}
        onNavigate={navigate}
      />
    </div>
  );
}
