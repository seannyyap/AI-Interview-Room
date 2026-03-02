import { Injectable } from '@angular/core';

@Injectable({
    providedIn: 'root'
})
export class InterviewService {
    constructor() { }

    /** Start a new interview is handled via WebSocket, but we can have a helper here */
    startInterview() {
        console.log('Interview logic initiated');
    }
}
