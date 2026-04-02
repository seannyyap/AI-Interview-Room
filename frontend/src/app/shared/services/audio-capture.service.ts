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
    private isCapturing = false;
    private audioChunksSubject = new Subject<Float32Array>();
    private silenceDetectionSubject = new Subject<boolean>();

    // --- FFT VAD Properties ---
    private analyser: AnalyserNode | null = null;
    private vadFrameId = 0;
    private readonly FFT_SIZE = 512;
    private readonly MIN_FREQ = 300;   // Hz (Ignore low rumble)
    private readonly MAX_FREQ = 3000;  // Hz (Ignore high hiss/clicks)
    // --- Hysteresis Thresholds ---
    // Raised to 160 to safely clear the user's peak noise/echo floor (~118 seen in logs)
    // Raised to 180 to ignore even more ambient noise/echo (User peak was 203)
    private readonly START_THRESHOLD = 180;
    // Kept at 110 for a wide hold window once speech is confirmed
    private readonly HOLD_THRESHOLD = 110;

    // Increased to 15 (~250ms) to ensure pops/bumps/clicks are ignored
    private readonly REQUIRED_FRAMES = 15;
    private readonly SILENCE_FRAMES = 120; // ~2.0s for natural thinking/pause room

    private activeFrames = 0;
    private silenceFramesCount = 0;
    private isSpeechActive = false;

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

            // 6. Set up AnalyserNode for FFT VAD
            this.analyser = this.audioContext.createAnalyser();
            this.analyser.fftSize = this.FFT_SIZE;
            this.analyser.smoothingTimeConstant = 0.2; // Fast response
            this.sourceNode.connect(this.analyser);

            // 7. Listen for raw bytes from the worklet (now just downsampling)
            this.workletNode.port.onmessage = (event: MessageEvent) => {
                const data = event.data;
                if (data && data.type === 'audio-chunk') {
                    const chunk = new Float32Array(data.data);

                    // Simple RMS fallback for UI volume meter if preferred,
                    // or we could use the analyser data. For now, we compute an RMS of the chunk.
                    let sumSquares = 0;
                    for (let i = 0; i < chunk.length; i++) {
                        sumSquares += chunk[i] * chunk[i];
                    }
                    const rms = Math.sqrt(sumSquares / chunk.length);
                    const normalizedVolume = Math.min(1, rms * 10);
                    this.deviceManager.micLevel.set(normalizedVolume);

                    this.audioChunksSubject.next(chunk);
                }
            };

            // 8. Connect: mic → worklet → (nowhere, we just capture)
            this.sourceNode.connect(this.workletNode);
            this.workletNode.connect(this.audioContext.destination);

            this.isCapturing = true;
            this.startFFTVAD();
            console.log('[AudioCapture] Started — 16kHz mono chunks streaming (FFT VAD Active)');
        } catch (error) {
            console.error('[AudioCapture] Failed to start:', error);
            this.stop();
            throw error;
        }
    }

    /** Stop capturing audio and release all resources. */
    stop(): void {
        this.stopFFTVAD();

        if (this.analyser) {
            this.analyser.disconnect();
            this.analyser = null;
        }

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

    // --- Native FFT Voice Activity Detection ---
    private startFFTVAD(): void {
        if (!this.analyser || !this.audioContext) return;

        const bufferLength = this.analyser.frequencyBinCount;
        const dataArray = new Uint8Array(bufferLength);
        const sampleRate = this.audioContext.sampleRate; // usually 48000
        const hzPerBin = (sampleRate / 2) / bufferLength;

        // Calculate which bins correspond to 300Hz - 3000Hz (human speech)
        const minBin = Math.floor(this.MIN_FREQ / hzPerBin);
        const maxBin = Math.ceil(this.MAX_FREQ / hzPerBin);

        const checkVAD = () => {
            if (!this.isCapturing || !this.analyser) return;

            this.analyser.getByteFrequencyData(dataArray);
            let peakEnergy = 0;
            let totalEnergy = 0;
            for (let i = minBin; i <= maxBin; i++) {
                if (dataArray[i] > peakEnergy) {
                    peakEnergy = dataArray[i];
                }
                totalEnergy += dataArray[i];
            }
            const averageEnergy = Math.round(totalEnergy / (maxBin - minBin + 1));

            const currentThreshold = this.isSpeechActive ? this.HOLD_THRESHOLD : this.START_THRESHOLD;

            // Calibration Telemetry: Log the peak energy every ~1 second (60 frames)
            if (this.vadFrameId % 60 === 0) {
                // Telemetry removed to reduce console noise (Signal Optimization)
                // console.log(`[VAD Telemetry] Peak: ${peakEnergy} | Avg: ${averageEnergy} | ActiveFrames: ${this.activeFrames}/${this.REQUIRED_FRAMES} | SilenceFrames: ${this.silenceFramesCount}/${this.SILENCE_FRAMES} | Threshold: ${currentThreshold}`);
            }
            if (peakEnergy > currentThreshold) {
                this.activeFrames++;
                this.silenceFramesCount = 0;

                if (this.activeFrames >= this.REQUIRED_FRAMES && !this.isSpeechActive) {
                    this.isSpeechActive = true;
                    this.silenceFramesCount = 0;
                    this.silenceDetectionSubject.next(false);
                    console.log(`[VAD Decision] Speech Started (Energy: ${peakEnergy} > ${currentThreshold})`);
                }
            } else {
                this.activeFrames = 0; // Reset continuous frames (filters out sharp claps/coughs instantly)
                this.silenceFramesCount++;

                if (this.isSpeechActive && this.silenceFramesCount >= this.SILENCE_FRAMES) {
                    this.isSpeechActive = false;
                    this.activeFrames = 0;
                    this.silenceDetectionSubject.next(true);
                    const graceSecs = (this.SILENCE_FRAMES * 16.6 / 1000).toFixed(1);
                    console.log(`[VAD Decision] Speech Ended (Grace period of ${graceSecs}s met)`);
                }
            }

            this.vadFrameId = requestAnimationFrame(checkVAD);
        };

        this.isSpeechActive = false;
        this.activeFrames = 0;
        this.silenceFramesCount = 0;
        this.vadFrameId = requestAnimationFrame(checkVAD);
    }

    private stopFFTVAD(): void {
        if (this.vadFrameId) {
            cancelAnimationFrame(this.vadFrameId);
            this.vadFrameId = 0;
        }
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
