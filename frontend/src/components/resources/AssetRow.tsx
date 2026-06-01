import { cn } from "@/utils/cn";
import { Badge } from "@/components/ui/Badge";
import { StatusDot } from "@/components/ui/StatusDot";
import type { Asset } from "@/types/asset";

interface AssetRowProps {
  asset: Asset;
  isSelected: boolean;
  onSelect: (id: string) => void;
  onClick: (asset: Asset) => void;
}

const PLATFORM_LABELS: Record<string, string> = {
  vmware: "VMware",
  kvm: "KVM",
  fusioncompute: "FusionCompute",
  "bare-metal": "Bare Metal",
};

/** Single asset row in the resource table */
export function AssetRow({ asset, isSelected, onSelect, onClick }: AssetRowProps) {
  return (
    <tr
      className={cn(
        "border-b border-border transition-all duration-200 ease-in-out cursor-pointer",
        "hover:bg-bg-hover/80",
        isSelected
          ? "border-l-2 border-l-accent bg-accent/10"
          : "border-l-2 border-l-transparent hover:border-l-accent/40",
      )}
      onClick={() => onClick(asset)}
      role="row"
      aria-selected={isSelected}
    >
      {/* Checkbox */}
      <td className="w-10 px-4 py-3" onClick={(e) => e.stopPropagation()}>
        <input
          type="checkbox"
          checked={isSelected}
          onChange={() => onSelect(asset.id)}
          className="h-4 w-4 rounded border-border bg-bg-tertiary text-accent focus:ring-accent/50"
          aria-label={`Select ${asset.name}`}
        />
      </td>

      {/* Name with status dot */}
      <td className="px-4 py-3">
        <div className="flex items-center gap-2">
          <StatusDot status={asset.status} />
          <span className="text-sm font-medium text-text-primary">{asset.name}</span>
        </div>
      </td>

      {/* Platform */}
      <td className="px-4 py-3">
        <span className="text-sm text-text-secondary">{PLATFORM_LABELS[asset.platform] ?? asset.platform}</span>
      </td>

      {/* Status */}
      <td className="px-4 py-3">
        <Badge severity={asset.status === "error" ? "P0" : asset.status === "warning" ? "P2" : undefined}>
          {asset.status}
        </Badge>
      </td>

      {/* CPU */}
      <td className="px-4 py-3">
        <span className={cn("text-sm", asset.cpu.percent >= 80 ? "text-danger" : asset.cpu.percent >= 60 ? "text-warning" : "text-text-primary")}>
          {asset.cpu.percent}%
        </span>
      </td>

      {/* Memory */}
      <td className="px-4 py-3">
        <span className={cn("text-sm", asset.memory.percent >= 80 ? "text-danger" : asset.memory.percent >= 60 ? "text-warning" : "text-text-primary")}>
          {asset.memory.percent}%
        </span>
      </td>

      {/* IP */}
      <td className="px-4 py-3">
        <span className="font-mono text-sm text-text-secondary">{asset.ip}</span>
      </td>
    </tr>
  );
}
