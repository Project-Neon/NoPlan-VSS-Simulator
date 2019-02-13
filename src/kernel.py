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

    robots_pid = [Robot() for _ in range(3)]

    def loop(self):
        self.count = 0
        self.state_receiver = StateReceiver()
        self.state_receiver.create_socket()

        self.command_sender = CommandSender()
        self.command_sender.create_socket()

        self.debug_sender = DebugSender()
        self.debug_sender.create_socket()

        while True:
            state = self.state_receiver.receive_state()

            state_data = build_for_noplan(state)

            udp_sender.sendto(bytes(json.dumps(state_data), 'utf-8'), dest_sender)

            self.command_sender.send_command(self.__build_command(state_data))
            # self.debug_sender.send_debug(self.__build_debug(state))

    def __build_command(self, state_data):
        command = Command()
        command.clean() 
        self.count += 1
        data, addr = udp_receiver.recvfrom(1024)
        commands_obj = json.loads(data.decode('utf-8'))
        commands_obj.sort(key=lambda x: x[0], reverse=False)

        for obj, r_pid in zip(commands_obj, self.robots_pid):
            print('robot message: ', obj)
            sp_lin = state_data['detection']['robots_yellow'][obj[0]]['linear_speed']
            sp_ang = state_data['detection']['robots_yellow'][obj[0]]['theta_speed']
            r_pid.set_target(obj[2], obj[3])
            wheel_right, wheel_left = r_pid.speed_to_power(sp_lin, sp_ang)
            lin = wheel_right
            ang = wheel_left
            print('robot {}:'.format(obj[0]), lin, ang)

            command.commands.append(WheelsCommand(lin, ang))

        return command
