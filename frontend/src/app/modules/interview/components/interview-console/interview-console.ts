import { Component, ChangeDetectionStrategy, inject } from '@angular/core';
import { InterviewStore } from '../../interview.store';
import { InterviewStatus } from '../../../../shared/models/interview.model';

@Component({
  selector: 'app-interview-console',
  standalone: false,
  templateUrl: './interview-console.html',
  styleUrl: './interview-console.scss',
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class InterviewConsoleComponent {
  readonly store = inject(InterviewStore);
  readonly InterviewStatus = InterviewStatus;
}
