from flask import Flask, render_template, request
from flask_socketio import SocketIO, join_room, leave_room
from flask_restful import Api, Resource

from ogd.core.managers.FeatureManager import FeatureManager
from ogd.core.schemas.games.GameSchema import GameSchema
from ogd.core.games.AQUALAB.AqualabLoader import AqualabLoader
from ogd.core.schemas.Event import Event
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

game_rooms = {}
game_managers = {}


@app.route('/')
def index():
    return render_template('index.html')

# when new client is "connect"
# add its id to default game room "aqualab"
@socketio.on('connect')
def handle_connect():
    client_id = request.sid
    # print(f'Client connected with ID: {client_id}')
    client_manager.add_client_by_client_id("AQUALAB", client_id)

# when current client is "disconnect"
# remove its id from game rooms
@socketio.on('disconnect')
def handle_disconnect():
    client_id = request.sid
    client_manager.remove_client_by_client_id(client_id)
    # print(f'Client disconnected with ID: {client_id}')

# when current client changes game selecor
# remove it from current game room and join to the new assigned room
@socketio.on('game_selector_changed')
def handle_game_selector_changed(selectedGame):
    client_id = request.sid
    client_manager.remove_client_by_client_id(client_id)
    client_manager.add_client_by_client_id(selectedGame, client_id)

# flask-restful api receiver
# allows data coming in through name space 'all-game'
# send data to corresponding room
class LoggerReceiver(Resource):
    def post(self):
        json_data = request.get_json() or {}
        _event = Event(session_id=json_data.get("session_id"),
                       app_id=json_data.get("app_id", "AQUALAB"))
        socketio.emit('logger_data', json_data, to=json_data.get('app_id'))
        return {'message': 'Received logger data successfully'}


api.add_resource(LoggerReceiver, '/all-game')

if __name__ == '__main__':
    socketio.run(app, port=5022, debug=True, use_reloader=True, log_output=True, allow_unsafe_werkzeug=True) # For debugging work
    # socketio.run(app, port=5022, debug=False, use_reloader=False, log_output=True, allow_unsafe_werkzeug=False) # For stable, production work
