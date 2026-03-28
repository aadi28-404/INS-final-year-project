import rclpy
from rclpy.node import Node
from std_msgs.msg import String
import RPi.GPIO as GPIO
import time

class MotorNode(Node):

    def __init__(self):
        super().__init__('motor_node')

        self.sub = self.create_subscription(String, '/cmd_move', self.move, 10)

        GPIO.setmode(GPIO.BCM)

        self.IN1, self.IN2, self.IN3, self.IN4 = 17,18,22,23

        for p in [self.IN1, self.IN2, self.IN3, self.IN4]:
            GPIO.setup(p, GPIO.OUT)

    def move(self, msg):
        try:
            cmd, duration = msg.data.split(',')
            duration = float(duration)

            if cmd == "forward":
                GPIO.output(self.IN1,1); GPIO.output(self.IN2,0)
                GPIO.output(self.IN3,1); GPIO.output(self.IN4,0)

            elif cmd == "left":
                GPIO.output(self.IN1,0); GPIO.output(self.IN2,1)
                GPIO.output(self.IN3,1); GPIO.output(self.IN4,0)

            elif cmd == "right":
                GPIO.output(self.IN1,1); GPIO.output(self.IN2,0)
                GPIO.output(self.IN3,0); GPIO.output(self.IN4,1)

            time.sleep(duration)

            # stop
            for p in [self.IN1, self.IN2, self.IN3, self.IN4]:
                GPIO.output(p,0)

        except:
            pass


def main():
    rclpy.init()
    node = MotorNode()
    rclpy.spin(node)
    GPIO.cleanup()
    rclpy.shutdown()