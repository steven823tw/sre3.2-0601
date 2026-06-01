import { create } from 'zustand';
import type { Platform, PlatformStore } from '@/types/platform';

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
