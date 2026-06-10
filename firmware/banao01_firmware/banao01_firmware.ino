/**
 * banao01_firmware.ino
 * 
 * Hardware Config:
 * - Arduino Leonardo (ATmega32U4)
 * - Potentiometers: P1 -> Pin A0, P2 -> Pin A1
 * - Rotary Encoder: CLK (A) -> Pin 2, DT (B) -> Pin 3, SW (Button) -> Pin 4
 * - 8 Buttons: Connected directly to Pins 5, 6, 7, 8, 9, 10, 14, 15
 *   (Other side of each button connects to GND)
 */

#define PIN_POT1 A0
#define PIN_POT2 A1

#define PIN_ENCODER_A 2
#define PIN_ENCODER_B 3
#define PIN_ENCODER_BTN 4

// Direct Button configuration
const int NUM_BUTTONS = 8;
const int BUTTON_PINS[NUM_BUTTONS] = {5, 6, 7, 8, 9, 10, 14, 15};

// State variables
int lastPot1 = -1;
int lastPot2 = -1;
bool buttonStates[NUM_BUTTONS] = {false};    // B1 - B8 (0-indexed state)
bool lastButtonStates[NUM_BUTTONS] = {false};
bool lastEncoderBtn = false;

// Encoder ISR variables
volatile bool encoderMoved = false;
const char* volatile encoderDir = "NONE";

// Debounce settings
unsigned long lastDebounceTime = 0;
const unsigned long DEBOUNCE_DELAY = 15; // ms

// Hysteresis threshold for Analog Potentiometers
const int POT_HYSTERESIS = 3;

// Interrupt Service Routine for Rotary Encoder (CLK/Pin 2)
void encoderISR() {
  static unsigned long lastInterruptTime = 0;
  unsigned long interruptTime = millis();
  
  // Software debouncing for encoder contacts
  if (interruptTime - lastInterruptTime > 4) {
    // Read DT (Pin 3) to determine direction on CLK falling edge
    if (digitalRead(PIN_ENCODER_A) == LOW) {
      if (digitalRead(PIN_ENCODER_B) == HIGH) {
        encoderDir = "CW";
      } else {
        encoderDir = "CCW";
      }
      encoderMoved = true;
    }
  }
  lastInterruptTime = interruptTime;
}

void setup() {
  Serial.begin(115200);
  
  // Configure Encoder Pins
  pinMode(PIN_ENCODER_A, INPUT_PULLUP);
  pinMode(PIN_ENCODER_B, INPUT_PULLUP);
  pinMode(PIN_ENCODER_BTN, INPUT_PULLUP);
  
  // Attach hardware interrupt to CLK (Pin 2)
  attachInterrupt(digitalPinToInterrupt(PIN_ENCODER_A), encoderISR, FALLING);
  
  // Configure Button Pins (Direct input with pullup)
  for (int i = 0; i < NUM_BUTTONS; i++) {
    pinMode(BUTTON_PINS[i], INPUT_PULLUP);
  }
}

// Reads the directly connected button states
void readButtons() {
  for (int i = 0; i < NUM_BUTTONS; i++) {
    // Active LOW logic (switch connects input pin to GND when pressed)
    buttonStates[i] = (digitalRead(BUTTON_PINS[i]) == LOW);
  }
}

// Reads pot with a deadzone/hysteresis to eliminate serial flood on signal drift
int readPotWithHysteresis(int pin, int &lastVal) {
  int raw = analogRead(pin);
  
  if (abs(raw - lastVal) > POT_HYSTERESIS) {
    lastVal = raw;
  }
  
  // Ensure we reach absolute boundaries cleanly
  if (raw < POT_HYSTERESIS) lastVal = 0;
  if (raw > 1023 - POT_HYSTERESIS) lastVal = 1023;
  
  return lastVal;
}

void loop() {
  // 100Hz Main Loop rate (10ms scan window)
  delay(10);
  
  // Read potentiometers
  int currentPot1 = readPotWithHysteresis(PIN_POT1, lastPot1);
  int currentPot2 = readPotWithHysteresis(PIN_POT2, lastPot2);
  
  // Read Buttons directly
  readButtons();
  
  // Read Encoder button (Active LOW)
  bool currentEncoderBtn = (digitalRead(PIN_ENCODER_BTN) == LOW);
  
  // Check if any state changed
  bool stateChanged = false;
  
  // Check potentiometers
  static int sentPot1 = -1;
  static int sentPot2 = -1;
  if (currentPot1 != sentPot1 || currentPot2 != sentPot2) {
    stateChanged = true;
  }
  
  // Check buttons
  for (int i = 0; i < NUM_BUTTONS; i++) {
    if (buttonStates[i] != lastButtonStates[i]) {
      stateChanged = true;
    }
  }
  
  // Check encoder button
  if (currentEncoderBtn != lastEncoderBtn) {
    stateChanged = true;
  }
  
  // Check rotary encoder movement
  if (encoderMoved) {
    stateChanged = true;
  }
  
  // If anything changed, send the packet
  if (stateChanged) {
    // Format: P1:512|P2:1023|B1:0|B2:1|B3:0|B4:0|B5:0|B6:0|B7:0|B8:0|E1:CW|EB:0
    Serial.print("P1:");
    Serial.print(currentPot1);
    Serial.print("|P2:");
    Serial.print(currentPot2);
    
    // Output B1 to B8
    for (int i = 0; i < NUM_BUTTONS; i++) {
      Serial.print("|B");
      Serial.print(i + 1);
      Serial.print(":");
      Serial.print(buttonStates[i] ? "1" : "0");
      lastButtonStates[i] = buttonStates[i];
    }
    
    // Output Encoder direction
    Serial.print("|E1:");
    Serial.print(encoderDir);
    
    // Output Encoder Button
    Serial.print("|EB:");
    Serial.print(currentEncoderBtn ? "1" : "0");
    Serial.println();
    
    // Sync sent state
    sentPot1 = currentPot1;
    sentPot2 = currentPot2;
    lastEncoderBtn = currentEncoderBtn;
    
    // Reset encoder movement variables after transmitting the event
    if (encoderMoved) {
      encoderMoved = false;
      encoderDir = "NONE";
    }
  }
}
