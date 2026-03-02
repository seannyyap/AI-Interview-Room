import { Component, ChangeDetectionStrategy, inject } from '@angular/core';
import { Role, InterviewStatus } from '../../../../shared/models/interview.model';
import { InterviewStore } from '../../interview.store';

@Component({
  selector: 'app-transcript',
  standalone: false,
  templateUrl: './transcript.html',
  styleUrl: './transcript.scss',
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class TranscriptComponent {
  readonly store = inject(InterviewStore);
  readonly Role = Role;
  readonly InterviewStatus = InterviewStatus;

  /* Scroll Indicator Logic */
  showScrollIndicator = false;

  onScroll(event: Event): void {
    const element = event.target as HTMLElement;
    // Show indicator if not at bottom (with small buffer)
    const isAtBottom = Math.abs(element.scrollHeight - element.scrollTop - element.clientHeight) < 20;
    this.showScrollIndicator = !isAtBottom;
  }

  /* Initial check */
  ngAfterViewInit() {
    // Small timeout to allow render
    setTimeout(() => {
      this.showScrollIndicator = true; // Assume true initially if content exists
    }, 100);
  }
}
