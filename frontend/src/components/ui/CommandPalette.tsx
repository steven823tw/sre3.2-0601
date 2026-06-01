import { useState, useEffect, useRef, useCallback } from "react";
import { cn } from "@/utils/cn";
import { Search, Server, Bell, MessageSquare, LayoutDashboard } from "lucide-react";

/**
 * Command Palette — Ctrl+K global search
 *
 * Provides quick access to:
 * - Navigation (go to pages)
 * - Resource search (VMs, hosts, storage)
 * - Quick actions (run commands)
 */

interface CommandItem {
  id: string;
  label: string;
  description: string;
  icon: React.ReactNode;
  action: () => void;
  category: "navigation" | "resource" | "action";
}

interface CommandPaletteProps {
  isOpen: boolean;
  onClose: () => void;
  onNavigate: (path: string) => void;
}

export function CommandPalette({ isOpen, onClose, onNavigate }: CommandPaletteProps) {
  const [query, setQuery] = useState("");
  const [selectedIndex, setSelectedIndex] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);
  const listRef = useRef<HTMLDivElement>(null);

  // Define available commands
  const commands: CommandItem[] = [
    {
      id: "nav-chat",
      label: "Go to Chat",
      description: "AI Agent chat interface",
      icon: <MessageSquare size={16} />,
      action: () => { onNavigate("/chat"); onClose(); },
      category: "navigation",
    },
    {
      id: "nav-dashboard",
      label: "Go to Dashboard",
      description: "System overview and metrics",
      icon: <LayoutDashboard size={16} />,
      action: () => { onNavigate("/dashboard"); onClose(); },
      category: "navigation",
    },
    {
      id: "nav-resources",
      label: "Go to Resources",
      description: "Manage VMs, hosts, storage",
      icon: <Server size={16} />,
      action: () => { onNavigate("/resources"); onClose(); },
      category: "navigation",
    },
    {
      id: "nav-alerts",
      label: "Go to Alerts",
      description: "View and manage alerts",
      icon: <Bell size={16} />,
      action: () => { onNavigate("/alerts"); onClose(); },
      category: "navigation",
    },
    {
      id: "action-diagnose",
      label: "Diagnose Issue",
      description: "Start diagnostic workflow",
      icon: <Search size={16} />,
      action: () => { onNavigate("/chat"); onClose(); },
      category: "action",
    },
  ];

  // Filter commands based on query
  const filteredCommands = commands.filter(
    (cmd) =>
      cmd.label.toLowerCase().includes(query.toLowerCase()) ||
      cmd.description.toLowerCase().includes(query.toLowerCase())
  );

  // Group by category
  const groupedCommands = filteredCommands.reduce(
    (acc, cmd) => {
      if (!acc[cmd.category]) acc[cmd.category] = [];
      acc[cmd.category]!.push(cmd);
      return acc;
    },
    {} as Record<string, CommandItem[]>
  );

  // Focus input when opened
  useEffect(() => {
    if (isOpen) {
      setQuery("");
      setSelectedIndex(0);
      setTimeout(() => inputRef.current?.focus(), 50);
    }
  }, [isOpen]);

  // Keyboard navigation
  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      switch (e.key) {
        case "ArrowDown":
          e.preventDefault();
          setSelectedIndex((prev) => Math.min(prev + 1, filteredCommands.length - 1));
          break;
        case "ArrowUp":
          e.preventDefault();
          setSelectedIndex((prev) => Math.max(prev - 1, 0));
          break;
        case "Enter":
          e.preventDefault();
          filteredCommands[selectedIndex]?.action();
          break;
        case "Escape":
          e.preventDefault();
          onClose();
          break;
      }
    },
    [filteredCommands, selectedIndex, onClose]
  );

  // Scroll selected item into view
  useEffect(() => {
    const list = listRef.current;
    if (list) {
      const selected = list.children[selectedIndex] as HTMLElement;
      selected?.scrollIntoView({ block: "nearest" });
    }
  }, [selectedIndex]);

  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-start justify-center pt-[20vh]"
      onClick={onClose}
    >
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/50 backdrop-blur-sm" />

      {/* Dialog */}
      <div
        className={cn(
          "relative w-full max-w-lg rounded-xl border border-border bg-bg-secondary shadow-2xl",
          "animate-in fade-in zoom-in-95 duration-200"
        )}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Search input */}
        <div className="flex items-center gap-3 border-b border-border px-4 py-3">
          <Search size={18} className="text-text-secondary" />
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={(e) => { setQuery(e.target.value); setSelectedIndex(0); }}
            onKeyDown={handleKeyDown}
            placeholder="Search commands, resources, pages..."
            className="flex-1 bg-transparent text-sm text-text-primary outline-none placeholder:text-text-secondary"
          />
          <kbd className="rounded border border-border bg-bg-tertiary px-1.5 py-0.5 text-[10px] text-text-secondary">
            ESC
          </kbd>
        </div>

        {/* Command list */}
        <div ref={listRef} className="max-h-80 overflow-y-auto p-2">
          {Object.entries(groupedCommands).map(([category, items]) => (
            <div key={category} className="mb-2">
              <div className="px-2 py-1 text-[10px] font-semibold uppercase tracking-wider text-text-secondary">
                {category}
              </div>
              {items.map((cmd) => {
                const globalIndex = filteredCommands.indexOf(cmd);
                return (
                  <button
                    key={cmd.id}
                    className={cn(
                      "flex w-full items-center gap-3 rounded-lg px-3 py-2 text-left text-sm transition-colors",
                      globalIndex === selectedIndex
                        ? "bg-accent/10 text-accent"
                        : "text-text-primary hover:bg-bg-tertiary"
                    )}
                    onClick={cmd.action}
                    onMouseEnter={() => setSelectedIndex(globalIndex)}
                  >
                    <span className="flex-shrink-0 text-text-secondary">{cmd.icon}</span>
                    <div className="flex-1 min-w-0">
                      <div className="font-medium">{cmd.label}</div>
                      <div className="text-xs text-text-secondary truncate">{cmd.description}</div>
                    </div>
                  </button>
                );
              })}
            </div>
          ))}

          {filteredCommands.length === 0 && (
            <div className="px-3 py-8 text-center text-sm text-text-secondary">
              No results found for &quot;{query}&quot;
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between border-t border-border px-4 py-2 text-[10px] text-text-secondary">
          <div className="flex items-center gap-2">
            <span>↑↓ Navigate</span>
            <span>↵ Select</span>
            <span>ESC Close</span>
          </div>
          <span>{filteredCommands.length} results</span>
        </div>
      </div>
    </div>
  );
}
