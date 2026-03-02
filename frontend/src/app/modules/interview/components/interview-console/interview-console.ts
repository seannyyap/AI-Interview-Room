import { Component, ChangeDetectionStrategy, inject, OnDestroy, signal } from '@angular/core';
import { Router } from '@angular/router';
import { Subscription } from 'rxjs';
import { InterviewStore } from '../../interview.store';
import { InterviewStatus, Role } from '../../../../shared/models/interview.model';
import { ConnectionState } from '../../../../shared/models/websocket.models';
import { AudioCaptureService } from '../../../../shared/services/audio-capture.service';
import { WebSocketService } from '../../../../shared/services/websocket.service';

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
  private audioSub: Subscription | null = null;
  private transcriptSub: Subscription | null = null;
  private aiResponseSub: Subscription | null = null;
  private errorSub: Subscription | null = null; // Phase 4: WS error sub

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
      this.store.toggleMicrophone(true);
      this.store.setStatus(InterviewStatus.LISTENING);

      // Pipe audio chunks to WebSocket
      this.audioSub = this.audioCapture.audioChunks$.subscribe((chunk) => {
        this.wsService.sendAudioChunk(chunk);
      });

      // Listen for transcript updates
      this.transcriptSub = this.wsService.transcript$.subscribe((msg) => {
        if (msg.isFinal) {
          this.store.addMessage({
            role: Role.USER,
            text: msg.text,
            timestamp: msg.timestamp,
          });
        }
      });

      // Listen for AI responses
      this.aiResponseSub = this.wsService.aiResponse$.subscribe((msg) => {
        if (msg.isComplete) {
          this.store.addMessage({
            role: Role.AI,
            text: msg.text,
            timestamp: msg.timestamp,
          });
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
