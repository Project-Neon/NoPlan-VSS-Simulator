import vsscorepy

import socket
import json
import math

from vsscorepy.communications.command_sender import CommandSender
from vsscorepy.communications.debug_sender import DebugSender
from vsscorepy.communications.state_receiver import StateReceiver
from vsscorepy.domain.command import Command
from vsscorepy.domain.wheels_command import WheelsCommand
from vsscorepy.domain.point import Point
from vsscorepy.domain.pose import Pose
from vsscorepy.domain.debug import Debug

HOST_SENDER = 'localhost'
PORT_SENDER = 5777

HOST_RECEIVER = 'localhost'
PORT_RECEIVER = 5778

def transform_coordinates(x, y, angle=None, robot_id=None):
    if angle and robot_id:
        return {'x':(x - 85)*(150/160)*10, 'y': (y - 65)*10, 'orientation': math.radians(angle), 'robot_id': robot_id}
    else:
        return {'x':(x - 85)*(150/160)*10, 'y': (y - 65)*10}

def build_for_noplan(state):
    entities_data = {}
    entities_data['robots_blue'] = [transform_coordinates(bot.x, bot.y, bot.angle, i) for i, bot in enumerate(state.team_blue)]
    entities_data['robots_yellow'] = [transform_coordinates(bot.x, bot.y, bot.angle, i) for i, bot in enumerate(state.team_yellow)]
    entities_data['balls'] = [transform_coordinates(state.ball.x, state.ball.y)]

    data = {
        'detection': entities_data,
        'geometry': {}
    }

    return bytes(json.dumps(data), 'utf-8')

udp_sender = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
dest_sender = (HOST_SENDER, PORT_SENDER)

udp_receiver = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
dest_receiver = (HOST_RECEIVER, PORT_RECEIVER)

udp_receiver.bind(dest_receiver)

class Kernel():
    state_receiver = None
    command_sender = None
    debug_sender = None

    def loop(self):
        self.state_receiver = StateReceiver()
        self.state_receiver.create_socket()

        self.command_sender = CommandSender()
        self.command_sender.create_socket()

        self.debug_sender = DebugSender()
        self.debug_sender.create_socket()

        while True: 
            state = self.state_receiver.receive_state()

            udp_sender.sendto(build_for_noplan(state), dest_sender)

            self.command_sender.send_command(self.__build_command())
            # self.debug_sender.send_debug(self.__build_debug(state))

    def __build_command(self):
        command = Command()
        data, addr = udp_receiver.recvfrom(1024)
        commands_obj = json.loads(data.decode('utf-8'))

        command.commands.append(WheelsCommand(10, -10))
        command.commands.append(WheelsCommand(10, -10))
        command.commands.append(WheelsCommand(10, -10))

        return command


    def __build_debug(self, state):
        debug = Debug()
        debug.clean()

        for robot in state.team_yellow:
            debug.step_points.append(Point(robot.x + 10, robot.y + 10))
            debug.final_poses.append(Pose(state.ball.x + 10, state.ball.y + 10, 10))

        return debug
