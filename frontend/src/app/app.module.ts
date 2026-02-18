import { NgModule } from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';
import { RouterModule, Routes } from '@angular/router';

import { AppComponent } from './app';
import { HeaderComponent } from './shared/components/header/header';

const routes: Routes = [
    {
        path: 'interview',
        loadChildren: () => import('./modules/interview/interview.module').then(m => m.InterviewModule)
    },
    { path: '', redirectTo: 'interview', pathMatch: 'full' }
];

@NgModule({
    declarations: [
        AppComponent,
        HeaderComponent
    ],
    imports: [
        BrowserModule,
        RouterModule.forRoot(routes)
    ],
    bootstrap: [AppComponent]
})
export class AppModule { }
