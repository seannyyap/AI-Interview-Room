import { Routes } from '@angular/router';
import { InterviewComponent } from './features/interview/interview';

export const routes: Routes = [
    { path: '', redirectTo: 'interview', pathMatch: 'full' },
    { path: 'interview', component: InterviewComponent }
];
