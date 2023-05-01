from copyreg import pickle
from unicodedata import name
from urllib import request
import grpc 
import quiplash_pb2
import quiplash_pb2_grpc
from concurrent import futures
import pickledb 
import os 
import argparse
import socket
import threading
import time 

def client_handle(instance): 
        # JoinGame routine 
        if not instance.is_primary: 
            while True: 
                username = input("Enter username: ").strip().lower()
                user = quiplash_pb2.User(username=username, ip_address=instance.ip)
                reply = instance.stubs[instance.primary_ip].JoinGame(user)
                if reply.request_status == quiplash_pb2.FAILED:
                    print(reply.reply)
                else:
                    break
            print(f"Successfully joined game, username {username}")

            while not instance.game_started: 
                time.sleep(0.5)
                continue 
            while instance.game_started: 
                continue 
        else: 
            while True: 
                username = input("Enter username: ").strip().lower()
                if username in instance._get_players(): 
                    print("Error: username taken")
                else: 
                    instance.add_new_player(username, instance.ip)
                    break 
            print("\n Once all players have joined the room, press enter to start game \n")
            while True: 
                start_game = input("")
                if start_game == '': 
                    break 
            game_start_text = "Starting the game. Ready... Set.... QUIPLASH"
            print(f"\n {game_start_text} \n")

            # notifies other players game will begin 
            for ip, stub in instance.stubs.items(): 
                notification = quiplash_pb2.GameNotification(type=quiplash_pb2.GameNotification.GAME_START, text=game_start_text)
                reply = stub.NotifyPlayers(notification)

            # starts the game 
            instance.start_game()



        