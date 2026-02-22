export const environment = {
    production: true,
    apiUrl: '',  // Same origin in production
    wsUrl: '',   // Determined at runtime from window.location
    features: {
        webcam: true,
        audioCapture: true,
    },
};
