import { patchState, signalStore, withComputed, withMethods, withState } from '@ngrx/signals';
import { computed } from '@angular/core';
import { Role, InterviewStatus, Message } from '../../shared/models/interview.model';
import { ConnectionState } from '../../shared/models/websocket.models';

export interface InterviewState {
    status: InterviewStatus;
    connectionState: ConnectionState;
    transcript: Message[];
    isMicrophoneActive: boolean;
    isCameraActive: boolean;
    error: string | null;
}

const initialState: InterviewState = {
    status: InterviewStatus.IDLE,
    connectionState: ConnectionState.DISCONNECTED,
    transcript: [],
    isMicrophoneActive: false,
    isCameraActive: false,
    error: null,
};

export const InterviewStore = signalStore(
    { providedIn: 'root' },
    withState(initialState),
    withComputed((store) => ({
        isSessionActive: computed(() =>
            store.status() !== InterviewStatus.IDLE
            && store.connectionState() !== ConnectionState.DISCONNECTED
        ),
        statusLabel: computed(() => {
            if (store.connectionState() === ConnectionState.CONNECTING) return 'Connecting...';
            if (store.connectionState() === ConnectionState.ERROR) return 'Connection Error';
            return store.status();
        }),
    })),
    withMethods((store) => ({
        setStatus(status: InterviewStatus) {
            patchState(store, { status });
        },
        setConnectionState(connectionState: ConnectionState) {
            patchState(store, { connectionState });
        },
        upsertMessage(message: Message) {
            patchState(store, (state) => {
                const transcript = [...state.transcript];
                const lastIdx = transcript.length - 1;

                // If same role and last message exists, append to it
                if (lastIdx >= 0 && transcript[lastIdx].role === message.role) {
                    transcript[lastIdx] = {
                        ...transcript[lastIdx],
                        text: transcript[lastIdx].text + message.text,
                        timestamp: message.timestamp || transcript[lastIdx].timestamp
                    };
                    return { transcript };
                }

                // Otherwise add as new message block
                return { transcript: [...transcript, message] };
            });
        },
        toggleMicrophone(isActive: boolean) {
            patchState(store, { isMicrophoneActive: isActive });
        },
        toggleCamera(isActive: boolean) {
            patchState(store, { isCameraActive: isActive });
        },
        setError(error: string | null) {
            patchState(store, { error });
        },
        reset() {
            patchState(store, initialState);
        }
    }))
);
