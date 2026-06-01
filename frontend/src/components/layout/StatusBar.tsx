/**
 * Status bar displayed at the bottom of the application layout.
 *
 * Shows the current API connection status (with automatic health
 * polling), application version, and platform name. The connection
 * indicator reflects real backend reachability by periodically
 * calling the /health endpoint.
 */
import { useEffect, useState, useRef, useCallback } from "react";
import { Circle, Wifi, WifiOff } from "lucide-react";
import { cn } from "@/utils/cn";

/** Possible connection states for the status indicator. */
type ConnectionStatus = "connected" | "disconnected" | "checking";

/** Health check polling interval in milliseconds. */
const HEALTH_POLL_INTERVAL_MS = 30_000;

/**
 * StatusBar component with live connection status polling.
 * Pings the backend /health endpoint every 30 seconds and
 * displays the result as a colored dot + label.
 */
export function StatusBar() {
  const [status, setStatus] = useState<ConnectionStatus>("checking");
  const [latency, setLatency] = useState<number | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  /**
   * Performs a single health check against the backend.
   * Updates connection status and measures response latency.
   */
  const checkHealth = useCallback(async () => {
    /* Abort any in-flight request before starting a new one. */
    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;

    setStatus("checking");
    const start = performance.now();

    try {
      const response = await fetch("/health", {
        method: "GET",
        signal: controller.signal,
      });
      const elapsed = Math.round(performance.now() - start);

      if (response.ok) {
        setStatus("connected");
        setLatency(elapsed);
      } else {
        setStatus("disconnected");
        setLatency(null);
      }
    } catch {
      /* Network error or timeout — mark as disconnected. */
      setStatus("disconnected");
      setLatency(null);
    }
  }, []);

  /* Poll health endpoint on mount and at regular intervals. */
  useEffect(() => {
    checkHealth();
    const interval = setInterval(checkHealth, HEALTH_POLL_INTERVAL_MS);
    return () => {
      clearInterval(interval);
      abortRef.current?.abort();
    };
  }, [checkHealth]);

  /** Status indicator color and label configuration. */
  const statusConfig = {
    connected: {
      dotColor: "fill-success text-success",
      label: "API Connected",
      icon: Wifi,
      iconClass: "text-success",
    },
    disconnected: {
      dotColor: "fill-danger text-danger",
      label: "API Disconnected",
      icon: WifiOff,
      iconClass: "text-danger",
    },
    checking: {
      dotColor: "fill-warning text-warning animate-pulse-p0",
      label: "Checking...",
      icon: Wifi,
      iconClass: "text-warning",
    },
  };

  const config = statusConfig[status];
  const StatusIcon = config.icon;

  return (
    <footer className="flex h-7 items-center justify-between border-t border-border bg-bg-secondary px-4 text-xs text-text-secondary">
      <div className="flex items-center gap-4">
        {/* Connection status indicator with live polling. */}
        <span className="flex items-center gap-1.5">
          <Circle className={cn("h-2 w-2", config.dotColor)} />
          <StatusIcon className={cn("h-3 w-3", config.iconClass)} />
          <span className={cn(
            "transition-colors",
            status === "connected" && "text-success",
            status === "disconnected" && "text-danger",
            status === "checking" && "text-warning",
          )}>
            {config.label}
          </span>
          {latency !== null && status === "connected" && (
            <span className="text-text-secondary/60">({latency}ms)</span>
          )}
        </span>
        <span className="text-text-secondary/50">v3.1.0</span>
      </div>
      <div className="flex items-center gap-4">
        <span>SRE Engineer Assist Platform</span>
      </div>
    </footer>
  );
}
