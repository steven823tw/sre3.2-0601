import type { Platform } from "@/utils/constants";

export interface Asset {
  id: string;
  name: string;
  type: "vm" | "physical" | "storage";
  platform: Platform;
  status: "online" | "offline" | "warning" | "error";
  os: string;
  ip: string;
  cluster: string;
  cpu: ResourceMetric;
  memory: ResourceMetric;
  storage: ResourceMetric;
  tags: string[];
  lastSeen: string;
  createdAt: string;
}

export interface ResourceMetric {
  used: number;
  total: number;
  percent: number;
}

export interface AssetListParams {
  type?: string;
  platform?: string;
  status?: string;
  search?: string;
  sort?: string;
  order?: "asc" | "desc";
  page?: number;
  pageSize?: number;
}

export interface AssetListResponse {
  items: Asset[];
  total: number;
  page: number;
  pageSize: number;
}
