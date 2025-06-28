#!/usr/bin/env python3
"""
Door Sequence Finger Count Recognizer
Recognizes finger count sequence to unlock door
"""

import cv2
import mediapipe as mp
import time
import threading
from DoorLib import turn_on, LEDController

class DoorSequenceRecognizer:
    def __init__(self):
        # Door sequence configuration
        self.DOOR_SEQUENCE = [0, 1, 0, 5]  # The secret sequence
        self.current_sequence = []
        self.sequence_timeout = 5.0  # Reset sequence after 5 seconds of no input
        self.last_input_time = time.time()
        
        # Initialize LED controller
        self.led_controller = LEDController()
        
        # Initialize MediaPipe hands
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.5
        )
        
        # Hand tracking state
        self.has_hands = False
        self.previous_has_hands = False
        self.stable_finger_count = 0
        self.finger_count_buffer = []
        self.buffer_size = 10
        self.last_stable_count = -1
        
        # Statistics
        self.finger_count_changes = 0
        self.session_start_time = time.time()
        self.door_opened = False
        
        # Video capture
        self.cap = cv2.VideoCapture(0)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.cap.set(cv2.CAP_PROP_FPS, 30)
        
        self.running = True
    
    def count_fingers(self, landmarks):
        """Count extended fingers from hand landmarks"""
        if not landmarks:
            return 0
        
        finger_tips = [4, 8, 12, 16, 20]
        finger_pips = [3, 6, 10, 14, 18]
        
        fingers_up = 0
        
        # Thumb (special case)
        if landmarks[4].x > landmarks[3].x:
            fingers_up += 1
        
        # Other fingers
        for i in range(1, 5):
            if landmarks[finger_tips[i]].y < landmarks[finger_pips[i]].y:
                fingers_up += 1
        
        return fingers_up
    
    def update_finger_count_buffer(self, count):
        """Update finger count buffer for stability"""
        self.finger_count_buffer.append(count)
        
        if len(self.finger_count_buffer) > self.buffer_size:
            self.finger_count_buffer = self.finger_count_buffer[-self.buffer_size:]
        
        # Get most common count from recent buffer
        if len(self.finger_count_buffer) >= 5:
            recent_counts = self.finger_count_buffer[-5:]
            most_common = max(set(recent_counts), key=recent_counts.count)
            
            if most_common != self.stable_finger_count:
                old_count = self.stable_finger_count
                self.stable_finger_count = most_common
                self.finger_count_changes += 1
                self.handle_finger_count_change(old_count, most_common)
    
    def handle_finger_count_change(self, old_count, new_count):
        """Handle finger count changes and sequence logic"""
        timestamp = time.strftime("%H:%M:%S")
        
        print(f"[{timestamp}] FINGER COUNT: {old_count} → {new_count}")
        
        # Check for sequence timeout
        current_time = time.time()
        if current_time - self.last_input_time > self.sequence_timeout:
            if self.current_sequence:
                print("⏰ Sequence timeout - resetting")
                self.current_sequence = []
        
        # Add to sequence if it's a new stable count
        if new_count != self.last_stable_count:
            self.current_sequence.append(new_count)
            self.last_input_time = current_time
            self.last_stable_count = new_count
            
            print(f"🔢 Sequence: {self.current_sequence}")
            print(f"🎯 Target:   {self.DOOR_SEQUENCE}")
            
            # Update LED display
            self.led_controller.set_sequence_display(self.current_sequence)
            
            # Check sequence
            self.check_sequence()
    
    def check_sequence(self):
        """Check if current sequence matches door sequence"""
        if len(self.current_sequence) > len(self.DOOR_SEQUENCE):
            # Sequence too long
            print("❌ Sequence too long - resetting")
            self.sequence_failed()
            return
        
        # Check if current sequence matches the beginning of door sequence
        matches = True
        for i, digit in enumerate(self.current_sequence):
            if digit != self.DOOR_SEQUENCE[i]:
                matches = False
                break
        
        if not matches:
            # Wrong sequence
            print("❌ Wrong sequence - resetting")
            self.sequence_failed()
            return
        
        if len(self.current_sequence) == len(self.DOOR_SEQUENCE):
            # Complete correct sequence!
            print("✅ CORRECT SEQUENCE!")
            self.sequence_success()
            return
        
        # Partial correct sequence
        remaining = len(self.DOOR_SEQUENCE) - len(self.current_sequence)
        print(f"✅ Partial match - {remaining} more digits needed")
    
    def sequence_success(self):
        """Handle successful sequence entry"""
        print("🚪 DOOR UNLOCKED!")
        print(f"🎉 Sequence {self.DOOR_SEQUENCE} entered correctly")
        
        # Flash green LEDs
        self.led_controller.flash_success()
        
        # Open door (turn on motor)
        try:
            turn_on()
            print("🔧 Motor activated - door opening")
            self.door_opened = True
            
            # TODO: Add turn_off() call here after desired time
            # Example: time.sleep(5); turn_off()  # Close door after 5 seconds
            
        except Exception as e:
            print(f"❌ Error activating motor: {e}")
        
        # Reset sequence
        self.current_sequence = []
        self.last_stable_count = -1
        
        # Optional: Add delay before allowing new sequence
        time.sleep(3)
        self.led_controller.set_idle()
    
    def sequence_failed(self):
        """Handle failed sequence entry"""
        print("🚫 Access denied")
        
        # Just reset sequence - no visual feedback
        self.current_sequence = []
        self.last_stable_count = -1
        
        # Return to normal operation
        self.led_controller.set_idle()
    
    def process_hand_detection(self, has_hands, finger_count=0):
        """Process hand detection state changes"""
        self.previous_has_hands = self.has_hands
        self.has_hands = has_hands
        
        if not self.has_hands:
            if self.previous_has_hands:
                print("🚫 Hand disappeared")
                self.finger_count_buffer.clear()
                self.stable_finger_count = 0
            
            # Show sequence progress or idle
            if self.current_sequence:
                self.led_controller.set_sequence_display(self.current_sequence)
            else:
                self.led_controller.set_idle()
        else:
            if not self.previous_has_hands:
                print("👋 Hand detected")
            
            # Show current finger count
            self.led_controller.set_finger_count_display(finger_count)
            self.update_finger_count_buffer(finger_count)
    
    def start_recognition(self):
        """Start the door sequence recognition"""
        print("🚪 DOOR SEQUENCE FINGER COUNT CONTROLLER")
        print("=" * 60)
        print(f"🔢 Secret sequence: {self.DOOR_SEQUENCE}")
        print(f"⏰ Sequence timeout: {self.sequence_timeout}s")
        print("📹 Camera active - show finger counts in sequence")
        print("💍 LED Ring shows:")
        print("   - Blue chase: Idle/waiting")
        print("   - Colored regions: Current finger count") 
        print("   - Cyan bars: Sequence progress")
        print("   - Green flash: Success (door opens)")
        print("   - No feedback: Wrong sequence (just resets)")
        print("⚡ Press Ctrl+C to stop")
        print("=" * 60)
        print("🖐️ Show your hand and enter the sequence...\n")
        
        try:
            while self.running:
                ret, frame = self.cap.read()
                if not ret:
                    continue
                
                # Convert BGR to RGB
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                # Process with MediaPipe
                results = self.hands.process(rgb_frame)
                
                if results.multi_hand_landmarks:
                    # Hand detected
                    hand_landmarks = results.multi_hand_landmarks[0]
                    finger_count = self.count_fingers(hand_landmarks.landmark)
                    self.process_hand_detection(True, finger_count)
                else:
                    # No hands detected
                    self.process_hand_detection(False)
                
                time.sleep(0.001)  # Prevent CPU overload
                
        except KeyboardInterrupt:
            print("\n🛑 Stopping recognition...")
        
        finally:
            self.cleanup()
    
    def print_session_summary(self):
        """Print session statistics"""
        session_duration = time.time() - self.session_start_time
        
        print(f"\n{'='*60}")
        print(f"DOOR SEQUENCE SESSION SUMMARY")
        print(f"{'='*60}")
        print(f"Duration: {session_duration:.1f} seconds")
        print(f"Total finger count changes: {self.finger_count_changes}")
        print(f"Door opened: {'Yes' if self.door_opened else 'No'}")
        
        if self.current_sequence:
            print(f"Final sequence attempt: {self.current_sequence}")
        
        print(f"{'='*60}\n")
    
    def cleanup(self):
        """Clean up resources"""
        self.running = False
        
        if hasattr(self, 'cap'):
            self.cap.release()
        
        self.led_controller.cleanup()
        self.print_session_summary()
        print("✅ Session ended")

def main():
    """Main function"""
    try:
        recognizer = DoorSequenceRecognizer()
        recognizer.start_recognition()
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()