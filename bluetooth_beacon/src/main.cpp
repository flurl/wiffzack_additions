#include <Arduino.h>
#include "BluetoothSerial.h"

#if !defined(CONFIG_BT_ENABLED) || !defined(CONFIG_BLUEDROID_ENABLED)
#error Bluetooth is not enabled! Please run `make menuconfig` to enable it.
#endif

const uint8_t LED_PIN = 26;

BluetoothSerial SerialBT;
String lastMessage = "";

// Add variables for blinking
unsigned long previousMillis = 0;
unsigned long lastMessageMillis = 0;
const unsigned long BLINK_INTERVAL = 1000; // 1 second
const unsigned long INTERVAL_WITHOUT_MESSAGE = 61000; // 61 seconds - two cycles of 30 seconds missed


void setup() {
  Serial.begin(115200); // Initialize USB Serial Monitor
  pinMode(LED_PIN, OUTPUT);
  SerialBT.begin("ESP32_Bluetooth_Beacon"); // Initialize Bluetooth SPP
  Serial.println("ESP32 Bluetooth Classic (SPP) Server Started. Waiting for connection...");
}

void loop() {
  // Check if data is available from Bluetooth
  if (SerialBT.available()) {
    lastMessage = SerialBT.readStringUntil('\n'); // Read until newline
    lastMessage.trim(); // Remove any whitespace/newline characters

    Serial.print("Received via BT: ");
    Serial.println(lastMessage);

    // Send a confirmation message back
    SerialBT.print("ACK:");
    SerialBT.println(lastMessage);

    // Blink the LED to indicate a message was received
    digitalWrite(LED_PIN, LOW);
    delay(500); // LED off for 500 ms
    digitalWrite(LED_PIN, HIGH);
    delay(500); // LED on for 500 ms

    lastMessageMillis = millis(); // Update the last message time
  }

  // Blink LED every 1 second to no messages received
  unsigned long currentMillis = millis();
  if (currentMillis - lastMessageMillis >= INTERVAL_WITHOUT_MESSAGE) { // 30 seconds without a message
    if (currentMillis - previousMillis >= BLINK_INTERVAL) {
      previousMillis = currentMillis;
      digitalWrite(LED_PIN, !digitalRead(LED_PIN)); // Toggle LED state
    }
  } else {
    if (lastMessage != "") {
      digitalWrite(LED_PIN, HIGH);
    } else {
      digitalWrite(LED_PIN, LOW);
    }
  }

  delay(10); // Small delay
}