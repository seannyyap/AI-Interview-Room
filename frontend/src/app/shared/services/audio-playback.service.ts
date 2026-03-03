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

    /** Whether TTS audio is currently playing */
    readonly isPlaying = signal(false);

    /** Default sample rate for incoming PCM (must match backend TTS_SAMPLE_RATE) */
    private sampleRate = 24000;

    /**
     * Set the sample rate for decoding incoming PCM.
     * Called when a tts-audio metadata message arrives.
     * If rate changes, we recreate the AudioContext.
     */
    setSampleRate(rate: number): void {
        if (this.sampleRate !== rate) {
            this.sampleRate = rate;
            // Rate changed — recreate context on next playback
            if (this.audioContext && this.playbackQueue.length === 0) {
                this.audioContext.close();
                this.audioContext = null;
            }
        }
    }

    /**
     * Enqueue raw PCM bytes for playback.
     * The bytes should be 16-bit signed integer, mono, at this.sampleRate.
     */
    enqueue(pcmBytes: ArrayBuffer): void {
        if (pcmBytes.byteLength === 0) return;

        this.playbackQueue.push(pcmBytes);
        this.processQueue();
    }

    /**
     * Stop all playback immediately (barge-in).
     * Clears the queue, stops all active source nodes, and resets state.
     */
    stop(): void {
        this.playbackQueue = [];
        this.isProcessing = false;
        this.nextPlayTime = 0;
        this.isPlaying.set(false);

        // Stop all active source nodes to prevent orphaned playback
        for (const source of this.activeSources) {
            try {
                source.stop();
                source.disconnect();
            } catch {
                // Already stopped — ignore
            }
        }
        this.activeSources = [];

        if (this.audioContext) {
            this.audioContext.close();
            this.audioContext = null;
        }
    }

    private async processQueue(): Promise<void> {
        if (this.isProcessing) return;
        this.isProcessing = true;
        this.isPlaying.set(true);

        if (!this.audioContext || this.audioContext.state === 'closed') {
            this.audioContext = new AudioContext({ sampleRate: this.sampleRate });
        }

        // Resume if suspended (browser autoplay policy)
        if (this.audioContext.state === 'suspended') {
            await this.audioContext.resume();
        }

        while (this.playbackQueue.length > 0) {
            const pcmBytes = this.playbackQueue.shift()!;
            await this.playChunk(pcmBytes);
        }

        this.isProcessing = false;
        this.isPlaying.set(false);
    }

    private playChunk(pcmBytes: ArrayBuffer): Promise<void> {
        return new Promise((resolve) => {
            if (!this.audioContext || this.audioContext.state === 'closed') {
                resolve();
                return;
            }

            // Convert Int16 PCM to Float32 for Web Audio API
            const int16Array = new Int16Array(pcmBytes);
            const float32Array = new Float32Array(int16Array.length);
            for (let i = 0; i < int16Array.length; i++) {
                float32Array[i] = int16Array[i] / 32768;
            }

            // Create AudioBuffer
            const audioBuffer = this.audioContext.createBuffer(
                1,                    // mono
                float32Array.length,
                this.sampleRate
            );
            audioBuffer.getChannelData(0).set(float32Array);

            // Schedule for gapless playback
            const source = this.audioContext.createBufferSource();
            source.buffer = audioBuffer;
            source.connect(this.audioContext.destination);

            const currentTime = this.audioContext.currentTime;
            const startTime = Math.max(currentTime, this.nextPlayTime);
            source.start(startTime);
            this.nextPlayTime = startTime + audioBuffer.duration;

            // Track active source for barge-in cleanup
            this.activeSources.push(source);

            source.onended = () => {
                // Remove from active list
                const idx = this.activeSources.indexOf(source);
                if (idx !== -1) this.activeSources.splice(idx, 1);
                resolve();
            };
        });
    }

    ngOnDestroy(): void {
        this.stop();
    }
}
