import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-transcript',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './transcript.html',
  styleUrl: './transcript.scss'
})
export class TranscriptComponent {
  isAiThinking = false;
  messages = [
    { role: 'ai', text: 'Hello! Welcome to your interview today. I am HRbot, your AI interviewer.', timestamp: '10:00 AM' },
    { role: 'user', text: 'Hi, thank you for having me. I am excited to get started!', timestamp: '10:01 AM' },
    { role: 'ai', text: 'Great. Let us begin. Can you tell me about a time you solved a complex technical problem?', timestamp: '10:01 AM' }
  ];
}
