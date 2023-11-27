#!/usr/bin/env python

import hashlib
import os
from random import randrange
from flask import Flask, request, jsonify
import implementation

###
### Central management system prototype (Drone refactored)
###
class DroneApp:
    def __init__(self):
        self.activated_drones = {}
        self.host_name = "0.0.0.0"
        self.port = os.environ['DRONE_PORT']
        self.CONTENT_HEADER = {"Content-Type": "application/json"}
        self.ATM_ENDPOINT_URI = "http://atm:6064/data_in"
        self.ATM_SIGN_UP_URI = "http://atm:6064/sign_up"
        self.ATM_SIGN_OUT_URI = "http://atm:6064/sign_out"
        self.FPS_ENDPOINT_URI = "http://fps:6065/data_in"
        self.DELIVERY_INTERVAL_SEC = 1

        self.app = Flask(__name__)
        self.define_routes()

    # Drone activation (fps initiate command handler)
    def _activate_drone(self, content):
        if content['name'] in self.activated_drones:
            print(f'DRONEAPP: NON-UNIQUE NAME: {content["name"]}')
            return jsonify({"message": "DRONEAPP: NON-UNIQUE NAME"}), 400
        self.activated_drones[content['name']] = implementation.Drone(
            content['coordinate'], content['name'], content['psswd'])
        print(f'DRONEAPP: DRONE ACTIVATED: {content["name"]}')
        print(f"DRONEAPP: ADDED IN POINT {content['coordinate']}")

    # Drone command handler
    def _execute_command(self, content):
        drone = self.activated_drones[content['name']]
        if content['command'] == 'set_token':
            drone.token = content['token']
            print(f'[DRONE_TOKEN_SET]')
        elif content['command'] == 'task_status_change':
            if drone.token == content['token']:
                drone.task_status = content['task_status']
                drone.hash = content['hash']
                print(f'[DRONE_TASK_ACCEPTED]')
        elif drone.psswd == content['psswd']:
            if content['command'] == 'start':
                drone.start(content["speed"])
            if content['command'] == 'stop':
                drone.stop()
            if content['command'] == 'sign_out':
                drone.sign_out()
                self.activated_drones.pop(content['name'])
            if content['command'] == 'clear_flag':
                drone.clear_emergency_flag()
            if content['command'] == 'set_task':
                if drone.hash == len(content["points"]):
                    print(f'[DRONE_SET_TASK]')
                    print(f'Point added!')
                    drone.task_points = content["points"]
            if content['command'] == 'register':
                drone.register()

    # DroneApp routes
    def define_routes(self):
        @self.app.route("/emergency", methods=['POST'])
        def emergency():
            self._handle_command(request.json)
            return jsonify({"status": True})

        @self.app.route("/set_command", methods=['POST'])
        def set_command():
            content = request.json
            if content is None:
                print(f'DRONEAPP: INVALID REQUEST BODY')
                return jsonify({"message": "INVALID REQUEST BODY"}), 400
            try:
                #print(f'[DRONE_DEBUG] received {content}')
                if content['command'] == 'initiate':
                    self._activate_drone(content)
                else:
                    self._execute_command(content)
                #print(f'[DRONE_DEBUG] sent {content}')
                return jsonify({"status": True})
            except Exception as e:
                print(f'exception raised: {e}')
                return "MALFORMED REQUEST", 400

    def run(self, port, host):
        self.app.run(port=port, host=host)

if __name__ == "__main__":
    DroneApp = DroneApp()
    DroneApp.run(port=DroneApp.port, host=DroneApp.host_name)
