/**
 * Application sidebar with responsive behavior.
 *
 * On desktop (>=768px): shows a collapsible sidebar (expanded or icon-only).
 * On mobile (<768px): hidden by default; opens as a full-height overlay with
 * a backdrop when triggered. Automatically closes on route change or backdrop click.
 *
 * The sidebar state is managed via the global UI store (useUIStore).
 */
import { useEffect, useCallback, useState } from "react";
import { NavLink, useLocation } from "react-router-dom";
import { cn } from "@/utils/cn";
import { useUIStore } from "@/stores/uiStore";
import {
  LayoutDashboard,
  Server,
  Bell,
  Terminal,
  MessageSquare,
  ChevronLeft,
  ChevronRight,
  Menu,
  X,
} from "lucide-react";

/** Navigation items rendered in the sidebar. */
const navItems = [
  { path: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { path: "/resources", label: "Resources", icon: Server },
  { path: "/alerts", label: "Alerts", icon: Bell },
  { path: "/operations", label: "Operations", icon: Terminal },
  { path: "/chat", label: "Engineer Assist", icon: MessageSquare },
];

/** Breakpoint for mobile detection (matches Tailwind md: 768px). */
const MOBILE_BREAKPOINT = 768;

/**
 * Sidebar component with desktop collapse and mobile overlay behavior.
 */
export function Sidebar() {
  const { sidebarCollapsed, toggleSidebar, setSidebarCollapsed } = useUIStore();
  const location = useLocation();
  const isMobile = useIsMobile();

  /**
   * On mobile: auto-collapse sidebar when the route changes so the
   * overlay closes after navigation.
   */
  useEffect(() => {
    if (isMobile) {
      setSidebarCollapsed(true);
    }
  }, [location.pathname, isMobile, setSidebarCollapsed]);

  /**
   * On mobile: close sidebar when the backdrop overlay is clicked.
   */
  const handleBackdropClick = useCallback(() => {
    if (isMobile) {
      setSidebarCollapsed(true);
    }
  }, [isMobile, setSidebarCollapsed]);

  /**
   * On resize: auto-collapse sidebar when viewport shrinks below
   * the mobile breakpoint.
   */
  useEffect(() => {
    const handleResize = () => {
      if (window.innerWidth < MOBILE_BREAKPOINT) {
        setSidebarCollapsed(true);
      }
    };
    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, [setSidebarCollapsed]);

  /* On mobile, "collapsed" means hidden; "expanded" means overlay open. */
  const sidebarVisible = isMobile ? !sidebarCollapsed : true;
  const sidebarExpanded = isMobile ? true : !sidebarCollapsed;

  return (
    <>
      {/* Mobile hamburger toggle button — visible only when sidebar is hidden. */}
      {isMobile && sidebarCollapsed && (
        <button
          onClick={toggleSidebar}
          className="fixed left-3 top-3 z-[60] rounded-lg bg-bg-secondary p-2 text-text-secondary hover:text-text-primary border border-border shadow-lg"
          aria-label="Open navigation menu"
        >
          <Menu className="h-5 w-5" />
        </button>
      )}

      {/* Backdrop overlay for mobile — fades in when sidebar is open. */}
      {isMobile && !sidebarCollapsed && (
        <div
          className="fixed inset-0 z-[70] bg-black/50 animate-fade-in"
          onClick={handleBackdropClick}
          aria-hidden="true"
        />
      )}

      {/* Sidebar panel. */}
      <aside
        className={cn(
          "flex h-full flex-col border-r border-border bg-bg-secondary transition-all duration-200",
          /* Desktop sizing */
          !isMobile && (sidebarCollapsed ? "w-16" : "w-56"),
          /* Mobile: fixed overlay panel. */
          isMobile && "fixed inset-y-0 left-0 z-[80] w-64",
          isMobile && sidebarVisible ? "translate-x-0" : "",
          isMobile && !sidebarVisible ? "-translate-x-full" : "",
          !isMobile ? "" : "transition-transform duration-200"
        )}
      >
        {/* Header area with brand and close button. */}
        <div className="flex h-14 items-center justify-between border-b border-border px-4">
          {sidebarExpanded ? (
            <span className="text-lg font-bold text-accent">SRE Assist</span>
          ) : (
            <span className="text-lg font-bold text-accent">SA</span>
          )}
          {/* Close button visible only on mobile overlay. */}
          {isMobile && (
            <button
              onClick={handleBackdropClick}
              className="rounded-lg p-1 text-text-secondary hover:text-text-primary"
              aria-label="Close navigation menu"
            >
              <X className="h-5 w-5" />
            </button>
          )}
        </div>

        {/* Navigation links. */}
        <nav className="flex-1 space-y-1 p-2">
          {navItems.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) =>
                cn(
                  "relative flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
                  isActive
                    ? "bg-accent/15 text-accent"
                    : "text-text-secondary hover:text-text-primary hover:bg-bg-hover"
                )
              }
              aria-label={item.label}
            >
              {({ isActive }) => (
                <>
                  {isActive && (
                    <span className="absolute left-0 h-5 w-0.5 rounded-r-full bg-accent" />
                  )}
                  <item.icon className="h-5 w-5 shrink-0" />
                  {sidebarExpanded && <span>{item.label}</span>}
                </>
              )}
            </NavLink>
          ))}
        </nav>

        {/* Collapse/expand toggle (desktop only). */}
        {!isMobile && (
          <div className="border-t border-border p-2">
            <button
              onClick={toggleSidebar}
              className="flex w-full items-center justify-center rounded-lg p-2 text-text-secondary hover:text-text-primary hover:bg-bg-hover"
              aria-label={sidebarCollapsed ? "Expand sidebar" : "Collapse sidebar"}
            >
              {sidebarCollapsed ? (
                <ChevronRight className="h-5 w-5" />
              ) : (
                <ChevronLeft className="h-5 w-5" />
              )}
            </button>
          </div>
        )}
      </aside>
    </>
  );
}

/**
 * Custom hook that tracks whether the viewport is below the mobile breakpoint.
 * Returns true when the screen width < 768px.
 */
function useIsMobile(): boolean {
  const [isMobile, setIsMobile] = useState(
    typeof window !== "undefined" && window.innerWidth < MOBILE_BREAKPOINT
  );

  useEffect(() => {
    const mql = window.matchMedia(`(max-width: ${MOBILE_BREAKPOINT - 1}px)`);
    const handler = (e: MediaQueryListEvent) => setIsMobile(e.matches);
    mql.addEventListener("change", handler);
    setIsMobile(mql.matches);
    return () => mql.removeEventListener("change", handler);
  }, []);

  return isMobile;
}
