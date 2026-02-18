import { Component } from '@angular/core';

@Component({
  selector: 'app-ai-avatar',
  standalone: true,
  imports: [],
  templateUrl: './ai-avatar.html',
  styleUrl: './ai-avatar.scss'
})
export class AiAvatarComponent {
  isSpeaking = false;

  constructor() {
    // Simulate speaking/listening states for demo
    setInterval(() => {
      this.isSpeaking = !this.isSpeaking;
    }, 5000);
  }
}
