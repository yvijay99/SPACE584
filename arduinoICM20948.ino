#include <Adafruit_ICM20X.h>
#include <Adafruit_ICM20948.h>
#include <Adafruit_Sensor.h>
#include <Wire.h>

// ============== CONFIGURATION ==============
#define DEBUG_MODE false  // Set to true for human-readable output, false for binary

#define ICM_ADDR_1 0x68   // AD0 = LOW
#define ICM_ADDR_2 0x69   // AD0 = HIGH
                                                                  
// Packet structure (86 bytes total):
// [0-1]   Header: 0x55, 0xAA
// [2]     Validity flags
// [3]     Reserved
// [4-7]   Sequence number (uint32)
// [8-11]  Timestamp (uint32)
// [12-23] Gyro1 XYZ (3 floats)
// [24-35] Accel1 XYZ (3 floats)
// [36-47] Mag1 XYZ (3 floats)
// [48-59] Gyro2 XYZ (3 floats)
// [60-71] Accel2 XYZ (3 floats)
// [72-83] Mag2 XYZ (3 floats)
// [84-85] CRC16-CCITT

#define PACKET_SIZE 86
#define HEADER_LOW  0x55
#define HEADER_HIGH 0xAA

// Validity flag bit positions
#define GYRO1_VALID_BIT   0
#define ACCEL1_VALID_BIT  1
#define MAG1_VALID_BIT    2
#define GYRO2_VALID_BIT   3
#define ACCEL2_VALID_BIT  4
#define MAG2_VALID_BIT    5

// ============== GLOBALS ==============
Adafruit_ICM20948 icm1;
Adafruit_ICM20948 icm2;

// Magnetometer calibration offsets
float mag1_offset[3] = {-14.02, 13.05, 30.15};
float mag2_offset[3] = {-21.20, -1.87, 36.00};

bool icm1_connected = false;
bool icm2_connected = false;

uint32_t sequence_number = 0;
uint8_t packet[PACKET_SIZE];

// Sensor data structures
struct SensorData {
  float gyro[3];
  float accel[3];
  float mag[3];
  bool gyro_valid;
  bool accel_valid;
  bool mag_valid;
};

SensorData sensor1, sensor2;

// ============== CRC16-CCITT ==============
uint16_t crc16_ccitt(uint8_t *data, uint16_t length) {
  uint16_t crc = 0xFFFF;
  
  for (uint16_t i = 0; i < length; i++) {
    crc ^= ((uint16_t)data[i] << 8);
    for (uint8_t j = 0; j < 8; j++) {
      if (crc & 0x8000) {
        crc = (crc << 1) ^ 0x1021;
      } else {
        crc <<= 1;
      }
    }
  }
  return crc & 0xFFFF;
}

// ============== SETUP ==============
void setup() {
  Serial.begin(115200);
  
  if (DEBUG_MODE) {
    while (!Serial) delay(10);
    Serial.println("Dual ICM-20948 - DEBUG MODE");
  }

  Wire.begin();

  // Initialize ICM #1
  if (icm1.begin_I2C(ICM_ADDR_1)) {
    icm1_connected = true;
    configureSensor(icm1);
    if (DEBUG_MODE) Serial.println("ICM #1 (0x68) initialized");
  } else {
    if (DEBUG_MODE) Serial.println("ICM #1 (0x68) NOT FOUND");
  }

  // Initialize ICM #2
  if (icm2.begin_I2C(ICM_ADDR_2)) {
    icm2_connected = true;
    configureSensor(icm2);
    if (DEBUG_MODE) Serial.println("ICM #2 (0x69) initialized");
  } else {
    if (DEBUG_MODE) Serial.println("ICM #2 (0x69) NOT FOUND");
  }

  if (DEBUG_MODE) {
    Serial.println("Setup complete\n");
  }
}

void configureSensor(Adafruit_ICM20948 &icm) {
  icm.setAccelRange(ICM20948_ACCEL_RANGE_4_G);
  icm.setGyroRange(ICM20948_GYRO_RANGE_500_DPS);
  icm.setAccelRateDivisor(4);
  icm.setGyroRateDivisor(4);
  icm.setMagDataRate(AK09916_MAG_DATARATE_100_HZ);
}

// ============== SENSOR READING ==============
void readSensor(Adafruit_ICM20948 &icm, SensorData &data, bool connected, float *mag_offset) {
  // Default to invalid
  data.gyro_valid = false;
  data.accel_valid = false;
  data.mag_valid = false;
  
  // Zero out data
  memset(data.gyro, 0, sizeof(data.gyro));
  memset(data.accel, 0, sizeof(data.accel));
  memset(data.mag, 0, sizeof(data.mag));

  if (!connected) return;

  sensors_event_t accel_event, gyro_event, mag_event, temp_event;
  
  if (icm.getEvent(&accel_event, &gyro_event, &temp_event, &mag_event)) {
    // Gyro (rad/s)
    data.gyro[0] = gyro_event.gyro.x;
    data.gyro[1] = gyro_event.gyro.y;
    data.gyro[2] = gyro_event.gyro.z;
    data.gyro_valid = true;

    // Accel (m/s^2)
    data.accel[0] = accel_event.acceleration.x;
    data.accel[1] = accel_event.acceleration.y;
    data.accel[2] = accel_event.acceleration.z;
    data.accel_valid = true;

   // Mag (uT) with calibration
    data.mag[0] = mag_event.magnetic.x - mag_offset[0];
    data.mag[1] = mag_event.magnetic.y - mag_offset[1];
    data.mag[2] = mag_event.magnetic.z - mag_offset[2];
    // Check for valid magnetometer reading (not all zeros or NaN)
    data.mag_valid = !(isnan(data.mag[0]) || (data.mag[0] == 0 && data.mag[1] == 0 && data.mag[2] == 0));
  }
}

// ============== PACKET BUILDING ==============
void writeFloat(uint8_t *buf, uint16_t offset, float value) {
  memcpy(&buf[offset], &value, sizeof(float));
}

void writeUint32(uint8_t *buf, uint16_t offset, uint32_t value) {
  buf[offset]     = value & 0xFF;
  buf[offset + 1] = (value >> 8) & 0xFF;
  buf[offset + 2] = (value >> 16) & 0xFF;
  buf[offset + 3] = (value >> 24) & 0xFF;
}

void buildPacket() {
  memset(packet, 0, PACKET_SIZE);

  // Header
  packet[0] = HEADER_LOW;
  packet[1] = HEADER_HIGH;

  // Validity flags
  uint8_t validity = 0;
  if (sensor1.gyro_valid)  validity |= (1 << GYRO1_VALID_BIT);
  if (sensor1.accel_valid) validity |= (1 << ACCEL1_VALID_BIT);
  if (sensor1.mag_valid)   validity |= (1 << MAG1_VALID_BIT);
  if (sensor2.gyro_valid)  validity |= (1 << GYRO2_VALID_BIT);
  if (sensor2.accel_valid) validity |= (1 << ACCEL2_VALID_BIT);
  if (sensor2.mag_valid)   validity |= (1 << MAG2_VALID_BIT);
  packet[2] = validity;
  packet[3] = 0;  // Reserved

  // Sequence number
  writeUint32(packet, 4, sequence_number);

  // Timestamp
  writeUint32(packet, 8, millis());

  // Sensor 1 data
  writeFloat(packet, 12, sensor1.gyro[0]);
  writeFloat(packet, 16, sensor1.gyro[1]);
  writeFloat(packet, 20, sensor1.gyro[2]);
  writeFloat(packet, 24, sensor1.accel[0]);
  writeFloat(packet, 28, sensor1.accel[1]);
  writeFloat(packet, 32, sensor1.accel[2]);
  writeFloat(packet, 36, sensor1.mag[0]);
  writeFloat(packet, 40, sensor1.mag[1]);
  writeFloat(packet, 44, sensor1.mag[2]);

  // Sensor 2 data
  writeFloat(packet, 48, sensor2.gyro[0]);
  writeFloat(packet, 52, sensor2.gyro[1]);
  writeFloat(packet, 56, sensor2.gyro[2]);
  writeFloat(packet, 60, sensor2.accel[0]);
  writeFloat(packet, 64, sensor2.accel[1]);
  writeFloat(packet, 68, sensor2.accel[2]);
  writeFloat(packet, 72, sensor2.mag[0]);
  writeFloat(packet, 76, sensor2.mag[1]);
  writeFloat(packet, 80, sensor2.mag[2]);

  // CRC16 over bytes 0-83
  uint16_t crc = crc16_ccitt(packet, 84);
  packet[84] = crc & 0xFF;
  packet[85] = (crc >> 8) & 0xFF;
}

// ============== DEBUG OUTPUT ==============
void printDebug() {
  Serial.println("========================================");
  Serial.print("Seq: "); Serial.print(sequence_number);
  Serial.print("  Time: "); Serial.println(millis());

  Serial.println("--- ICM #1 ---");
  Serial.print("Gyro  ["); Serial.print(sensor1.gyro_valid ? "OK" : "NA"); Serial.print("]: ");
  Serial.print(sensor1.gyro[0], 4); Serial.print(", ");
  Serial.print(sensor1.gyro[1], 4); Serial.print(", ");
  Serial.println(sensor1.gyro[2], 4);

  Serial.print("Accel ["); Serial.print(sensor1.accel_valid ? "OK" : "NA"); Serial.print("]: ");
  Serial.print(sensor1.accel[0], 4); Serial.print(", ");
  Serial.print(sensor1.accel[1], 4); Serial.print(", ");
  Serial.println(sensor1.accel[2], 4);

  Serial.print("Mag   ["); Serial.print(sensor1.mag_valid ? "OK" : "NA"); Serial.print("]: ");
  Serial.print(sensor1.mag[0], 4); Serial.print(", ");
  Serial.print(sensor1.mag[1], 4); Serial.print(", ");
  Serial.println(sensor1.mag[2], 4);

  Serial.println("--- ICM #2 ---");
  Serial.print("Gyro  ["); Serial.print(sensor2.gyro_valid ? "OK" : "NA"); Serial.print("]: ");
  Serial.print(sensor2.gyro[0], 4); Serial.print(", ");
  Serial.print(sensor2.gyro[1], 4); Serial.print(", ");
  Serial.println(sensor2.gyro[2], 4);

  Serial.print("Accel ["); Serial.print(sensor2.accel_valid ? "OK" : "NA"); Serial.print("]: ");
  Serial.print(sensor2.accel[0], 4); Serial.print(", ");
  Serial.print(sensor2.accel[1], 4); Serial.print(", ");
  Serial.println(sensor2.accel[2], 4);

  Serial.print("Mag   ["); Serial.print(sensor2.mag_valid ? "OK" : "NA"); Serial.print("]: ");
  Serial.print(sensor2.mag[0], 4); Serial.print(", ");
  Serial.print(sensor2.mag[1], 4); Serial.print(", ");
  Serial.println(sensor2.mag[2], 4);

  Serial.println();
}

// ============== MAIN LOOP ==============
void loop() {
  // Read both sensors
  readSensor(icm1, sensor1, icm1_connected, mag1_offset);
  readSensor(icm2, sensor2, icm2_connected, mag2_offset);

  if (DEBUG_MODE) {
    printDebug();
    delay(500);
  } else {
    // Binary mode
    buildPacket();
    Serial.write(packet, PACKET_SIZE);
  }

  sequence_number++;
  
  if (!DEBUG_MODE) {
    delay(20);  // ~20 Hz in binary mode
  }
}