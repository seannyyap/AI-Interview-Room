import { Injectable, OnDestroy } from '@angular/core';
import { Observable, Subject } from 'rxjs';
import { DeviceManagerService } from './device-manager.service';

/**
 * AudioCaptureService — Captures microphone audio using Web Audio API + AudioWorklet.
 *
 * Outputs Float32Array chunks at 16kHz mono (~250ms each) via an RxJS Observable.
 * All heavy lifting (downsampling) happens in the AudioWorklet thread, not the main thread.
 */
@Injectable({
    providedIn: 'root',
})
export class AudioCaptureService implements OnDestroy {
    private audioContext: AudioContext | null = null;
    private mediaStream: MediaStream | null = null;
    private sourceNode: MediaStreamAudioSourceNode | null = null;
    private workletNode: AudioWorkletNode | null = null;

    private audioChunksSubject = new Subject<Float32Array>();
    private isCapturing = false;

    /** Observable stream of 16kHz mono Float32 PCM chunks (~250ms each) */
    readonly audioChunks$: Observable<Float32Array> = this.audioChunksSubject.asObservable();

    constructor(private deviceManager: DeviceManagerService) { }

    /**
     * Start capturing audio from the microphone.
     * Requests mic permission, initialises AudioWorklet, and begins streaming chunks.
     */
    async start(): Promise<void> {
        if (this.isCapturing) {
            console.warn('[AudioCapture] Already capturing');
            return;
        }

        try {
            const selectedDeviceId = this.deviceManager.selectedMicId();
            const audioConstraints: any = {
                echoCancellation: true,
                noiseSuppression: true,
                channelCount: 1,          // Mono
                sampleRate: { ideal: 48000 },
            };

            if (selectedDeviceId !== 'default') {
                audioConstraints.deviceId = { exact: selectedDeviceId };
            }

            // 1. Request microphone access (mic only — never camera)
            this.mediaStream = await navigator.mediaDevices.getUserMedia({
                audio: audioConstraints,
                video: false,
            });

            // 2. Create AudioContext
            this.audioContext = new AudioContext({ sampleRate: 48000 });

            // 3. Load the AudioWorklet processor
            await this.audioContext.audioWorklet.addModule('audio-processor.worklet.js');

            // 4. Create source from mic stream
            this.sourceNode = this.audioContext.createMediaStreamSource(this.mediaStream);

            // 5. Create worklet node
            this.workletNode = new AudioWorkletNode(this.audioContext, 'audio-capture-processor');

            // 6. Listen for audio chunks from the worklet
            this.workletNode.port.onmessage = (event: MessageEvent) => {
                if (event.data?.type === 'audio-chunk') {
                    const chunk = new Float32Array(event.data.data);

                    // Phase 4: Calculate real-time volume (RMS) for the AI Orb
                    let sumSquares = 0;
                    for (let i = 0; i < chunk.length; i++) {
                        sumSquares += chunk[i] * chunk[i];
                    }
                    const rms = Math.sqrt(sumSquares / chunk.length);
                    // Map RMS to 0.0 - 1.0 range (RMS usually peaks around 0.5-0.7 for loud speech)
                    const normalizedVolume = Math.min(1, rms * 10);
                    this.deviceManager.micLevel.set(normalizedVolume);

                    this.audioChunksSubject.next(chunk);
                }
            };

            // 7. Connect: mic → worklet → (nowhere, we just capture)
            this.sourceNode.connect(this.workletNode);
            this.workletNode.connect(this.audioContext.destination); // Required for process() to be called

            this.isCapturing = true;
            console.log('[AudioCapture] Started — 16kHz mono chunks streaming');
        } catch (error) {
            console.error('[AudioCapture] Failed to start:', error);
            this.stop();
            throw error;
        }
    }

    /** Stop capturing audio and release all resources. */
    stop(): void {
        if (this.workletNode) {
            this.workletNode.port.onmessage = null;
            this.workletNode.disconnect();
            this.workletNode = null;
        }

        if (this.sourceNode) {
            this.sourceNode.disconnect();
            this.sourceNode = null;
        }

        if (this.mediaStream) {
            this.mediaStream.getTracks().forEach((track) => track.stop());
            this.mediaStream = null;
        }

        if (this.audioContext) {
            this.audioContext.close();
            this.audioContext = null;
        }

        this.isCapturing = false;
        console.log('[AudioCapture] Stopped');
    }

    /** Whether audio capture is currently active */
    get capturing(): boolean {
        return this.isCapturing;
    }

    ngOnDestroy(): void {
        this.stop();
        this.audioChunksSubject.complete();
    }
}
