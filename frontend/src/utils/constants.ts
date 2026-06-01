export const SEVERITY_LEVELS = ["P0", "P1", "P2", "P3", "P4"] as const;
export type Severity = (typeof SEVERITY_LEVELS)[number];

export const SEVERITY_CONFIG: Record<Severity, { label: string; bg: string; text: string; border: string; dot: string }> = {
  P0: { label: "Critical", bg: "bg-red-500/15", text: "text-red-400", border: "border-red-500/30", dot: "bg-red-500" },
  P1: { label: "High", bg: "bg-orange-500/15", text: "text-orange-400", border: "border-orange-500/30", dot: "bg-orange-500" },
  P2: { label: "Medium", bg: "bg-yellow-500/15", text: "text-yellow-400", border: "border-yellow-500/30", dot: "bg-yellow-500" },
  P3: { label: "Low", bg: "bg-blue-500/15", text: "text-blue-400", border: "border-blue-500/30", dot: "bg-blue-500" },
  P4: { label: "Info", bg: "bg-gray-500/15", text: "text-gray-400", border: "border-gray-500/30", dot: "bg-gray-400" },
};

export const ASSET_TYPES = ["vm", "physical", "storage"] as const;
export type AssetType = (typeof ASSET_TYPES)[number];

export const ALERT_STATUSES = ["active", "acknowledged", "resolved"] as const;
export type AlertStatus = (typeof ALERT_STATUSES)[number];

export const OPERATION_STATUSES = ["pending", "running", "completed", "failed", "cancelled"] as const;
export type OperationStatus = (typeof OPERATION_STATUSES)[number];

export const PLATFORMS = ["vsphere", "kvm", "fusionsphere", "bare-metal"] as const;
export type PlatformSlug = (typeof PLATFORMS)[number];

export const RISK_LEVELS = ["low", "medium", "high", "critical"] as const;
export type RiskLevel = (typeof RISK_LEVELS)[number];

export const STATUS_COLORS: Record<string, string> = {
  online: "text-success",
  healthy: "text-success",
  active: "text-danger",
  running: "text-info",
  offline: "text-text-secondary",
  warning: "text-warning",
  error: "text-danger",
  critical: "text-danger",
  completed: "text-success",
  failed: "text-danger",
  pending: "text-warning",
  acknowledged: "text-info",
  resolved: "text-success",
  cancelled: "text-text-secondary",
};
