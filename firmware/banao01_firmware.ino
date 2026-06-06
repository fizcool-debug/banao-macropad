/**
 * banao01_firmware.ino
 * 
 * Hardware Config:
 * - Arduino Leonardo (ATmega32U4)
 * - Potentiometers: P1 -> Pin A0, P2 -> Pin A1
 * - Rotary Encoder: CLK (A) -> Pin 2, DT (B) -> Pin 3, SW (Button) -> Pin 4
 * - 8-Button Matrix: Rows -> Pins 5, 6, 7; Columns -> Pins 8, 9, 10
 *   Layout (3x3 Matrix with bottom-left empty):
 *     Row 0: B1 (Col 0), B2 (Col 1), B3 (Col 2)
 *     Row 1: B4 (Col 0), B5 (Col 1), B6 (Col 2)
 *     Row 2: Empty (Col 0), B7 (Col 1), B8 (Col 2)
 */

#define PIN_POT1 A0
#define PIN_POT2 A1

#define PIN_ENCODER_A 2
#define PIN_ENCODER_B 3
#define PIN_ENCODER_BTN 4

// Matrix definitions
const int NUM_ROWS = 3;
const int NUM_COLS = 3;
const int ROW_PINS[NUM_ROWS] = {5, 6, 7};
const int COL_PINS[NUM_COLS] = {8, 9, 10};

// Map (row, col) to button index (1-8). 0 indicates the empty slot.
const int BUTTON_MAP[NUM_ROWS][NUM_COLS] = {
  {1, 2, 3}, // Row 0
  {4, 5, 6}, // Row 1
  {0, 7, 8}  // Row 2 (bottom-left coordinate [2][0] is empty)
};

// State variables
int lastPot1 = -1;
int lastPot2 = -1;
bool buttonStates[8] = {false};    // B1 - B8 (0-indexed state)
bool lastButtonStates[8] = {false};
bool lastEncoderBtn = false;
bool encoderBtnState = false;

// Encoder ISR variables
volatile bool encoderMoved = false;
volatile const char* encoderDir = "NONE";

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
  
  // Configure Matrix Row Pins (Outputs, idle HIGH)
  for (int r = 0; r < NUM_ROWS; r++) {
    pinMode(ROW_PINS[r], OUTPUT);
    digitalWrite(ROW_PINS[r], HIGH);
  }
  
  // Configure Matrix Column Pins (Inputs, internal pullup)
  for (int c = 0; c < NUM_COLS; c++) {
    pinMode(COL_PINS[c], INPUT_PULLUP);
  }
}

// Scans the 3x3 matrix and debounces the 8 buttons
void scanMatrix() {
  for (int r = 0; r < NUM_ROWS; r++) {
    // Activate current row by pulling it LOW
    digitalWrite(ROW_PINS[r], LOW);
    delayMicroseconds(10); // Settling time
    
    for (int c = 0; c < NUM_COLS; c++) {
      int btnIndex = BUTTON_MAP[r][c];
      if (btnIndex == 0) continue; // Skip empty position
      
      // Active LOW logic (switch pulls input column to GND)
      bool rawState = (digitalRead(COL_PINS[c]) == LOW);
      buttonStates[btnIndex - 1] = rawState;
    }
    
    // Deactivate row by pulling it HIGH
    digitalWrite(ROW_PINS[r], HIGH);
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
  
  // Scan Button Grid
  scanMatrix();
  
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
  
  // Check matrix buttons
  for (int i = 0; i < 8; i++) {
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
    for (int i = 0; i < 8; i++) {
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
