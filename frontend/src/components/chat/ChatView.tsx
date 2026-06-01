import { useState, useRef, useEffect, useCallback } from "react";
import { cn } from "@/utils/cn";
import { useChat } from "@/hooks/useChat";
import { MessageBubble } from "./MessageBubble";
import { QuickActions } from "./QuickActions";
import { RecommendationCard } from "./RecommendationCard";
import { StepProgress } from "./StepProgress";
import { ConfirmDialog } from "./ConfirmDialog";

import { Send, Sparkles } from "lucide-react";

/** Main chat interface with message list, input, and recommendation display */
export function ChatView() {
  const { messages, isLoading, send, addMessage } = useChat();
  const [input, setInput] = useState("");
  const [confirmOpen, setConfirmOpen] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    try {
      messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    } catch {
      // JSDOM doesn't implement scrollIntoView
    }
  }, [messages]);

  // Auto-resize textarea
  useEffect(() => {
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = "auto";
      textarea.style.height = `${Math.min(textarea.scrollHeight, 160)}px`;
    }
  }, [input]);

  const handleSend = useCallback(() => {
    const trimmed = input.trim();
    if (!trimmed || isLoading) return;
    send(trimmed);
    setInput("");
  }, [input, isLoading, send]);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        handleSend();
      }
    },
    [handleSend],
  );

  const handleQuickAction = useCallback(
    (message: string) => {
      send(message);
    },
    [send],
  );

  // Get the last assistant message with recommendations (must be before callbacks that use it)
  const lastAssistantWithRecs = [...messages]
    .reverse()
    .find((m) => m.role === "assistant" && m.recommendations && m.recommendations.length > 0);

  const lastOperation = [...messages]
    .reverse()
    .find((m) => m.role === "assistant" && m.operation);

  const handleExecuteAll = useCallback(() => {
    setConfirmOpen(true);
  }, []);

  const handleExecuteSelected = useCallback((_ids: string[]) => {
    setConfirmOpen(true);
  }, []);

  const handleConfirmExecute = useCallback(async () => {
    setConfirmOpen(false);
    if (!lastAssistantWithRecs?.recommendations) return;

    try {
      // Call backend to create operation
      const response = await fetch('/api/v1/operations', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title: `AI 推荐操作: ${lastAssistantWithRecs.intent || 'diagnose'}`,
          description: lastAssistantWithRecs.content,
          steps: lastAssistantWithRecs.recommendations.map((rec, i) => ({
            step_number: i + 1,
            action: rec.action,
            description: rec.description,
            params: rec.params || {},
          })),
        }),
      });

      const result = await response.json();
      if (result.success) {
        // Add success message to chat
        addMessage({
          id: `msg-ops-${Date.now()}`,
          role: 'assistant',
          content: `✅ 操作已创建，工单编号: ${result.data?.id || 'N/A'}`,
          timestamp: new Date().toISOString(),
        });
      } else {
        addMessage({
          id: `msg-err-${Date.now()}`,
          role: 'assistant',
          content: `❌ 操作创建失败: ${result.error?.message || '未知错误'}`,
          timestamp: new Date().toISOString(),
        });
      }
    } catch (error) {
      addMessage({
        id: `msg-err-${Date.now()}`,
        role: 'assistant',
        content: `❌ 操作创建失败: 网络错误`,
        timestamp: new Date().toISOString(),
      });
    }
  }, [lastAssistantWithRecs, addMessage]);

  return (
    <div className="flex h-full flex-col">
      {/* Message area */}
      <div className="flex-1 overflow-y-auto px-4 py-6">
        <div className="mx-auto max-w-3xl space-y-4">
          {messages.length === 0 ? (
            /* Welcome screen */
            <div className="flex flex-col items-center justify-center py-12">
              <div className="rounded-2xl border border-accent/20 bg-gradient-to-br from-accent/10 via-bg-secondary to-accent/5 p-8 text-center max-w-lg">
                <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-xl bg-accent/20">
                  <Sparkles className="h-7 w-7 text-accent" />
                </div>
                <h1 className="mb-2 text-2xl font-bold text-text-primary">SRE Engineer Assistant</h1>
                <p className="mb-6 text-sm text-text-secondary">
                  Ask me about your infrastructure, alerts, or let me help diagnose issues.
                </p>
                <QuickActions onAction={handleQuickAction} />
              </div>
            </div>
          ) : (
            /* Message list */
            messages.map((msg) => (
              <MessageBubble key={msg.id} message={msg} />
            ))
          )}

          {/* Loading indicator */}
          {isLoading && (
            <div className="flex items-center gap-2 px-4 py-2">
              <div className="flex gap-1">
                <span className="h-2 w-2 animate-loading-dot rounded-full bg-accent" style={{ animationDelay: "0s" }} />
                <span className="h-2 w-2 animate-loading-dot rounded-full bg-accent" style={{ animationDelay: "0.16s" }} />
                <span className="h-2 w-2 animate-loading-dot rounded-full bg-accent" style={{ animationDelay: "0.32s" }} />
              </div>
              <span className="text-xs text-text-secondary">Thinking...</span>
            </div>
          )}

          {/* Recommendation card */}
          {lastAssistantWithRecs?.recommendations && (
            <RecommendationCard
              recommendations={lastAssistantWithRecs.recommendations}
              onExecuteAll={handleExecuteAll}
              onExecuteSelected={handleExecuteSelected}
            />
          )}

          {/* Step progress */}
          {lastOperation?.operation && (
            <StepProgress operation={lastOperation.operation} />
          )}

          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input area */}
      <div className="border-t border-border bg-bg-secondary px-4 py-3">
        <div className="mx-auto max-w-3xl">
          <div className="flex items-end gap-2 rounded-lg border border-border bg-bg-tertiary px-3 py-2 focus-within:border-accent/50">
            <textarea
              ref={textareaRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask about your infrastructure..."
              rows={1}
              className="min-h-[24px] max-h-[160px] flex-1 resize-none bg-transparent text-sm text-text-primary placeholder:text-text-secondary focus:outline-none"
              aria-label="Chat message input"
              disabled={isLoading}
            />
            <button
              onClick={handleSend}
              disabled={!input.trim() || isLoading}
              className={cn(
                "flex h-8 w-8 shrink-0 items-center justify-center rounded-lg transition-colors",
                input.trim() && !isLoading
                  ? "bg-accent text-bg-primary hover:bg-accent-hover"
                  : "text-text-secondary cursor-not-allowed",
              )}
              aria-label="Send message"
            >
              <Send className="h-4 w-4" />
            </button>
          </div>
          <p className="mt-1.5 text-center text-[11px] text-text-secondary">
            Press Enter to send, Shift+Enter for new line
          </p>
        </div>
      </div>

      {/* Confirmation dialog */}
      <ConfirmDialog
        isOpen={confirmOpen}
        onClose={() => setConfirmOpen(false)}
        onConfirm={handleConfirmExecute}
        title="Execute Recommended Actions"
        description="This will execute all recommended remediation steps. Please review carefully before confirming."
        risk="medium"
      />
    </div>
  );
}
