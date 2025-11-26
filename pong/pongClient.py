# =================================================================================================
# Contributing Authors:     David Macara
# Email Addresses:          david@macarasoftware.com
# Date:                     November 21, 2025
# Purpose:                  Client logic for multiplayer Pong game with server communication
# Misc:                     Connects to server and synchronizes game state between players
# =================================================================================================

import pygame
import tkinter as tk
import sys
import socket
import json
import threading
import time

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


def playGame(screenWidth:int, screenHeight:int, playerPaddle:str, client:socket.socket) -> None:
    
    # Pygame inits
    pygame.mixer.pre_init(44100, -16, 2, 2048)
    pygame.init()

    # Constants
    WHITE = (255,255,255)
    clock = pygame.time.Clock()
    scoreFont = pygame.font.Font("./assets/fonts/pong-score.ttf", 32)
    winFont = pygame.font.Font("./assets/fonts/visitor.ttf", 48)
    waitFont = pygame.font.Font("./assets/fonts/visitor.ttf", 32)
    pointSound = pygame.mixer.Sound("./assets/sounds/point.wav")
    bounceSound = pygame.mixer.Sound("./assets/sounds/bounce.wav")

    # Display objects
    screen = pygame.display.set_mode((screenWidth, screenHeight))
    pygame.display.set_caption(f"Pong - {playerPaddle.upper()} Player")
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

    # Waiting for opponent screen
    waiting = True
    while waiting:
        screen.fill((0,0,0))
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
        
        # Send a heartbeat to server to trigger response with both_connected flag
        try:
            heartbeat = {
                'paddle_y': playerPaddleObj.rect.y,
                'moving': '',
                'sync': 0
            }
            client.sendall(json.dumps(heartbeat).encode() + b'\n')
        except:
            pass
        
        # Check if opponent connected
        with data_lock:
            if server_data.get('both_connected', False):
                waiting = False
        
        # Draw waiting message
        waitText = "Waiting for opponent to connect..."
        textSurface = waitFont.render(waitText, False, WHITE, (0,0,0))
        textRect = textSurface.get_rect()
        textRect.center = ((screenWidth/2), screenHeight/2)
        screen.blit(textSurface, textRect)
        
        pygame.display.flip()
        clock.tick(10)
        time.sleep(0.1)  # Small delay to not spam server
    
    # Brief countdown
    for count in [3, 2, 1]:
        screen.fill((0,0,0))
        countText = str(count)
        textSurface = winFont.render(countText, False, WHITE, (0,0,0))
        textRect = textSurface.get_rect()
        textRect.center = ((screenWidth/2), screenHeight/2)
        screen.blit(textSurface, textRect)
        pygame.display.flip()
        time.sleep(0.5)

    # Main game loop
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

        # Receive updates from server
        with data_lock:
            if server_data:
                # Update opponent paddle position
                if playerPaddle == "left":
                    opponentPaddleObj.rect.y = server_data.get('right_paddle_y', opponentPaddleObj.rect.y)
                    opponentPaddleObj.moving = server_data.get('right_moving', '')
                else:
                    opponentPaddleObj.rect.y = server_data.get('left_paddle_y', opponentPaddleObj.rect.y)
                    opponentPaddleObj.moving = server_data.get('left_moving', '')
                
                # RIGHT player receives ball position from server (left player is authoritative)
                if playerPaddle == "right":
                    ball.rect.x = server_data.get('ball_x', ball.rect.x)
                    ball.rect.y = server_data.get('ball_y', ball.rect.y)
                    ball.xVel = server_data.get('ball_xVel', ball.xVel)
                    ball.yVel = server_data.get('ball_yVel', ball.yVel)
                
                # Always update scores from server
                lScore = server_data.get('left_score', lScore)
                rScore = server_data.get('right_score', rScore)

        # Update the player paddle position
        if playerPaddleObj.moving == "down":
            if playerPaddleObj.rect.bottomleft[1] < screenHeight-10:
                playerPaddleObj.rect.y += playerPaddleObj.speed
        elif playerPaddleObj.moving == "up":
            if playerPaddleObj.rect.topleft[1] > 10:
                playerPaddleObj.rect.y -= playerPaddleObj.speed

        # If the game is over, display the win message
        if lScore > 4 or rScore > 4:
            winText = "Player 1 Wins! " if lScore > 4 else "Player 2 Wins! "
            textSurface = winFont.render(winText, False, WHITE, (0,0,0))
            textRect = textSurface.get_rect()
            textRect.center = ((screenWidth/2), screenHeight/2)
            winMessage = screen.blit(textSurface, textRect)
        else:
            # ==== Ball Logic (ONLY for LEFT player) =============================================
            if playerPaddle == "left":
                ball.updatePos()

                # If the ball makes it past the edge of the screen, update score
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
            # ==== End Ball Logic =================================================================
            
            pygame.draw.rect(screen, WHITE, ball)

        # Drawing the dotted line in the center
        for i in centerLine:
            pygame.draw.rect(screen, WHITE, i)
        
        # Drawing the paddles
        for paddle in [playerPaddleObj, opponentPaddleObj]:
            pygame.draw.rect(screen, WHITE, paddle)

        pygame.draw.rect(screen, WHITE, topWall)
        pygame.draw.rect(screen, WHITE, bottomWall)
        scoreRect = updateScore(lScore, rScore, screen, WHITE, scoreFont)
        
        # Full screen update to prevent trailing
        pygame.display.flip()
        clock.tick(60)
        
        sync += 1

        # Send update to server
        try:
            update = {
                'paddle_y': playerPaddleObj.rect.y,
                'moving': playerPaddleObj.moving,
                'sync': sync
            }
            
            # Only LEFT player sends ball data
            if playerPaddle == "left":
                update['ball_x'] = ball.rect.x
                update['ball_y'] = ball.rect.y
                update['ball_xVel'] = ball.xVel
                update['ball_yVel'] = ball.yVel
                update['left_score'] = lScore
                update['right_score'] = rScore
            
            client.sendall(json.dumps(update).encode() + b'\n')
        except Exception as e:
            print(f"Error sending update to server: {e}")
            pygame.quit()
            sys.exit()


def joinServer(ip:str, port:str, errorLabel:tk.Label, app:tk.Tk) -> None:
    # Validate inputs
    if not ip or not port:
        errorLabel.config(text="Please enter both IP address and port")
        errorLabel.update()
        return
    
    try:
        port_num = int(port)
    except ValueError:
        errorLabel.config(text="Port must be a number")
        errorLabel.update()
        return
    
    # Create a socket and connect to the server
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.settimeout(10)
    
    try:
        errorLabel.config(text=f"Connecting to {ip}:{port}...")
        errorLabel.update()
        
        # Connect to server
        client.connect((ip, port_num))
        
        errorLabel.config(text="Connected! Waiting for game info...")
        errorLabel.update()
        
        # Receive initial game info from server
        buffer = ""
        while '\n' not in buffer:
            data = client.recv(1024).decode()
            if not data:
                raise Exception("Server closed connection")
            buffer += data
        
        message = buffer.split('\n')[0]
        game_info = json.loads(message)
        
        # Check for errors
        if 'error' in game_info:
            errorLabel.config(text=f"Server error: {game_info['error']}")
            errorLabel.update()
            client.close()
            return
        
        # Extract game parameters
        screenWidth = game_info['screen_width']
        screenHeight = game_info['screen_height']
        playerPaddle = game_info['player_paddle']
        
        errorLabel.config(text=f"Starting game as {playerPaddle} player...")
        errorLabel.update()
        
        # Remove timeout for gameplay
        client.settimeout(None)
        
        # Close this window and start the game
        app.withdraw()
        playGame(screenWidth, screenHeight, playerPaddle, client)
        app.quit()
        
    except socket.timeout:
        errorLabel.config(text="Connection timeout - server not responding")
        errorLabel.update()
        client.close()
    except ConnectionRefusedError:
        errorLabel.config(text="Connection refused - is the server running?")
        errorLabel.update()
        client.close()
    except json.JSONDecodeError:
        errorLabel.config(text="Invalid response from server")
        errorLabel.update()
        client.close()
    except Exception as e:
        errorLabel.config(text=f"Error: {str(e)}")
        errorLabel.update()
        client.close()


def startScreen():
    app = tk.Tk()
    app.title("Server Info")

    image = tk.PhotoImage(file="./assets/images/logo.png")

    titleLabel = tk.Label(image=image)
    titleLabel.grid(column=0, row=0, columnspan=2)

    ipLabel = tk.Label(text="Server IP:")
    ipLabel.grid(column=0, row=1, sticky="W", padx=8)

    ipEntry = tk.Entry(app)
    ipEntry.grid(column=1, row=1)
    ipEntry.insert(0, "127.0.0.1")

    portLabel = tk.Label(text="Server Port:")
    portLabel.grid(column=0, row=2, sticky="W", padx=8)

    portEntry = tk.Entry(app)
    portEntry.grid(column=1, row=2)
    portEntry.insert(0, "12345")

    errorLabel = tk.Label(text="")
    errorLabel.grid(column=0, row=4, columnspan=2)

    joinButton = tk.Button(text="Join", command=lambda: joinServer(ipEntry.get(), portEntry.get(), errorLabel, app))
    joinButton.grid(column=0, row=3, columnspan=2)

    app.mainloop()

if __name__ == "__main__":
    startScreen()