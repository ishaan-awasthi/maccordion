# keyboard.py - get inputs and map with notes
from pynput.keyboard import Key, Listener

def freq_from_midi(midi_note):
    return 440 * (2 ** ((midi_note - 69) / 12))

# Bass notes: Z through Shift_R (C3-A#3, MIDI 48-58) - 11 notes (no B because i can't fit it lol)
BASS_KEYS = {
    'z': 48,          # C3
    'x': 49,          # C#3
    'c': 50,          # D3
    'v': 51,          # D#3
    'b': 52,          # E3
    'n': 53,          # F3
    'm': 54,          # F#3
    ',': 55,          # G3
    '.': 56,          # G#3
    '/': 57,          # A3
    'shift_r': 58,    # A#3
}

# Major chords: A through Enter (C4-B4 major triads, MIDI 60-71) - 12 chords
MAJOR_CHORD_ROOTS = {
    'a': 60,          # C4 major
    's': 61,          # C#4 major
    'd': 62,          # D4 major
    'f': 63,          # D#4 major
    'g': 64,          # E4 major
    'h': 65,          # F4 major
    'j': 66,          # F#4 major
    'k': 67,          # G4 major
    'l': 68,          # G#4 major
    ';': 69,          # A4 major
    "'": 70,          # A#4 major
    'enter': 71,      # B4 major
}

# Minor chords: Q through ] (C4-B4 minor triads, MIDI 60-71) - 12 chords
MINOR_CHORD_ROOTS = {
    'q': 60,          # C4 minor
    'w': 61,          # C#4 minor
    'e': 62,          # D4 minor
    'r': 63,          # D#4 minor
    't': 64,          # E4 minor
    'y': 65,          # F4 minor
    'u': 66,          # F#4 minor
    'i': 67,          # G4 minor
    'o': 68,          # G#4 minor
    'p': 69,          # A4 minor
    '[': 70,          # A#4 minor
    ']': 71,          # B4 minor
}

# Melody/Treble: 1 through Backspace (C6-C7, MIDI 84-96) - 13 notes (full octave C to C)
TREBLE_KEYS = {
    '1': 84,          # C6
    '2': 85,          # C#6
    '3': 86,          # D6
    '4': 87,          # D#6
    '5': 88,          # E6
    '6': 89,          # F6
    '7': 90,          # F#6
    '8': 91,          # G6
    '9': 92,          # G#6
    '0': 93,          # A6
    '-': 94,          # A#6
    '=': 95,          # B6
    'backspace': 96,  # C7 (higher C) - Mac's delete key is backspace in pynput
}

def get_major_chord(root_midi):
    # major chords for a to return, uses inversions when higher notes
    if root_midi >= 68:  # G#4 and above - use first inversion (3rd in bass)
        return [root_midi + 4, root_midi + 7, root_midi + 12]
    elif root_midi >= 65:  # F4 to G4 - use second inversion (5th in bass)
        return [root_midi + 7, root_midi + 12, root_midi + 16]
    else:  # Lower notes - root position
        return [root_midi, root_midi + 4, root_midi + 7]

def get_minor_chord(root_midi):
    # minor chords for q to ], uses inversions when higher ntoes
    if root_midi >= 68:  # G#4 and above - use first inversion
        return [root_midi + 3, root_midi + 7, root_midi + 12]
    elif root_midi >= 65:  # F4 to G4 - use second inversion
        return [root_midi + 7, root_midi + 12, root_midi + 15]
    else:  # Lower notes - root position
        return [root_midi, root_midi + 3, root_midi + 7]

class KeyboardHandler:
    def __init__(self, synth):
        self.synth = synth
        self.currently_pressed = set()
        self.key_frequencies = {}  # {key_char: [freq1, freq2, freq3]}
        self.sustained_keys = {}  # {key_char: [freq1, freq2, freq3]} - keys held by sustain
        self.listener = None
        self.muted = False
        
    def normalize_key(self, key):
        try:
            return key.char.lower()
        except AttributeError:
            # Special keys (Enter, Shift, etc)
            key_name = str(key).replace('Key.', '')
            return key_name.lower()
    
    def on_press(self, key):
        key_char = self.normalize_key(key)
        
        # ESC to quit/stop the program
        if key_char == 'esc':
            print("\nESC pressed - shutting down maccordion...\n")
            return False
        
        # CapsLock toggles mute!
        if key_char == 'caps_lock':
            self.muted = not self.muted
            status = "MUTED" if self.muted else "UNMUTED"
            print(f"\n{status}\n")
            return
        
        # TAB toggles sustain for currently playing notes
        if key_char == 'tab':
            if self.sustained_keys:
                # Clear all sustained notes
                for key, freqs in self.sustained_keys.items():
                    for freq in freqs:
                        self.synth.note_off(freq)
                    print(f"UNSUSTAIN: {key}")
                self.sustained_keys.clear()
                print("All sustains released\n")
            else:
                # Sustain all currently playing notes
                for key, freqs in self.key_frequencies.items():
                    if key not in self.sustained_keys:
                        self.sustained_keys[key] = freqs
                        print(f"SUSTAIN: {key}")
                if self.sustained_keys:
                    print("Notes sustained (press Tab to release)\n")
            return
        
        if self.muted:
            return
        
        # Prevent key repeat
        if key_char in self.currently_pressed:
            return
        
        self.currently_pressed.add(key_char)
        frequencies = []
        note_type = None
        
        if key_char in BASS_KEYS:
            midi_note = BASS_KEYS[key_char]
            frequencies = [freq_from_midi(midi_note)]
            note_type = "BASS"
            
        elif key_char in MAJOR_CHORD_ROOTS:
            root = MAJOR_CHORD_ROOTS[key_char]
            chord_midis = get_major_chord(root)
            frequencies = [freq_from_midi(m) for m in chord_midis]
            note_type = "MAJOR"
            
        elif key_char in MINOR_CHORD_ROOTS:
            root = MINOR_CHORD_ROOTS[key_char]
            chord_midis = get_minor_chord(root)
            frequencies = [freq_from_midi(m) for m in chord_midis]
            note_type = "MINOR"
            
        elif key_char in TREBLE_KEYS:
            midi_note = TREBLE_KEYS[key_char]
            frequencies = [freq_from_midi(midi_note)]
            note_type = "TREBLE"
        
        # Play all frequencies for this key
        if frequencies:
            self.key_frequencies[key_char] = frequencies
            for freq in frequencies:
                self.synth.note_on(freq)
            
            freq_str = ", ".join([f"{f:.1f}Hz" for f in frequencies])
            print(f"{note_type} ON: {key_char} -> {freq_str}")
    
    def on_release(self, key):
        key_char = self.normalize_key(key)
        
        if key_char in self.currently_pressed:
            self.currently_pressed.remove(key_char)
            
            # Only turn off if NOT sustained
            if key_char in self.key_frequencies:
                if key_char not in self.sustained_keys:
                    # Normal release - turn off the note
                    for freq in self.key_frequencies[key_char]:
                        self.synth.note_off(freq)
                    del self.key_frequencies[key_char]
                    if not self.muted:
                        print(f"OFF: {key_char}")
                else:
                    # Key is sustained - remove from active but keep in sustained
                    del self.key_frequencies[key_char]
                    if not self.muted:
                        print(f"OFF (sustained): {key_char}")
    
    def start(self):
        self.listener = Listener(
            on_press=self.on_press,
            on_release=self.on_release
        )
        self.listener.start()
    
    def stop(self):
        if self.listener:
            self.listener.stop()