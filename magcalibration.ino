#include <Adafruit_ICM20X.h>
#include <Adafruit_ICM20948.h>
#include <Adafruit_Sensor.h>
#include <Wire.h>

Adafruit_ICM20948 icm1;
Adafruit_ICM20948 icm2;

// Track min/max for each axis
float mag1_min[3] = {9999, 9999, 9999};
float mag1_max[3] = {-9999, -9999, -9999};
float mag2_min[3] = {9999, 9999, 9999};
float mag2_max[3] = {-9999, -9999, -9999};

void setup() {
  Serial.begin(115200);
  while (!Serial) delay(10);
  
  Wire.begin();
  icm1.begin_I2C(0x68);
  icm2.begin_I2C(0x69);
  
  icm1.setMagDataRate(AK09916_MAG_DATARATE_100_HZ);
  icm2.setMagDataRate(AK09916_MAG_DATARATE_100_HZ);
  
  Serial.println("=== MAGNETOMETER CALIBRATION ===");
  Serial.println("Rotate sensor slowly in ALL directions");
  Serial.println("Cover all orientations for 60 seconds");
  Serial.println("================================\n");
}

void loop() {
  sensors_event_t a, g, t, m;
  
  // Read ICM1
  if (icm1.getEvent(&a, &g, &t, &m)) {
    mag1_min[0] = min(mag1_min[0], m.magnetic.x);
    mag1_max[0] = max(mag1_max[0], m.magnetic.x);
    mag1_min[1] = min(mag1_min[1], m.magnetic.y);
    mag1_max[1] = max(mag1_max[1], m.magnetic.y);
    mag1_min[2] = min(mag1_min[2], m.magnetic.z);
    mag1_max[2] = max(mag1_max[2], m.magnetic.z);
  }
  
  // Read ICM2
  if (icm2.getEvent(&a, &g, &t, &m)) {
    mag2_min[0] = min(mag2_min[0], m.magnetic.x);
    mag2_max[0] = max(mag2_max[0], m.magnetic.x);
    mag2_min[1] = min(mag2_min[1], m.magnetic.y);
    mag2_max[1] = max(mag2_max[1], m.magnetic.y);
    mag2_min[2] = min(mag2_min[2], m.magnetic.z);
    mag2_max[2] = max(mag2_max[2], m.magnetic.z);
  }
  
  // Print current offsets (these are what you'll copy)
  Serial.println("--- Copy these to your main sketch ---");
  Serial.print("float mag1_offset[3] = {");
  Serial.print((mag1_min[0] + mag1_max[0]) / 2, 2); Serial.print(", ");
  Serial.print((mag1_min[1] + mag1_max[1]) / 2, 2); Serial.print(", ");
  Serial.print((mag1_min[2] + mag1_max[2]) / 2, 2); Serial.println("};");
  
  Serial.print("float mag2_offset[3] = {");
  Serial.print((mag2_min[0] + mag2_max[0]) / 2, 2); Serial.print(", ");
  Serial.print((mag2_min[1] + mag2_max[1]) / 2, 2); Serial.print(", ");
  Serial.print((mag2_min[2] + mag2_max[2]) / 2, 2); Serial.println("};");
  Serial.println();
  
  delay(200);
}
