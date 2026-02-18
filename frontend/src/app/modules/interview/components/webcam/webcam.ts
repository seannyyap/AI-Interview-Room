import { Component, ChangeDetectionStrategy, inject } from '@angular/core';
import { InterviewStore } from '../../interview.store';

@Component({
  selector: 'app-webcam',
  standalone: false,
  templateUrl: './webcam.html',
  styleUrl: './webcam.scss',
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class WebcamComponent {
  readonly store = inject(InterviewStore);
}
