import { create } from 'zustand';
import type { Platform, PlatformStore, MigrationStore } from '../types/platform';

/**
 * Platform management store
 */
export const usePlatformStore = create<PlatformStore>((set) => ({
  platforms: [],
  selectedPlatform: null,
  wizardOpen: false,
  importDialogOpen: false,
  setPlatforms: (platforms: Platform[]) => set({ platforms }),
  setSelectedPlatform: (platform: Platform | null) =>
    set({ selectedPlatform: platform }),
  setWizardOpen: (open: boolean) => set({ wizardOpen: open }),
  setImportDialogOpen: (open: boolean) => set({ importDialogOpen: open }),
}));

/**
 * Migration store
 */
export const useMigrationStore = create<MigrationStore>((set) => ({
  selectedVM: null,
  targetPlatform: null,
  currentPlan: null,
  execution: null,
  setSelectedVM: (vm) => set({ selectedVM: vm }),
  setTargetPlatform: (platform) => set({ targetPlatform: platform }),
  setCurrentPlan: (plan) => set({ currentPlan: plan }),
  setExecution: (execution) => set({ execution }),
  reset: () =>
    set({
      selectedVM: null,
      targetPlatform: null,
      currentPlan: null,
      execution: null,
    }),
}));
