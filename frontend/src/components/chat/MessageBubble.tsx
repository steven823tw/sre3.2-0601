import { cn } from "@/utils/cn";
import { formatRelativeTime } from "@/utils/formatTime";
import { User, Bot } from "lucide-react";
import type { ChatMessage } from "@/types/chat";

interface MessageBubbleProps {
  message: ChatMessage;
}

/** Renders a single chat message with role-based styling */
export function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === "user";

  return (
    <div className={cn("flex gap-3", isUser ? "flex-row-reverse" : "flex-row")}>
      {/* Role icon */}
      <div
        className={cn(
          "flex h-8 w-8 shrink-0 items-center justify-center rounded-full",
          isUser ? "bg-accent/20 text-accent" : "bg-bg-tertiary text-text-secondary",
        )}
        aria-label={isUser ? "User" : "Assistant"}
      >
        {isUser ? <User className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
      </div>

      {/* Message content */}
      <div
        className={cn(
          "max-w-[70%] px-4 py-2.5 text-sm",
          isUser
            ? "rounded-lg rounded-tr-none bg-accent/15 text-text-primary border border-accent/20"
            : "rounded-lg rounded-tl-none bg-bg-tertiary text-text-primary border-l-2 border-accent/40",
        )}
      >
        <div className="whitespace-pre-wrap break-words">{message.content}</div>
        <time className="mt-1 block text-xs text-text-secondary">
          {formatRelativeTime(message.timestamp)}
        </time>
      </div>
    </div>
  );
}
