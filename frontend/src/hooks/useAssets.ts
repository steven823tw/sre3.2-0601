import { useQuery } from "@tanstack/react-query";
import { getAssets, getAssetById } from "@/api/assets";
import type { AssetListParams } from "@/types/asset";

export function useAssets(params?: AssetListParams) {
  return useQuery({
    queryKey: ["assets", params],
    queryFn: () => getAssets(params),
  });
}

export function useAsset(id: string) {
  return useQuery({
    queryKey: ["assets", id],
    queryFn: () => getAssetById(id),
    enabled: !!id,
  });
}
