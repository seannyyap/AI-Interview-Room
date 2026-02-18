import { Component } from '@angular/core';
import { AiAvatarComponent } from './components/ai-avatar/ai-avatar';
import { WebcamComponent } from './components/webcam/webcam';
import { TranscriptComponent } from './components/transcript/transcript';

@Component({
  selector: 'app-interview',
  standalone: true,
  imports: [AiAvatarComponent, WebcamComponent, TranscriptComponent],
  templateUrl: './interview.html',
  styleUrl: './interview.scss'
})
export class InterviewComponent {

}
