from multiprocessing import Process, Queue
import random
from time import sleep
from flask import Flask, jsonify, request
import json
import requests


host_name = "0.0.0.0"
port = 6062

REQUEST_HEADERS = {
    "Content-Type": "application/json",
    "auth": "very-secure-token"
}

FPS_REGUSER_ENDPOINT_URI = 'http://0.0.0.0:6065/fps_reg_user'
FPS_REGDRONE_ENDPOINT_URI = 'http://0.0.0.0:6065/fps_reg_drone'
FPS_COMMAND_ENDPOINT_URI = 'http://0.0.0.0:6065/set_command'
ATM_COMMAND_ENDPOINT_URI = 'http://0.0.0.0:6064/set_area'

global_events_log = Queue()


app = Flask(__name__)  # create an app instance


def test_security():
    global global_events_log
    server = Process(target=lambda: app.run(port=port, host=host_name))
    server.start()

    # Test with invalid command
    data = {
        "command": "invalid_command",
        "name": "ITEM1",
        "psswd": "12345"
    }
    response = requests.post(
        FPS_COMMAND_ENDPOINT_URI,
        data=json.dumps(data),
        headers=REQUEST_HEADERS,
    )
    assert response.status_code != 200

    # Test with missing required fields
    data = {
        "command": "initiate",
        "name": "ITEM1",
        "psswd": "12345"
    }
    response = requests.post(
        FPS_REGDRONE_ENDPOINT_URI,
        data=json.dumps(data),
        headers=REQUEST_HEADERS,
    )
    assert response.status_code != 200

    # Test with missing required fields
    data = {
        "command": "initiate",
        "coordinate": [2, 2, 2],
        "psswd": "12345"
    }
    response = requests.post(
        FPS_REGDRONE_ENDPOINT_URI,
        data=json.dumps(data),
        headers=REQUEST_HEADERS,
    )
    assert response.status_code != 200

    # Test with missing required fields
    data = {
        "command": "initiate",
        "name": "ITEM1",
        "coordinate": [2, 2, 2]
    }
    response = requests.post(
        FPS_REGDRONE_ENDPOINT_URI,
        data=json.dumps(data),
        headers=REQUEST_HEADERS,
    )
    assert response.status_code != 200

    # Test reguser
    data = {
        "username" : "SamAltman",
        "userpsswd": 12345
    }
    response = requests.post(
        FPS_REGUSER_ENDPOINT_URI,
        data=json.dumps(data),
        headers=REQUEST_HEADERS,
    )
    assert response.status_code == 200

    # Test regdrone with wrong credentials
    data = {
        "command" : "initiate",
        "username" : "SamAltman",
        "userpsswd": 1234,
        "name" : "ITEM1", #
        "points" : [[5,5,5,0],[8,8,8,1],[11,11,11,1],[16,16,11,0]],
        "psswd": 12345
    }
    response = requests.post(
        FPS_COMMAND_ENDPOINT_URI,
        data=json.dumps(data),
        headers=REQUEST_HEADERS,
    )
    assert response.status_code != 200

    # Test new_task without user
    data = {
        "command" : "new_task",
        "username" : "SamAltman", 
        "userpsswd": 1234, 
        "name" : "ITEM1", 
        "points" : [[5,5,5,0],[8,8,8,1],[11,11,11,1],[16,16,11,0]],
        "psswd": 12345
    }
    response = requests.post(
        FPS_COMMAND_ENDPOINT_URI,
        data=json.dumps(data),
        headers=REQUEST_HEADERS,
    )
    assert response.status_code != 200

    # stop
    server.terminate()
    server.join()
