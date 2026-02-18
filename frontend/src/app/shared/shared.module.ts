import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { FloatingGlassPanelComponent } from './components/floating-glass-panel/floating-glass-panel';
import { HeaderComponent } from './components/header/header';

@NgModule({
    declarations: [
        FloatingGlassPanelComponent,
        HeaderComponent
    ],
    imports: [
        CommonModule,
        RouterModule
    ],
    exports: [
        FloatingGlassPanelComponent,
        HeaderComponent,
        CommonModule
    ]
})
export class SharedModule { }
