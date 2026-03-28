import rclpy
from rclpy.node import Node
from nav_msgs.msg import Path
from std_msgs.msg import Float32

class LaptopNode(Node):

    def __init__(self):
        super().__init__('laptop_node')

        self.create_subscription(Path, '/path/raw', self.raw_cb, 10)
        self.create_subscription(Path, '/path/corrected', self.corr_cb, 10)
        self.create_subscription(Path, '/path/ideal', self.ideal_cb, 10)
        self.create_subscription(Float32, '/accuracy', self.acc_cb, 10)

    def raw_cb(self, msg):
        pass

    def corr_cb(self, msg):
        pass

    def ideal_cb(self, msg):
        pass

    def acc_cb(self, msg):
        self.get_logger().info(f"Accuracy: {msg.data:.2f}%")

def main():
    rclpy.init()
    node = LaptopNode()
    rclpy.spin(node)
    rclpy.shutdown()