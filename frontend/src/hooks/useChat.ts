import { useMutation } from "@tanstack/react-query";
import { sendMessage } from "@/api/chat";
import { useChatStore } from "@/stores/chatStore";
import type { ChatMessage } from "@/types/chat";
import { useCallback } from "react";

export function useChat() {
  const { messages, isLoading, addMessage, setLoading, setSessionId } = useChatStore();

  const mutation = useMutation({
    mutationFn: sendMessage,
    onMutate: (variables) => {
      const userMsg: ChatMessage = {
        id: `msg-user-${Date.now()}`,
        role: "user",
        content: variables.message,
        timestamp: new Date().toISOString(),
      };
      addMessage(userMsg);
      setLoading(true);
    },
    onSuccess: (data) => {
      addMessage(data.message);
      setSessionId(data.sessionId);
      setLoading(false);
    },
    onError: (error: Error) => {
      const errorMsg: ChatMessage = {
        id: `msg-error-${Date.now()}`,
        role: "assistant",
        content: `⚠️ 请求失败: ${error.message || "网络错误，请重试"}`,
        timestamp: new Date().toISOString(),
      };
      addMessage(errorMsg);
      setLoading(false);
    },
  });

  const send = useCallback(
    (message: string) => {
      mutation.mutate({ message });
    },
    [mutation]
  );

  return { messages, isLoading, send, addMessage };
}
