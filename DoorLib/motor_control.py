#!/usr/bin/env python3
"""
Arduino Serial Control Library
Simple library to control Arduino via serial communication
"""

import serial
import time

class ArduinoController:
    def __init__(self, port='/dev/ttyACM0', baudrate=9600, timeout=1):
        """
        Initialize Arduino controller
        
        Args:
            port (str): Serial port path (default: /dev/ttyACM0)
            baudrate (int): Serial communication speed (default: 9600)
            timeout (int): Serial timeout in seconds (default: 1)
        """
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
    
    def _send_command(self, command):
        """
        Send command to Arduino via serial
        
        Args:
            command (str): Command to send
            
        Returns:
            str: Response from Arduino (if any)
        """
        try:
            # Open serial connection
            ser = serial.Serial(self.port, self.baudrate, timeout=self.timeout)
            
            # Wait for Arduino to initialize
            time.sleep(2)
            
            # Send command
            ser.write(command.encode('utf-8'))
            
            # Read response (optional)
            time.sleep(0.1)
            response = ""
            if ser.in_waiting > 0:
                response = ser.readline().decode('utf-8').strip()
            
            # Close connection
            ser.close()
            
            return response
            
        except serial.SerialException as e:
            raise Exception(f"Serial error: {e}. Make sure Arduino is connected to {self.port}")
        except Exception as e:
            raise Exception(f"Communication error: {e}")
    
    def turn_on(self):
        """Turn on the Arduino device"""
        response = self._send_command("#on")
        print(f"Sent: ON")
        if response:
            print(f"Arduino response: {response}")
        return response
    
    def turn_off(self):
        """Turn off the Arduino device"""
        response = self._send_command("#off")
        print(f"Sent: OFF")
        if response:
            print(f"Arduino response: {response}")
        return response
    
    def send_custom_command(self, command):
        """
        Send custom command to Arduino
        
        Args:
            command (str): Custom command to send
            
        Returns:
            str: Response from Arduino
        """
        response = self._send_command(command)
        print(f"Sent: {command}")
        if response:
            print(f"Arduino response: {response}")
        return response


# Convenience functions for quick use
def turn_on(port='/dev/ttyACM0', baudrate=9600):
    """Quick function to turn on Arduino"""
    controller = ArduinoController(port, baudrate)
    return controller.turn_on()

def turn_off(port='/dev/ttyACM0', baudrate=9600):
    """Quick function to turn off Arduino"""
    controller = ArduinoController(port, baudrate)
    return controller.turn_off()