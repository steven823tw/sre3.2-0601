import { cn } from "@/utils/cn";
import { Modal } from "@/components/ui/Modal";
import { Button } from "@/components/ui/Button";
import { AlertTriangle } from "lucide-react";
import type { RiskLevel } from "@/utils/constants";

interface ConfirmDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  title: string;
  description: string;
  risk: RiskLevel;
  parameters?: Record<string, string>;
}

const RISK_STYLES: Record<RiskLevel, { bg: string; text: string; label: string }> = {
  low: { bg: "bg-green-500/15", text: "text-green-400", label: "Low Risk" },
  medium: { bg: "bg-yellow-500/15", text: "text-yellow-400", label: "Medium Risk" },
  high: { bg: "bg-orange-500/15", text: "text-orange-400", label: "High Risk" },
  critical: { bg: "bg-red-500/15", text: "text-red-400", label: "Critical Risk" },
};

/** Confirmation modal for operations with risk level warning */
export function ConfirmDialog({ isOpen, onClose, onConfirm, title, description, risk, parameters }: ConfirmDialogProps) {
  const riskStyle = RISK_STYLES[risk];

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Confirm Operation" size="md">
      <div className="space-y-4">
        {/* Risk warning */}
        <div className={cn("flex items-center gap-3 rounded-lg p-3", riskStyle.bg)}>
          <AlertTriangle className={cn("h-5 w-5 shrink-0", riskStyle.text)} />
          <span className={cn("text-sm font-medium", riskStyle.text)}>{riskStyle.label}</span>
        </div>

        {/* Operation details */}
        <div>
          <h3 className="text-sm font-semibold text-text-primary">{title}</h3>
          <p className="mt-1 text-sm text-text-secondary">{description}</p>
        </div>

        {/* Parameter summary */}
        {parameters && Object.keys(parameters).length > 0 && (
          <div className="rounded-lg border border-border bg-bg-primary/50 p-3">
            <h4 className="mb-2 text-xs font-medium text-text-secondary uppercase tracking-wider">Parameters</h4>
            <dl className="space-y-1">
              {Object.entries(parameters).map(([key, value]) => (
                <div key={key} className="flex justify-between text-sm">
                  <dt className="text-text-secondary">{key}</dt>
                  <dd className="font-mono text-text-primary">{value}</dd>
                </div>
              ))}
            </dl>
          </div>
        )}

        {/* Actions */}
        <div className="flex justify-end gap-2 pt-2">
          <Button variant="secondary" onClick={onClose} aria-label="Cancel operation">
            Cancel
          </Button>
          <Button variant="danger" onClick={onConfirm} aria-label="Confirm operation">
            Confirm
          </Button>
        </div>
      </div>
    </Modal>
  );
}
