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
    private silenceDetectionSubject = new Subject<boolean>();
    private isCapturing = false;
    private silenceTimer: any = null;

    // --- Noise Robustness Properties ---
    private noiseFloor = 0.005;
    private isActiveSpeech = false;
    private speechStrikes = 0; // Require consecutive frames to confirm speech
    private readonly NOISE_ADAPT_SPEED = 0.98; // Slower adaptation to noise
    private readonly SPEECH_MULTIPLIER = 4.0;  // Higher threshold (4x floor)
    private readonly SILENCE_WAIT_MS = 1000;

    /** Observable stream of 16kHz mono Float32 PCM chunks (~250ms each) */
    readonly audioChunks$: Observable<Float32Array> = this.audioChunksSubject.asObservable();

    /** Emits true when silence is detected for > 1s, false when speech resumes */
    readonly silenceDetected$: Observable<boolean> = this.silenceDetectionSubject.asObservable();

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

                    // Phase 4: Calculate real-time volume (RMS)
                    let sumSquares = 0;
                    for (let i = 0; i < chunk.length; i++) {
                        sumSquares += chunk[i] * chunk[i];
                    }
                    const rms = Math.sqrt(sumSquares / chunk.length);

                    // Map RMS to 0.0 - 1.0 range for UI
                    const normalizedVolume = Math.min(1, rms * 10);
                    this.deviceManager.micLevel.set(normalizedVolume);

                    // --- Adaptive Noise & VAD ---
                    const speechThreshold = this.noiseFloor * this.SPEECH_MULTIPLIER;

                    if (rms < speechThreshold) {
                        // Slowly adapt the noise floor downward if the room is quiet
                        this.noiseFloor = (this.noiseFloor * this.NOISE_ADAPT_SPEED) + (rms * (1 - this.NOISE_ADAPT_SPEED));
                        this.speechStrikes = 0; // Reset confirmation strikes

                        if (this.isActiveSpeech) {
                            // Only start the silence timer if we were previously talking
                            if (!this.silenceTimer) {
                                this.silenceTimer = setTimeout(() => {
                                    console.log('[AudioCapture] Silence met (Adaptive Floor)');
                                    this.silenceDetectionSubject.next(true);
                                    this.isActiveSpeech = false;
                                }, this.SILENCE_WAIT_MS);
                            }
                        }
                    } else {
                        // Potential speech detected! 
                        this.speechStrikes++;

                        if (this.silenceTimer) {
                            clearTimeout(this.silenceTimer);
                            this.silenceTimer = null;
                        }

                        // Require 2 consecutive frames (~500ms total) to confirm it's not a blip
                        if (this.speechStrikes >= 2) {
                            if (!this.isActiveSpeech) {
                                console.log('[AudioCapture] Active speech confirmed (Barge-in ready)');
                            }
                            this.isActiveSpeech = true;
                            this.silenceDetectionSubject.next(false);
                        }
                    }

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

        if (this.silenceTimer) {
            clearTimeout(this.silenceTimer);
            this.silenceTimer = null;
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
