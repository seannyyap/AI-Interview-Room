import { Component, ChangeDetectionStrategy, inject, ViewChild, ElementRef, OnDestroy, effect } from '@angular/core';
import { InterviewStore } from '../../interview.store';
import { DeviceManagerService } from '../../../../shared/services/device-manager.service';

@Component({
  selector: 'app-webcam',
  standalone: false,
  templateUrl: './webcam.html',
  styleUrl: './webcam.scss',
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class WebcamComponent implements OnDestroy {
  readonly store = inject(InterviewStore);
  private deviceManager = inject(DeviceManagerService);

  @ViewChild('videoElement', { static: true }) videoRef!: ElementRef<HTMLVideoElement>;

  private stream: MediaStream | null = null;

  constructor() {
    // React to camera toggle from InterviewStore (set by console component)
    effect(() => {
      const shouldBeActive = this.store.isCameraActive();
      const isCurrentlyActive = !!this.stream;

      if (shouldBeActive && !isCurrentlyActive) {
        this.startCamera();
      } else if (!shouldBeActive && isCurrentlyActive) {
        this.stopStream();
      }
    });
  }

  private async startCamera(): Promise<void> {
    try {
      const selectedCamId = this.deviceManager.selectedCamId();
      const videoConstraints: any = { width: { ideal: 1280 }, height: { ideal: 720 } };

      if (selectedCamId !== 'default') {
        videoConstraints.deviceId = { exact: selectedCamId };
      }

      this.stream = await navigator.mediaDevices.getUserMedia({
        video: videoConstraints,
        audio: false,
      });

      this.videoRef.nativeElement.srcObject = this.stream;
    } catch (err) {
      console.error('[Webcam] Failed to start camera:', err);
      this.store.setError('Failed to access camera');
      this.store.toggleCamera(false);
    }
  }

  private stopStream(): void {
    if (this.stream) {
      this.stream.getTracks().forEach(t => t.stop());
      this.stream = null;
    }
    if (this.videoRef?.nativeElement) {
      this.videoRef.nativeElement.srcObject = null;
    }
  }

  ngOnDestroy(): void {
    this.stopStream();
  }
}
