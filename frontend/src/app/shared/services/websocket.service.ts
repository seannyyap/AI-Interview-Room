import { Injectable, OnDestroy, signal, computed, inject } from '@angular/core';
import { Subject, Observable } from 'rxjs';
import { webSocket, WebSocketSubject } from 'rxjs/webSocket';
import {
    ConnectionState,
    IncomingMessage,
    TranscriptMessage,
    AIResponseMessage,
    TTSAudioMetaMessage,
    ErrorMessage,
} from '../models/websocket.models';
import { AudioPlaybackService } from './audio-playback.service';
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
    private socket$: WebSocketSubject<any> | null = null;
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
    private ttsAudioSubject = new Subject<TTSAudioMetaMessage>();
    private errorSubject = new Subject<ErrorMessage>();

    /** Stream of transcript messages from the server */
    readonly transcript$: Observable<TranscriptMessage> = this.transcriptSubject.asObservable();

    /** Stream of AI response messages from the server */
    readonly aiResponse$: Observable<AIResponseMessage> = this.aiResponseSubject.asObservable();

    /** Stream of TTS audio metadata from the server */
    readonly ttsAudio$: Observable<TTSAudioMetaMessage> = this.ttsAudioSubject.asObservable();

    /** Stream of error messages from the server */
    readonly error$: Observable<ErrorMessage> = this.errorSubject.asObservable();

    private audioPlayback = inject(AudioPlaybackService);

    constructor() {
        console.log('[WebSocketService] Initialized');
    }

    /**
     * Connect to the WebSocket server.
     */
    connect(): void {
        if (this.socket$) {
            console.warn('[WebSocket) Already connected');
            return;
        }

        this.connectionStateSignal.set(ConnectionState.CONNECTING);
        const wsUrl = this.getWsUrl();
        console.log(`[WebSocket] Connecting to ${wsUrl}...`);

        this.socket$ = webSocket({
            url: wsUrl,
            deserializer: (msg) => msg.data,
            serializer: (msg) => {
                if (msg instanceof ArrayBuffer || msg instanceof Blob) {
                    return msg;
                }
                return JSON.stringify(msg);
            },
            binaryType: 'arraybuffer',
            openObserver: {
                next: () => {
                    console.log('[WebSocket] Connection established');
                    this.connectionStateSignal.set(ConnectionState.CONNECTED);
                    this.reconnectAttempts = 0;
                }
            },
            closeObserver: {
                next: (closeEvent) => {
                    console.log('[WebSocket] Connection closed', closeEvent);
                    this.cleanup();
                    this.connectionStateSignal.set(ConnectionState.DISCONNECTED);

                    // Auto-reconnect on unexpected close
                    if (!closeEvent.wasClean && this.reconnectAttempts < this.maxReconnectAttempts) {
                        this.scheduleReconnect();
                    }
                }
            }
        });

        this.socket$.subscribe({
            next: (message: any) => this.handleRawMessage(message),
            error: (error) => {
                console.error('[WebSocket] Error:', error);
                this.connectionStateSignal.set(ConnectionState.ERROR);
                this.cleanup();
                this.scheduleReconnect();
            }
        });
    }

    /**
     * Disconnect from the WebSocket server.
     */
    disconnect(): void {
        this.cancelReconnect();
        this.cleanup();
        this.connectionStateSignal.set(ConnectionState.DISCONNECTED);
        console.log('[WebSocket] Disconnected');
    }

    /**
     * Send binary audio chunk (Float32Array) to the server.
     */
    sendAudioChunk(chunk: Float32Array): void {
        if (!this.socket$) return;
        this.socket$.next(chunk.buffer);
        this.connectionStateSignal.set(ConnectionState.STREAMING);
    }

    /**
     * Send a JSON message to the server.
     */
    sendMessage(message: object): void {
        if (!this.socket$) {
            console.warn('[WebSocket] Cannot send — not connected');
            return;
        }
        this.socket$.next(message);
    }

    // --- Private Helpers ---

    private getWsUrl(): string {
        if (environment.wsUrl) {
            return environment.wsUrl;
        }
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        return `${protocol}//${window.location.host}/ws/audio`;
    }

    private handleRawMessage(data: any): void {
        if (data instanceof ArrayBuffer) {
            // Phase 4: Forward TTS audio to the playback service
            this.audioPlayback.enqueue(data);
            return;
        }

        try {
            const message: IncomingMessage = JSON.parse(data as string);

            switch (message.type) {
                case 'transcript':
                    this.transcriptSubject.next(message as TranscriptMessage);
                    break;
                case 'ai-response':
                    this.aiResponseSubject.next(message as AIResponseMessage);
                    break;
                case 'tts-audio':
                    // Metadata arrives before the binary payload — configure playback
                    this.audioPlayback.setSampleRate((message as TTSAudioMetaMessage).sampleRate);
                    this.ttsAudioSubject.next(message as TTSAudioMetaMessage);
                    break;
                case 'error':
                    this.errorSubject.next(message as ErrorMessage);
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

    private cleanup(): void {
        if (this.socket$) {
            this.socket$.complete();
            this.socket$ = null;
        }
    }

    private scheduleReconnect(): void {
        if (this.reconnectAttempts >= this.maxReconnectAttempts) {
            console.error('[WebSocket] Max reconnect attempts reached');
            return;
        }

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
    }

    ngOnDestroy(): void {
        this.disconnect();
        this.transcriptSubject.complete();
        this.aiResponseSubject.complete();
        this.ttsAudioSubject.complete();
        this.errorSubject.complete();
    }
}
