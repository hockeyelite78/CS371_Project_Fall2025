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




# This is where you will connect to the server to get the info required to call the game loop.  Mainly
# the screen width, height and player paddle (either "left" or "right")
# If you want to hard code the screen's dimensions into the code, that's fine, but you will need to know
# which client is which
def joinServer(ip:str, port:str, errorLabel:tk.Label, app:tk.Tk) -> None:
    # Purpose:      This method is fired when the join button is clicked
    # Arguments:
    # ip            A string holding the IP address of the server
    # port          A string holding the port the server is using
    # errorLabel    A tk label widget, modify it's text to display messages to the user (example below)
    # app           The tk window object, needed to kill the window
    
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
    client.settimeout(10)  # 10 second timeout for connection
    
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


# This displays the opening screen, you don't need to edit this (but may if you like)
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
    ipEntry.insert(0, "127.0.0.1")  # Default to localhost

    portLabel = tk.Label(text="Server Port:")
    portLabel.grid(column=0, row=2, sticky="W", padx=8)

    portEntry = tk.Entry(app)
    portEntry.grid(column=1, row=2)
    portEntry.insert(0, "12345")  # Default port

    errorLabel = tk.Label(text="")
    errorLabel.grid(column=0, row=4, columnspan=2)

    joinButton = tk.Button(text="Join", command=lambda: joinServer(ipEntry.get(), portEntry.get(), errorLabel, app))
    joinButton.grid(column=0, row=3, columnspan=2)

    app.mainloop()

if __name__ == "__main__":
    startScreen()
    
    # Uncomment the line below if you want to play the game without a server to see how it should work
    # the startScreen() function should call playGame with the arguments given to it by the server this is
    # here for demo purposes only
    # playGame(640, 480,"left",socket.socket(socket.AF_INET, socket.SOCK_STREAM))