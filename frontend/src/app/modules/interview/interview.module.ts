import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';

import { INTERVIEW_ROUTES } from './interview.routes';
import { InterviewComponent } from './pages/interview';
import { AiAvatarComponent } from './components/ai-avatar/ai-avatar';
import { WebcamComponent } from './components/webcam/webcam';
import { TranscriptComponent } from './components/transcript/transcript';

@NgModule({
    declarations: [
        InterviewComponent,
        AiAvatarComponent,
        WebcamComponent,
        TranscriptComponent
    ],
    imports: [
        CommonModule,
        RouterModule.forChild(INTERVIEW_ROUTES)
    ],
    exports: [RouterModule]
})
export class InterviewModule { }
