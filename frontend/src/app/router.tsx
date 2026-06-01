import { createBrowserRouter, Navigate } from "react-router-dom";
import { AppLayout } from "@/components/layout/AppLayout";
import { ChatView } from "@/components/chat/ChatView";
import { DashboardView } from "@/components/dashboard/DashboardView";
import { ResourcesView } from "@/components/resources/ResourcesView";
import { AlertsView } from "@/components/alerts/AlertsView";
import { OperationsView } from "@/components/operations/OperationsView";

export const router = createBrowserRouter([
  {
    path: "/",
    element: <AppLayout />,
    children: [
      { index: true, element: <Navigate to="/chat" replace /> },
      { path: "chat", element: <ChatView /> },
      { path: "dashboard", element: <DashboardView /> },
      { path: "resources", element: <ResourcesView /> },
      { path: "alerts", element: <AlertsView /> },
      { path: "operations", element: <OperationsView /> },
    ],
  },
]);
