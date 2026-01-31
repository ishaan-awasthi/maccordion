# main.py - duh
import threading
import time
from audio import RealtimeSynth
from keyboard import KeyboardHandler
from lid import LidBellows

def main():
    print("MACCORDION")
    print("Starting synth...")
    synth = RealtimeSynth()
    
    print("Starting keyboard listener...")
    print("Press ESC to quit")
    
    # Initialize keyboard
    kbd = KeyboardHandler(synth)
    kbd.start()
    
    print("Starting bellows tracker...")
    print("Open/close lid to control volume")
    
    # Initialize lid tracker in separate thread
    bellows = LidBellows(synth)
    bellows_thread = threading.Thread(target=bellows.start, daemon=True)
    bellows_thread.start()
    
    print("\nREADY! Pump the lid and play keys!\n")
    
    try:
        # Keep main thread alive
        while kbd.listener.is_alive():
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        bellows.stop()
        kbd.stop()
        synth.cleanup()
        print("bye bye!")

if __name__ == "__main__":
    main()