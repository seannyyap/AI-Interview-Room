import { Injectable, signal, computed } from '@angular/core';
import { fromEvent, Observable, Subject, takeUntil, timer } from 'rxjs';

/**
 * DeviceManagerService — Manages audio input (mic), audio output (speaker),
 * and video input (camera) devices.
 * Handles enumeration, selection persistence, and hardware testing.
 */
@Injectable({
    providedIn: 'root',
})
export class DeviceManagerService {
    private readonly MIC_KEY = 'ai_interview_mic_id';
    private readonly SPK_KEY = 'ai_interview_speaker_id';
    private readonly CAM_KEY = 'ai_interview_cam_id';

    // State
    private microphones = signal<MediaDeviceInfo[]>([]);
    private speakers = signal<MediaDeviceInfo[]>([]);
    private cameras = signal<MediaDeviceInfo[]>([]);

    readonly microphones$ = computed(() => this.microphones());
    readonly speakers$ = computed(() => this.speakers());
    readonly cameras$ = computed(() => this.cameras());

    readonly selectedMicId = signal<string>(localStorage.getItem(this.MIC_KEY) || 'default');
    readonly selectedSpeakerId = signal<string>(localStorage.getItem(this.SPK_KEY) || 'default');
    readonly selectedCamId = signal<string>(localStorage.getItem(this.CAM_KEY) || 'default');

    readonly isTestingSpeaker = signal<boolean>(false);
    readonly micLevel = signal<number>(0); // Real-time volume for AI Orb (0.0 to 1.0)

    constructor() {
        this.refreshDevices();

        // Auto-refresh when devices are plugged/unplugged
        fromEvent(navigator.mediaDevices, 'devicechange').subscribe(() => {
            this.refreshDevices();
        });
    }

    /** Fetch available audio and video devices */
    async refreshDevices(): Promise<void> {
        try {
            // We need to request permission at least once to get device labels
            if (!localStorage.getItem('mic_permission_granted')) {
                const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                stream.getTracks().forEach(t => t.stop());
                localStorage.setItem('mic_permission_granted', 'true');
            }

            const devices = await navigator.mediaDevices.enumerateDevices();

            const mics = devices.filter(d => d.kind === 'audioinput');
            const spks = devices.filter(d => d.kind === 'audiooutput');
            const cams = devices.filter(d => d.kind === 'videoinput');

            this.microphones.set(mics);
            this.speakers.set(spks);
            this.cameras.set(cams);

            // Verify if currently selected IDs still exist, otherwise fallback to default
            if (this.selectedMicId() !== 'default' && !mics.find(m => m.deviceId === this.selectedMicId())) {
                this.setMic('default');
            }
            if (this.selectedSpeakerId() !== 'default' && !spks.find(s => s.deviceId === this.selectedSpeakerId())) {
                this.setSpeaker('default');
            }
            if (this.selectedCamId() !== 'default' && !cams.find(c => c.deviceId === this.selectedCamId())) {
                this.setCam('default');
            }

        } catch (err) {
            console.error('[DeviceManager] Failed to refresh devices:', err);
        }
    }

    setMic(id: string) {
        this.selectedMicId.set(id);
        localStorage.setItem(this.MIC_KEY, id);
    }

    setSpeaker(id: string) {
        this.selectedSpeakerId.set(id);
        localStorage.setItem(this.SPK_KEY, id);
    }

    setCam(id: string) {
        this.selectedCamId.set(id);
        localStorage.setItem(this.CAM_KEY, id);
    }

    /** 
     * Test the microphone: Returns an Observable of volume levels (0-100) 
     * for a duration of 5 seconds.
     */
    getMicLevelStream(deviceId: string): Observable<number> {
        const level$ = new Subject<number>();
        const stop$ = timer(5000);

        const runTest = async () => {
            try {
                const stream = await navigator.mediaDevices.getUserMedia({
                    audio: { deviceId: { exact: deviceId } }
                });

                const audioContext = new AudioContext();
                const source = audioContext.createMediaStreamSource(stream);
                const analyser = audioContext.createAnalyser();
                analyser.fftSize = 256;
                source.connect(analyser);

                const dataArray = new Uint8Array(analyser.frequencyBinCount);

                const updateLevel = () => {
                    analyser.getByteFrequencyData(dataArray);
                    const average = dataArray.reduce((p, c) => p + c, 0) / dataArray.length;
                    const normalized = Math.min(100, Math.round((average / 128) * 100));
                    level$.next(normalized);
                };

                const interval = setInterval(updateLevel, 50);

                stop$.subscribe(() => {
                    clearInterval(interval);
                    stream.getTracks().forEach(t => t.stop());
                    audioContext.close();
                    level$.next(0);
                    level$.complete();
                });

            } catch (err) {
                console.error('[DeviceManager] Mic test failed:', err);
                level$.error(err);
            }
        };

        runTest();
        return level$.asObservable().pipe(takeUntil(stop$));
    }

    /** 
     * Play a 5-second ringtone melody through the specified speaker.
     * Uses a pleasant ascending/descending pattern of notes.
     */
    async playTestRingtone(deviceId: string): Promise<void> {
        if (this.isTestingSpeaker()) return;
        this.isTestingSpeaker.set(true);

        const audioContext = new AudioContext();

        // setSinkId is still experimental but supported in Chrome/Edge
        if ((audioContext as any).setSinkId && deviceId !== 'default') {
            await (audioContext as any).setSinkId(deviceId);
        }

        // Pleasant ringtone pattern: C5, E5, G5, C6, G5, E5 repeated
        const notes = [
            523.25, 659.25, 783.99, 1046.50, 783.99, 659.25,  // ascending then descending
            523.25, 659.25, 783.99, 1046.50, 783.99, 659.25,  // repeat
            523.25, 783.99, 1046.50, 1318.51, 1046.50, 783.99, // higher octave variation
        ];

        const noteDuration = 0.25;  // 250ms per note
        const gap = 0.03;           // 30ms gap between notes
        const startTime = audioContext.currentTime + 0.05;

        for (let i = 0; i < notes.length; i++) {
            const osc = audioContext.createOscillator();
            const gain = audioContext.createGain();

            osc.type = 'sine';
            const noteStart = startTime + i * (noteDuration + gap);
            osc.frequency.setValueAtTime(notes[i], noteStart);

            // Smooth envelope: fade in, sustain, fade out
            gain.gain.setValueAtTime(0, noteStart);
            gain.gain.linearRampToValueAtTime(0.15, noteStart + 0.03);
            gain.gain.setValueAtTime(0.15, noteStart + noteDuration - 0.05);
            gain.gain.exponentialRampToValueAtTime(0.001, noteStart + noteDuration);

            osc.connect(gain);
            gain.connect(audioContext.destination);

            osc.start(noteStart);
            osc.stop(noteStart + noteDuration);
        }

        const totalDuration = notes.length * (noteDuration + gap);
        setTimeout(() => {
            audioContext.close();
            this.isTestingSpeaker.set(false);
        }, (totalDuration + 0.5) * 1000);
    }
}
