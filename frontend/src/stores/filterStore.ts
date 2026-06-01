import { create } from "zustand";
import type { Severity, AlertStatus } from "@/utils/constants";

interface FilterState {
  assetType: string;
  assetPlatform: string;
  assetStatus: string;
  assetSearch: string;
  alertSeverity: Severity | "";
  alertStatus: AlertStatus | "";
  alertSearch: string;
  setAssetType: (type: string) => void;
  setAssetPlatform: (platform: string) => void;
  setAssetStatus: (status: string) => void;
  setAssetSearch: (search: string) => void;
  setAlertSeverity: (severity: Severity | "") => void;
  setAlertStatus: (status: AlertStatus | "") => void;
  setAlertSearch: (search: string) => void;
  resetAssetFilters: () => void;
  resetAlertFilters: () => void;
}

export const useFilterStore = create<FilterState>((set) => ({
  assetType: "",
  assetPlatform: "",
  assetStatus: "",
  assetSearch: "",
  alertSeverity: "",
  alertStatus: "",
  alertSearch: "",
  setAssetType: (assetType) => set({ assetType }),
  setAssetPlatform: (assetPlatform) => set({ assetPlatform }),
  setAssetStatus: (assetStatus) => set({ assetStatus }),
  setAssetSearch: (assetSearch) => set({ assetSearch }),
  setAlertSeverity: (alertSeverity) => set({ alertSeverity }),
  setAlertStatus: (alertStatus) => set({ alertStatus }),
  setAlertSearch: (alertSearch) => set({ alertSearch }),
  resetAssetFilters: () => set({ assetType: "", assetPlatform: "", assetStatus: "", assetSearch: "" }),
  resetAlertFilters: () => set({ alertSeverity: "", alertStatus: "", alertSearch: "" }),
}));
