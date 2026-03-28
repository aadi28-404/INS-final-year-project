import os

def main():
    os.system("gnome-terminal -- bash -c 'ros2 run my_robot imu_node'")
    os.system("gnome-terminal -- bash -c 'ros2 run my_robot motor_node'")
    os.system("gnome-terminal -- bash -c 'ros2 run my_robot oled_node'")
    os.system("gnome-terminal -- bash -c 'ros2 run my_robot web_node'")

if __name__ == "__main__":
    main()