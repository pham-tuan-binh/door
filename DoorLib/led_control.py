#!/usr/bin/env python3
"""
LED Controller Module
Handles NeoPixel LED ring animations and displays
"""

import time
import threading
import board
import neopixel

class LEDController:
    def __init__(self, pixel_pin=board.D18, num_pixels=20, brightness=1.0):
        """
        Initialize LED Controller
        
        Args:
            pixel_pin: GPIO pin for NeoPixel data
            num_pixels: Number of LEDs in ring
            brightness: LED brightness (0.0 to 1.0)
        """
        self.PIXEL_PIN = pixel_pin
        self.NUM_PIXELS = num_pixels
        self.BRIGHTNESS = brightness
        
        # Initialize NeoPixel ring
        self.pixels = neopixel.NeoPixel(self.PIXEL_PIN, self.NUM_PIXELS, 
                                       brightness=self.BRIGHTNESS, auto_write=False)
        print(f"✅ NeoPixel LED Ring initialized on GPIO 18 with {self.NUM_PIXELS} LEDs")
        
        # LED animation state
        self.led_state = "idle"  # idle, finger_count, no_hands, sequence, success
        self.current_finger_count = 0
        self.chase_position = 0
        self.led_thread = None
        self.led_running = True
        self.flash_count = 0
        self.max_flashes = 6
        
        # Finger count color mapping (no red colors)
        self.finger_colors = {
            0: (255, 255, 255),  # White - Fist
            1: (255, 165, 0),    # Orange - One finger
            2: (255, 255, 0),    # Yellow - Two fingers
            3: (0, 255, 0),      # Green - Three fingers
            4: (0, 0, 255),      # Blue - Four fingers
            5: (128, 0, 128),    # Purple - Five fingers (open hand)
        }
        
        # Special colors
        self.SUCCESS_COLOR = (0, 255, 0)    # Green
        self.SEQUENCE_COLOR = (0, 255, 255) # Cyan
        
        # Start LED animation thread
        self.led_thread = threading.Thread(target=self.led_animation_loop, daemon=True)
        self.led_thread.start()
    
    def set_all_leds(self, r, g, b):
        """Set all LEDs to specific RGB color"""
        for i in range(self.NUM_PIXELS):
            self.pixels[i] = (r, g, b)
        self.pixels.show()
    
    def set_finger_count_display(self, count):
        """Set LEDs to display finger count"""
        self.current_finger_count = count
        self.led_state = "finger_count"
    
    def set_sequence_display(self, sequence):
        """Display current sequence progress"""
        self.led_state = "sequence"
        self.current_sequence = sequence
    
    def flash_success(self):
        """Flash green for successful sequence"""
        self.led_state = "success"
        self.flash_count = 0
    
    def set_idle(self):
        """Set to idle chase animation"""
        self.led_state = "idle"
    
    def chase_animation(self):
        """Create chasing light animation for idle state"""
        # Clear all LEDs
        for i in range(self.NUM_PIXELS):
            self.pixels[i] = (0, 0, 0)
        
        # Set chase LEDs with trail
        chase_color = (0, 100, 255)  # Blue chase
        tail_length = 8
        
        for i in range(tail_length):
            led_pos = (self.chase_position - i) % self.NUM_PIXELS
            intensity = (tail_length - i) / tail_length
            r = int(chase_color[0] * intensity)
            g = int(chase_color[1] * intensity)
            b = int(chase_color[2] * intensity)
            self.pixels[led_pos] = (r, g, b)
        
        self.pixels.show()
        self.chase_position = (self.chase_position + 1) % self.NUM_PIXELS
    
    def finger_count_animation(self, count):
        """Display finger count on LED ring using regions"""
        # Clear all LEDs
        for i in range(self.NUM_PIXELS):
            self.pixels[i] = (0, 0, 0)
        
        if count in self.finger_colors:
            color = self.finger_colors[count]
            
            if count == 0:
                # Fist - all LEDs red
                self.set_all_leds(*color)
            elif count == 1:
                # One finger - rotating region of 4 LEDs
                base_pos = int(time.time() * 2) % self.NUM_PIXELS
                region_size = 4
                for i in range(region_size):
                    led_pos = (base_pos + i) % self.NUM_PIXELS
                    self.pixels[led_pos] = color
            elif count == 2:
                # Two fingers - two regions opposite sides
                base_pos = int(time.time() * 1.5) % self.NUM_PIXELS
                region_size = 3
                
                for i in range(region_size):
                    led_pos = (base_pos + i) % self.NUM_PIXELS
                    self.pixels[led_pos] = color
                
                opposite_pos = (base_pos + self.NUM_PIXELS // 2) % self.NUM_PIXELS
                for i in range(region_size):
                    led_pos = (opposite_pos + i) % self.NUM_PIXELS
                    self.pixels[led_pos] = color
            elif count >= 3:
                # Multiple regions for 3+ fingers
                region_size = max(1, self.NUM_PIXELS // (count * 2))
                spacing = self.NUM_PIXELS // count
                
                for region in range(count):
                    base_pos = region * spacing
                    for i in range(region_size):
                        led_pos = (base_pos + i) % self.NUM_PIXELS
                        self.pixels[led_pos] = color
        
        self.pixels.show()
    
    def sequence_animation(self, sequence):
        """Display sequence progress with cyan color"""
        # Clear all LEDs
        for i in range(self.NUM_PIXELS):
            self.pixels[i] = (0, 0, 0)
        
        # Light up LEDs based on sequence length
        sequence_length = len(sequence)
        if sequence_length > 0:
            leds_per_digit = self.NUM_PIXELS // 4  # Assuming max 4 digits
            
            for i in range(sequence_length):
                start_led = i * leds_per_digit
                for j in range(leds_per_digit):
                    if start_led + j < self.NUM_PIXELS:
                        self.pixels[start_led + j] = self.SEQUENCE_COLOR
        
        self.pixels.show()
    
    def flash_animation(self, color):
        """Flash animation for success/error"""
        if self.flash_count < self.max_flashes:
            if self.flash_count % 2 == 0:
                self.set_all_leds(*color)
            else:
                self.set_all_leds(0, 0, 0)
            self.flash_count += 1
        else:
            # Return to idle after flashing
            self.set_idle()
    
    def led_animation_loop(self):
        """Background thread for LED animations"""
        while self.led_running:
            if self.led_state == "idle":
                self.chase_animation()
                time.sleep(0.1)
            
            elif self.led_state == "finger_count":
                self.finger_count_animation(self.current_finger_count)
                time.sleep(0.05)
            
            elif self.led_state == "sequence":
                self.sequence_animation(getattr(self, 'current_sequence', []))
                time.sleep(0.1)
            
            elif self.led_state == "success":
                self.flash_animation(self.SUCCESS_COLOR)
                time.sleep(0.2)
            
            else:
                time.sleep(0.05)
    
    def cleanup(self):
        """Clean up LED controller"""
        self.led_running = False
        self.set_all_leds(0, 0, 0)
        print("💡 All LEDs turned off")