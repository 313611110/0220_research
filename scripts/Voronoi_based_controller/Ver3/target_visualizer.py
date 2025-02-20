#!/usr/bin/env python3

import rospy
from gazebo_msgs.srv import SetModelState
from gazebo_msgs.msg import ModelState
from voronoi_cbsa.msg import TargetInfoArray

class TargetVisualizer:
    def __init__(self):
        rospy.init_node('target_visualizer', anonymous=True)

        # 訂閱 GroundControlStation 發送的目標資訊
        rospy.Subscriber("/target", TargetInfoArray, self.target_callback)

        # 等待 Gazebo 服務啟動
        rospy.wait_for_service('/gazebo/set_model_state')
        self.set_model_state = rospy.ServiceProxy('/gazebo/set_model_state', SetModelState)

        rospy.loginfo("Target Visualizer Initialized. Listening for /target updates.")

    def target_callback(self, msg):
        rospy.loginfo(f"Received target data with {len(msg.targets)} targets.")

        for target in msg.targets:
            model_name = f"target_{target.id}"

            # 更新模型位姿
            self.update_target_pose(model_name, target.position.x, target.position.y)

    def update_target_pose(self, model_name, x, y):
        """ 更新 Gazebo 內的 target 位置 """
        state = ModelState()
        state.model_name = model_name
        state.pose.position.x = x
        state.pose.position.y = y
        state.pose.position.z = 0  # 確保模型不會沉入地面
        state.reference_frame = "world"

        try:
            self.set_model_state(state)
            rospy.loginfo(f"Updated position of {model_name} to ({x}, {y})")
        except Exception as e:
            rospy.logwarn(f"Failed to update pose for {model_name}: {e}")

if __name__ == '__main__':
    try:
        TargetVisualizer()
        rospy.spin()
    except rospy.ROSInterruptException:
        pass
