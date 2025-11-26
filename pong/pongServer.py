# =================================================================================================
# Contributing Authors:     David Macara
# Email Addresses:          david@macarasoftware.com
# Date:                     November 21, 2025
# Purpose:                  Server logic for multiplayer Pong game
# Misc:                     Handles two simultaneous clients and synchronizes game state
# =================================================================================================
import socket
import threading
import json

# Global game state
game_state = {
    'left_paddle_y': 215,
    'right_paddle_y': 215,
    'ball_x': 320,
    'ball_y': 240,
    'ball_xVel': -5,
    'ball_yVel': 0,
    'left_score': 0,
    'right_score': 0,
    'sync': 0,
    'left_moving': '',
    'right_moving': '',
    'both_connected': False
}

# Lock for thread-safe access to game state
state_lock = threading.Lock()

# Client connection tracking
clients = {'left': None, 'right': None}
client_lock = threading.Lock()

# Screen dimensions
SCREEN_WIDTH = 640
SCREEN_HEIGHT = 480


def handle_client(client_socket: socket.socket, address: tuple, player_side: str) -> None:
    """
    # Author:       David Macara
    # Purpose:      Handle communication with a single client
    # Pre:          Client socket is connected, player_side is 'left' or 'right'
    # Post:         Client is disconnected and removed from clients dictionary
    """
    print(f"Player {player_side} connected from {address}")
    
    try:
        # Send initial game info to client
        init_data = {
            'screen_width': SCREEN_WIDTH,
            'screen_height': SCREEN_HEIGHT,
            'player_paddle': player_side
        }
        client_socket.sendall(json.dumps(init_data).encode() + b'\n')
        
        # Main communication loop
        buffer = ""
        while True:
            # Receive data from client
            data = client_socket.recv(4096).decode()
            if not data:
                break
            
            buffer += data
            
            # Process all complete messages (delimited by newlines)
            while '\n' in buffer:
                message, buffer = buffer.split('\n', 1)
                
                if message:
                    try:
                        update = json.loads(message)
                        
                        # Update game state with client's data
                        with state_lock:
                            if player_side == 'left':
                                game_state['left_paddle_y'] = update.get('paddle_y', game_state['left_paddle_y'])
                                game_state['left_moving'] = update.get('moving', '')
                                
                                # LEFT player is authoritative for ball and scores
                                if 'ball_x' in update:
                                    game_state['ball_x'] = update['ball_x']
                                    game_state['ball_y'] = update['ball_y']
                                    game_state['ball_xVel'] = update['ball_xVel']
                                    game_state['ball_yVel'] = update['ball_yVel']
                                
                                if 'left_score' in update:
                                    game_state['left_score'] = update['left_score']
                                if 'right_score' in update:
                                    game_state['right_score'] = update['right_score']
                                    
                            else:  # right player
                                game_state['right_paddle_y'] = update.get('paddle_y', game_state['right_paddle_y'])
                                game_state['right_moving'] = update.get('moving', '')
                            
                            # Update sync counter
                            client_sync = update.get('sync', 0)
                            if client_sync > game_state['sync']:
                                game_state['sync'] = client_sync
                            
                            # Check if both players are connected
                            with client_lock:
                                game_state['both_connected'] = (clients['left'] is not None and clients['right'] is not None)
                        
                        # Send current game state back to client
                        with state_lock:
                            response = {
                                'left_paddle_y': game_state['left_paddle_y'],
                                'right_paddle_y': game_state['right_paddle_y'],
                                'ball_x': game_state['ball_x'],
                                'ball_y': game_state['ball_y'],
                                'ball_xVel': game_state['ball_xVel'],
                                'ball_yVel': game_state['ball_yVel'],
                                'left_score': game_state['left_score'],
                                'right_score': game_state['right_score'],
                                'sync': game_state['sync'],
                                'left_moving': game_state['left_moving'],
                                'right_moving': game_state['right_moving'],
                                'both_connected': game_state['both_connected']
                            }
                        
                        client_socket.sendall(json.dumps(response).encode() + b'\n')
                        
                    except json.JSONDecodeError:
                        print(f"Invalid JSON from {player_side} player")
                        continue
                    except Exception as e:
                        print(f"Error processing message from {player_side}: {e}")
                        continue
    
    except Exception as e:
        print(f"Error with {player_side} player: {e}")
    
    finally:
        print(f"Player {player_side} disconnected")
        with client_lock:
            clients[player_side] = None
        with state_lock:
            game_state['both_connected'] = False
        client_socket.close()


def start_server(host: str = '0.0.0.0', port: int = 12345) -> None:
    """
    # Author:       David Macara
    # Purpose:      Start the Pong game server and accept client connections
    # Pre:          Port is available for binding
    # Post:         Server is running and accepting connections
    """
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        server_socket.bind((host, port))
        server_socket.listen(2)
        print(f"Pong server started on {host}:{port}")
        print("Waiting for 2 players to connect...")
        
        while True:
            client_socket, address = server_socket.accept()
            
            # Determine which paddle to assign
            with client_lock:
                if clients['left'] is None:
                    player_side = 'left'
                    clients['left'] = client_socket
                elif clients['right'] is None:
                    player_side = 'right'
                    clients['right'] = client_socket
                else:
                    # Server is full
                    print(f"Connection from {address} rejected - server full")
                    client_socket.sendall(b'{"error": "Server full"}\n')
                    client_socket.close()
                    continue
            
            # Start a new thread to handle this client
            client_thread = threading.Thread(
                target=handle_client,
                args=(client_socket, address, player_side),
                daemon=True
            )
            client_thread.start()
            
            print(f"Assigned {player_side} paddle to {address}")
            
            # Check if both players are connected
            with client_lock:
                if clients['left'] is not None and clients['right'] is not None:
                    print("Both players connected! Game starting...")
    
    except KeyboardInterrupt:
        print("\nServer shutting down...")
    finally:
        server_socket.close()


if __name__ == "__main__":
    PORT = 12345
    
    print("=" * 50)
    print("Pong Game Server")
    print("=" * 50)
    
    try:
        start_server(port=PORT)
    except Exception as e:
        print(f"Failed to start server: {e}")