import { create } from 'zustand';
import type { MigrationStore } from '@/types/platform';

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
