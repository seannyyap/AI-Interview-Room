import { Injectable, OnDestroy, signal, computed } from '@angular/core';
import { Subject, Observable, Subscription, timer, EMPTY } from 'rxjs';
import { switchMap, retry, tap } from 'rxjs/operators';
import { webSocket, WebSocketSubject } from 'rxjs/webSocket';
import {
    ConnectionState,
    IncomingMessage,
    TranscriptMessage,
    AIResponseMessage,
    ErrorMessage,
} from '../models/websocket.models';
import { environment } from '../../../environments/environment';

/**
 * WebSocketService — Manages WebSocket connection for real-time interview communication.
 *
 * Sends binary audio chunks and receives JSON messages (transcripts, AI responses, errors).
 * Exposes connection state as an Angular Signal for reactive UI updates.
 */
@Injectable({
    providedIn: 'root',
})
export class WebSocketService implements OnDestroy {
    private socket: WebSocket | null = null;
    private reconnectAttempts = 0;
    private maxReconnectAttempts = 5;
    private reconnectDelay = 1000; // ms, doubles each attempt
    private reconnectTimer: ReturnType<typeof setTimeout> | null = null;

    // --- Signals for reactive state ---
    private connectionStateSignal = signal<ConnectionState>(ConnectionState.DISCONNECTED);
    readonly connectionState = this.connectionStateSignal.asReadonly();
    readonly isConnected = computed(() => this.connectionStateSignal() === ConnectionState.CONNECTED
        || this.connectionStateSignal() === ConnectionState.STREAMING);

    // --- Subjects for incoming message streams ---
    private transcriptSubject = new Subject<TranscriptMessage>();
    private aiResponseSubject = new Subject<AIResponseMessage>();
    private errorSubject = new Subject<ErrorMessage>();

    /** Stream of transcript messages from the server */
    readonly transcript$: Observable<TranscriptMessage> = this.transcriptSubject.asObservable();

    /** Stream of AI response messages from the server */
    readonly aiResponse$: Observable<AIResponseMessage> = this.aiResponseSubject.asObservable();

    /** Stream of error messages from the server */
    readonly error$: Observable<ErrorMessage> = this.errorSubject.asObservable();

    /**
     * Connect to the WebSocket server.
     */
    connect(): void {
        if (this.socket && this.socket.readyState === WebSocket.OPEN) {
            console.warn('[WebSocket] Already connected');
            return;
        }

        this.connectionStateSignal.set(ConnectionState.CONNECTING);

        const wsUrl = this.getWsUrl();
        console.log(`[WebSocket] Connecting to ${wsUrl}`);

        this.socket = new WebSocket(wsUrl);
        this.socket.binaryType = 'arraybuffer';

        this.socket.onopen = () => {
            console.log('[WebSocket] Connected');
            this.connectionStateSignal.set(ConnectionState.CONNECTED);
            this.reconnectAttempts = 0;
        };

        this.socket.onmessage = (event: MessageEvent) => {
            this.handleMessage(event);
        };

        this.socket.onerror = (event: Event) => {
            console.error('[WebSocket] Error:', event);
            this.connectionStateSignal.set(ConnectionState.ERROR);
        };

        this.socket.onclose = (event: CloseEvent) => {
            console.log(`[WebSocket] Closed: code=${event.code}, reason=${event.reason}`);
            this.connectionStateSignal.set(ConnectionState.DISCONNECTED);
            this.socket = null;

            // Auto-reconnect on unexpected close
            if (!event.wasClean && this.reconnectAttempts < this.maxReconnectAttempts) {
                this.scheduleReconnect();
            }
        };
    }

    /**
     * Disconnect from the WebSocket server.
     */
    disconnect(): void {
        this.cancelReconnect();

        if (this.socket) {
            this.socket.close(1000, 'Client disconnect');
            this.socket = null;
        }

        this.connectionStateSignal.set(ConnectionState.DISCONNECTED);
        console.log('[WebSocket] Disconnected');
    }

    /**
     * Send a binary audio chunk to the server.
     * @param audioData Float32Array of PCM audio at 16kHz mono
     */
    sendAudioChunk(audioData: Float32Array): void {
        if (!this.socket || this.socket.readyState !== WebSocket.OPEN) {
            return;
        }

        this.socket.send(audioData.buffer);
        this.connectionStateSignal.set(ConnectionState.STREAMING);
    }

    /**
     * Send a JSON message to the server.
     */
    sendMessage(message: object): void {
        if (!this.socket || this.socket.readyState !== WebSocket.OPEN) {
            console.warn('[WebSocket] Cannot send — not connected');
            return;
        }

        this.socket.send(JSON.stringify(message));
    }

    // --- Private Helpers ---

    private getWsUrl(): string {
        if (environment.wsUrl) {
            return environment.wsUrl;
        }
        // Derive from current location in production
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        return `${protocol}//${window.location.host}/ws/audio`;
    }

    private handleMessage(event: MessageEvent): void {
        // Binary data = audio response from TTS
        if (event.data instanceof ArrayBuffer) {
            // Audio response handling will be added in Phase 4
            return;
        }

        // Text data = JSON message
        try {
            const message: IncomingMessage = JSON.parse(event.data as string);

            switch (message.type) {
                case 'transcript':
                    this.transcriptSubject.next(message);
                    break;
                case 'ai-response':
                    this.aiResponseSubject.next(message);
                    break;
                case 'error':
                    this.errorSubject.next(message);
                    console.error('[WebSocket] Server error:', message.message);
                    break;
                case 'status':
                    console.log('[WebSocket] Status:', message.status);
                    break;
                default:
                    console.warn('[WebSocket] Unknown message type:', message);
            }
        } catch (error) {
            console.error('[WebSocket] Failed to parse message:', error);
        }
    }

    private scheduleReconnect(): void {
        this.reconnectAttempts++;
        const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);
        console.log(`[WebSocket] Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`);

        this.reconnectTimer = setTimeout(() => {
            this.connect();
        }, delay);
    }

    private cancelReconnect(): void {
        if (this.reconnectTimer) {
            clearTimeout(this.reconnectTimer);
            this.reconnectTimer = null;
        }
        this.reconnectAttempts = 0;
    }

    ngOnDestroy(): void {
        this.disconnect();
        this.transcriptSubject.complete();
        this.aiResponseSubject.complete();
        this.errorSubject.complete();
    }
}
