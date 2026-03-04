/**
 * AudioWorklet Processor — Captures PCM audio and downsamples from native rate to 16kHz.
 *
 * This runs on the audio rendering thread (not the main thread), so it won't block the UI.
 * It accumulates samples and sends Float32Array chunks to the main thread every ~250ms.
 */
class AudioCaptureProcessor extends AudioWorkletProcessor {
    constructor() {
        super();
        this._buffer = [];
        this._bufferSize = 0;
        // 16kHz * 0.25s = 4000 samples per chunk
        this._targetSampleRate = 16000;
        this._chunkSamples = 4000;
    }

    /**
     * Downsample audio from source rate to target rate using linear interpolation.
     * @param {Float32Array} inputBuffer - Input samples at source rate
     * @param {number} sourceRate - Source sample rate (e.g., 48000)
     * @param {number} targetRate - Target sample rate (16000)
     * @returns {Float32Array} Downsampled audio
     */
    downsample(inputBuffer, sourceRate, targetRate) {
        if (sourceRate === targetRate) {
            return inputBuffer;
        }

        const ratio = sourceRate / targetRate;
        const outputLength = Math.floor(inputBuffer.length / ratio);
        const output = new Float32Array(outputLength);

        for (let i = 0; i < outputLength; i++) {
            const srcIndex = i * ratio;
            const srcIndexFloor = Math.floor(srcIndex);
            const srcIndexCeil = Math.min(srcIndexFloor + 1, inputBuffer.length - 1);
            const fraction = srcIndex - srcIndexFloor;

            // Linear interpolation between samples
            output[i] = inputBuffer[srcIndexFloor] * (1 - fraction) + inputBuffer[srcIndexCeil] * fraction;
        }

        return output;
    }

    /**
     * Called by the Web Audio API with 128 samples per frame.
     * We accumulate frames, downsample, and emit chunks to the main thread.
     */
    process(inputs, outputs, parameters) {
        const input = inputs[0];
        if (!input || !input[0]) {
            return true; // Keep processor alive
        }

        // Take mono channel (channel 0)
        const channelData = input[0];

        // Downsample this frame from native rate (usually 48000) to 16kHz
        const downsampled = this.downsample(channelData, sampleRate, this._targetSampleRate);

        // Accumulate into buffer
        this._buffer.push(...downsampled);
        this._bufferSize += downsampled.length;

        // When we have enough samples (~250ms at 16kHz), send the chunk
        if (this._bufferSize >= this._chunkSamples) {
            const chunk = new Float32Array(this._buffer.splice(0, this._chunkSamples));
            this._bufferSize -= this._chunkSamples;

            this.port.postMessage({
                type: 'audio-chunk',
                data: chunk.buffer,
            }, [chunk.buffer]); // Transfer ownership for zero-copy
        }

        return true;
    }
}

registerProcessor('audio-capture-processor', AudioCaptureProcessor);
