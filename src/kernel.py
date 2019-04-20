import vsscorepy

import socket
import json
import math
import time

from vsscorepy.communications.command_sender import CommandSender
from vsscorepy.communications.debug_sender import DebugSender
from vsscorepy.communications.state_receiver import StateReceiver
from vsscorepy.domain.command import Command
from vsscorepy.domain.wheels_command import WheelsCommand
from vsscorepy.domain.point import Point
from vsscorepy.domain.pose import Pose
from vsscorepy.domain.debug import Debug
from src.pid import Robot


HOST_SENDER = 'localhost'
PORT_SENDER = 5777

HOST_RECEIVER = 'localhost'
PORT_RECEIVER = 5778

def transform_coordinates(element, is_ball=False, robot_id=-1):
    if not is_ball:
        return {
            'x':(element.x - 85)*(150/160)*10,
            'y': (element.y - 65)*10, 
            'orientation': math.radians(element.angle),
            'robot_id': robot_id,
            'linear_speed': math.sqrt(math.pow(element.speed_x, 2) + math.pow(element.speed_y, 2)),
            'theta_speed': element.speed_angle
        }
    else:
        return {'x':(element.x - 85)*(150/160)*10, 'y': (element.y - 65)*10}

def build_for_noplan(state):
    entities_data = {}
    entities_data['robots_blue'] = [transform_coordinates(bot, robot_id=i) for i, bot in enumerate(state.team_blue)]
    entities_data['robots_yellow'] = [transform_coordinates(bot, robot_id=i) for i, bot in enumerate(state.team_yellow)]
    entities_data['balls'] = [transform_coordinates(state.ball, is_ball=True)]

    data = {
        'detection': entities_data,
        'geometry': {}
    }

    return data

udp_sender = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
dest_sender = (HOST_SENDER, PORT_SENDER)

udp_receiver = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
dest_receiver = (HOST_RECEIVER, PORT_RECEIVER)

udp_receiver.bind(dest_receiver)

class Kernel():
    state_receiver = None
    command_sender = None
    debug_sender = None

    robots_pid = [Robot(i) for i in range(6)]

    def __init__(self, two_teams):
        self.two_teams = two_teams

    def loop(self):
        self.count = 0
        self.state_receiver = StateReceiver()
        self.state_receiver.create_socket()

        self.command_sender_yellow = CommandSender()
        self.command_sender_yellow.create_socket(port=5556)

        self.command_sender_blue = CommandSender()
        self.command_sender_blue.create_socket(port=5557)

        self.debug_sender = DebugSender()
        self.debug_sender.create_socket()

        while True:
            state = self.state_receiver.receive_state()

            state_data = build_for_noplan(state)

            udp_sender.sendto(bytes(json.dumps(state_data), 'utf-8'), dest_sender)

            data, addr = udp_receiver.recvfrom(1024)

            self.command_sender_yellow.send_command(self.__build_command(data, state_data, 'yellow'))
            if self.two_teams:
                self.command_sender_blue.send_command(self.__build_command(data, state_data, 'blue'))
            # self.debug_sender.send_debug(self.__build_debug(state))

    def __build_command(self, data, state_data, team_color):
        command = Command()
        command.clean() 
        commands_obj = json.loads(data.decode('utf-8'))
        commands_obj.sort(key=lambda x: x[0], reverse=False)
        last_angles = [0, 0, 0, 0, 0, 0]
        allowed_ids = [0,1,2] if team_color == 'yellow' else [3,4,5]
        output = []
        for obj, r_pid in zip(commands_obj, self.robots_pid):
            # print(state_data)
            if (obj[0] not in allowed_ids):          
                continue

            sp_lin = state_data['detection']['robots_{}'.format(team_color)][obj[0]%3]['linear_speed']
            ang = math.degrees(
                state_data['detection']['robots_{}'.format(team_color)][obj[0]%3]['orientation']
            )

            delta_angle = (ang - last_angles[obj[0]])

            if delta_angle > 180:
                delta_angle -= 360
            elif delta_angle < -180:    
                delta_angle += 360

            last_angles[obj[0]] = ang
            print(obj)
            sp_ang = delta_angle/r_pid.dt

            r_pid.set_target(obj[2], obj[3])
            wheel_right, wheel_left = r_pid.speed_to_power(sp_lin, sp_ang)
            lin = wheel_right
            ang = wheel_left
            # print('wheels_power: ', wheel_right, wheel_left)

            command.commands.append(WheelsCommand(wheel_right, wheel_left))

        # Partindo do principio que havera no maximo 3 robos em cada time
        mock_commands_left = 3 -len(command.commands)

        for i in range(mock_commands_left):
            command.commands.append(WheelsCommand(0, 0))

        print(len(command.commands))
        return command
