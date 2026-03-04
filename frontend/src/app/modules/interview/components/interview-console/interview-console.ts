import { Component, ChangeDetectionStrategy, inject, OnDestroy, signal, effect } from '@angular/core';
import { Subscription } from 'rxjs';
import { InterviewStore } from '../../interview.store';
import { InterviewStatus, Role } from '../../../../shared/models/interview.model';
import { AudioCaptureService } from '../../../../shared/services/audio-capture.service';
import { WebSocketService } from '../../../../shared/services/websocket.service';
import { AudioPlaybackService } from '../../../../shared/services/audio-playback.service';

@Component({
  selector: 'app-interview-console',
  standalone: false,
  templateUrl: './interview-console.html',
  styleUrl: './interview-console.scss',
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class InterviewConsoleComponent implements OnDestroy {
  readonly store = inject(InterviewStore);
  readonly InterviewStatus = InterviewStatus;
  showSettings = signal<boolean>(false);
  isTogglingMic = signal<boolean>(false);
  isTogglingCam = signal<boolean>(false);

  private audioCapture = inject(AudioCaptureService);
  private wsService = inject(WebSocketService);
  private audioPlayback = inject(AudioPlaybackService);
  private audioSub: Subscription | null = null;
  private transcriptSub: Subscription | null = null;
  private aiResponseSub: Subscription | null = null;
  private silenceSub: Subscription | null = null;
  private errorSub: Subscription | null = null;

  private textGenerationComplete = false;

  constructor() {
    // Effect to return to LISTENING status only after audio finishes playing
    effect(() => {
      const isPlaying = this.audioPlayback.isPlaying();
      if (!isPlaying && this.textGenerationComplete && this.store.status() === InterviewStatus.PROCESSING) {
        console.log('[Console Decision] AI playback finished. Returning to LISTENING.');
        this.store.setStatus(InterviewStatus.LISTENING);
        this.textGenerationComplete = false; // Reset for next turn
      }
    });
  }

  /**
   * Toggle microphone: start/stop audio capture and WebSocket streaming.
   */
  async toggleMic(): Promise<void> {
    if (this.isTogglingMic()) return;
    this.isTogglingMic.set(true);

    try {
      if (this.store.isMicrophoneActive()) {
        this.stopCapture();
      } else {
        await this.startCapture();
      }
    } finally {
      this.isTogglingMic.set(false);
    }
  }

  /**
   * Toggle settings popup.
   */
  toggleSettings(): void {
    this.showSettings.update(val => !val);
  }

  /**
   * Toggle camera: start/stop video capture via store signal.
   */
  async toggleCam(): Promise<void> {
    if (this.isTogglingCam()) return;
    this.isTogglingCam.set(true);

    try {
      this.store.toggleCamera(!this.store.isCameraActive());
      // Small artificial delay to prevent button hammering
      await new Promise(resolve => setTimeout(resolve, 500));
    } finally {
      this.isTogglingCam.set(false);
    }
  }

  private router = inject(Router);

  /**
   * End the current interview session.
   */
  endInterview(): void {
    // Send end signal to server if connected
    if (this.wsService.isConnected()) {
      this.wsService.sendMessage({ type: 'interview-end' });
    }

    this.stopCapture();
    this.store.toggleCamera(false);
    this.wsService.disconnect();
    this.store.reset();

    // Navigate back to landing page
    this.router.navigate(['/']);
  }

  private async startCapture(): Promise<void> {
    try {
      // Connect WebSocket if not already connected
      if (!this.wsService.isConnected()) {
        this.wsService.connect();
        this.store.setConnectionState(ConnectionState.CONNECTING);
      }

      // Start audio capture
      await this.audioCapture.start();

      // Phase 4/5: Preemptively initialize and resume the playback AudioContext 
      // during this user gesture to satisfy browser autoplay policies.
      await this.audioPlayback.ensureUnlocked();

      this.store.toggleMicrophone(true);
      this.store.setStatus(InterviewStatus.LISTENING);

      // Tell backend to start the interview session
      this.wsService.sendMessage({
        type: 'interview-start',
        config: {
          position: 'Software Engineer', // Default — in real app, get from store/form
          difficulty: 'medium'
        }
      });

      // Pipe audio chunks to WebSocket
      this.audioSub = this.audioCapture.audioChunks$.subscribe((chunk) => {
        this.wsService.sendAudioChunk(chunk);
      });

      // Listen for transcript updates (User Speaking)
      this.transcriptSub = this.wsService.transcript$.subscribe((msg) => {
        this.store.upsertMessage({
          role: Role.USER,
          text: msg.text,
          timestamp: msg.timestamp,
        });

        if (msg.isFinal) {
          // Additional logic if needed for final user transcript
        }
      });

      // Listen for AI responses (Bot Speaking)
      this.aiResponseSub = this.wsService.aiResponse$.subscribe((msg) => {
        this.store.upsertMessage({
          role: Role.AI,
          text: msg.text,
          timestamp: msg.timestamp,
        });

        if (msg.isComplete) {
          this.textGenerationComplete = true;
          // Only return to LISTENING if audio is already finished playing.
          // Otherwise, the playback listener below will handle it.
          if (!this.audioPlayback.isPlaying()) {
            this.store.setStatus(InterviewStatus.LISTENING);
          }
        } else {
          this.textGenerationComplete = false;
          this.store.setStatus(InterviewStatus.PROCESSING);
        }
      });

      // Listen for silence (Client-Side VAD)
      this.silenceSub = this.audioCapture.silenceDetected$.subscribe((isSilent) => {
        const currentStatus = this.store.status();

        // --- Half-Duplex Logic ---
        // If the AI is currently working or playing audio, IGNORE all microphone triggers.
        // This ensures the AI is never interrupted and avoids echo-induced loops.
        if (currentStatus === InterviewStatus.PROCESSING || this.audioPlayback.isPlaying()) {
          // Do nothing while AI has the "floor"
          return;
        }

        if (isSilent) {
          // Rule: If we were listening and it's now silent for 1s, trigger speech-end
          if (currentStatus === InterviewStatus.LISTENING) {
            console.log('[Console Decision] Rule: Silence (1.0s met) -> sending speech-end to server');
            this.wsService.sendMessage({ type: 'speech-end' });
            this.store.setStatus(InterviewStatus.PROCESSING);
          }
        } else {
          // Rule: User STARTS speaking (isSilent=false)
          console.log('[Console Decision] Rule: Speech Start Detected -> sending speech-start to server to clear buffers');
          this.wsService.sendMessage({ type: 'speech-start' });
        }
      });

      // Phase 4: Pipe WS errors to store
      this.errorSub = this.wsService.error$.subscribe((msg) => {
        this.store.setError(msg.message);
      });
    } catch (err) {
      console.error('[Console] Failed to start capture:', err);
      this.store.setError('Failed to access microphone');
      this.store.toggleMicrophone(false);
    }
  }

  private stopCapture(): void {
    this.audioSub?.unsubscribe();
    this.audioSub = null;
    this.transcriptSub?.unsubscribe();
    this.transcriptSub = null;
    this.aiResponseSub?.unsubscribe();
    this.aiResponseSub = null;
    this.silenceSub?.unsubscribe();
    this.silenceSub = null;
    this.errorSub?.unsubscribe();
    this.errorSub = null;

    this.audioCapture.stop();
    this.store.toggleMicrophone(false);
    this.store.setStatus(InterviewStatus.IDLE);
  }

  ngOnDestroy(): void {
    this.stopCapture();
    this.wsService.disconnect();
  }
}
