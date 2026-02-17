/**
 * EduSMS WebSocket Client
 * Real-time communication utilities for notifications and live updates
 */

import { getSession } from './supabase';

export type MessageType =
  | 'connected'
  | 'disconnected'
  | 'error'
  | 'ping'
  | 'pong'
  | 'notification'
  | 'announcement'
  | 'alert'
  | 'data_update'
  | 'attendance_update'
  | 'grade_update'
  | 'payment_update'
  | 'user_online'
  | 'user_offline'
  | 'typing'
  | 'chat_message';

export interface WebSocketMessage {
  type: MessageType;
  [key: string]: unknown;
}

export interface NotificationMessage extends WebSocketMessage {
  type: 'notification';
  title: string;
  body: string;
  notification_type: 'info' | 'success' | 'warning' | 'error';
  data?: Record<string, unknown>;
  timestamp: string;
}

export interface AlertMessage extends WebSocketMessage {
  type: 'alert';
  title: string;
  body: string;
  severity: 'info' | 'warning' | 'error' | 'critical';
  timestamp: string;
}

export interface DataUpdateMessage extends WebSocketMessage {
  type: 'data_update' | 'attendance_update' | 'grade_update' | 'payment_update';
  entity_type: string;
  entity_id: string;
  action: 'create' | 'update' | 'delete';
  data?: Record<string, unknown>;
}

type MessageHandler = (message: WebSocketMessage) => void;
type ConnectionHandler = () => void;

interface WebSocketClientOptions {
  autoReconnect?: boolean;
  reconnectInterval?: number;
  maxReconnectAttempts?: number;
  heartbeatInterval?: number;
}

const DEFAULT_OPTIONS: WebSocketClientOptions = {
  autoReconnect: true,
  reconnectInterval: 3000,
  maxReconnectAttempts: 10,
  heartbeatInterval: 30000,
};

export class WebSocketClient {
  private ws: WebSocket | null = null;
  private options: WebSocketClientOptions;
  private reconnectAttempts = 0;
  private reconnectTimer: NodeJS.Timeout | null = null;
  private heartbeatTimer: NodeJS.Timeout | null = null;
  private messageHandlers: Map<string, Set<MessageHandler>> = new Map();
  private connectionHandlers: {
    onConnect: Set<ConnectionHandler>;
    onDisconnect: Set<ConnectionHandler>;
    onError: Set<(error: Event) => void>;
  } = {
    onConnect: new Set(),
    onDisconnect: new Set(),
    onError: new Set(),
  };

  constructor(options: WebSocketClientOptions = {}) {
    this.options = { ...DEFAULT_OPTIONS, ...options };
  }

  /**
   * Connect to the WebSocket server
   */
  async connect(): Promise<void> {
    if (this.ws?.readyState === WebSocket.OPEN) {
      return;
    }

    // Get auth token
    const session = await getSession();
    if (!session?.access_token) {
      console.warn('WebSocket: No auth token available');
      return;
    }

    // Build WebSocket URL
    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsHost = process.env.NEXT_PUBLIC_WS_HOST || window.location.host;
    const wsUrl = `${wsProtocol}//${wsHost}/api/v1/realtime/ws?token=${session.access_token}`;

    try {
      this.ws = new WebSocket(wsUrl);
      this.setupEventHandlers();
    } catch (error) {
      console.error('WebSocket connection failed:', error);
      this.scheduleReconnect();
    }
  }

  /**
   * Disconnect from the WebSocket server
   */
  disconnect(): void {
    this.clearTimers();
    this.reconnectAttempts = 0;

    if (this.ws) {
      this.ws.close(1000, 'Client disconnect');
      this.ws = null;
    }
  }

  /**
   * Subscribe to a channel
   */
  subscribe(channel: string): void {
    this.send({ type: 'subscribe', channel });
  }

  /**
   * Unsubscribe from a channel
   */
  unsubscribe(channel: string): void {
    this.send({ type: 'unsubscribe', channel });
  }

  /**
   * Send a message to the server
   */
  send(message: Record<string, unknown>): boolean {
    if (this.ws?.readyState !== WebSocket.OPEN) {
      console.warn('WebSocket not connected');
      return false;
    }

    try {
      this.ws.send(JSON.stringify(message));
      return true;
    } catch (error) {
      console.error('WebSocket send error:', error);
      return false;
    }
  }

  /**
   * Add a message handler for a specific message type
   */
  on(type: string, handler: MessageHandler): () => void {
    if (!this.messageHandlers.has(type)) {
      this.messageHandlers.set(type, new Set());
    }
    this.messageHandlers.get(type)!.add(handler);

    // Return unsubscribe function
    return () => {
      this.messageHandlers.get(type)?.delete(handler);
    };
  }

  /**
   * Add a handler for all messages
   */
  onMessage(handler: MessageHandler): () => void {
    return this.on('*', handler);
  }

  /**
   * Add connection event handlers
   */
  onConnect(handler: ConnectionHandler): () => void {
    this.connectionHandlers.onConnect.add(handler);
    return () => this.connectionHandlers.onConnect.delete(handler);
  }

  onDisconnect(handler: ConnectionHandler): () => void {
    this.connectionHandlers.onDisconnect.add(handler);
    return () => this.connectionHandlers.onDisconnect.delete(handler);
  }

  onError(handler: (error: Event) => void): () => void {
    this.connectionHandlers.onError.add(handler);
    return () => this.connectionHandlers.onError.delete(handler);
  }

  /**
   * Check if connected
   */
  get isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }

  private setupEventHandlers(): void {
    if (!this.ws) return;

    this.ws.onopen = () => {
      console.log('WebSocket connected');
      this.reconnectAttempts = 0;
      this.startHeartbeat();
      this.connectionHandlers.onConnect.forEach((handler) => handler());
    };

    this.ws.onclose = (event) => {
      console.log('WebSocket disconnected:', event.code, event.reason);
      this.clearTimers();
      this.connectionHandlers.onDisconnect.forEach((handler) => handler());

      if (this.options.autoReconnect && event.code !== 1000) {
        this.scheduleReconnect();
      }
    };

    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      this.connectionHandlers.onError.forEach((handler) => handler(error));
    };

    this.ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data) as WebSocketMessage;
        this.handleMessage(message);
      } catch (error) {
        console.error('WebSocket message parse error:', error);
      }
    };
  }

  private handleMessage(message: WebSocketMessage): void {
    // Handle ping/pong
    if (message.type === 'ping') {
      this.send({ type: 'pong', timestamp: new Date().toISOString() });
      return;
    }

    // Notify specific handlers
    const handlers = this.messageHandlers.get(message.type);
    if (handlers) {
      handlers.forEach((handler) => handler(message));
    }

    // Notify wildcard handlers
    const wildcardHandlers = this.messageHandlers.get('*');
    if (wildcardHandlers) {
      wildcardHandlers.forEach((handler) => handler(message));
    }
  }

  private startHeartbeat(): void {
    this.clearHeartbeat();
    this.heartbeatTimer = setInterval(() => {
      if (this.isConnected) {
        this.send({ type: 'pong', timestamp: new Date().toISOString() });
      }
    }, this.options.heartbeatInterval!);
  }

  private clearHeartbeat(): void {
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer);
      this.heartbeatTimer = null;
    }
  }

  private scheduleReconnect(): void {
    if (this.reconnectAttempts >= this.options.maxReconnectAttempts!) {
      console.log('WebSocket: Max reconnect attempts reached');
      return;
    }

    this.reconnectAttempts++;
    const delay = this.options.reconnectInterval! * Math.min(this.reconnectAttempts, 5);

    console.log(`WebSocket: Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts})`);

    this.reconnectTimer = setTimeout(() => {
      this.connect();
    }, delay);
  }

  private clearTimers(): void {
    this.clearHeartbeat();
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
  }
}

// Global WebSocket client instance
let wsClient: WebSocketClient | null = null;

export function getWebSocketClient(): WebSocketClient {
  if (!wsClient) {
    wsClient = new WebSocketClient();
  }
  return wsClient;
}

export function connectWebSocket(): Promise<void> {
  return getWebSocketClient().connect();
}

export function disconnectWebSocket(): void {
  if (wsClient) {
    wsClient.disconnect();
    wsClient = null;
  }
}
