import { httpClient } from "./client";
import type { Asset, AssetListParams, AssetListResponse } from "@/types/asset";

export async function getAssets(params?: AssetListParams): Promise<AssetListResponse> {
  return httpClient.get<AssetListResponse>("/assets", params as Record<string, string | number | boolean | undefined>);
}

export async function getAssetById(id: string): Promise<Asset> {
  return httpClient.get<Asset>(`/assets/${id}`);
}
