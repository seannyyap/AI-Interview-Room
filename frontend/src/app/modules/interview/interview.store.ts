import { patchState, signalStore, withMethods, withState } from '@ngrx/signals';
import { Role, InterviewStatus, Message } from '../../shared/models/interview.model';

export interface InterviewState {
    status: InterviewStatus;
    transcript: Message[];
    isMicrophoneActive: boolean;
    isCameraActive: boolean;
    error: string | null;
}

const initialState: InterviewState = {
    status: InterviewStatus.IDLE,
    transcript: [],
    isMicrophoneActive: false,
    isCameraActive: false,
    error: null,
};

export const InterviewStore = signalStore(
    { providedIn: 'root' },
    withState(initialState),
    withMethods((store) => ({
        setStatus(status: InterviewStatus) {
            patchState(store, { status });
        },
        addMessage(message: Message) {
            patchState(store, (state) => ({ transcript: [...state.transcript, message] }));
        },
        toggleMicrophone(isActive: boolean) {
            patchState(store, { isMicrophoneActive: isActive });
        },
        toggleCamera(isActive: boolean) {
            patchState(store, { isCameraActive: isActive });
        },
        reset() {
            patchState(store, initialState);
        }
    }))
);
