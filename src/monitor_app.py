#!/bin/env python
"""
The 'Events App' receives events and distributes them via sockets to registered clients.
This includes other sockets services, such as CI versions and realtime feature generators,
as well as end-users who open the monitor webpage.
"""
# global imports
from typing import Dict
# 3rd-party imports
from flask import Flask, render_template, request
from flask_socketio import SocketIO
from flask_restful import Api, Resource
# ogd imports
from ogd.common.models.Event import Event
from ogd.common.schemas.games.GameSchema import GameSchema
from ogd.core.managers.FeatureManager import FeatureManager
from ogd.core.managers.ExportManager import ExportManager
# local imports
from utils.ClientManager import ClientManager

app = Flask(__name__)
api = Api(app)
app.config['SECRET_KEY'] = 'secret-key'
socketio = SocketIO(app, cors_allowed_origins="*")

# game_rooms is a dict storing {game_room} and corresponding {client_id}
# { 
#   'aqualab' : ['clientIDxxxxxinRoomAqualab', 'clientIDyyyyyyinRoomAqualab'],
#   ...
# }

client_manager = ClientManager()

game_schema = GameSchema.FromFile(game_id="AQUALAB")
loader = ExportManager._loadLoaderClass(game_id="AQUALAB")
feature_manager = FeatureManager(game_schema=game_schema, LoaderClass=loader, feature_overrides=["ActiveTime"])


@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('connect')
def handle_connect():
    """When a new client connects, add its ID to the default game room, "AQUALAB"
    """
    client_id = request.sid
    # print(f'Client connected with ID: {client_id}')
    client_manager.add_client_by_client_id("AQUALAB", client_id)

@socketio.on('disconnect')
def handle_disconnect():
    """When current client "disconnects," remove its ID from game rooms
    """
    client_id = request.sid
    client_manager.remove_client_by_client_id(client_id)
    # print(f'Client disconnected with ID: {client_id}')

@socketio.on('game_selector_changed')
def handle_game_selector_changed(selectedGame:str):
    """When current client changes game selecor, remove it from current game room and join to the newly-assigned room

    :param selectedGame: The newly-selected game to which the client should be moved.
    :type selectedGame: str
    """
    client_id = request.sid
    client_manager.remove_client_by_client_id(client_id)
    client_manager.add_client_by_client_id(selectedGame, client_id)

class LoggerReceiver(Resource):
    """flask-restful API receiver.
    
    Allows data coming in through name space '/log/event' to send data to corresponding room
    """
    def post(self):
    # 1. Get event data, and send.
        event_data : Dict = request.get_json() or {}
        _room = event_data.get('app_id', "APP ID NOT FOUND")
        socketio.emit('logger_data', event_data, to=_room)
    # 2. Get updated feature data from events, and send.
        try:
            print(f"Received LoggerReceiver request, with data {event_data}")
            _event = Event.FromJSON(event_data)
        except Exception as err:
            socketio.emit('feature_data', {"Error":f"Got a parse error when extracting an Event from {event_data} : {type(err)} : {err}"}, to=_room)
        else:
            feature_manager.ProcessEvent(event=_event)
            feature_data = feature_manager.GetFeatureValues()
            socketio.emit('feature_data', {"features" : feature_data}, to=_room)
    # 3. Wrap up
        return {'message': 'Received logger data successfully'}


api.add_resource(LoggerReceiver, '/log/event')

if __name__ == '__main__':
    socketio.run(app, port=5022, debug=True, use_reloader=True, log_output=True, allow_unsafe_werkzeug=True) # For debugging work
    # socketio.run(app, port=5022, debug=False, use_reloader=False, log_output=True, allow_unsafe_werkzeug=False) # For stable, production work
