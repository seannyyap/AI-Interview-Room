import { Component, ChangeDetectionStrategy } from '@angular/core';

@Component({
    selector: 'app-landing',
    standalone: false,
    templateUrl: './landing.html',
    styleUrl: './landing.scss',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class LandingComponent { }
