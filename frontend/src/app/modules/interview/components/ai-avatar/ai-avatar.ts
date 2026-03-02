import { Component, ChangeDetectionStrategy, inject, computed } from '@angular/core';
import { InterviewStore } from '../../interview.store';
import { DeviceManagerService } from '../../../../shared/services/device-manager.service';
import { InterviewStatus } from '../../../../shared/models/interview.model';

@Component({
  selector: 'app-ai-avatar',
  standalone: false,
  templateUrl: './ai-avatar.html',
  styleUrl: './ai-avatar.scss',
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class AiOrbComponent {
  readonly store = inject(InterviewStore);
  private deviceManager = inject(DeviceManagerService);
  readonly InterviewStatus = InterviewStatus;

  /**
   * Calculate a dynamic scale for the orb based on real mic volume.
   * Only applied when the status is LISTENING.
   */
  readonly orbScale = computed(() => {
    if (this.store.status() !== InterviewStatus.LISTENING) return 1;

    const volume = this.deviceManager.micLevel();
    // Normalize volume (0-1) to a breathable scale (1.0 to 1.3)
    return 1 + (volume * 0.3);
  });

  // Computed signals for animation states
  readonly isSpeaking = computed(() => this.store.status() === InterviewStatus.SPEAKING);
  readonly isListening = computed(() => this.store.status() === InterviewStatus.LISTENING);
}
