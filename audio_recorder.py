import pyaudiowpatch as pyaudio
import wave

class AudioRecorder:
    def __init__(self):
        self.p = pyaudio.PyAudio()
        self.is_recording = False
        self.stream = None
        self.frames = []
        self.output_filename = "recorded_audio.wav"
        
        try:
            self.wasapi_info = self.p.get_host_api_info_by_type(pyaudio.paWASAPI)
        except OSError:
            print("Error: WASAPI is not available on this system.")
            self.wasapi_info = None

    def _get_default_loopback_device(self):
        if not self.wasapi_info:
            return None
            
        default_speakers = self.p.get_device_info_by_index(self.wasapi_info["defaultOutputDevice"])
        
        if not default_speakers["isLoopbackDevice"]:
            for loopback in self.p.get_loopback_device_info_generator():
                if default_speakers["name"] in loopback["name"]:
                    return loopback
            
            # Fallback to the first available loopback device
            for loopback in self.p.get_loopback_device_info_generator():
                return loopback
                
        return default_speakers

    def start_recording(self, output_filename="recorded_audio.wav"):
        if self.is_recording or self.wasapi_info is None:
            return False

        self.output_filename = output_filename
        self.device_info = self._get_default_loopback_device()
        if not self.device_info:
            return False
            
        self.channels = self.device_info["maxInputChannels"] if (self.device_info["maxInputChannels"] > 0) else 2
        self.rate = int(self.device_info["defaultSampleRate"])
        
        self.frames = []
        self.is_recording = True

        def callback(in_data, frame_count, time_info, status):
            if self.is_recording:
                self.frames.append(in_data)
                return (in_data, pyaudio.paContinue)
            else:
                return (in_data, pyaudio.paComplete)

        self.stream = self.p.open(format=pyaudio.paInt16,
                channels=self.channels,
                rate=self.rate,
                frames_per_buffer=pyaudio.get_sample_size(pyaudio.paInt16) * self.channels,
                input=True,
                input_device_index=self.device_info["index"],
                stream_callback=callback
        )
        
        self.stream.start_stream()
        return True

    def stop_recording(self):
        if not self.is_recording:
            return
            
        self.is_recording = False
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
            self.stream = None

        return self._save_to_wav()

    def _save_to_wav(self):
        captured_audio = True
        if not self.frames:
            captured_audio = False
            # Generate 1 second of silence so the file is still created validly
            bytes_per_sample = self.p.get_sample_size(pyaudio.paInt16)
            silence = b'\x00' * (self.rate * self.channels * bytes_per_sample)
            self.frames.append(silence)
            
        wf = wave.open(self.output_filename, 'wb')
        wf.setnchannels(self.channels)
        wf.setsampwidth(self.p.get_sample_size(pyaudio.paInt16))
        wf.setframerate(self.rate)
        wf.writeframes(b''.join(self.frames))
        wf.close()
        return captured_audio

    def terminate(self):
        if self.is_recording:
            self.stop_recording()
        self.p.terminate()

if __name__ == "__main__":
    import time
    recorder = AudioRecorder()
    print("Recording for 5 seconds...")
    if recorder.start_recording("test_audio.wav"):
        time.sleep(5)
        recorder.stop_recording()
        print("Recording stopped, saved to test_audio.wav")
    else:
        print("Failed to start recording.")
    recorder.terminate()
