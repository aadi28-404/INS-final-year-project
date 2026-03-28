import rclpy
from rclpy.node import Node
from nav_msgs.msg import Path
from geometry_msgs.msg import PoseStamped
from visualization_msgs.msg import Marker
import random
import math


class AdvancedSim(Node):

    def __init__(self):
        super().__init__('advanced_sim')

        self.raw_pub = self.create_publisher(Path, '/path/raw', 10)
        self.corrected_pub = self.create_publisher(Path, '/path/corrected', 10)
        self.ideal_pub = self.create_publisher(Path, '/path/ideal', 10)
        self.marker_pub = self.create_publisher(Marker, '/accuracy_text', 10)

        self.timer = self.create_timer(0.1, self.update)

        self.t = 0.0

        # drift
        self.drift_x = 0.0
        self.drift_y = 0.0

        # path buffers
        self.MAX_POINTS = 3000

        self.raw_path = Path()
        self.corrected_path = Path()
        self.ideal_path = Path()

        self.raw_path.header.frame_id = "odom"
        self.corrected_path.header.frame_id = "odom"
        self.ideal_path.header.frame_id = "odom"

    def create_pose(self, x, y):
        pose = PoseStamped()
        pose.header.frame_id = "odom"
        pose.pose.position.x = float(x)
        pose.pose.position.y = float(y)
        pose.pose.orientation.w = 1.0
        return pose

    def generate_path(self):
        """
        1m square + 2m forward line (NO overlap)
        """

        segment_time = 6.0
        segment = int(self.t // segment_time)
        progress = (self.t % segment_time) / segment_time

        phase = segment % 5
        cycle = segment // 5

        base_x = cycle * 3.0  # forward shift (prevents overlap)
        size = 1.0

        if phase == 0:
            x = base_x + size * progress
            y = 0.0

        elif phase == 1:
            x = base_x + size
            y = size * progress

        elif phase == 2:
            x = base_x + size * (1 - progress)
            y = size

        elif phase == 3:
            x = base_x
            y = size * (1 - progress)

        else:
            x = base_x + size + (2.0 * progress)
            y = 0.0

        return x, y

    def update(self):
        self.t += 0.1

        # ---------------- IDEAL ----------------
        x, y = self.generate_path()

        # small realistic noise
        x += random.uniform(-0.002, 0.002)
        y += random.uniform(-0.002, 0.002)

        # ---------------- DRIFT ----------------
        self.drift_x += random.uniform(-0.002, 0.002)
        self.drift_y += random.uniform(-0.002, 0.002)

        bias_x = 0.002 * math.sin(self.t * 0.1)
        bias_y = 0.002 * math.cos(self.t * 0.1)

        noise_x = random.uniform(-0.003, 0.003)
        noise_y = random.uniform(-0.003, 0.003)

        # rare spikes
        if random.random() < 0.01:
            noise_x += random.uniform(-0.01, 0.01)
            noise_y += random.uniform(-0.01, 0.01)

        drift_x = x + self.drift_x + bias_x + noise_x
        drift_y = y + self.drift_y + bias_y + noise_y

        # ---------------- CORRECTION ----------------
        error = math.sqrt((drift_x - x)**2 + (drift_y - y)**2)

        if error > 0.05:
            correction_factor = 0.25
        else:
            correction_factor = 0.05

        corr_x = drift_x - (self.drift_x * correction_factor) + random.uniform(-0.0015, 0.0015)
        corr_y = drift_y - (self.drift_y * correction_factor) + random.uniform(-0.0015, 0.0015)

        # ---------------- STORE PATH ----------------
        self.ideal_path.poses.append(self.create_pose(x, y))
        self.raw_path.poses.append(self.create_pose(drift_x, drift_y))
        self.corrected_path.poses.append(self.create_pose(corr_x, corr_y))

        # prevent disappearing
        if len(self.ideal_path.poses) > self.MAX_POINTS:
            self.ideal_path.poses.pop(0)
            self.raw_path.poses.pop(0)
            self.corrected_path.poses.pop(0)

        now = self.get_clock().now().to_msg()
        self.ideal_path.header.stamp = now
        self.raw_path.header.stamp = now
        self.corrected_path.header.stamp = now

        # ---------------- ACCURACY ----------------
        error_raw = math.sqrt((drift_x - x)**2 + (drift_y - y)**2)
        error_corr = math.sqrt((corr_x - x)**2 + (corr_y - y)**2)

        accuracy = 100.0 if error_raw == 0 else (1 - error_corr / error_raw) * 100

        # ---------------- TEXT (FIXED VISIBILITY) ----------------
        marker = Marker()
        marker.header.frame_id = "odom"
        marker.header.stamp = now
        marker.type = Marker.TEXT_VIEW_FACING
        marker.id = 0

        # follow robot so it never disappears
        marker.pose.position.x = x + 1.5
        marker.pose.position.y = y + 1.5
        marker.pose.position.z = 2.0

        marker.scale.z = 0.6
        marker.color.r = 0.0
        marker.color.g = 1.0
        marker.color.b = 0.0
        marker.color.a = 1.0

        marker.text = f"Accuracy: {accuracy:.1f}%"

        self.marker_pub.publish(marker)

        # ---------------- PUBLISH ----------------
        self.ideal_pub.publish(self.ideal_path)
        self.raw_pub.publish(self.raw_path)
        self.corrected_pub.publish(self.corrected_path)


def main():
    rclpy.init()
    node = AdvancedSim()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()