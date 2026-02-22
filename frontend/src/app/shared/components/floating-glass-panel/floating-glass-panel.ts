import { Component, ChangeDetectionStrategy, Input } from '@angular/core';

@Component({
  selector: 'app-floating-glass-panel',
  standalone: false,
  templateUrl: './floating-glass-panel.html',
  styleUrl: './floating-glass-panel.scss',
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class FloatingGlassPanelComponent {
  @Input() width = 'auto';
  @Input() height = 'auto';
  @Input() maxWidth = '100vw';
  @Input() maxHeight = '100vh';
  @Input() positionClass = ''; // e.g. 'top-right', 'bottom-right'
  @Input() isMobileSheet = false; // Add option for bottom sheet behavior
}
