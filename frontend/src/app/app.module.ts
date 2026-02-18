import { NgModule } from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';
import { RouterModule, Routes } from '@angular/router';

import { AppComponent } from './app';
import { SharedModule } from './shared/shared.module';

const routes: Routes = [
    {
        path: 'interview',
        loadChildren: () => import('./modules/interview/interview.module').then(m => m.InterviewModule)
    },
    { path: '', redirectTo: 'interview', pathMatch: 'full' }
];

@NgModule({
    declarations: [
        AppComponent
    ],
    imports: [
        BrowserModule,
        RouterModule.forRoot(routes),
        SharedModule
    ],
    bootstrap: [AppComponent]
})
export class AppModule { }
