'use client';

/**
 * EduSMS Real-time Hook
 * React hook for WebSocket integration and real-time updates
 */

import { useEffect, useCallback, useState, useRef } from 'react';
import {
  getWebSocketClient,
  WebSocketClient,
  WebSocketMessage,
  NotificationMessage,
  AlertMessage,
  DataUpdateMessage,
  MessageType,
} from '@/lib/websocket';

interface UseRealtimeOptions {
  autoConnect?: boolean;
  channels?: string[];
  onNotification?: (notification: NotificationMessage) => void;
  onAlert?: (alert: AlertMessage) => void;
  onDataUpdate?: (update: DataUpdateMessage) => void;
}

interface UseRealtimeReturn {
  isConnected: boolean;
  connect: () => Promise<void>;
  disconnect: () => void;
  subscribe: (channel: string) => void;
  unsubscribe: (channel: string) => void;
  send: (message: Record<string, unknown>) => boolean;
}

export function useRealtime(options: UseRealtimeOptions = {}): UseRealtimeReturn {
  const {
    autoConnect = true,
    channels = [],
    onNotification,
    onAlert,
    onDataUpdate,
  } = options;

  const [isConnected, setIsConnected] = useState(false);
  const clientRef = useRef<WebSocketClient | null>(null);
  const cleanupRef = useRef<(() => void)[]>([]);

  // Initialize client
  useEffect(() => {
    clientRef.current = getWebSocketClient();
    return () => {
      cleanupRef.current.forEach((cleanup) => cleanup());
      cleanupRef.current = [];
    };
  }, []);

  // Handle connection state
  useEffect(() => {
    const client = clientRef.current;
    if (!client) return;

    const unsubConnect = client.onConnect(() => {
      setIsConnected(true);
    });

    const unsubDisconnect = client.onDisconnect(() => {
      setIsConnected(false);
    });

    cleanupRef.current.push(unsubConnect, unsubDisconnect);

    // Auto-connect if enabled
    if (autoConnect) {
      client.connect();
    }

    return () => {
      unsubConnect();
      unsubDisconnect();
    };
  }, [autoConnect]);

  // Subscribe to channels
  useEffect(() => {
    const client = clientRef.current;
    if (!client || !isConnected || channels.length === 0) return;

    channels.forEach((channel) => {
      client.subscribe(channel);
    });

    return () => {
      channels.forEach((channel) => {
        client.unsubscribe(channel);
      });
    };
  }, [isConnected, channels]);

  // Set up message handlers
  useEffect(() => {
    const client = clientRef.current;
    if (!client) return;

    const handlers: (() => void)[] = [];

    if (onNotification) {
      handlers.push(
        client.on('notification', (msg) => {
          onNotification(msg as NotificationMessage);
        })
      );
    }

    if (onAlert) {
      handlers.push(
        client.on('alert', (msg) => {
          onAlert(msg as AlertMessage);
        })
      );
    }

    if (onDataUpdate) {
      const updateTypes: MessageType[] = [
        'data_update',
        'attendance_update',
        'grade_update',
        'payment_update',
      ];

      updateTypes.forEach((type) => {
        handlers.push(
          client.on(type, (msg) => {
            onDataUpdate(msg as DataUpdateMessage);
          })
        );
      });
    }

    return () => {
      handlers.forEach((unsub) => unsub());
    };
  }, [onNotification, onAlert, onDataUpdate]);

  const connect = useCallback(async () => {
    await clientRef.current?.connect();
  }, []);

  const disconnect = useCallback(() => {
    clientRef.current?.disconnect();
  }, []);

  const subscribe = useCallback((channel: string) => {
    clientRef.current?.subscribe(channel);
  }, []);

  const unsubscribe = useCallback((channel: string) => {
    clientRef.current?.unsubscribe(channel);
  }, []);

  const send = useCallback((message: Record<string, unknown>) => {
    return clientRef.current?.send(message) ?? false;
  }, []);

  return {
    isConnected,
    connect,
    disconnect,
    subscribe,
    unsubscribe,
    send,
  };
}

/**
 * Hook for real-time notifications with toast integration
 */
export function useRealtimeNotifications(showToast?: (notification: NotificationMessage) => void) {
  const handleNotification = useCallback(
    (notification: NotificationMessage) => {
      // Show browser notification if permitted
      if ('Notification' in window && Notification.permission === 'granted') {
        new Notification(notification.title, {
          body: notification.body,
          icon: '/icon-192x192.png',
        });
      }

      // Show toast notification
      showToast?.(notification);
    },
    [showToast]
  );

  return useRealtime({
    onNotification: handleNotification,
  });
}

/**
 * Hook for real-time data updates with cache invalidation
 */
export function useRealtimeData<T>(
  entityType: string,
  onUpdate?: (data: DataUpdateMessage) => void
) {
  const [lastUpdate, setLastUpdate] = useState<DataUpdateMessage | null>(null);

  const handleUpdate = useCallback(
    (update: DataUpdateMessage) => {
      if (update.entity_type === entityType) {
        setLastUpdate(update);
        onUpdate?.(update);
      }
    },
    [entityType, onUpdate]
  );

  const { isConnected, subscribe, unsubscribe } = useRealtime({
    onDataUpdate: handleUpdate,
  });

  return {
    isConnected,
    lastUpdate,
    subscribe,
    unsubscribe,
  };
}

/**
 * Hook for tracking online users
 */
export function useOnlineUsers() {
  const [onlineUsers, setOnlineUsers] = useState<Set<string>>(new Set());

  useEffect(() => {
    const client = getWebSocketClient();

    const unsubOnline = client.on('user_online', (msg) => {
      const userId = (msg as { user_id: string }).user_id;
      setOnlineUsers((prev) => new Set([...prev, userId]));
    });

    const unsubOffline = client.on('user_offline', (msg) => {
      const userId = (msg as { user_id: string }).user_id;
      setOnlineUsers((prev) => {
        const next = new Set(prev);
        next.delete(userId);
        return next;
      });
    });

    return () => {
      unsubOnline();
      unsubOffline();
    };
  }, []);

  const isOnline = useCallback(
    (userId: string) => onlineUsers.has(userId),
    [onlineUsers]
  );

  return {
    onlineUsers: Array.from(onlineUsers),
    isOnline,
    count: onlineUsers.size,
  };
}
