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

  readonly dummyData = [
    { role: Role.AI, text: "Hello! I'm HRbot. I'm here to conduct your system design interview.", timestamp: '10:00 AM' },
    { role: Role.USER, text: "Hi, I'm ready. I've prepared my environment.", timestamp: '10:01 AM' },
    { role: Role.AI, text: "Excellent. Let's start with a high-level question: How would you design a scalable notification system?", timestamp: '10:01 AM' },
    { role: Role.USER, text: "I would start by decoupling the producers from consumers using a message queue like Kafka.", timestamp: '10:02 AM' },
    { role: Role.AI, text: "That's a solid start. How would you handle rate limiting to prevent overwhelming the users?", timestamp: '10:03 AM' },
    { role: Role.USER, text: "I'd implement a token bucket algorithm at the API gateway level, and also have per-user limits in the notification service itself.", timestamp: '10:04 AM' },
    { role: Role.AI, text: "Good. What database would you choose for storing notification preferences and history, and why?", timestamp: '10:05 AM' },
    { role: Role.USER, text: "For preferences, a relational DB like PostgreSQL is fine. For history, since it's write-heavy and time-series like, maybe Cassandra or just partitioned Postgres.", timestamp: '10:06 AM' },
    { role: Role.AI, text: "Interesting choice. How would you handle the case where a user has multiple devices and we need to sync read status?", timestamp: '10:07 AM' },
    { role: Role.USER, text: "We could use a WebSocket connection to push updates to all active devices when a notification is marked read on one.", timestamp: '10:08 AM' },
    { role: Role.AI, text: "That works. Let's shift gears. Can you explain the difference between vertical and horizontal scaling?", timestamp: '10:09 AM' },
    { role: Role.AI, text: "That works. Let's shift gears. Can you explain the difference between vertical and horizontal scaling?", timestamp: '10:09 AM' }
  ];

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
