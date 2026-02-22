import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';

import { INTERVIEW_ROUTES } from './interview.routes';
import { InterviewComponent } from './pages/interview';
import { AiOrbComponent } from './components/ai-avatar/ai-avatar';
import { WebcamComponent } from './components/webcam/webcam';
import { TranscriptComponent } from './components/transcript/transcript';
import { InterviewConsoleComponent } from './components/interview-console/interview-console';
import { DeviceSettingsComponent } from './components/device-settings/device-settings';


import { SharedModule } from '../../shared/shared.module';

@NgModule({
    declarations: [
        InterviewComponent,
        AiOrbComponent,
        WebcamComponent,
        TranscriptComponent,
        InterviewConsoleComponent,
        DeviceSettingsComponent
    ],

    imports: [
        CommonModule,
        RouterModule.forChild(INTERVIEW_ROUTES),
        SharedModule
    ],
    exports: [RouterModule]
})
export class InterviewModule { }
