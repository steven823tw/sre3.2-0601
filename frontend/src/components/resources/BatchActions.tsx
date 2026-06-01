
import { Button } from "@/components/ui/Button";
import { ArrowRightLeft, Power, PowerOff, Trash2, X } from "lucide-react";

interface BatchActionsProps {
  selectedCount: number;
  onClearSelection: () => void;
  onMigrate: () => void;
  onShutdown: () => void;
  onBoot: () => void;
  onDelete: () => void;
}

/** Batch operation bar shown when assets are selected */
export function BatchActions({
  selectedCount,
  onClearSelection,
  onMigrate,
  onShutdown,
  onBoot,
  onDelete,
}: BatchActionsProps) {
  if (selectedCount === 0) return null;

  return (
    <div className="flex items-center gap-4 rounded-lg border border-accent/30 bg-accent/10 px-4 py-2.5">
      <span className="text-sm font-medium text-accent">
        {selectedCount} selected
      </span>

      <div className="flex items-center gap-2">
        <Button size="sm" variant="secondary" onClick={onMigrate} aria-label="Migrate selected">
          <ArrowRightLeft className="h-3.5 w-3.5" />
          Migrate
        </Button>
        <Button size="sm" variant="secondary" onClick={onShutdown} aria-label="Shutdown selected">
          <PowerOff className="h-3.5 w-3.5" />
          Shutdown
        </Button>
        <Button size="sm" variant="secondary" onClick={onBoot} aria-label="Boot selected">
          <Power className="h-3.5 w-3.5" />
          Boot
        </Button>
        <Button size="sm" variant="danger" onClick={onDelete} aria-label="Delete selected">
          <Trash2 className="h-3.5 w-3.5" />
          Delete
        </Button>
      </div>

      <button
        onClick={onClearSelection}
        className="ml-auto text-text-secondary hover:text-text-primary"
        aria-label="Clear selection"
      >
        <X className="h-4 w-4" />
      </button>
    </div>
  );
}
