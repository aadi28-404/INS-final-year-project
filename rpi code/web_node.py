from flask import Flask, request
import rclpy
from rclpy.node import Node
from std_msgs.msg import String
import threading
from std_msgs.msg import Float32

app = Flask(__name__)

class WebNode(Node):

    def __init__(self):
        super().__init__('web_node')
        self.pub = self.create_publisher(String, '/cmd_move', 10)
        # inside WebNode init:
        self.create_subscription(Float32, '/accuracy', acc_callback, 10)

    def send(self, cmd, duration):
        msg = String()
        msg.data = f"{cmd},{duration}"
        self.pub.publish(msg)

node = None

@app.route('/move')
def move():
    direction = request.args.get('dir')
    dist = float(request.args.get('dist', 1))

    duration = dist  # simple mapping

    node.send(direction, duration)
    return f"{direction} for {dist}m"

@app.route('/rectangle')
def rectangle():
    side = float(request.args.get('side', 1))

    for _ in range(4):
        node.send("forward", side)
        node.send("left", 1)

    return "Rectangle executed"

@app.route('/accuracy')
def accuracy():
    return {"accuracy": latest_accuracy}

latest_accuracy = 0.0

def acc_callback(msg):
    global latest_accuracy
    latest_accuracy = msg.data

def ros_thread():
    global node
    rclpy.init()
    node = WebNode()
    rclpy.spin(node)

if __name__ == "__main__":
    threading.Thread(target=ros_thread).start()
    app.run(host='0.0.0.0', port=5000)