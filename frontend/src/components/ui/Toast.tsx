/**
 * Toast notification system with auto-dismiss, progress bar, and pause-on-hover.
 *
 * Renders a fixed-position container in the bottom-right corner.
 * Each toast displays an icon, message, dismiss button, and a visual
 * progress bar that counts down the auto-dismiss timer.
 * Hovering a toast pauses the countdown; leaving resumes it.
 */
import { useEffect, useRef, useState, useCallback } from "react";
import { cn } from "@/utils/cn";
import { useUIStore } from "@/stores/uiStore";
import { CheckCircle, XCircle, AlertTriangle, Info, X } from "lucide-react";

/** Icon component lookup by toast severity type. */
const icons = {
  success: CheckCircle,
  error: XCircle,
  warning: AlertTriangle,
  info: Info,
};

/** Tailwind class map for each toast severity. */
const colors = {
  success: "border-success/30 bg-success/10 text-success",
  error: "border-danger/30 bg-danger/10 text-danger",
  warning: "border-warning/30 bg-warning/10 text-warning",
  info: "border-info/30 bg-info/10 text-info",
};

/** Progress bar color classes matching toast severity. */
const progressColors = {
  success: "bg-success/40",
  error: "bg-danger/40",
  warning: "bg-warning/40",
  info: "bg-info/40",
};

/** Default auto-dismiss duration in milliseconds. */
const AUTO_DISMISS_MS = 5000;

/**
 * Container that renders all active toasts from the UI store.
 * Positioned fixed at the bottom-right of the viewport.
 */
export function ToastContainer() {
  const { toasts, removeToast } = useUIStore();

  return (
    <div
      className="fixed bottom-4 right-4 z-[100] flex flex-col gap-2 max-w-sm w-full"
      aria-live="polite"
      role="region"
      aria-label="Notifications"
    >
      {toasts.map((toast) => (
        <ToastItem
          key={toast.id}
          {...toast}
          onClose={() => removeToast(toast.id)}
        />
      ))}
    </div>
  );
}

/** Props for an individual toast item. */
interface ToastItemProps {
  type: "success" | "error" | "warning" | "info";
  message: string;
  onClose: () => void;
}

/**
 * Single toast notification with auto-dismiss, progress indicator, and
 * pause-on-hover behavior.
 */
function ToastItem({ type, message, onClose }: ToastItemProps) {
  const Icon = icons[type];
  const [progress, setProgress] = useState(100);
  const [isHovered, setIsHovered] = useState(false);
  const startTimeRef = useRef(Date.now());
  const remainingRef = useRef(AUTO_DISMISS_MS);
  const animFrameRef = useRef<number>(0);

  /**
   * Updates the progress bar on each animation frame.
   * When progress reaches 0, the toast is dismissed.
   */
  const tick = useCallback(() => {
    if (isHovered) return;

    const elapsed = Date.now() - startTimeRef.current;
    const pct = Math.max(0, 100 - (elapsed / remainingRef.current) * 100);
    setProgress(pct);

    if (pct <= 0) {
      onClose();
      return;
    }
    animFrameRef.current = requestAnimationFrame(tick);
  }, [isHovered, onClose]);

  /* Start or resume the countdown timer. */
  useEffect(() => {
    if (isHovered) {
      /* Pause: capture remaining time and cancel animation frame. */
      const elapsed = Date.now() - startTimeRef.current;
      remainingRef.current = Math.max(0, remainingRef.current - elapsed);
      cancelAnimationFrame(animFrameRef.current);
      return;
    }

    /* Resume: reset start time and begin animation loop. */
    startTimeRef.current = Date.now();
    animFrameRef.current = requestAnimationFrame(tick);

    return () => cancelAnimationFrame(animFrameRef.current);
  }, [isHovered, tick]);

  return (
    <div
      className={cn(
        "relative flex items-center gap-3 rounded-lg border px-4 py-3 shadow-lg",
        "animate-slide-up overflow-hidden",
        colors[type]
      )}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      role="alert"
    >
      <Icon className="h-5 w-5 shrink-0" />
      <p className="text-sm flex-1">{message}</p>
      <button
        onClick={onClose}
        className="ml-auto shrink-0 opacity-70 hover:opacity-100 transition-opacity"
        aria-label="Dismiss notification"
      >
        <X className="h-4 w-4" />
      </button>

      {/* Auto-dismiss progress bar at the bottom edge. */}
      <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-bg-tertiary">
        <div
          className={cn("h-full transition-none", progressColors[type])}
          style={{ width: `${progress}%` }}
        />
      </div>
    </div>
  );
}
