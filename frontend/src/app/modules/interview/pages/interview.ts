import { Component, ChangeDetectionStrategy, inject } from '@angular/core';
import { InterviewStore } from '../interview.store';
import { InterviewStatus } from '../../../shared/models/interview.model';

@Component({
  selector: 'app-interview',
  standalone: false,
  templateUrl: './interview.html',
  styleUrl: './interview.scss',
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class InterviewComponent {
  readonly store = inject(InterviewStore);
  readonly InterviewStatus = InterviewStatus;
}


