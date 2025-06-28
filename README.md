# Door Opener with Hand Gesture Recognition

A Raspberry Pi-based smart door opener that uses computer vision to recognize hand gesture sequences for secure door access. The system uses MediaPipe for real-time finger counting and controls a stepper motor via serial communication to a Seeed XIAO ESP32-C6.

## Features

- **Hand Gesture Recognition**: Uses MediaPipe to detect and count fingers in real-time
- **Sequence-based Security**: Requires a specific finger count sequence to unlock (default: 0, 1, 0, 5)
- **Visual Feedback**: NeoPixel LED ring provides status indication and feedback
- **Stepper Motor Control**: Serial communication with ESP32-C6 for precise door mechanism control
- **Session Statistics**: Tracks usage and provides summary reports

## Hardware Requirements

### Raspberry Pi Setup

- Raspberry Pi 4 (recommended) or Pi 3B+
- USB webcam
- MicroSD card (32GB+ recommended)
- Power supply (5V 3A)

### LED Ring (NeoPixel)

- WS2812B LED ring (20 LEDs recommended)
- Connected to GPIO 18 (configurable)

**Wiring:**

```
LED Ring -> Raspberry Pi
VCC      -> 5V (Pin 2)
GND      -> GND (Pin 6)
DIN      -> GPIO 18 (Pin 12)
```

### ESP32-C6 Motor Controller

- Seeed XIAO ESP32-C6 development board
- DRV8825 stepper motor driver
- Stepper motor (NEMA 17 recommended)
- 12V power supply for motor driver

**ESP32-C6 Wiring:**

```
ESP32-C6 -> DRV8825 Driver
D10      -> STEP
D9       -> DIR
D0       -> ENABLE
3.3V     -> VDD (logic power)
GND      -> GND

DRV8825 -> Motor/Power
VMOT     -> 12V+ (motor power)
GND      -> 12V- & logic GND
A1/A2    -> Motor coil A
B1/B2    -> Motor coil B
```

**Serial Connection:**

```
Raspberry Pi -> ESP32-C6
GND         -> GND
GPIO 14 (TX) -> RX (D7)
GPIO 15 (RX) -> TX (D6)
```

**Alternative USB Connection:**

- Connect ESP32-C6 via USB-C cable
- Default port: `/dev/ttyACM0`

## 3D Printed Parts

The `3D/` folder contains STL files for 3D printable components:

- **Board Holder.3mf**: Mounting case for the ESP32 and DRV8825
- **Camera Cover - Plate.3mf** & **Camera Cover - Top.3mf**: Protective housing for the camera
- **Door Gear.3mf**: Door mechanism gear component
- **Holder - Motor Holder.3mf**: Mounting bracket for the stepper motor
- **Motor Gear.3mf**: Motor-side gear for the door mechanism

Print these components before assembly to ensure proper mounting and protection of your hardware.

## Software Installation

### 1. System Setup (Raspberry Pi)

```bash
# Update Raspberry Pi OS
sudo apt update && sudo apt upgrade -y

# Install system dependencies
sudo apt install git
```

### 2. Install uv (Python Package Manager)

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Restart shell or source profile
source ~/.bashrc
```

### 3. Project Installation

```bash
# Clone repository
git clone <repository-url>
cd door-pi

# Install Python dependencies with uv
uv sync
```

### 4. ESP32-C6 Firmware Setup

#### Install PlatformIO

```bash
# Install PlatformIO Core
curl -fsSL -o get-platformio.py https://raw.githubusercontent.com/platformio/platformio-core-installer/master/get-platformio.py
python3 get-platformio.py

# Add to PATH (add to ~/.bashrc for permanent)
export PATH=$PATH:~/.platformio/penv/bin
```

#### Build and Upload Firmware

```bash
# Navigate to firmware directory
cd Firmware

# Build firmware
pio run

# Upload firmware (ESP32-C6 connected via USB)
pio run --target upload

# Optional: Monitor serial output
pio device monitor --port /dev/ttyACM0 --baud 9600
```

### 5. Enable GPIO/Serial (Raspberry Pi)

```bash
# Add user to gpio group
sudo usermod -a -G gpio $USER

# Enable serial communication (if using GPIO serial)
sudo raspi-config
# Navigate to: Interface Options -> Serial Port
# Disable login shell over serial: No
# Enable serial port hardware: Yes
```

## Configuration

### Door Sequence

Edit `main.py` to change the unlock sequence:

```python
self.DOOR_SEQUENCE = [0, 1, 0, 5]  # Change to your desired sequence
```

### Serial Port

Modify the port in `DoorLib/motor_control.py`:

```python
def turn_on(port='/dev/ttyACM0', baudrate=9600):  # Change port as needed
```

### LED Settings

Adjust LED configuration in `DoorLib/led_control.py`:

```python
def __init__(self, pixel_pin=board.D18, num_pixels=20, brightness=1.0):
```

### Motor Settings

Adjust stepper motor parameters in `Firmware/src/main.cpp`:

```cpp
#define STEP 50              // Steps to move (adjustable)
#define WAITING_TIME 5000    // Hold time in milliseconds
```

## Usage

### Running the System

```bash
# Activate virtual environment
uv run python main.py
```

### Operation

1. **Idle State**: Blue chasing light animation on LED ring
2. **Hand Detection**: LEDs show current finger count with colored regions
3. **Sequence Entry**: Enter the finger count sequence (default: fist → 1 finger → fist → 5 fingers)
4. **Success**: Green flash, door unlocks, stepper motor rotates and holds
5. **Failure**: LEDs return to idle, sequence resets

### Motor Commands

The ESP32-C6 accepts these serial commands:

- `#on`: Move stepper motor forward, hold for 5 seconds, then disable
- `#off`: Rewind stepper motor to original position and disable

### LED Indicators

- **Blue chase**: Idle/waiting for input
- **Colored regions**: Current finger count display
- **Cyan segments**: Sequence progress indication
- **Green flash**: Successful unlock
- **Return to idle**: Wrong sequence (no error indication)

## Development

### Python Environment

```bash
# Add new dependencies
uv add package-name

# Run specific commands
uv run python main.py
uv run pytest  # if tests exist
```

### ESP32-C6 Development

```bash
# Build without upload
pio run -e seeed_xiao_esp32c6

# Clean build
pio run --target clean

# Update libraries
pio lib update
```

## Security Notes

- Change the default sequence before deployment
- Consider adding time delays between sequence attempts
- Monitor the system logs for unauthorized access attempts
- Ensure proper physical security of the Raspberry Pi and ESP32-C6
- Use appropriate power ratings for your stepper motor

## Troubleshooting

### Camera Issues

```bash
# List USB cameras
lsusb | grep -i camera

# Test camera with OpenCV
python3 -c "import cv2; cap = cv2.VideoCapture(0); print('Camera available:', cap.isOpened()); cap.release()"
```

### Serial Communication

```bash
# List available serial ports
ls /dev/tty*

# Test serial connection to ESP32-C6
minicom -D /dev/ttyACM0 -b 9600
```

### LED Issues

```bash
# Check GPIO permissions
sudo chown root:gpio /dev/gpiomem
sudo chmod g+rw /dev/gpiomem
```

### ESP32-C6 Issues

```bash
# Check if device is detected
lsusb | grep -i esp

# Reset ESP32-C6 permissions
sudo chmod 666 /dev/ttyACM0
```

### Python Dependencies

```bash
# Reinstall dependencies
uv sync --reinstall
```

## License

This project is open source. Please use responsibly and ensure proper security measures for your specific use case.

## Contributing

Contributions are welcome! Please ensure all changes maintain the security and reliability of the system.
