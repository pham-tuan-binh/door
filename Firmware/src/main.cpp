#include <AccelStepper.h>

// ========== Motor pin definitions ==========
#define MOTOR1_STEP_PIN D10
#define MOTOR1_DIR_PIN D9
#define MOTOR2_STEP_PIN D8
#define MOTOR2_DIR_PIN D7
#define ENABLE_PIN D0
#define STEP 50
#define WAITING_TIME 5000 // 10 seconds in milliseconds
// Create stepper motor object (driver type, step pin, direction pin)
AccelStepper motor1(AccelStepper::DRIVER, MOTOR1_STEP_PIN, MOTOR1_DIR_PIN);

bool motorRunning = false;
bool isRewinding = false;
unsigned long waitStartTime = 0;
bool isWaiting = false;

void setup()
{
  Serial.begin(9600);

  // Set enable pin as output and disable motors initially
  pinMode(ENABLE_PIN, OUTPUT);
  digitalWrite(ENABLE_PIN, HIGH); // HIGH = disabled for DRV8825

  // Configure motor settings
  motor1.setMaxSpeed(1000);    // steps per second
  motor1.setAcceleration(500); // steps per second squared

  Serial.println("DRV8825 Motor Controller Ready");
  Serial.println("Send '#on' to run STEP steps clockwise, wait 10s, then auto-disable");
  Serial.println("Send '#off' to rewind STEP steps and disable motor");
}

void loop()
{
  // Check for serial commands
  if (Serial.available() > 0)
  {
    String command = Serial.readStringUntil('\n');
    command.trim(); // Remove whitespace
    command.toLowerCase();

    if (command == "#on")
    {
      if (!motorRunning && !isRewinding && !isWaiting)
      {
        Serial.println("Motor ON - Running STEP steps clockwise");
        digitalWrite(ENABLE_PIN, LOW);                  // LOW = enabled for DRV8825
        motor1.moveTo(motor1.currentPosition() + STEP); // Move STEP steps clockwise
        motorRunning = true;
        isWaiting = false;
      }
      else
      {
        Serial.println("Motor is already running, rewinding, or waiting to be disabled");
      }
    }
    else if (command == "#off")
    {
      if (!isRewinding)
      {
        Serial.println("Motor OFF - Rewinding STEP steps");
        digitalWrite(ENABLE_PIN, LOW);                  // Enable motor for rewinding
        motor1.moveTo(motor1.currentPosition() - STEP); // Rewind STEP steps
        motorRunning = false;
        isWaiting = false;
        isRewinding = true;
      }
      else
      {
        Serial.println("Motor is already rewinding");
      }
    }
    else
    {
      Serial.println("Unknown command. Use '#on' or '#off'");
    }
  }

  // Handle motor movement and timing
  if (motorRunning)
  {
    motor1.run();

    // Check if motor finished moving STEP steps
    if (motor1.distanceToGo() == 0 && !isWaiting)
    {
      Serial.println("STEP steps completed. Waiting 5 seconds...");
      waitStartTime = millis();
      isWaiting = true;
    }
  }

  // Handle rewinding movement
  if (isRewinding)
  {
    motor1.run();

    // Check if rewind is complete
    if (motor1.distanceToGo() == 0)
    {
      Serial.println("Rewind complete. Motor disabled.");
      digitalWrite(ENABLE_PIN, HIGH); // Disable motor
      isRewinding = false;
    }
  }

  // Handle 10-second wait and auto-disable
  if (isWaiting)
  {
    if (millis() - waitStartTime >= WAITING_TIME)
    { // 10 seconds = WAITING_TIME milliseconds
      Serial.println("Wait complete. Motor OFF - Disabled");
      digitalWrite(ENABLE_PIN, HIGH); // Disable motor
      motorRunning = false;
      isWaiting = false;
    }
  }
}