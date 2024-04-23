from flask import Flask, request, jsonify
import sounddevice as sd
import numpy as np
import scipy.io.wavfile as wav
import threading

app = Flask(__name__)

# Global variables
audio_buffer = []
fs = 44100  # Sample rate
chunk_duration = 10  # Duration of each chunk in seconds
save_interval = 10  # Save interval in seconds
recording_stopped = False  # Flag to indicate if recording has stopped

# Function to record audio for a given duration
def record_audio(duration):
    global fs
    print("Recording...")
    recording = sd.rec(int(duration * fs), samplerate=fs, channels=1, dtype=np.int16)
    sd.wait()  # Wait until recording is finished
    return recording

# Function to save audio chunks periodically
def save_audio_periodically():
    global audio_buffer
    global fs
    global chunk_duration
    global save_interval
    global recording_stopped

    while not recording_stopped:
        # Wait for save interval
        sd.sleep(int(save_interval * 1000))
        
        if len(audio_buffer) >= chunk_duration * fs:
            full_audio = np.concatenate(audio_buffer)
            filename = '/audio_files/audio_chunk.wav'
            wav.write(filename, fs, full_audio)
            print("Chunk saved as", filename)
            audio_buffer = []  # Clear the buffer

# Route to start recording
@app.route('/start_record', methods=['POST'])
def start_record():
    global audio_buffer
    global recording_stopped
    audio_buffer = []  # Clear the buffer
    recording_stopped = False
    # Start a thread to save audio periodically
    save_thread = threading.Thread(target=save_audio_periodically)
    save_thread.start()
    return "Recording started."

# Route to stop recording and save the audio
@app.route('/stop_record', methods=['POST'])
def stop_record():
    global audio_buffer
    global fs
    global recording_stopped
    recording_stopped = True

    if len(audio_buffer) > 0:
        full_audio = np.concatenate(audio_buffer)
        filename = '/audio_files/audio.wav'
        wav.write(filename, fs, full_audio)
        print("Audio saved as", filename)
        audio_buffer = []  # Clear the buffer
        return jsonify({"message": "Audio saved successfully."})
    else:
        return jsonify({"message": "No audio to save."})

# Route to handle incoming audio chunks
@app.route('/audio_chunk', methods=['POST'])
def audio_chunk():
    global audio_buffer
    data = request.data
    chunk = np.frombuffer(data, dtype=np.int16)
    audio_buffer.append(chunk)
    return "Chunk received."

if __name__ == '__main__':
    app.run(debug=True)
