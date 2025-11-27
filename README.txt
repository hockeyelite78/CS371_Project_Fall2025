Contact Info
============

Group Members & Email Addresses:

    David MacDonald, David.Macdonald@uky.edu
    Ian Thornsburg, Ian.Thornsburg@uky.edu
    Renish Poudel, renish.poudel@uky.edu

Versioning
==========

Github Link: https://github.com/hockeyelite78/CS371_Project_Fall2025.git

General Info
============
This file describes how to install/run your program and anything else you think the user should know


Install Instructions
====================

WHAT YOU NEED
- 2 computers 
- Python installed
- This project folder

=============================
          SET UP 
=============================

- install python, either 3.12 or 3.11 from the python website

- if already downloaded or download finished, open terminal

- use "python --version" to check version of python

- in terminal enter "git clone https://github.com/hockeyelite78/CS371_Project_Fall2025.git"
     - this should add the project code to your computer 

- now enter "cd CS371_Project_Fall2025"
     - you are now in the project folder 

- enter "python -m venv venv" 
     - this create the virtual environment

- enter "venv\Scripts\activate"
     - this activates the virtual environment

- enter "cd pong"
     - change to pong folder of project

- enter "pip install pygame"
     - installs the necessary packages to the pong folder

================================================
              PLAYING THE GAME
================================================

------------------------------------------------
PLAYER ON COMPUTER WITH SERVER RUNNING:
------------------------------------------------

RUNNING THE SERVER:

- open a terminal window and navigate to the pong folder
     - path should be "(venv)...(default user path)...\CS371_Project_Fall2025\pong>"
     - make sure you see (venv), if not, enter venv\Scripts\activate in terminal

- enter "python pongServer.py"
     - should see "==================================================
                   Pong Game Server
                   ==================================================
                   Pong server started on 0.0.0.0:12345
                   Waiting for 2 players to connect..."


RUNNING THE CLIENT:

- open a NEW terminal window

- navigate to the pong folder of the project
     - path should be "(default user path)...\CS371_Project_Fall2025\pong>"

- activate the virtual environment
     - enter "venv\Scripts\activate"

- path should now show "(venv)...(default user path)...\CS371_Project_Fall2025\pong>"

- enter "python pongClient.py"

- a window pops up showing the join button, it also has two fields for "Server IP" and "Server Port"

- do not change either the "Server IP" or "Server Port" fields, and click join

- the game window screen should pop up showing "Waiting for opponent to connect"
     
- once opponent connects a countdown from 3, 2, 1 shows and the game starts

- use the up and down arrows to move your paddle


------------------------------------------------
PLAYER ON COMPUTER WITHOUT SERVER RUNNING:
------------------------------------------------

- open terminal

- make sure you are in the pong folder
     - path should be "(venv)...(default user path)...\CS371_Project_Fall2025\pong>"

- enter "python pongClient.py"
     - a window pops up showing the join button, it also has two fields for "Server IP" and "Server Port"
       * do not change server port number *

- get the IP address from the computer running the pongServer.py
     - do this by entering "ifconfig | grep "inet " | grep -v 127.0.0.1" on the computer with the running server          window
     - you will get something like "inet 192.168.1.243 netmask 0xffffff00 broadcast 192.168.1.255"
     - inet 192.168.1.243 <-- this is the correct IP address to enter into the "Server IP" field 

- enter the Server IP into the "Server IP" field and click join
     - the game window screen should pop up showing "Waiting for opponent to connect"

- once opponent connects, a countdown from 3, 2, 1 shows and the game starts

- use the up and down arrow keys to move your paddle


================================================= 
                IMPORTANT NOTES
=================================================

- both computers must be on the same wifi or vpn networks

- to play a new game after one has finished, you must restart the server and connect the clients again
     - to restart the server: * disconnect both client winows by closing the game windows on each computer,
                              * close the server by navigating to the server window and pressing "ctrl+c"
                              * in the same server window enter "python pongServer.py" to restart the server
                              * go into both client windows and enter "python pongClient.py" 
                              * simply click join on the client game window on the computer in which the server                                   is running on
                              * in the client window that is not running the server, you must enter in the IP                                     address of the computer that is running the Server again, once the correct IP is                                  entered into the "Server IP" field, click join
                         
