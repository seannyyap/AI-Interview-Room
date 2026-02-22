import { Component, Output, EventEmitter, OnInit, signal, ViewChild, ElementRef, OnDestroy, AfterViewInit, HostListener } from '@angular/core';
import { DeviceManagerService } from '../../../../shared/services/device-manager.service';

@Component({
    selector: 'app-device-settings',
    standalone: false,
    templateUrl: './device-settings.html',
    styleUrl: './device-settings.scss'
})
export class DeviceSettingsComponent implements OnInit, AfterViewInit, OnDestroy {
    @Output() close = new EventEmitter<void>();

    micLevel = signal<number>(0);
    isTestingMic = signal<boolean>(false);

    @ViewChild('previewVideo') previewVideoRef?: ElementRef<HTMLVideoElement>;
    private previewStream: MediaStream | null = null;
    isPreviewActive = false;

    constructor(
        public deviceManager: DeviceManagerService,
        private elementRef: ElementRef
    ) { }

    @HostListener('document:click', ['$event'])
    onDocumentClick(event: MouseEvent): void {
        const target = event.target as HTMLElement;

        // If click is inside the settings modal, do nothing
        if (this.elementRef.nativeElement.contains(target)) {
            return;
        }

        // If click is on the "Audio Settings" toggle button itself, do nothing
        // because the toggle button's own (click) handler will close it.
        if (target.closest('button[title="Audio Settings"]')) {
            return;
        }

        this.close.emit();
    }

    ngOnInit(): void {
        this.deviceManager.refreshDevices();
    }

    ngAfterViewInit(): void {
        this.startPreview();
    }

    onMicChange(event: any): void {
        this.deviceManager.setMic(event.target.value);
    }

    onSpeakerChange(event: any): void {
        this.deviceManager.setSpeaker(event.target.value);
    }

    onCamChange(event: any): void {
        this.deviceManager.setCam(event.target.value);
        this.startPreview();
    }

    async startPreview(): Promise<void> {
        this.stopPreview();
        try {
            const selectedCamId = this.deviceManager.selectedCamId();
            const videoConstraints: any = { width: { ideal: 640 }, height: { ideal: 360 } };

            if (selectedCamId !== 'default') {
                videoConstraints.deviceId = { exact: selectedCamId };
            }

            this.previewStream = await navigator.mediaDevices.getUserMedia({
                video: videoConstraints,
                audio: false,
            });

            if (this.previewVideoRef?.nativeElement) {
                this.previewVideoRef.nativeElement.srcObject = this.previewStream;
                this.isPreviewActive = true;
            }
        } catch (err) {
            console.error('[DeviceSettings] Failed to start camera preview:', err);
            this.isPreviewActive = false;
        }
    }

    stopPreview(): void {
        if (this.previewStream) {
            this.previewStream.getTracks().forEach(t => t.stop());
            this.previewStream = null;
        }
        if (this.previewVideoRef?.nativeElement) {
            this.previewVideoRef.nativeElement.srcObject = null;
        }
        this.isPreviewActive = false;
    }

    testMic(): void {
        if (this.isTestingMic()) return;

        this.isTestingMic.set(true);
        this.deviceManager.getMicLevelStream(this.deviceManager.selectedMicId()).subscribe({
            next: (level) => this.micLevel.set(level),
            complete: () => {
                this.micLevel.set(0);
                this.isTestingMic.set(false);
            },
            error: () => this.isTestingMic.set(false)
        });
    }

    testSpeaker(): void {
        this.deviceManager.playTestRingtone(this.deviceManager.selectedSpeakerId());
    }

    ngOnDestroy(): void {
        this.stopPreview();
    }
}
