import { Search, Bell } from "lucide-react";
import { useUIStore } from "@/stores/uiStore";

export function Header() {
  const { openModal } = useUIStore();

  return (
    <header className="flex h-14 items-center justify-between border-b border-border bg-bg-secondary px-4">
      <button
        onClick={() => openModal("search")}
        className="flex items-center gap-2 rounded-lg border border-border bg-bg-tertiary px-3 py-1.5 text-sm text-text-secondary hover:text-text-primary hover:border-accent/50 transition-colors w-80"
        aria-label="Open search (Ctrl+K)"
      >
        <Search className="h-4 w-4" />
        <span>Search resources, alerts...</span>
        <kbd className="ml-auto rounded border border-border bg-bg-primary px-1.5 py-0.5 text-xs">Ctrl+K</kbd>
      </button>
      <div className="flex items-center gap-3">
        <button className="relative rounded-lg p-2 text-text-secondary hover:text-text-primary hover:bg-bg-hover" aria-label="Notifications">
          <Bell className="h-5 w-5" />
          <span className="absolute right-1 top-1 h-2 w-2 rounded-full bg-danger" />
        </button>
      </div>
    </header>
  );
}
