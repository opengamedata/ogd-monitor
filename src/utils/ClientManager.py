# global imports
from typing import Dict, List
# 3rd-party imports
from flask_socketio import join_room, leave_room

class ClientManager:
    def __init__(self):
        self.game_rooms : Dict[str, List[str]] = {}
    # given client session id
    # remove it from game rooms
    def remove_client_by_client_id(self, client_id:str):
        """Given a client's session ID, remove it from all game rooms.

        :param client_id: The ID of the client to be removed from all game rooms
        :type client_id: str
        """
        for game_name, clients in self.game_rooms.items():
            if client_id in clients:
                clients.remove(client_id)
                leave_room(game_name, client_id)
                # print(f'Client ID: {client_id} removed from Room {game_name}')

    # given game room name and client session id
    # join client to the corresponding game room
    def add_client_by_client_id(self, game_name:str, client_id:str):
        """Given the name of a game room and a client's session id, join client to the corresponding game room

        :param game_name: The name of the game to whose room the client should be added
        :type game_name: str
        :param client_id: The ID of the client session to be added into the room
        :type client_id: str
        """
        if game_name not in self.game_rooms:
            self.game_rooms[game_name] = []

        if client_id not in self.game_rooms[game_name]:
            self.game_rooms[game_name].append(client_id)
            join_room(game_name, client_id)
            # print(f'Client ID: {client_id} added to Room {game_name}')