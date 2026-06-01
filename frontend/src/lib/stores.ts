/**
 * Re-export stores from their canonical locations in stores/ directory.
 * Kept for backward compatibility — prefer importing from @/stores/* directly.
 */
export { usePlatformStore } from '@/stores/platformStore';
export { useMigrationStore } from '@/stores/migrationStore';
