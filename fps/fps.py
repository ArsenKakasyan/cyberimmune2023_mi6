#!/usr/bin/env python

import requests
import json
from random import randrange
from flask import Flask, request, jsonify
from fps_sec import Security

class Drone:

    def __init__(self, coordinate, name, psswd, port, index):
        self.coordinate = coordinate
        self.name = name
        self.psswd = psswd
        self.status = "Initiated"
        self.endpoint = "http://drone" + \
            str(index) + ":" + str(port) + "/set_command"

    def check_credentials(self, name, psswd):
       return Security.check_credentials(self, name, psswd)

class User:

    def __init__(self, name, psswd):
        self.name = name
        self.psswd = psswd
        self.drones = []

    def check_credentials(self, name, psswd):
       return Security.check_credentials(self, name, psswd)

    def add_drone(self, drone):
        self.drones.append(drone)

    def get_drones(self):
        return [drone.name for drone in self.drones]

###
### FPS refactored
### 
class Fps:
    def __init__(self):
        self.users = {}
        self.drones = {}
        self.supported_commands = ['start', 'stop', 'sign_out', 'new_task', 'register', 'clear_flag']
        self.port = 6065
        self.host_name = "0.0.0.0"
        self.CONTENT_HEADER = {"Content-Type": "application/json"}
        self.ATM_ENDPOINT_URI = "http://atm:6064/new_task"

        self.app = Flask(__name__)
        self.define_routes()
    
    # fps command handler (security valuable code) 
    def _handle_command(self, drone, command, data):
        if not drone.check_credentials(data['name'], data['psswd']):
            print(f'FPS: CREDENTIALS ERROR')
            return jsonify({"message": "FPS: CREDENTIALS ERROR"}), 400
        if not data['username'] in self.users:
                print(f'FPS: USER NOT REGISTERED: {data["username"]}')
                return jsonify({"message": "FPS: USER NOT REGISTERED"}), 400
        if not self.users[data['username']].check_credentials(data['username'], data['userpsswd']):
            print(f'FPS: USER CREDENTIALS ERROR: {data["username"]}')
            return jsonify({"message": "FPS: USER CREDENTIALS ERROR"}), 400
        
        # most of the time i spent on debugging this (because its the only 1 endpoint to atm)
        if command == 'new_task':
            try:
                requests.post(
                    self.ATM_ENDPOINT_URI,
                    data=json.dumps(data),
                    headers=self.CONTENT_HEADER,
                )
            except Exception as e:
                print(f'exception raised: {e}')
                return jsonify({"message": "CANNOT CONNECT TO ATM"}), 400
        if command == 'sign_out':
            drone.status = 'Initiated'
        try:
            requests.post(
                drone.endpoint,
                data=json.dumps(data),
                headers=self.CONTENT_HEADER,
            )
        except Exception as e:
            print(f'exception raised: {e}')
            return jsonify({"message": "CANNOT CONNECT TO DRONE"}), 400

        print(f'FPS: proccessed {command} for {data["name"]}')
        return jsonify({"operation": "set_command", "status": True})
    
    # fps routes
    def define_routes(self):

        # register new user in fps
        @self.app.route("/fps_reg_user", methods=['POST'])
        def fps_reg_user():
            content = request.json
            if content['username'] in self.users:
                print(f'FPS: USER ALREADY EXISTS: {content["username"]}')
                return jsonify({"message": "FPS: USER ALREADY EXISTS"}), 400

            self.users[content['username']] = User(content['username'], content['userpsswd'])
            print(f'FPS: USER REGISTERED: {content["username"]}')
            return jsonify({"message": "FPS: USER REGISTERED"}), 200

        # initiate new drone in fps and activate it
        @self.app.route("/fps_reg_drone", methods=['POST'])
        def fps_reg_drone():
            content = request.json
            if len(self.drones) == 3:
                print(f'FPS: TOO MANY DRONES')
                return jsonify({"message": "FPS: TOO MANY DRONES"}), 400
            if content['name'] in self.drones:
                print(f'FPS: DRONE ALREADY INITIATED: {content["name"]}')
                return jsonify({"message": "FPS: DRONE ALREADY INITIATED"}), 400
            if not content['username'] in self.users:
                print(f'FPS: USER NOT REGISTERED: {content["username"]}')
                return jsonify({"message": "FPS: USER NOT REGISTERED"}), 400
            if not self.users[content['username']].check_credentials(content['username'], content['userpsswd']):
                print(f'FPS: USER CREDENTIALS ERROR: {content["username"]}')
                return jsonify({"message": "FPS: USER CREDENTIALS ERROR"}), 400
            
            self.drones[content['name']] = Drone(
                content['coordinate'], content['name'], content['psswd'], 6066 + len(self.drones), len(self.drones))
            print(f'FPS: DRONE INITIATED: {content["name"]}')

            self.users[content['username']].add_drone(self.drones[content['name']])
            print(f'FPS: DRONE ACTIVATED BY: {content["username"]}')

            drone = self.drones[content['name']]
            drone.status = 'Working'
            return self._handle_command(drone, content['command'], content)
        
        # get user's drones from fps
        @self.app.route("/fps_get_drones", methods=['POST'])
        def fps_get_drones():
            content = request.json
            if not content['username'] in self.users:
                print(f'FPS: USER NOT REGISTERED: {content["username"]}')
                return jsonify({"message": "FPS: USER NOT REGISTERED"}), 400

            if not self.users[content['username']].check_credentials(content['username'], content['userpsswd']):
                print(f'FPS: USER CREDENTIALS ERROR: {content["username"]}')
                return jsonify({"message": "FPS: USER CREDENTIALS ERROR"}), 400

            user = self.users[content['username']]
            print(f'[FPS_GET_DRONES]: {user.get_drones()}')
            return jsonify({"FPS INITED DRONES": list(self.drones.keys())})

        # route refactored using _handle_command
        @self.app.route("/set_command", methods=['POST'])
        def set_command():
            content = request.json
            if content is None: 
                print(f'FPS: INVALID REQUEST BODY')
                return jsonify({"message": "FPS: INVALID REQUEST BODY"}), 400
            try:
                if content['command'] in self.supported_commands and content['name'] in self.drones:
                    drone = self.drones[content['name']]
                    return self._handle_command(drone, content['command'], content)

                elif content['name'] not in self.drones:
                    print(f'FPS: DRONE NOT FOUND: {content["name"]}')
                    return jsonify({"message": "FPS: DRONE NOT FOUND"}), 400
                else:
                    print(f'FPS: COMMAND NOT FOUND: {content["command"]}')
                    return jsonify({"message": "FPS: COMMAND NOT FOUND"}), 400

                return jsonify({"message": "FPS proccessed your request"}), 200

            except Exception as e:
                print(e)
                error_message = f"malformed request {request.data}"
                return error_message, 400

        @self.app.route("/data_in", methods=['POST'])
        def data_in():
            content = request.json
            if content is None:
                print(f'FPS: INVALID REQUEST BODY')
                return jsonify({"message": "INVALID REQUEST BODY"}), 400

            try:
                drone = self.drones[content['name']]
                print(f'[FPS_DATA_IN]')

                if content['operation'] == 'log':
                    if content['msg'] == "Task finished":
                        drone.status = 'Initiated'
                        print(f'FPS: {content["name"]} successfully finished!')
                    else:
                        print(f'FPS: Successfully received {content}')
                elif content['operation'] == 'data':
                    print(f'FPS: Successfully received {content}')
            except Exception as _:
                error_message = f"malformed request {request.data}"
                return error_message, 400
            return jsonify({"operation": "new_task", "status": True})

        @self.app.route("/atm_input", methods=['POST'])
        def atm_input():
            content = request.json
            if content is None:
                print(f'FPS: INVALID REQUEST BODY')
                return jsonify({"message": "INVALID REQUEST BODY"}), 400
            drone = self.drones[content['name']]
            try:
                """if content['name'] in self.drones:
                    print(f'FPS: DRONE ALREADY REGISTERED: {content["name"]}')
                    return jsonify({"message": "FPS: DRONE ALREADY REGISTERED"}), 400"""

                if content['task_status'] == 'Accepted':
                    data = {
                        "name": content['name'],
                        "points": content['points'],
                        "command": content['command'],
                        "psswd": drone.psswd, 
                    }
                    
                    requests.post(
                        drone.endpoint,
                        data=json.dumps(data),
                        headers=self.CONTENT_HEADER,
                    )
                    print(
                        f'FPS: NEW TASK FOR {content["name"]}')
                else:
                    print(
                        f'FPS: CANT ACCEPT NEW TASK FOR {content["name"]}')

            except Exception as _:
                error_message = f"malformed request {request.data}"
                return error_message, 400
            return jsonify({"operation": "new_task", "status": True})

    def run(self, port, host):
        self.app.run(port=port, host=host)

if __name__ == "__main__":
    Fps = Fps()
    Fps.run(port=Fps.port, host=Fps.host_name)
