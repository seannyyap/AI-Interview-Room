import { Component, ChangeDetectionStrategy, inject, computed } from '@angular/core';
import { InterviewStore } from '../../interview.store';
import { InterviewStatus } from '../../../../shared/models/interview.model';

@Component({
  selector: 'app-ai-orb',
  standalone: false,
  templateUrl: './ai-avatar.html',
  styleUrl: './ai-avatar.scss',
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class AiOrbComponent {
  readonly store = inject(InterviewStore);

  // Computed signals for animation states
  readonly isSpeaking = computed(() => this.store.status() === InterviewStatus.SPEAKING);
  readonly isListening = computed(() => this.store.status() === InterviewStatus.LISTENING);
}
