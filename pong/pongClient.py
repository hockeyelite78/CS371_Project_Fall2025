# =================================================================================================
# Contributing Authors:     David Macara
# Email Addresses:          david@macarasoftware.com
# Date:                     November 21, 2025
# Purpose:                  Client logic for multiplayer Pong game with server communication
# Misc:                     Connects to server and synchronizes game state between players
# =================================================================================================

import pygame
import sys
import socket
import json
import threading

from assets.code.helperCode import *

# Global variable for receiving data from server
server_data = {}
data_lock = threading.Lock()

def receive_updates(client: socket.socket) -> None:
    """
    # Author:       David Macara
    # Purpose:      Continuously receive game state updates from server
    # Pre:          Client socket is connected to server
    # Post:         server_data is updated with latest game state
    """
    global server_data
    buffer = ""
    
    try:
        while True:
            data = client.recv(4096).decode()
            if not data:
                break
            
            buffer += data
            
            # Process all complete messages
            while '\n' in buffer:
                message, buffer = buffer.split('\n', 1)
                
                if message:
                    try:
                        update = json.loads(message)
                        with data_lock:
                            server_data.update(update)
                    except json.JSONDecodeError:
                        continue
    except Exception as e:
        print(f"Error receiving updates: {e}")


# This is the main game loop.  For the most part, you will not need to modify this.  The sections
# where you should add to the code are marked.  Feel free to change any part of this project
# to suit your needs.
def playGame(screenWidth:int, screenHeight:int, playerPaddle:str, client:socket.socket) -> None:
    
    # Pygame inits
    pygame.mixer.pre_init(44100, -16, 2, 2048)
    pygame.init()

    # Constants
    WHITE = (255,255,255)
    clock = pygame.time.Clock()
    scoreFont = pygame.font.Font("./assets/fonts/pong-score.ttf", 32)
    winFont = pygame.font.Font("./assets/fonts/visitor.ttf", 48)
    pointSound = pygame.mixer.Sound("./assets/sounds/point.wav")
    bounceSound = pygame.mixer.Sound("./assets/sounds/bounce.wav")

    # Display objects
    screen = pygame.display.set_mode((screenWidth, screenHeight))
    winMessage = pygame.Rect(0,0,0,0)
    topWall = pygame.Rect(-10,0,screenWidth+20, 10)
    bottomWall = pygame.Rect(-10, screenHeight-10, screenWidth+20, 10)
    centerLine = []
    for i in range(0, screenHeight, 10):
        centerLine.append(pygame.Rect((screenWidth/2)-5,i,5,5))

    # Paddle properties and init
    paddleHeight = 50
    paddleWidth = 10
    paddleStartPosY = (screenHeight/2)-(paddleHeight/2)
    leftPaddle = Paddle(pygame.Rect(10,paddleStartPosY, paddleWidth, paddleHeight))
    rightPaddle = Paddle(pygame.Rect(screenWidth-20, paddleStartPosY, paddleWidth, paddleHeight))

    ball = Ball(pygame.Rect(screenWidth/2, screenHeight/2, 5, 5), -5, 0)

    if playerPaddle == "left":
        opponentPaddleObj = rightPaddle
        playerPaddleObj = leftPaddle
    else:
        opponentPaddleObj = leftPaddle
        playerPaddleObj = rightPaddle

    lScore = 0
    rScore = 0

    sync = 0
    
    # Start receiver thread
    receiver_thread = threading.Thread(target=receive_updates, args=(client,), daemon=True)
    receiver_thread.start()

    while True:
        # Wiping the screen
        screen.fill((0,0,0))

        # Getting keypress events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_DOWN:
                    playerPaddleObj.moving = "down"

                elif event.key == pygame.K_UP:
                    playerPaddleObj.moving = "up"

            elif event.type == pygame.KEYUP:
                playerPaddleObj.moving = ""

        # =========================================================================================
        # Your code here to send an update to the server on your paddle's information,
        # where the ball is and the current score.
        # Feel free to change when the score is updated to suit your needs/requirements
        
        # Receive updates from server and apply to opponent
        with data_lock:
            if server_data:
                # Update opponent paddle position
                if playerPaddle == "left":
                    opponentPaddleObj.rect.y = server_data.get('right_paddle_y', opponentPaddleObj.rect.y)
                    opponentPaddleObj.moving = server_data.get('right_moving', '')
                else:
                    opponentPaddleObj.rect.y = server_data.get('left_paddle_y', opponentPaddleObj.rect.y)
                    opponentPaddleObj.moving = server_data.get('left_moving', '')
                
                # Sync check - if server is ahead, update our ball position
                server_sync = server_data.get('sync', 0)
                if server_sync > sync:
                    ball.rect.x = server_data.get('ball_x', ball.rect.x)
                    ball.rect.y = server_data.get('ball_y', ball.rect.y)
                    ball.xVel = server_data.get('ball_xVel', ball.xVel)
                    ball.yVel = server_data.get('ball_yVel', ball.yVel)
                    sync = server_sync
                
                # Update scores from server
                lScore = server_data.get('left_score', lScore)
                rScore = server_data.get('right_score', rScore)
        
        # =========================================================================================

        # Update the player paddle and opponent paddle's location on the screen
        for paddle in [playerPaddleObj, opponentPaddleObj]:
            if paddle.moving == "down":
                if paddle.rect.bottomleft[1] < screenHeight-10:
                    paddle.rect.y += paddle.speed
            elif paddle.moving == "up":
                if paddle.rect.topleft[1] > 10:
                    paddle.rect.y -= paddle.speed

        # If the game is over, display the win message
        if lScore > 4 or rScore > 4:
            winText = "Player 1 Wins! " if lScore > 4 else "Player 2 Wins! "
            textSurface = winFont.render(winText, False, WHITE, (0,0,0))
            textRect = textSurface.get_rect()
            textRect.center = ((screenWidth/2), screenHeight/2)
            winMessage = screen.blit(textSurface, textRect)
        else:

            # ==== Ball Logic =====================================================================
            ball.updatePos()

            # If the ball makes it past the edge of the screen, update score, etc.
            if ball.rect.x > screenWidth:
                lScore += 1
                pointSound.play()
                ball.reset(nowGoing="left")
            elif ball.rect.x < 0:
                rScore += 1
                pointSound.play()
                ball.reset(nowGoing="right")
                
            # If the ball hits a paddle
            if ball.rect.colliderect(playerPaddleObj.rect):
                bounceSound.play()
                ball.hitPaddle(playerPaddleObj.rect.center[1])
            elif ball.rect.colliderect(opponentPaddleObj.rect):
                bounceSound.play()
                ball.hitPaddle(opponentPaddleObj.rect.center[1])
                
            # If the ball hits a wall
            if ball.rect.colliderect(topWall) or ball.rect.colliderect(bottomWall):
                bounceSound.play()
                ball.hitWall()
            
            pygame.draw.rect(screen, WHITE, ball)
            # ==== End Ball Logic =================================================================

        # Drawing the dotted line in the center
        for i in centerLine:
            pygame.draw.rect(screen, WHITE, i)
        
        # Drawing the player's new location
        for paddle in [playerPaddleObj, opponentPaddleObj]:
            pygame.draw.rect(screen, WHITE, paddle)

        pygame.draw.rect(screen, WHITE, topWall)
        pygame.draw.rect(screen, WHITE, bottomWall)
        scoreRect = updateScore(lScore, rScore, screen, WHITE, scoreFont)
        pygame.display.update([topWall, bottomWall, ball, leftPaddle, rightPaddle, scoreRect, winMessage])
        clock.tick(60)
        
        # This number should be synchronized between you and your opponent.  If your number is larger
        # then you are ahead of them in time, if theirs is larger, they are ahead of you, and you need to
        # catch up (use their info)
        sync += 1
        # =========================================================================================
        # Send your server update here at the end of the game loop to sync your game with your
        # opponent's game

        try:
            # Prepare update to send to server
            update = {
                'paddle_y': playerPaddleObj.rect.y,
                'moving': playerPaddleObj.moving,
                'ball_x': ball.rect.x,
                'ball_y': ball.rect.y,
                'ball_xVel': ball.xVel,
                'ball_yVel': ball.yVel,
                'left_score': lScore,
                'right_score': rScore,
                'sync': sync
            }
            
            # Send update to server
            client.sendall(json.dumps(update).encode() + b'\n')
        except Exception as e:
            print(f"Error sending update to server: {e}")
            pygame.quit()
            sys.exit()
        
        # =========================================================================================


def joinServer(ip: str, port: int) -> None:
    """
    # Author:       David Macara
    # Purpose:      Connect to server and start the game
    # Pre:          Server is running at ip:port
    # Post:         Game starts with received parameters
    """
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.settimeout(10)
    
    try:
        print(f"Connecting to {ip}:{port}...")
        client.connect((ip, port))
        print("Connected! Waiting for game info...")
        
        # Receive initial game info
        buffer = ""
        while '\n' not in buffer:
            data = client.recv(1024).decode()
            if not data:
                raise Exception("Server closed connection")
            buffer += data
        
        message = buffer.split('\n')[0]
        game_info = json.loads(message)
        
        if 'error' in game_info:
            print(f"Server error: {game_info['error']}")
            return
        
        screenWidth = game_info['screen_width']
        screenHeight = game_info['screen_height']
        playerPaddle = game_info['player_paddle']
        
        print(f"Starting game as {playerPaddle} player...")
        client.settimeout(None)
        
        playGame(screenWidth, screenHeight, playerPaddle, client)
        
    except socket.timeout:
        print("Connection timeout - server not responding")
    except ConnectionRefusedError:
        print("Connection refused - is the server running?")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()


if __name__ == "__main__":
    # Direct connection - no GUI needed
    SERVER_IP = "127.0.0.1"  # Change this if server is on different machine
    SERVER_PORT = 12345
    
    print("=" * 50)
    print("Pong Game Client")
    print("=" * 50)
    
    joinServer(SERVER_IP, SERVER_PORT)