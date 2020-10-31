#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
The battle client program, needs to be implemented by the participating teams.
"""

from queue import PriorityQueue
import random  # to be removed

ELEMENTS_ALLOWED = ["O", "Z", "X", "2", "3", "T"]  # 允许通行的元素
ELEMENTS_ALLOWED_TARGET = ["O", "Z", "X", "2", "3"]  # 允许玩家停留的元素
ELEMENTS_TOOLS = ["Z", "X", "2", "3"]
TEMAID = "90135"
TEAMMATE=[]
ENERMY = []

removeH = None
addH = None
canSend = False

class Player:

    def __init__(self):
        self.team_id = 90135  # Need to be updated to your own team id !!!
        self.player_dict = {}
        self.map_list = []
        self.control_ball = False
        self.players = []
        self.ennermy_controll_ball = None # 地方控球人信息

    def move(self, battle_data: dict) -> dict:
        # 只有该你走的时候才会收到消息，等自己行动。
        # to be removed
        player_id = battle_data.get("turn")
        for player_index in battle_data.get("players"):
            if player_id == player_index.get("id"):
                self.player_dict = player_index
                self.map_list = battle_data.get("lastMap")
                # self.team_id = self.player_dict.get("teamId")
                self.player_id = player_id
                self.control_ball = True if self.player_dict["controlBall"] == 1 else False
            if player_index.get("teamId") == TEMAID and player_index.get("id") not in TEAMMATE:
                TEAMMATE.append(player_index.get("id"))
            if player_index.get("teamId") != TEMAID and player_index.get("id") not in ENERMY:
                ENERMY.append(player_index.get("id"))
            if player_index.get("teamId") != TEMAID and player_index.get("controlBall") == 1:
                self.ennermy_controll_ball = Point(player_index.get("col"), player_index.get("row"), player_index.get("state"))
        self.players = battle_data.get("players")
        graph = Graph(self.map_list, self.player_dict)
        print("playerId :{} row:{},col:{}".format(self.player_id,self.player_dict["row"],self.player_dict["col"]))
        action = self.common_decion()
        if action:
            return action
        action = self.attack_decision(battle_data)
        if action:
            return action
        if self.control_ball:
            decision = self.captain_decision(graph)
        else:
            # decision = self.captain_decision()
            decision = self.help_decision()
        return decision

    def attack_decision(self, battle_data):
        # 简单的判断敌人的情况， 只堵住篮筐， 先判断它离篮筐距离
        graph = Graph(self.map_list, self.player_dict)
        goal = graph.goal
        index = ""
        for player_index in battle_data.get("players"):
            if str(self.team_id) != player_index.get("teamId"):
                y, x = player_index["row"], player_index["col"]
                enemy = Point(x, y, "O")
                if self.heuristic(enemy, goal) == 2:
                    # 总共有8 种情况， 对方的人在篮筐的八个方向 上下左右，右上、右下、左上、左下
                    if goal.y > y  and goal.x > x:
                        temp = self.map_list[goal.y - 1]
                        if temp[goal.x] == "O":
                            index = "{},{}".format(goal.y-1, goal.x)
                        temp = self.map_list[goal.y]
                        if temp[goal.x-1] =="O":
                            index = "{},{}".format(goal.y, goal.x - 1)
                    if goal.y > y  and goal.x < x:
                        temp = self.map_list[goal.y - 1]
                        if temp[goal.x] == "O":
                            index = "{},{}".format(goal.y-1, goal.x)
                        temp = self.map_list[goal.y]
                        if temp[goal.x-1] =="O":
                            index = "{},{}".format(goal.y, goal.x + 1)
                    if goal.y < y  and goal.x > x:
                        temp = self.map_list[goal.y + 1]
                        if temp[goal.x] == "O":
                            index = "{},{}".format(goal.y+1, goal.x)
                        temp = self.map_list[goal.y]
                        if temp[goal.x-1] == "O":
                            index = "{},{}".format(goal.y, goal.x - 1)
                    if goal.y < y  and goal.x < x:
                        temp = self.map_list[goal.y + 1]
                        if temp[goal.x] == "O":
                            index = "{},{}".format(goal.y+1, goal.x)
                        temp = self.map_list[y]
                        if temp[goal.x-1] =="O":
                            index = "{},{}".format(goal.y, goal.x + 1)
                    if goal.y == y and goal.x < x:
                        temp = self.map_list[goal.y]
                        if temp[goal.x+1] == "O":
                            index = "{},{}".format(goal.y,goal. x + 1)
                    if goal.y == y and goal.x < x:
                        temp = self.map_list[goal.y]
                        if temp[goal.x - 1] == "O":
                            index = "{},{}".format(goal.y, goal.x - 1)
                    if goal.x == x and goal.y > y:
                        temp = self.map_list[goal.y-1]
                        if temp[goal.x] == "O":
                            index = "{},{}".format(goal.y-1, goal.x)
                    if goal.x == x and goal.y < y:
                        temp = self.map_list[goal.y+1]
                        if temp[goal.x] == "O":
                            index = "{},{}".format(goal.y+1, goal.x)
        if self.player_dict["blockNum"] == 0:
            global addH
            addH = index
            return None
        if index == "":
            return None
        action = {"actionType": "B", "actionDesc": ""}
        action["actionDesc"] = index
        return action



    def common_decion(self):
        '''
        用来优先进行 使用障碍包 和 清障包
        :return:
        '''
        action = {"actionType": "", "actionDesc": ""}
        global removeH
        global addH
        if removeH and self.player_dict["boomNum"] != 0:
            action["actionType"] = "C"
            action[ "actionDesc"] = removeH
            removeH = None
            return action
        if addH and self.player_dict["blockNum"] != 0:
            action["actionType"] = "B"
            action[ "actionDesc"] = addH
            addH = None
            return action
        return None

    def captain_decision(self, graph):
        '''
        持球人执行的决策
        :return:
        '''
        action = {"actionType": "M", "actionDesc": ""}
        work_path = self.path_finding(graph)
        directs = self.point2direction(work_path)
        length = len(directs)
        if self.player_dict["energy3Num"] != 0 and length > 2:
            action["actionDesc"] = "".join(directs[0:3])
            return action
        if self.player_dict["energy2Num"] != 0 and length > 1:
            action["actionDesc"] = "".join(directs[0:2])
            return action
        if length == 0:
            action["actionType"] = "N"
        if length == 1:
            decision = directs[0]
            # 最后投球的时候可以等到最后再投球。
            if type(decision) == tuple:
                # todo 如果想最大化分数 ，可以调整阈值 step，最大也就是3. last_tool_num 为最后剩余的道具数量
                step = 2
                last_tool_num = 3
                if self.heuristic(self.ennermy_controll_ball, graph.goal) < step or len(graph.all_tools) < last_tool_num:
                    action["actionType"] = "N"
                    return action
                action["actionType"] = decision[0]
                action["actionDesc"] = decision[1]
            else:
                action["actionDesc"] = decision
        elif length > 1:
            action["actionDesc"] = directs[0]
        return action

    def point2direction(self, path:list):
        directs = []
        if len(path) == 0:
            return directs
        start = path[0]
        for index in range(1, len(path)):
            next = path[index]
            if next.state == "T":
                directs.append(("S",start.get_direct(next)))
                break
            if next.state in TEAMMATE:
                break
            if next.state == "H" and len(directs) < 2:
                global removeH
                removeH = str(next.y) + "," + str(next.x)
                break
            direction = start.get_direct(next)
            directs.append(direction)
            start = next
        return directs

    def path_finding(self, graph)->list:
        frontier = PriorityQueue()
        start = Point(self.player_dict["col"], self.player_dict["row"], "O")
        frontier.put(start)
        came_from = dict()
        cost_so_far = dict()
        came_from[start] = None
        cost_so_far[start] = 0
        # graph = Graph(self.map_list, self.player_dict)
        goal = graph.goal
        while not frontier.empty():
            current = frontier.get()
            if current == goal:
                break
            for next in graph.neighbors(current):
                new_cost = cost_so_far[current] + graph.cost(next)
                if next not in cost_so_far or new_cost < cost_so_far[next]:
                    cost_so_far[next] = new_cost
                    priority = new_cost + self.heuristic(goal, next)
                    next.priority = priority
                    frontier.put(next)
                    came_from[next] = current
        work_path = []
        work_path.append(goal)
        from_point = came_from[goal]
        while not from_point.__eq__(start):
            work_path.insert(0, from_point)
            from_point = came_from[from_point]
        work_path.insert(0, start)
        return work_path

    def heuristic(self, a, b):
        # Manhattan distance on a square grid
        return abs(a.x - b.x) + abs(a.y - b.y)

    def help_decision(self):
        action = {"actionType": "M", "actionDesc": ""}
        start = Point(self.player_dict["col"], self.player_dict["row"], "O")
        graph = Graph(self.map_list, self.player_dict)
        # todo 攻击持球人的代码，好像没有起很大作用
        controll_ball = self.attack_controll_ball(graph)
        ready_send = False
        for player in self.players:
            if TEMAID == player["teamId"] and player["controlBall"] == 1:
                point = Point(player["col"], player["row"], player["id"])
                distance = self.heuristic(point, graph.goal)
                if distance == 1:
                    ready_send = True
        if ready_send and controll_ball and self.player_dict["blockNum"] != 0:
            print("attack controll ball")
            action["actionType"] = "B"
            action["actionDesc"] = str(controll_ball.y)+","+str(controll_ball.x)
            return action
        path = self.find_goal_path(graph, start, ready_send)
        print("path :{}".format(path))
        directs = self.point2direction(path)

        length = len(directs)
        # todo 如果准备投球了，就不消耗道具了
        if ready_send:
            if len(directs) > 0:
                action["actionDesc"] = directs[0]
                return action
            else:
                action["actionType"] = "N"
                return action
        if self.player_dict["energy3Num"] != 0 and length > 2:
            action["actionDesc"] = "".join(directs[0:3])
            return action
        if self.player_dict["energy2Num"] != 0 and length > 1:
            action["actionDesc"] = "".join(directs[0:2])
            return action
        if length == 0:
            action["actionType"] = "N"
            return action
        if length > 0:
            action["actionDesc"] = directs[0]
        return action

    def attack_controll_ball(self, graph):
        '''
        不持球的队友优先攻击对方拿球的人 -_-， 堵住他通往篮筐的路
        :param battle_data:
        :return:
        '''
        for player in self.players:
            if player.get("teamId") != TEMAID and player.get("controlBall") == 1:
                point = Point(player["col"], player["row"], player["id"])
                goal_path = self.find_goal_path(graph, point)
                if len(goal_path) > 1:
                    state = goal_path[1].state
                    goal_path[1].state = "H"
                    goal_path1 = self.find_goal_path(graph, point)
                    goal_path[1].state = state
                    if len(goal_path1) - len(goal_path) > 5:
                        print("emermy position, row:{},col:{}".format(point.y, point.x))
                        block_point = goal_path[1]  # 0 为持球人所在的位置， 1为该持球人下个人要走的位置
                        return block_point
                return None

    def get_controll_ball_length(self, graph):
        '''
        不持球的队友优先攻击对方拿球的人 -_-， 堵住他通往篮筐的路
        :param battle_data:
        :return:
        '''
        for player in self.players:
            if player.get("teamId") != TEMAID and player.get("controlBall") == 1:
                point = Point(player["col"], player["row"], player["id"])

    def find_goal_path(self, graph, start, ready_send = False):
        all_goal_path = []
        tools = []
        if ready_send:
            tools = graph.all_tools
        else:
            tools = graph.tools
        for g in tools:
            length = self.heuristic(start, g)
            g.priority = length
            all_goal_path.append(g)
        all_goal_path = sorted(all_goal_path)
        if len(all_goal_path) > 1:
            path1, cost1 = self.path_finding_teammate(graph, start,all_goal_path[0])
            path2, cost2 = self.path_finding_teammate(graph, start,all_goal_path[1])
            if cost1 > cost2:
                return path2
            if cost1 < cost2:
                return path1
            if cost1 == cost2:
                if len(path1) < len(path2):
                    return path1
                else:
                    return path2
        if len(all_goal_path) == 1:
            path1, cost1 = self.path_finding_teammate(graph, start, all_goal_path[0])
            return path1
        return all_goal_path

    def path_finding_teammate(self, graph, start, goal) -> list:
        frontier = PriorityQueue()
        frontier.put(start)
        came_from = dict()
        cost_so_far = dict()
        came_from[start] = None
        cost_so_far[start] = 0
        while not frontier.empty():
            current = frontier.get()
            if current == goal:
                break
            for next in graph.neighbors(current):
                new_cost = cost_so_far[current] + graph.cost(next)
                if next not in cost_so_far or new_cost < cost_so_far[next]:
                    cost_so_far[next] = new_cost
                    priority = new_cost + self.heuristic(goal, next)
                    next.priority = priority
                    frontier.put(next)
                    came_from[next] = current
        work_path = []
        work_path.append(goal)
        from_point = came_from[goal]
        while not from_point.__eq__(start):
            work_path.insert(0, from_point)
            from_point = came_from[from_point]
        work_path.insert(0, start)
        return work_path, cost_so_far[goal]

    def get_state(self, row:int, col:int):
        row = self.map_list[row]
        return self.map_list[col]


class Point:
    def __init__(self, x, y, state, priority = 0):
        self.x = x
        self.y = y
        self.state = state
        self.priority = priority

    def get_direct(self, other):
        if self.x > other.x:
            return "L"
        if self.x < other.x:
            return "R"
        if self.y > other.y:
            return "U"
        if self.y < other.y:
            return "D"

    def __str__(self):
        return str(self.x) + "," + str(self.y)

    def __repr__(self):
        return self.__str__()

    def __lt__(self, other):
        return self.priority < other.priority

    def __eq__(self, other):
        if self.x == other.x and self.y == other.y:
            return True
        else:
            False

    def __hash__(self):
        return hash(self.__str__())


class Graph:
    def __init__(self, map_array:list, player:dict):
        col_size = len(map_array)
        row_size= len(map_array[0])
        self.row_size = row_size
        self.col_size = col_size
        self.map_list = []
        self.player = player
        # 存储 障碍包，炸药包
        self.tools = []

        # 存储所有道具
        self.all_tools = []
        for row_idx, row in enumerate(map_array):
            row_list = []
            for col_idx, val in enumerate(row):
                graph = Point(col_idx, row_idx, val, 0)
                if val == "T":
                    self.goal = graph
                row_list.append(graph)
                if val in ["Z", "X"]:
                    self.tools.append(graph)
                if val in ["2", "3", "Z", "X"]:
                    self.all_tools.append(graph)
            self.map_list.append(row_list)

    def neighbors(self, current:Point):
        neighbors = []
        if current.x > 0:
            row = self.map_list[current.y]
            neighbors.append(row[current.x - 1])
        if current.y > 0:
            row = self.map_list[current.y - 1]
            neighbors.append(row[current.x])
        if current.x < self.row_size -1:
            row = self.map_list[current.y]
            neighbors.append(row[current.x + 1])
        if current.y < self.col_size - 1:
            row = self.map_list[current.y + 1]
            neighbors.append(row[current.x])
        return neighbors

    def cost(self, next:Point):
        '''
        对数据进行评估cost
        :param current: 当前位置
        :param next: 下一个位置
        :return: 路程花销
        '''
        cost = 0
        if next.state == "O": # 空位置
            cost = 1
        if next.state == "H": # 障碍物
            if self.player["boomNum"] != 0:
                cost = 2
            else:
                cost = 4
            if self.player["controlBall"] == 0:  # 不控球的人尽量不使用炸弹包
                cost = 30
        if next.state == "2": # 2倍包
            cost == -1
        if next.state == "3": # 3倍包
            cost == -2
        if next.state == "Z": # 障碍包
            cost == 0
        if next.state == "X": # 炸药包
            cost == -1
        if next.state == "T": # 篮筐
            cost == 2
        id = self.player["id"]

        if next.state in TEAMMATE: # 队友之间不是障碍物,可穿过不可停留
            cost = 2
        if next.state in ENERMY: # 敌人未障碍物，不可穿过不可停留
            cost = 4
        # print("id:{},teama:{}, teamb:{},cost:{}".format(id, TEAMMATE, ENERMY,cost))
        return cost

    def heuristic(self, current, goal)->int:
        # 简单的计算cost值
        cost = 0
        start = None
        end = None
        if current.x > goal.x:
            start = goal
            end = current
        else:
            start = current
            end = goal
        row_data = self.map_list[start.y]
        while start.x != end.x:
            start.x += 1
            cost += self.cost(row_data[start.x])

        while start.y != end.y:
            if start.y > end.y:
                start.y -= 1
            else:
                start.y += 1
            row_data = self.map_list[start.y]
            cost += self.cost(row_data[start.x])
        return cost

