#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Battle platform client framework, has been implemented. Need not modify !!!
"""

import json
import sys
import time

from socket import socket
from socket import AF_INET
from socket import SOCK_STREAM
from time import ctime

from player import Player

MAX_DATA_SIZE = 4096
REPLY_MSG_SIZE = 64

EXIT_GAME = "bye"

GET_DATA_OK = 0
GET_DATA_BLANK = 1
GET_DATA_BYE = 2


class Battle:
    """
    Battle platform client framework
    """

    def __init__(self, team_id: int, server_ip: str, server_port: int):
        self.team_id = team_id
        self.server_ip = server_ip
        self.server_port = server_port
        self.client = None
        self.battle_data = {}
        self.player = Player()

    def conn_server(self) -> bool:
        """
        First connect to the server, then send the team id to the server
        to complete the registration.
        """
        try:
            self.client = socket(AF_INET, SOCK_STREAM)
            self.client.connect((self.server_ip, self.server_port))

            data_str = "%s\n" % self.team_id
            self.client.send(data_str.encode(encoding="utf-8"))
            data_buf = self.client.recv(REPLY_MSG_SIZE)
            if not data_buf \
                    or data_buf.decode(encoding="utf-8").strip() != "OK":
                print("Registering team id(%s) failed." % self.team_id)
                self.close_server()
                return False

            print("Connecting server(%s, %s) succeeded."
                  % (self.server_ip, self.server_port))
            return True
        except Exception as err:
            print("Connecting server(%s, %s) exception: %s"
                  % (self.server_ip, self.server_port, err))
            return False

    def close_server(self):
        self.client.close()
        self.client = None
        print("Closing server(%s, %s) succeeded."
              % (self.server_ip, self.server_port))

    def get_data(self) -> int:
        """
        Receives data from the server. The received data may be a valid
        json object, which should be parsed and processed.
        """
        try:
            data_buf = self.client.recv(MAX_DATA_SIZE)
            if not data_buf or not data_buf.strip():
                return GET_DATA_BLANK
            data_str = data_buf.decode(encoding="utf-8").strip()
            if data_str == EXIT_GAME:
                print("[%s] Good bye." % ctime())
                return GET_DATA_BYE

            data = json.loads(data_str)
            rows, cols = data["row"], data["col"]
            maps = [['O'] * cols for j in range(rows)]
            index = 0
            for row in range(rows):
                for col in range(cols):
                    maps[row][col] = data["lastMap"][index]
                    index += 1
            data["lastMap"] = maps
            self.battle_data = data
            # print("[%s] %s" % (ctime(), self.battle_data))
            return GET_DATA_OK
        except Exception as err:
            print("Getting battle data exception: %s" % err)
            raise

    def play(self):
        """
        The player calculates the next action, which will be sent back to
        server, based on the incoming parsed json object.
        """
        try:
            action = self.player.move(self.battle_data)
            print("[%s] %s" % (ctime(), action))
            action_str = "%s\n" % json.dumps(action)
            self.client.send(action_str.encode(encoding="utf-8"))
            self.battle_data = {}
            return
        except Exception as err:
            import traceback
            print("Playing exception: %s" % err)
            print(traceback.format_exc())
            raise

    def start(self):
        """
        The client attempts to receive data from server every 100
        milliseconds. These data will be parsed and passed to the player
        for processing. If "bye" received, the processing will end.
        """
        result = self.conn_server()
        if not result:
            return

        print("[%s] Battle starts." % ctime())
        try:
            while True:
                result = self.get_data()
                if result == GET_DATA_OK:
                    self.play()
                elif result == GET_DATA_BYE:
                    break
                else:  # get blank data, sleep and retry
                    time.sleep(0.1)
        except Exception as err:
            print("[%s] Battle ends by exception: %s" % (ctime(), err))
        finally:
            self.close_server()
        print("[%s] Battle ends." % ctime())
        return


if __name__ == '__main__':
    print(sys.argv)
    if len(sys.argv) != 4:
        print("Invalid input parameters, at least including "
              "session id, server ip and server port.")
        sys.exit(1)

    battle = Battle(team_id=sys.argv[1],
                    server_ip=sys.argv[2],
                    server_port=int(sys.argv[3]))
    battle.start()
