export enum Role {
    AI = 'ai',
    USER = 'user'
}

export enum InterviewStatus {
    IDLE = 'idle',
    LISTENING = 'listening',
    SPEAKING = 'speaking',
    PROCESSING = 'processing'
}

export interface Message {
    role: Role;
    text: string;
    timestamp: string;
}

export interface InterviewState {
    isSpeaking: boolean;
    isListening: boolean;
    transcript: Message[];
}
