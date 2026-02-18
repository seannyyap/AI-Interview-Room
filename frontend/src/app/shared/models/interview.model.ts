export interface Message {
    role: 'ai' | 'user';
    text: string;
    timestamp: string;
}

export interface InterviewState {
    isSpeaking: boolean;
    isListening: boolean;
    transcript: Message[];
}
