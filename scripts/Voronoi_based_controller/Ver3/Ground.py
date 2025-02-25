#!/usr/bin/env python3

import rospy
from voronoi_cbsa.msg import TargetInfoArray, TargetInfo
from std_msgs.msg   import Int8

import pygame
import numpy as np
from time import time, sleep
from control import PTZCamera
from math import cos, acos, sqrt, exp, sin
from scipy.stats import multivariate_normal
import itertools

def norm(arr):
    sum = 0
    for i in range(len(arr)):
        sum += arr[i]**2

    return sqrt(sum)

def TargetDynamics(x, y, v, seed=0, cnt=0):
    spd = 0.003  # 速度
    turn_angle = np.random.uniform(-10, 10) * np.pi / 180  # 讓目標隨機轉彎（-10 到 10 度）

    # 旋轉速度方向
    rotation_matrix = np.array([[cos(turn_angle), -sin(turn_angle)],
                                [sin(turn_angle), cos(turn_angle)]])
    new_v = rotation_matrix @ v.reshape(2, 1)
    
    # 更新位置
    new_x = x + new_v[0] * spd
    new_y = y + new_v[1] * spd

    # 確保目標不會超出地圖範圍
    new_x = np.clip(new_x, 0, 24)
    new_y = np.clip(new_y, 0, 24)

    return (new_x, new_y), new_v.flatten()  # ✅ 回傳新的位置和速度


def RandomUnitVector():
    v = np.asarray([np.random.normal() for i in range(2)])
    return v/norm(v)

if __name__ == "__main__":
    rospy.init_node('ground_control_station', anonymous=True, disable_signals=True)
    rate = rospy.Rate(30)

    target_pub = rospy.Publisher("/target", TargetInfoArray, queue_size=10)
    start_pub   = rospy.Publisher("/start", Int8, queue_size=1)

    def random_pos(pos=(0,0)):
        if pos == (0,0):
            x = np.random.random()*15 + 5
            y = np.random.random()*15 + 5
            return np.array((x,y))
        else:
            return np.asarray(pos)
        
    # targets = [[random_pos((8,16)), 0.8, 10,np.array([1.,1.]), ['camera', 'manipulator']],
    #            [random_pos((16,8)), 0.8, 10,np.array([1.,1.]), ['camera', 'smoke_detector']]]
    
    #targets = [[random_pos((16,16)), 2, 10,np.array([1.,1.]), ['camera', 'manipulator']]]
    
    targets = [[random_pos((10,10)), 2, 10,np.array([1.,1.]), ['camera', 'manipulator']],
               [random_pos((6,12.81)), 2, 10,np.array([1.,1.]), ['camera', 'manipulator']],
               [random_pos((12.81,6)), 2, 10,np.array([1.,1.]), ['camera', 'manipulator']]]
    
    # targets = [[random_pos((12,12)), 1.2, 10,np.array([1.,1.]), ['camera', 'manipulator', 'smoke_detector']],
    #            [random_pos((8,16)), 1.2, 10,np.array([1.,1.]), ['camera', 'smoke_detector']],
    #            [random_pos((16,8)), 1.2, 10,np.array([1.,1.]), ['camera', 'manipulator']]]
    
    # targets = [[random_pos((12,6)), 1.2, 10,np.array([1.,1.]), ['manipulator']],
    #            [random_pos((6,18)), 1.2, 10,np.array([1.,1.]), ['smoke_detector']],
    #            [random_pos((18,18)), 1.2, 10,np.array([1.,1.]), ['camera']]]
    
    # targets = [[random_pos((5,5)), 0.8, 10,np.array([1.,1.]), ['camera', 'manipulator']],
    #            [random_pos((19,19)), 0.8, 10,np.array([1.,1.]), ['camera', 'smoke_detector']],
    #            [random_pos((5,19)), 0.8, 10,np.array([1.,1.]), ['camera', 'manipulator']],
    #            [random_pos((19,5)), 0.8, 10,np.array([1.,1.]), ['camera', 'smoke_detector']]]
    
    cnt = 0
    a = 5
    seeds = [range(10000*a - 9999, 10000*a), range(20001*a - 10000, 20000*a),
             range(30001*a - 10000, 30000*a),range(40001*a - 10000, 40000*a)]
    
    rospy.logwarn("Press 's' then enter to start experiment")
    a = input('').split(" ")[0]
    if a == 's':
        rospy.logwarn("Experiment Start")
        msg = Int8()
        msg.data = 1
        start_pub.publish(msg)
    else:
        print("Unknown command")
        
    while not rospy.is_shutdown():
            
        grid_size = rospy.get_param("/grid_size", 0.1)
        tmp = []
        cnt += 1
        for i in range(len(targets)):
            pos, vel = TargetDynamics(targets[i][0][0], targets[i][0][1], targets[i][3])
            #pos = np.array([6*np.cos(((-1)**i)*(cnt/5)/180*np.pi) + 12, 6*np.sin((((-1)**i)*cnt/5)/180*np.pi) + 12])
            targets[i][0] = pos
            targets[i][3] = vel

            target_msg = TargetInfo()
            target_msg.id = i
            target_msg.position.x = pos[0]
            target_msg.position.y = pos[1]
            target_msg.standard_deviation = targets[i][1]
            target_msg.weight = targets[i][2]
            target_msg.velocity.linear.x = vel[0]
            target_msg.velocity.linear.y = vel[1]
            target_msg.required_sensor = targets[i][4]

            tmp.append(target_msg)
        
        targets_array = TargetInfoArray()
        targets_array.targets = [tmp[i] for i in range(len(tmp))]

        target_pub.publish(targets_array)
        rate.sleep()