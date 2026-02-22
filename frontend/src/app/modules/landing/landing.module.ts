import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';

import { LANDING_ROUTES } from './landing.routes';
import { LandingComponent } from './pages/landing';

import { SharedModule } from '../../shared/shared.module';

@NgModule({
    declarations: [
        LandingComponent
    ],
    imports: [
        CommonModule,
        RouterModule.forChild(LANDING_ROUTES),
        SharedModule
    ],
    exports: [RouterModule]
})
export class LandingModule { }
