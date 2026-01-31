# lid.py - lid tracking stuff
import time
from pybooklid import read_lid_angle

class LidBellows:
    def __init__(self, synth, smoothing=0.08, noise_threshold=2.0):
        self.synth = synth
        self.smoothing = smoothing
        self.noise_threshold = noise_threshold
        self.velocity = 0.0
        self.last_angle = None
        self.last_time = None
        self.running = False
        
    def update_pressure(self, angle):
        # we use the delta angle (angular velocity of the lid) rather than the angle itself
        # this simulates actual bellows better
        current_time = time.time()
        
        if self.last_angle is None:
            self.last_angle = angle
            self.last_time = current_time
            return
        
        dt = current_time - self.last_time
        if dt > 0:
            # Angular velocity (degrees per second)
            raw_velocity = abs(angle - self.last_angle) / dt
            
            # Kill noise from screen wobble
            if raw_velocity < self.noise_threshold:
                raw_velocity = 0.0
            
            # Smooth with exponential moving average, lower smoothing = faster decay to zero
            self.velocity = (self.smoothing * raw_velocity + 
                           (1 - self.smoothing) * self.velocity)
            
            # Hard cutoff - if velocity drops below threshold, kill it completely
            if self.velocity < self.noise_threshold:
                self.velocity = 0.0
            
            MAX_VELOCITY = 150.0
            pressure = min(self.velocity / MAX_VELOCITY, 1.0)
            
            # Power curve for more dramatic response
            pressure = pressure ** 2.0
            
            if pressure < 0.001:
                pressure = 0.0
            
            self.synth.set_bellows_pressure(pressure)
            
            # Visual feedback, thanks claude
            if pressure > 0:
                bar_length = int(pressure * 40)
                bar = "█" * bar_length + "░" * (40 - bar_length)
                print(f"Vel: {self.velocity:6.1f}°/s | [{bar}] {pressure:.3f}")
            else:
                print(f"Vel: {self.velocity:6.1f}°/s | [░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░] 0.000 SILENCE")
        
        self.last_angle = angle
        self.last_time = current_time
    
    def start(self):
        self.running = True
        
        while self.running:
            angle = read_lid_angle()
            
            if angle is not None:
                self.update_pressure(angle)
            else:
                print("WARNING: Sensor read failed")
            
            # 100 Hz polling rate
            time.sleep(0.01)
    
    def stop(self):
        self.running = False