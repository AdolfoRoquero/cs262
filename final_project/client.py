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
        else: 
            while True: 
                username = input("Enter username: ").strip().lower()
                if username in instance._get_players(): 
                    print("Error: username taken")
                else: 
                    instance.add_new_player(username, instance.ip)
                    break 
        