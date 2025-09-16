// Filename: FinalProjectReceiver.ino
// Authors: Akhil Srinivasan
// Date: 03/15/2025
// Description: This file controls an ESP32 that receives light and temperature sensor readings from a separate sender. Based on the values,
// it updates an LCD display that shows raw values and headlight/AC status, switching every 15 seconds. It also uses an external LED to display
// the headlights, turning it on or off accordingly.

// ========================= Includes =========================
#include <Arduino.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include <esp_now.h>
#include <WiFi.h>
#include <Wire.h>
#include <LiquidCrystal_I2C.h>

// ========================= Macros =========================
#define LED_PIN 4
#define LIGHT_THRESHOLD 300
#define TEMP_LOW 60
#define TEMP_HIGH 75

// ========================= Global Variables =========================
volatile bool displayVal = true; // Keeps track of whether LCD should display raw values or headlight and AC status
volatile bool toggled = false; // Flag that tracks whether display type was just toggled
volatile bool messageReceived = false; // Flag that tracks whether ESP-NOW message was just received
bool headlights = false; // Flag that tracks whether headlights should be on

typedef struct sensor_message {
  int light;
  int temp;
} sensor_message; // Struct that holds sensor readings
sensor_message msg = {0, 0}; // Initalize struct to hold received data

// FreeRTOS Handles
SemaphoreHandle_t headlightSemaphore = NULL; // Handle for headlight semaphore

QueueHandle_t lightQueue = NULL; // Handle for light sensor readings queue
QueueHandle_t tempQueue = NULL; // Handle for temperature sensor readings queue

TimerHandle_t displayTimer = NULL; // Handle for software timer controlling LCD display type

TaskHandle_t Message_Handle = NULL; // Handle for message receiving task
TaskHandle_t LCD_Handle = NULL; // Handle for LCD display task
TaskHandle_t Headlight_Handle = NULL; // Handle for headlight LED task

LiquidCrystal_I2C lcd(0x27, 16, 2); // Initalize LCD display

// Name: dataReceived
// Description: ISR that updates messageReceived flag and copies received data into msg struct when a message is received
void IRAM_ATTR dataReceived(const esp_now_recv_info_t * esp_now_info, const uint8_t *incomingData, int len) {
  messageReceived = true;
  memcpy(&msg, (sensor_message *) incomingData, sizeof(sensor_message)); // Copy the incoming data into the struct
}

// Name: DisplayTimer_Callback
// Description: Callback function that toggles display type when timer alarm is triggered every 15 seconds
void DisplayTimer_Callback(TimerHandle_t xTimer) {
  displayVal = !displayVal;
  toggled = true;
}

void setup() {
  // Initialize LED pin
  pinMode(LED_PIN, OUTPUT);
  // Initalize Serial Monitor
  Serial.begin(9600);
  while(!Serial);
  // Initialize LCD display
  lcd.init();
  lcd.begin(16, 2);
  lcd.backlight();
  delay(2);

  // Create software timer that triggers every 15 seconds to toggle LCD display type, and attach it to callback function
  displayTimer = xTimerCreate("Display Timer", pdMS_TO_TICKS(15000), pdTRUE, NULL, DisplayTimer_Callback);
  // Check if timer was created successfully, and start it
  if (displayTimer != NULL) {
    xTimerStart(displayTimer, 0);
  } else {
    Serial.println("Error initializing timer");
    return;
  }

  // Create semaphore for headlights
  headlightSemaphore = xSemaphoreCreateBinary();
  // Check if semaphore was created successfully, and give it initially
  if (headlightSemaphore != NULL) {
    xSemaphoreGive(headlightSemaphore);
  } else {
    Serial.println("Error initializing semaphore");
    return;
  }

  // Create queues for light and temperature readings
  lightQueue = xQueueCreate(3, sizeof(int));
  tempQueue = xQueueCreate(3, sizeof(int));

  // Create FreeRTOS tasks
  xTaskCreate(Message_Task, "Message", 2048, NULL, 1, &Message_Handle);
  xTaskCreate(LCD_Task, "LCD", 4096, NULL, 1, &LCD_Handle);
  xTaskCreate(Headlight_Task, "Headlight", 2048, NULL, 1, &Headlight_Handle);
  
  // Initalize ESP-NOW and wifi mode
  WiFi.mode(WIFI_STA);
  if (esp_now_init() != ESP_OK) {
    Serial.println("Error initializing ESP-NOW"); // Make sure ESP-NOW initalized properly
    return;
  }
  // Registers the callback function 'dataReceived' to be called when data is received via ESP-NOW
  esp_now_register_recv_cb(dataReceived);
}

void loop() {
  // FreeRTOS does not use loop function
}

// Name: Message_Task
// Description: Checks whether a message was just received. If received, then extracts data from struct and sends it with corresponding queues.
void Message_Task(void *pvParameter) {
  while(1) {
    // Check if message received
    if (messageReceived) {
      // Send light and temp data with queues
      xQueueSend(lightQueue, &msg.light, portMAX_DELAY);
      xQueueSend(tempQueue, &msg.temp, portMAX_DELAY);
      messageReceived = false; // Reset messageReceived flag
    }
    vTaskDelay(pdMS_TO_TICKS(1000)); // Delay to prevent CPU overuse
  }
}

// Name: Headlight_Task
// Description: Checks whether or not headlights should be on, and toggles LED accordingly.
void Headlight_Task(void *pvParameter) {
  bool oldLight = false; // Tracks if headlights are on currently
  bool changed = false; // Tracks whether headlight status has changed
  while(1) {
    // Take semaphore to ensure consistent access to headlight flag
    if (xSemaphoreTake(headlightSemaphore, portMAX_DELAY) == pdPASS) {
      // If headlight status has changed, update flags
      if (oldLight != headlights) {
        changed = true;
        oldLight = headlights; // Store new headlight value
      }
      xSemaphoreGive(headlightSemaphore); // Give back semaphore once updated
    }
    
    // If headlight status has changed, then toggle LED accordingly
    if (changed) {
      digitalWrite(LED_PIN, oldLight ? HIGH : LOW); // LED is on if headlights should be on, and off otherwise
      changed = false; // Reset changed flag
    }
    vTaskDelay(pdMS_TO_TICKS(100)); // Small delay to prevent CPU overuse
  }
}

// Name: LCD_Task
// Description: Controls the LCD display to show raw sensor values or headlight and AC status, switching every 15 seconds.
void LCD_Task(void *arg) {
    int light, temp = 0; // Tracks current light and temperature readings
    bool changed = false; // Tracks whether new data has been received
    while(1) {
      // Check whether data has been received
      if (xQueueReceive(lightQueue, &light, 0) == pdPASS || xQueueReceive(tempQueue, &temp, 0) == pdPASS) {
        // If new data is received, update changed flag
        changed = true;
        // Based on new light level, check if headlights should be on, taking semaphore to ensure consistency
        if (xSemaphoreTake(headlightSemaphore, portMAX_DELAY) == pdPASS) {
          // Update headlight status based on light threshold
          headlights = light < LIGHT_THRESHOLD ? true : false;
          xSemaphoreGive(headlightSemaphore); // Give back semaphore once updated
        }
      }

      // If LCD values have changed, or display type was toggled, refresh display with new information
      if (changed || toggled) {
        // Check if display should show raw values
        if (displayVal) {
          lcd.clear();
          // Print raw values for light and temperature
          lcd.print("Light: ");
          lcd.print(light);
          lcd.setCursor(0, 1);
          lcd.print("Temp: ");
          lcd.print(temp);
          lcd.print(" °F");
        } else {
          // If LCD should show headlight and AC status, display correspondingly
          lcd.clear();
          lcd.print("Headlights: ");
          lcd.print(light < LIGHT_THRESHOLD ? "On" : "Off");  // Ternary for headlights status
          lcd.setCursor(0, 1);
          lcd.print("AC: ");
          lcd.print(temp < TEMP_LOW ? "Heat" : (temp > TEMP_HIGH ? "Cool" : "Off"));  // Ternary for AC status
        }
        toggled = false; // Reset toggled flag
        changed = false; // Reset changed flag
      }
      vTaskDelay(pdMS_TO_TICKS(100)); // Small delay to prevent CPU overuse
    }
}
