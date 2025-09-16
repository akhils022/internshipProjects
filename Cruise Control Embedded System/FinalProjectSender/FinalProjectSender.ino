// Filename: FinalProjectSender.ino
// Authors: Akhil Srinivasan
// Date: 03/15/2025
// Description: This file controls a complex cruise control system. It uses a stepper motor as the car, and an LCD display as the speedometer to provide
// a visual of the speed for the user. It uses three user input buttons that control that starting/stopping of the car engine, the acceleration,
// and the braking respectively. The "car" maintains constant speed unless the user increases or decreases the speed. The system also includes
// and ultrasonic collision detection system that, depending on if an object is detected nearby, brakes for the user until the car reaches safety.
// The user sees a flashing warning light when an object is detected nearby. The system also records outside lighting and temperature, sending it
// to another ESP32 that conntrols the headlights and air conditioning system.

// ========================= Includes =========================
#include <Arduino.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "freertos/timers.h"
#include <Stepper.h>
#include <esp_now.h>
#include <WiFi.h>
#include "Adafruit_Sensor.h"
#include "Adafruit_AM2320.h"
#include "Wire.h"
#include <LiquidCrystal_I2C.h>

// ========================= Macros =========================
#define LED_PIN 1 // Pin for warning light
#define BUTTON_GAS 40 // Acceleration button
#define BUTTON_BRAKE 41 // Deceleration button
#define BUTTON_START 4 // Button to start system
#define PHOTO_PIN 2 // Pin for photoresistor
#define TRIG_PIN 11 // trig pin for distance sensor
#define ECHO_PIN 10 // echo pin for distance sensor
#define DIST_THRESHOLD 25 // Threshold for collision distance
#define MAX_SPEED 75 // Maximum motor speed
#define STEPS 200 // Motor steps per revolution

// ========================= Global Variables =========================
uint8_t broadcastAddress[] = {0x24, 0xEC, 0x4A, 0x0E, 0xAE, 0xF8}; // Broadcast address for receiving ESP32
volatile int speed = 0; // Current motor speed
volatile int count = 0; // Counter to ensure acceleration is slowing than braking
volatile bool speedUpdate = false; // Flag for updating speed
bool collision = false; // Flag for potential collision object being detected
bool started = false; // Flag for starting program
volatile bool distanceUpdate = false; // Flag for running distance sensor
hw_timer_t * timer = NULL; // Hardware timer

// Initialize peripherals
Stepper stepper(STEPS, 39, 38, 37, 36); // Stepper motor
Adafruit_AM2320 tempSensor = Adafruit_AM2320(); // Temperature sensor
LiquidCrystal_I2C lcd(0x27, 16, 2); // LCD display

// FreeRTOS Handles
SemaphoreHandle_t collisionSemaphore = NULL; // Handle for collision semaphore
SemaphoreHandle_t speedSemaphore = NULL; // Handle for speed semaphore

// Handles for FreeRTOS tasks
TaskHandle_t Led_Handle = NULL; // Handle for warning light task
TaskHandle_t Motor_Handle = NULL; // Handle for motor control task
TaskHandle_t Distance_Handle = NULL; // Handle for distance sensor task
TaskHandle_t Sensor_Handle = NULL; // Handle for temperature and light sensor task
TaskHandle_t Speedometer_Handle = NULL; // Handle for LCD speedometer task
TaskHandle_t Start_Handle = NULL; // Handle for engine starting and stopping task

typedef struct sensor_message {
  int light;
  int temp;
} sensor_message; // Struct for storing sensor data

// Name: CollisionUpdate
// Description: ISR that updates flags to ensure distance is measured and speed is updated at timer alarm
void IRAM_ATTR TimerUpdate() {
  distanceUpdate = true; // Update distance flag to ensure distance is measured
  count = (count + 1) % 4; // Increment count with wrap around to ensure gas is 4x slower than braking
  speedUpdate = true; // Update flag to ensure speed is updated
}

// Name: onDataSent
// Description: Callback function that checks whether data was sent successfuly by ESP-NOW
void onDataSent(const uint8_t *mac_addr, esp_now_send_status_t status) {
  // Check if the delivery was successful and print the status
  Serial.println(status == ESP_NOW_SEND_SUCCESS ? "Success" : "Failed");
}

void setup() {
  // Initialize input and output hardware pins
  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);
  pinMode(LED_PIN, OUTPUT);
  pinMode(BUTTON_BRAKE, INPUT_PULLUP);
  pinMode(BUTTON_GAS, INPUT_PULLUP);
  pinMode(BUTTON_START, INPUT_PULLUP);
  pinMode(PHOTO_PIN, INPUT);
  // Ensure analog resolution is 10 bits
  analogReadResolution(10);

  // Begin I2C communication with SDA pin 5, SCL pin 6
  Wire.begin(5, 6);
  // Initalize LCD display
  lcd.init();
  lcd.begin(16, 2);
  lcd.backlight();
  // Initalize temperature sensor and ensure proper functionality
  if (!tempSensor.begin()) {
    Serial.println("Error initializing temperature sensor");
    return;
  }
  delay(2);
  // Open serial communication
  Serial.begin(9600);
  while (!Serial);
  
  // Initialize hardware timer that has 32 Hz alarm signal
  timer = timerBegin(32000);  // Frequency of 32000 (32 kHz)
  timerAttachInterrupt(timer, &TimerUpdate);  // Attach the interrupt service routine
  timerAlarm(timer, 1000, true, 0);  // 32000 / 1000 = 32 Hz frequency

  // Initalize ESP-NOW and wifi modes, and check for success
  WiFi.mode(WIFI_STA);
  if (esp_now_init() != ESP_OK) {
    Serial.println("Error initializing ESP-NOW");
    return;
  }
  esp_now_register_send_cb(onDataSent);  // Register the send callback function
  esp_now_peer_info_t peerInfo;  // Data structure for handling peer information
  // Copy the receiver's MAC address to peer information
  memset(&peerInfo, 0, sizeof(peerInfo));
  memcpy(peerInfo.peer_addr, broadcastAddress, 6);
  peerInfo.channel = 0; // Set WiFi channel to 0 (default)
  peerInfo.encrypt = false; // Disable encryption
  // Add peer and check for success
  if (esp_now_add_peer(&peerInfo) != ESP_OK){
    Serial.println("Error initializing ESP-NOW");
    return; 
  } 

  // Create binary semaphores for collision and speed, and give them initially
  collisionSemaphore = xSemaphoreCreateBinary();
  if (collisionSemaphore != NULL) {
    xSemaphoreGive(collisionSemaphore);
  } else {
    Serial.println("Error initializing semaphore");
    return;
  }
  speedSemaphore = xSemaphoreCreateBinary();
  if (speedSemaphore != NULL) {
    xSemaphoreGive(speedSemaphore);
  } else {
    Serial.println("Error initializing semaphore");
    return;
  }

  // Create FreeRTOS tasks and pin all to core 0 except motor task, which runs separately because of its high priority and high frequency
  // Suspend all tasks initially, except Start_Task, to ensure system begins off until start button pressed
  xTaskCreatePinnedToCore(Distance_Task, "Distance Task", 2048, NULL, 1, &Distance_Handle, 0);
  vTaskSuspend(Distance_Handle);
  xTaskCreatePinnedToCore(Motor_Task, "Motor Task", 2048, NULL, 1, &Motor_Handle, 1);
  vTaskSuspend(Motor_Handle);
  xTaskCreatePinnedToCore(LED_Task, "LED Task", 2048, NULL, 1, &Led_Handle, 0);
  vTaskSuspend(Led_Handle);
  xTaskCreatePinnedToCore(Sensor_Task, "Sensor Task", 2048, NULL, 1, &Sensor_Handle, 0);
  vTaskSuspend(Sensor_Handle);
  xTaskCreatePinnedToCore(Speedometer_Task, "Speedometer Task", 2048, NULL, 1, &Speedometer_Handle, 0);
  vTaskSuspend(Speedometer_Handle);
  xTaskCreatePinnedToCore(Start_Task, "Start Task", 2048, NULL, 1, &Start_Handle, 0);
}

void loop() {
  // FreeRTOS does not use loop function
}

// Name: Distance_Task
// Description: Uses the ultrasonic distance sensor to measure the closest object. If an object is detected within the threshold, it toggles the collision
// flag to true. The task runs at a frequency of 32 Hz, handled by the hardware timer.
void Distance_Task(void *pvParameter) {
  while(1) {
    // Checks whether we should run distance sensor based on 32 Hz hardware timer flag
    if (distanceUpdate) {
      // Measure distance using trig and echo pins
      digitalWrite(TRIG_PIN, LOW);
      delayMicroseconds(2);
      digitalWrite(TRIG_PIN, HIGH);
      delayMicroseconds(10);
      digitalWrite(TRIG_PIN, LOW);
      float duration = pulseIn(ECHO_PIN, HIGH);
      // Calculate distance using speed of sound, capped at 400 cm to ensure consistency
      int distance;
      if (duration == 0) {
        distance = 400; // If no pulse is detected, assume max distance.
      } else {
        distance = min((int)((duration * .0343) / 2), 400);
      }

      // Take semaphore to ensure synchronization across cores
      if (xSemaphoreTake(collisionSemaphore, portMAX_DELAY) == pdPASS) {
        // If object detected in threshold, update collision flag to true
        if (distance < DIST_THRESHOLD) {
          collision = true;
        } else {
          collision = false;
        }
        xSemaphoreGive(collisionSemaphore); // Give back semaphore once updated
      }
      distanceUpdate = false; // Reset distanceUpdate flag
    }
    vTaskDelay(pdMS_TO_TICKS(5)); // small delay to prevent CPU overuse
  }
}

// Name: Motor_Task
// Description: Controls the speed of the stepper motor when running it. Updates the current motor speed based on inputs from
// the gas and brake buttons and the collision detector.
void Motor_Task(void *pvParameter) {
  int change = 0; // flag that handles how to update speed: 0 = no change, 1 = decrement, 2 = increment
  while(1) {
    // Checks if speed should be updated, which is controlled by 32 Hz hardware timer
    if (speedUpdate) {
      // Take semaphore before accessing collision flag
      if (xSemaphoreTake(collisionSemaphore, pdMS_TO_TICKS(10)) == pdPASS) {
        // If collision possible, or brake held, then set flag to 1 to decrement speed
        // Ensures collision detector stops car fastest at 32 Hz, and brake stops car a bit slower at 16 Hz to add safety
        if (collision || (count == 1 || count == 3) && digitalRead(BUTTON_BRAKE) == LOW) {
          change = 1;
        // Otherwise, if gas button held, and speed is below maximum, set flag to 1 to increment speed
        // Acceleration happens 4x slower at 8 Hz for more realistic speeding up
        } else if (count == 3 && digitalRead(BUTTON_GAS) == LOW && speed < MAX_SPEED) {
          change = 2;
        } // Otherwise, flag is 0 for constant speed
        xSemaphoreGive(collisionSemaphore); // Give back semaphore
      }

      // Take speed semaphore before updating motor speed
      if (xSemaphoreTake(speedSemaphore, pdMS_TO_TICKS(10)) == pdPASS) {
        // If car is moving and should slow, decrement speed
        if (change == 1 && speed > 0) {
          speed--;
        // If car should accelerate and has not reached maxiumum speed, increment speed
        } else if (change == 2) {
          speed++;
        }
        xSemaphoreGive(speedSemaphore); // Give back semaphore
      }
      speedUpdate = false; // Reset speedUpdate flag
      change = 0; // Reset change flag
    }

    // Run motor at specified rate if speed is above 0
    // Note: Semaphore not needed here because the only possibility of a conflict is a Read-Read
    // conflict with Speedometer_Task, which will not result in any issues
    if (speed > 0) {
      stepper.setSpeed(speed); // Set motor speed
      stepper.step(STEPS / 100); // Move 1/100th of a revolution
    }
    vTaskDelay(pdMS_TO_TICKS(2)); // Small delay to prevent CPU overuse
  }
}

// Name: LED_Task
// Description: Controls an external LED warning light that flashes 3 times when the distance sensor detects an object 
// within the threshold, indicating a possibiliy of collision.
void LED_Task(void *pvParameter) {
  bool alarm = false; // Flag for object detected
  while(1) {
    // Take semaphore and update alarm flag to ensure synchronization without hogging semaphore
    if (xSemaphoreTake(collisionSemaphore, portMAX_DELAY) == pdPASS) {
      alarm = collision;
      xSemaphoreGive(collisionSemaphore); // Give back semaphore
    }
    
    // If collision possibility is detected, flash LED 3 times at half second intervals
    if (alarm) {
      for (int i = 0; i < 3; i++) {
        digitalWrite(LED_PIN, HIGH);
        vTaskDelay(pdMS_TO_TICKS(500));
        digitalWrite(LED_PIN, LOW);
        vTaskDelay(pdMS_TO_TICKS(500));
      }
      alarm = false; // Reset alarm flag
    }
    vTaskDelay(pdMS_TO_TICKS(20)); // Small delay to prevent CPU overuse
  }
}

// Name: Speedometer_Task
// Description: Controls external LCD display that acts as an speedometer, displaying current motor speed as miles per hour (MPH)
void Speedometer_Task(void *pvParameter) {
  int oldSpeed = 0; // Tracks previously recorded motor speed
  bool update = false; // Flag that tracks whether speed has changed
  // Clear and initialize LCD
  lcd.clear();
  lcd.print("Speed: 00 MPH");
  while(1) {
    // Take speed semaphore to ensure consistency and prevent data race
    if (xSemaphoreTake(speedSemaphore, pdMS_TO_TICKS(10)) == pdPASS) {
      // If speed has changed, update flag and oldSpeed
      if (oldSpeed != speed) {
        oldSpeed = speed;
        update = true;
      }
      xSemaphoreGive(speedSemaphore); // Give back semaphore
    }

    // If speed has changed, then update LCD display with new speed
    if (update) {
      lcd.setCursor(7, 0);
      if (oldSpeed < 10) { // Extra 0 if single digit speed
        lcd.print(0);
      }
      lcd.print(oldSpeed); // Replace old speed with new speed
    }
    update = false; // Reset update flag
    vTaskDelay(pdMS_TO_TICKS(100)); // Small delay to prevent CPU overuse
  }
}

// Name: Sensor_Task
// Description: Measures ambient lighting and temperature, and uses ESP-NOW to send it to receiving device
void Sensor_Task(void *arg) {
    sensor_message message = {0, 0}; // Initalize sensor message struct with default values
    while(1) {
        message.light = analogRead(PHOTO_PIN); // Read photoresistor value
        message.temp = (int) (tempSensor.readTemperature() * 1.8 + 32); // Read temperature value, convert to Fahrenheit (°F), and cast it to integer
        esp_now_send(broadcastAddress, (uint8_t *) &message, sizeof(sensor_message)); // Send message to receiving device
        vTaskDelay(pdMS_TO_TICKS(5000)); // Delay to ensure sensor measurements are taken every 5 seconds
    }
}

// Name: Start_Task
// Description: Controls the starting and stopping of the cruise control system using a start button
void Start_Task(void *arg) {
    while(1) {
        // Check if start button is held down
        if (digitalRead(BUTTON_START) == LOW) {
          vTaskDelay(pdMS_TO_TICKS(50)); // debouncing for metastability
          started = !started; // Toggle started flag
          // If system is now running, resume all tasks
          if (started) {
            vTaskResume(Distance_Handle);
            vTaskResume(Motor_Handle);
            vTaskResume(Led_Handle);
            vTaskResume(Sensor_Handle);
            vTaskResume(Speedometer_Handle);
          // If system is now stopped, suspend all tasks
          } else {
            vTaskSuspend(Distance_Handle);
            vTaskSuspend(Led_Handle);
            vTaskSuspend(Sensor_Handle);
            // Ensure speed decreases down to 0 and motor stops before suspending motor and speedometer tasks
            collision = true; // Temporarily force collision system to slow down car
            while (speed != 0) {
              vTaskDelay(pdMS_TO_TICKS(10));
            }
            vTaskDelay(pdMS_TO_TICKS(100));
            vTaskSuspend(Speedometer_Handle);
            vTaskSuspend(Motor_Handle);
            collision = false; // Reset collision flag until system is started again
          }
        }
      vTaskDelay(pdMS_TO_TICKS(2000)); // Delay that forces button to be held longer to start/stop system, similar to a real car engine button
    }
}