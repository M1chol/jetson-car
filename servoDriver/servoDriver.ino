#include <SCServo.h>

#define S_RXD 18
#define S_TXD 19

SMS_STS st;

const int SERVO_ID_1 = 1;
const int SERVO_ID_2 = 2;
const int CENTER_POSITION = 2047;        // 90 deg
const float DEG_TO_UNITS = 4096.0 / 360.0;
const int PREFIX_LENGTH = 3;

float servoId1Angle = 0;
float servoId2Angle = 0;
bool sendFeedback = false;
unsigned long lastFeedbackTime = 0;
unsigned long FEEDBACK_INTERVAL = 20; // ms

// RETURN TYPE FIXED TO INT (position units)
int calculateAngle(float targetAngle) {
  return CENTER_POSITION + (int)(targetAngle * DEG_TO_UNITS);
}

void setup() {
  Serial.begin(115200);
  Serial1.begin(1000000, SERIAL_8N1, S_RXD, S_TXD);
  st.pSerial = &Serial1;

  Serial.println("READY");
}

void loop() {
  if (Serial.available() > 0) {
    String command = Serial.readStringUntil('\n');
    command.trim();

    if (command.startsWith("CMD")) {
      String args = command.substring(PREFIX_LENGTH);
      int idx = args.indexOf(';');
      if (idx > 0) {
        servoId1Angle = args.substring(0, idx).toFloat();
        servoId2Angle = args.substring(idx + 1).toFloat();

        // Use int positions
        st.RegWritePosEx(SERVO_ID_1, calculateAngle(servoId1Angle), 3400, 50);
        st.RegWritePosEx(SERVO_ID_2, calculateAngle(servoId2Angle), 3400, 50);
        st.RegWriteAction();

        Serial.print("ACK;");
        Serial.print(servoId1Angle);
        Serial.print(';');
        Serial.println(servoId2Angle);
      }
    }
    else if (!sendFeedback && command.startsWith("BEG")) {
      String val = command.substring(PREFIX_LENGTH);
      unsigned long interval = val.toInt();
      if (interval > 0) {
        FEEDBACK_INTERVAL = interval;
        sendFeedback = true;
        Serial.print("ACK BEG");
        Serial.println(FEEDBACK_INTERVAL);
      }
    }
    else if (command.startsWith("CAL")) {
      st.CalibrationOfs(1);
      st.CalibrationOfs(2);
      Serial.println("ACK CAL");
    }
    else if (command.startsWith("STP")) {
        sendFeedback = false;
        Serial.print("ACK STP");
    }
  }

  if (sendFeedback) {
    unsigned long now = millis();
    if (now - lastFeedbackTime >= FEEDBACK_INTERVAL) {
      lastFeedbackTime = now;

      int pos1 = -1, pos2 = -1;
      if (st.FeedBack(SERVO_ID_1) != -1) pos1 = st.ReadPos(-1);
      if (st.FeedBack(SERVO_ID_2) != -1) pos2 = st.ReadPos(-1);

      // Avoid printing invalid feedback
      if (pos1 == -1 || pos2 == -1) {
        Serial.println("FBK_ERR");
        return;
      }

      float angle1 = (pos1 - CENTER_POSITION) / DEG_TO_UNITS;
      float angle2 = (pos2 - CENTER_POSITION) / DEG_TO_UNITS;

      Serial.print("FBK;");
      Serial.print(angle1, 2);
      Serial.print(";");
      Serial.println(angle2, 2);
    }
  }
}