import { Injectable, OnDestroy, signal } from '@angular/core';

/**
 * AudioPlaybackService — plays TTS audio received over WebSocket.
 *
 * Receives PCM audio bytes (16-bit signed, 24kHz, mono), queues them,
 * and plays them sequentially via Web Audio API with seamless gapless playback.
 */
@Injectable({
    providedIn: 'root',
})
export class AudioPlaybackService implements OnDestroy {
    private audioContext: AudioContext | null = null;
    private playbackQueue: ArrayBuffer[] = [];
    private isProcessing = false;
    private nextPlayTime = 0;
    private activeSources: AudioBufferSourceNode[] = [];

    /** Jitter Buffer Configuration */
    private readonly MIN_CHUNKS_TO_START = 2; // Safety margin for rapid chunks
    private readonly BUFFERING_DELAY_MS = 300; // Final deadline for the first chunk to start playing
    private bufferingTimeout: any = null;
    private isBuffering = true;

    /** Whether TTS audio is currently playing or being prepared */
    readonly isPlaying = signal(false);

    /** Default sample rate for incoming PCM (must match backend TTS_SAMPLE_RATE) */
    private sampleRate = 24000;

    /**
     * Set the sample rate for decoding incoming PCM.
     */
    setSampleRate(rate: number): void {
        if (this.sampleRate !== rate) {
            this.sampleRate = rate;
            if (this.audioContext && this.playbackQueue.length === 0) {
                this.audioContext.close();
                this.audioContext = null;
            }
        }
    }

    /**
     * Unlock the AudioContext initialized by a user gesture.
     */
    async ensureUnlocked(): Promise<void> {
        if (!this.audioContext || this.audioContext.state === 'closed') {
            this.audioContext = new AudioContext({ sampleRate: this.sampleRate });
        }
        if (this.audioContext.state === 'suspended') {
            await this.audioContext.resume().catch(e => console.warn('Failed to unlock audio context:', e));
        }
    }

    /**
     * Enqueue raw PCM bytes for playback.
     */
    enqueue(pcmBytes: ArrayBuffer): void {
        if (pcmBytes.byteLength === 0) return;

        this.playbackQueue.push(pcmBytes);

        // --- Floor Lock ---
        // As soon as the first byte of a response turn arrives, we set isPlaying = true.
        // This ensures the Half-Duplex logic in the console locks out the mic immediately.
        this.isPlaying.set(true);

        if (this.isBuffering) {
            // Start a timer for the first chunk
            if (!this.bufferingTimeout) {
                console.log(`[AI Audio] First chunk arrived. Buffering for ${this.BUFFERING_DELAY_MS}ms safety...`);
                this.bufferingTimeout = setTimeout(() => {
                    console.log(`[AI Audio] Safety buffer ready (Started with ${this.playbackQueue.length} chunks).`);
                    this.startPlayback();
                }, this.BUFFERING_DELAY_MS);
            }

            // If we hit our safety chunk count early, start now
            if (this.playbackQueue.length >= this.MIN_CHUNKS_TO_START) {
                console.log(`[AI Audio] Quality margin reached (${this.playbackQueue.length} chunks). Starting early.`);
                this.startPlayback();
            }
        } else {
            this.processQueue();
        }
    }

    /**
     * Force start playback of whatever is in the queue (e.g. called on AI response complete).
     */
    flush(): void {
        if (this.isBuffering && this.playbackQueue.length > 0) {
            console.log('[AI Audio] Manual flush triggered (Turn complete).');
            this.startPlayback();
        }
    }

    private startPlayback(): void {
        if (this.bufferingTimeout) {
            clearTimeout(this.bufferingTimeout);
            this.bufferingTimeout = null;
        }
        this.isBuffering = false;
        this.processQueue();
    }

    /**
     * Stop all playback immediately (barge-in).
     */
    stop(): void {
        if (this.bufferingTimeout) {
            clearTimeout(this.bufferingTimeout);
            this.bufferingTimeout = null;
        }
        this.playbackQueue = [];
        this.isProcessing = false;
        this.nextPlayTime = 0;
        this.isBuffering = true;
        this.isPlaying.set(false);

        for (const source of this.activeSources) {
            try {
                source.stop();
                source.disconnect();
            } catch { }
        }
        this.activeSources = [];

        if (this.audioContext) {
            this.audioContext.close();
            this.audioContext = null;
        }
    }

    private async processQueue(): Promise<void> {
        if (this.isProcessing || this.isBuffering) return;
        this.isProcessing = true;
        this.isPlaying.set(true);

        if (!this.audioContext || this.audioContext.state === 'closed') {
            this.audioContext = new AudioContext({ sampleRate: this.sampleRate });
        }

        if (this.audioContext.state === 'suspended') {
            await this.audioContext.resume();
        }

        while (this.playbackQueue.length > 0) {
            const pcmBytes = this.playbackQueue.shift()!;
            await this.scheduleChunk(pcmBytes);
        }

        this.isProcessing = false;
    }

    private scheduleChunk(pcmBytes: ArrayBuffer): Promise<void> {
        return new Promise((resolve) => {
            if (!this.audioContext || this.audioContext.state === 'closed') {
                resolve();
                return;
            }

            const int16Array = new Int16Array(pcmBytes);
            const float32Array = new Float32Array(int16Array.length);
            for (let i = 0; i < int16Array.length; i++) {
                float32Array[i] = int16Array[i] / 32768;
            }

            const audioBuffer = this.audioContext.createBuffer(1, float32Array.length, this.sampleRate);
            audioBuffer.getChannelData(0).set(float32Array);

            const source = this.audioContext.createBufferSource();
            source.buffer = audioBuffer;
            source.connect(this.audioContext.destination);

            const currentTime = this.audioContext.currentTime;

            if (this.nextPlayTime < currentTime) {
                this.nextPlayTime = currentTime + 0.05;
            }

            const startTime = this.nextPlayTime;
            source.start(startTime);
            this.nextPlayTime = startTime + audioBuffer.duration;

            this.activeSources.push(source);

            source.onended = () => {
                const idx = this.activeSources.indexOf(source);
                if (idx !== -1) {
                    this.activeSources.splice(idx, 1);
                    if (this.activeSources.length === 0 && this.playbackQueue.length === 0) {
                        this.isPlaying.set(false);
                        this.isBuffering = true;
                    }
                }
            };

            resolve();
        });
    }

    ngOnDestroy(): void {
        this.stop();
    }
}


