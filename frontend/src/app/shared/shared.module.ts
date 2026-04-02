import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { FloatingGlassPanelComponent } from './components/floating-glass-panel/floating-glass-panel';

@NgModule({
    declarations: [
        FloatingGlassPanelComponent,
    ],
    imports: [
        CommonModule,
        RouterModule
    ],
    exports: [
        FloatingGlassPanelComponent,
        CommonModule
    ]
})
export class SharedModule { }
