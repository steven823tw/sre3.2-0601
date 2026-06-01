import { httpClient } from "./client";
import type { ChatRequest, ChatResponse } from "@/types/chat";

export async function sendMessage(request: ChatRequest): Promise<ChatResponse> {
  return httpClient.post<ChatResponse>("/chat/messages", request);
}
