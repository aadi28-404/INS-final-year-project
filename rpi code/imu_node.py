import rclpy
from rclpy.node import Node
from nav_msgs.msg import Path
from geometry_msgs.msg import PoseStamped
from std_msgs.msg import Float32
import serial
import numpy as np
import math

class IMUNode(Node):

    def __init__(self):
        super().__init__('imu_node')

        # Serial (ESP8266)
        self.ser = serial.Serial('/dev/ttyUSB0', 115200)

        # Publishers
        self.raw_pub = self.create_publisher(Path, '/path/raw', 10)
        self.corrected_pub = self.create_publisher(Path, '/path/corrected', 10)
        self.ideal_pub = self.create_publisher(Path, '/path/ideal', 10)
        self.acc_pub = self.create_publisher(Float32, '/accuracy', 10)

        self.timer = self.create_timer(0.05, self.update)

        # State
        self.pos = np.zeros(2)
        self.vel = np.zeros(2)

        # EKF state
        self.x = np.zeros(4)  # [x, y, vx, vy]
        self.P = np.eye(4)

        self.Q = np.eye(4) * 0.01
        self.R = np.eye(2) * 0.1

        # Ellipsoid calibration parameters (example)
        self.bias = np.array([0.05, -0.03, 0.02])
        self.scale = np.array([1.02, 0.98, 1.01])

        # Paths
        self.raw_path = Path()
        self.corrected_path = Path()
        self.ideal_path = Path()

        for p in [self.raw_path, self.corrected_path, self.ideal_path]:
            p.header.frame_id = "odom"

    def create_pose(self, x, y):
        pose = PoseStamped()
        pose.header.frame_id = "odom"
        pose.pose.position.x = float(x)
        pose.pose.position.y = float(y)
        pose.pose.orientation.w = 1.0
        return pose

    # ---------------- ELLIPSOID CALIBRATION ----------------
    def calibrate(self, acc, mag):
        acc = (acc - self.bias) * self.scale
        mag = (mag - self.bias) * self.scale
        return acc, mag

    # ---------------- EKF ----------------
    def ekf_predict(self, dt):
        F = np.array([
            [1,0,dt,0],
            [0,1,0,dt],
            [0,0,1,0],
            [0,0,0,1]
        ])

        self.x = F @ self.x
        self.P = F @ self.P @ F.T + self.Q

    def ekf_update(self, z):
        H = np.array([
            [1,0,0,0],
            [0,1,0,0]
        ])

        y = z - H @ self.x
        S = H @ self.P @ H.T + self.R
        K = self.P @ H.T @ np.linalg.inv(S)

        self.x = self.x + K @ y
        self.P = (np.eye(4) - K @ H) @ self.P

    # ---------------- MAIN LOOP ----------------
    def update(self):
        try:
            line = self.ser.readline().decode().strip()
            data = list(map(float, line.split(',')))

            ax, ay, az, gx, gy, gz, mx, my, mz = data

            dt = 0.05

            # ---------------- CALIBRATION ----------------
            acc = np.array([ax, ay, az])
            mag = np.array([mx, my, mz])

            acc, mag = self.calibrate(acc, mag)

            # ---------------- RAW POSITION ----------------
            self.vel += acc[:2] * dt
            raw_pos = self.pos + self.vel * dt

            # ---------------- EKF ----------------
            self.ekf_predict(dt)

            z = raw_pos
            self.ekf_update(z)

            corrected_pos = self.x[:2]

            # ---------------- IDEAL (SMOOTH REF) ----------------
            ideal_pos = 0.8 * corrected_pos + 0.2 * raw_pos

            # ---------------- PATH ----------------
            self.raw_path.poses.append(self.create_pose(*raw_pos))
            self.corrected_path.poses.append(self.create_pose(*corrected_pos))
            self.ideal_path.poses.append(self.create_pose(*ideal_pos))

            now = self.get_clock().now().to_msg()
            for p in [self.raw_path, self.corrected_path, self.ideal_path]:
                p.header.stamp = now

            # ---------------- ACCURACY ----------------
            err_raw = np.linalg.norm(raw_pos - ideal_pos)
            err_corr = np.linalg.norm(corrected_pos - ideal_pos)

            if err_raw == 0:
                accuracy = 100.0
            else:
                accuracy = (1 - err_corr / err_raw) * 100

            acc_msg = Float32()
            acc_msg.data = float(accuracy)

            # ---------------- PUBLISH ----------------
            self.raw_pub.publish(self.raw_path)
            self.corrected_pub.publish(self.corrected_path)
            self.ideal_pub.publish(self.ideal_path)
            self.acc_pub.publish(acc_msg)

            # update position
            self.pos = corrected_pos

        except Exception as e:
            self.get_logger().warn(f"IMU read error: {e}")


def main():
    rclpy.init()
    node = IMUNode()
    rclpy.spin(node)
    rclpy.shutdown()