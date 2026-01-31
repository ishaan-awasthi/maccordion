# audio.py - makes the actual sound
import pyaudio
import numpy as np
from threading import Lock

class RealtimeSynth:
    def __init__(self, sample_rate=44100):
        self.sample_rate = sample_rate
        self.active_notes = {} 
        self.phase = {}
        self.master_volume = 0.0
        self.lock = Lock()
        
        self.p = pyaudio.PyAudio()
        self.stream = self.p.open(
            format=pyaudio.paFloat32,
            channels=1,
            rate=sample_rate,
            output=True,
            frames_per_buffer=512,
            stream_callback=self.audio_callback
        )
        
    def audio_callback(self, in_data, frame_count, time_info, status):
        with self.lock:
            # mathy stuff with numpy to generate and add the waveforms
            if self.master_volume == 0.0 or not self.active_notes:
                return (np.zeros(frame_count, dtype=np.float32).tobytes(), 
                       pyaudio.paContinue)
            
            output = np.zeros(frame_count, dtype=np.float32)
            
            for freq in self.active_notes.keys():
                if freq not in self.phase:
                    self.phase[freq] = 0.0
                
                t = np.arange(frame_count) / self.sample_rate
                samples = self.master_volume * np.sin(
                    2 * np.pi * freq * t + self.phase[freq]
                )
                output += samples
                
                self.phase[freq] += 2 * np.pi * freq * frame_count / self.sample_rate
                self.phase[freq] %= (2 * np.pi)
            
            # Normalize to prevent clipping
            if len(self.active_notes) > 1:
                output /= len(self.active_notes)
            
            # If master volume is somehow tiny, force to silence
            if self.master_volume < 0.001:
                output = np.zeros(frame_count, dtype=np.float32)
            
            return (output.astype(np.float32).tobytes(), pyaudio.paContinue)
    
    def note_on(self, frequency):
        with self.lock:
            self.active_notes[frequency] = True
    
    def note_off(self, frequency):
        with self.lock:
            if frequency in self.active_notes:
                del self.active_notes[frequency]
    
    def set_bellows_pressure(self, pressure):
        #Set volume based on bellows movement (can be 0.0!)
        with self.lock:
            if pressure < 0.001:
                self.master_volume = 0.0
            else:
                self.master_volume = min(pressure, 0.6)  # Cap max volume to prevent clipping
    
    def cleanup(self):
        self.stream.stop_stream()
        self.stream.close()
        self.p.terminate()