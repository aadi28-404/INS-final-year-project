#include <Wire.h>
#include <ICM_20948.h>

ICM_20948_I2C imu;

void setup() {
  Serial.begin(115200);
  delay(1000);

  Wire.begin(D2, D1);  // SDA, SCL

  Serial.println("Initializing IMU...");

  bool initialized = false;

  while (!initialized) {
    imu.begin(Wire, 0x68);

    if (imu.status == ICM_20948_Stat_Ok) {
      initialized = true;
      Serial.println("IMU initialized successfully!");
    } else {
      Serial.println("IMU not detected. Retrying...");
      delay(1000);
    }
  }
}

void loop() {

  if (imu.dataReady()) {
    imu.getAGMT();  // read all data

    // Accelerometer (m/s^2)
    float ax = imu.accX();
    float ay = imu.accY();
    float az = imu.accZ();

    // Gyroscope (deg/s)
    float gx = imu.gyrX();
    float gy = imu.gyrY();
    float gz = imu.gyrZ();

    // Magnetometer (µT)
    float mx = imu.magX();
    float my = imu.magY();
    float mz = imu.magZ();

    // Print nicely
    Serial.print("ACC: ");
    Serial.print(ax); Serial.print(", ");
    Serial.print(ay); Serial.print(", ");
    Serial.print(az);

    Serial.print(" | GYRO: ");
    Serial.print(gx); Serial.print(", ");
    Serial.print(gy); Serial.print(", ");
    Serial.print(gz);

    Serial.print(" | MAG: ");
    Serial.print(mx); Serial.print(", ");
    Serial.print(my); Serial.print(", ");
    Serial.print(mz);

    Serial.println();
  }

  delay(50); // ~20 Hz
}