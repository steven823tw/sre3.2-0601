import { useEffect, useRef, useCallback, useState } from "react";

interface WebSocketOptions {
  url: string;
  onMessage?: (data: unknown) => void;
  onOpen?: () => void;
  onClose?: () => void;
  reconnectInterval?: number;
}

export function useWebSocket({ url, onMessage, onOpen, onClose, reconnectInterval = 5000 }: WebSocketOptions) {
  const wsRef = useRef<WebSocket | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const reconnectTimer = useRef<ReturnType<typeof setTimeout>>();

  const connect = useCallback(() => {
    try {
      const ws = new WebSocket(url);
      ws.onopen = () => { setIsConnected(true); onOpen?.(); };
      ws.onmessage = (event) => { onMessage?.(JSON.parse(event.data) as unknown); };
      ws.onclose = () => {
        setIsConnected(false);
        onClose?.();
        reconnectTimer.current = setTimeout(connect, reconnectInterval);
      };
      ws.onerror = () => ws.close();
      wsRef.current = ws;
    } catch {
      reconnectTimer.current = setTimeout(connect, reconnectInterval);
    }
  }, [url, onMessage, onOpen, onClose, reconnectInterval]);

  useEffect(() => {
    connect();
    return () => {
      clearTimeout(reconnectTimer.current);
      wsRef.current?.close();
    };
  }, [connect]);

  const send = useCallback((data: unknown) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(data));
    }
  }, []);

  return { isConnected, send };
}
