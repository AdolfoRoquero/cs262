"""Chat App - GRPC ChatAppServicer Class

This script defines the GRPC ChatAppServicer class that implements the Wire Protocol (as defined in `chat_app.proto`)

This file can be imported as a module and can ALSO be run to spawn a running server.
"""

from concurrent import futures
from multiprocessing import Process
import grpc
import chat_app_pb2
import chat_app_pb2_grpc
from collections import defaultdict
import fnmatch 
import os
import pickledb
import time
from google.protobuf.timestamp_pb2 import Timestamp
from datetime import datetime
from enum import Enum
import sys

class LogActionType(Enum):
    """Action types to be used in log"""
    NEW_USER = 'new_user'
    DELETE_USER = 'del_user'
    ENQUEUE_MSG = 'enqueue_msg'
    DEQUEUE_MSG = 'dequeue_msg'

def dict_to_ChatMessage(message_dict):
    """Function converting from the dictionary 
       format of a message (Used in our key value store)
       to a ChatMessage object 
       
       Messages are stored as:
       {"sender": str, 
        "text": str,
        "destinataries": list of str
        "date": request.date.ToDatetime().strftime("%d/%m/%Y, %H:%M")}
       """
    msg_datetime = Timestamp()
    msg_datetime.FromDatetime(datetime.strptime(message_dict['date'], "%d/%m/%Y, %H:%M"))

    destinataries = chat_app_pb2.UserList(users=[chat_app_pb2.User(username=username) 
                                                 for username in message_dict['destinataries']])
    chat_message = chat_app_pb2.ChatMessage(sender=chat_app_pb2.User(username=message_dict['sender']),
                                            destinataries=destinataries,
                                            text=message_dict['text'],
                                            date=msg_datetime)
    return chat_message

class ChatAppServicer(chat_app_pb2_grpc.ChatAppServicer):
    """Interface exported by the server."""
    def __init__(self, 
                 server_id, 
                 primary_server_id, 
                 rep_servers_config):
        """
        Parameters
        ----------
        id : str
          id of replicated server
        primary_server_id : str
          id of the replicated server that is running as PRIMARY
        rep_servers_config : dict
          dictionary of the configuration of all the severs
        """
        assert server_id in rep_servers_config.keys(), f"{server_id} is not a valid id for a replicated server"
        self.server_id = server_id

        assert primary_server_id in rep_servers_config.keys(), f"{primary_server_id} is not a valid id for a replicated server"
        self.primary_server_id = primary_server_id

        # Boolean indicator of whether this instance is running as the primary
        self.is_primary = primary_server_id == server_id

        
        self.host = rep_servers_config[server_id]['host']
        self.port = rep_servers_config[server_id]['port']
        self.rep_servers_config = rep_servers_config
        self._initialize_storage()
        self._initialize_replica_stubs()
    
    def _initialize_replica_stubs(self):
        """ Initialize a stub to communicate with the other server replicas"""
        self.replica_stubs = {}
        for rep_server in self.rep_servers_config:
            if rep_server != self.server_id:
                channel = grpc.insecure_channel(f"{self.rep_servers_config[rep_server]['host']}:{self.rep_servers_config[rep_server]['port']}")
                self.replica_stubs[rep_server] = chat_app_pb2_grpc.ChatAppStub(channel)

    def _initialize_storage(self, dir=os.getcwd()):
        print(f"Server {self.server_id}: Initializing storage")

        # Delete previous pending log
        pend_log_filename = self.rep_servers_config[self.server_id]['pend_log_file']
        if pend_log_filename in os.listdir(dir):
            os.remove(pend_log_filename)

        # Create pickledb db instance, auto_dump is set to True, 
        # because we are manually handling the dumps to the database
        self.pend_log = pickledb.load(pend_log_filename, True)

        self.pend_log.set('last_entry', 0)
        self.pend_log.set('current_ptr', 0)
        self.pend_log.set('log', [])

        # Delete previous database
        db_filename = self.rep_servers_config[self.server_id]['db_file']
        if db_filename in os.listdir(dir):
            os.remove(db_filename)


        # Create pickledb db instance, auto_dump is set to True, 
        # because we are manually handling the dumps to the database
        self.db = pickledb.load(db_filename, True)

        # Add ROOT user to database
        self.db.set('root', [])


    def _get_pending_messages(self, username):
        """extracts list of pending messages from db for a given user"""
        return self.db.get(username)

    def _get_registered_users(self):
        """extracts list of pending messages from db"""
        return self.db.getall()

    def _execute_log(self):
        # TODO: Write function that executes the things that are pending in the log
        # Function that loops through unexecuted lines in the log and adds them
        current_ptr = self.pend_log.get('current_ptr')
        last_entry = self.pend_log.get('last_entry')
        log = self.pend_log.get("log")
        
        for entry in log[current_ptr:]:
            params = entry['params']
            if entry['action_type'] == LogActionType.NEW_USER.value:
                self.db.set(params['username'], [])

            elif entry['action_type'] == LogActionType.DELETE_USER.value:
                self.db.rem(params['username'])

            elif entry['action_type'] == LogActionType.DEQUEUE_MSG.value:
                self.db.set(params['username'], [])

            elif entry['action_type'] == LogActionType.ENQUEUE_MSG.value:
                destinataries = params['destinataries']
                for destinatary in destinataries:
                    if destinatary in self._get_registered_users():

                        # Add message to database
                        self.db.ladd(destinatary, {"sender": params["sender_username"],
                                                    "destinataries": params["destinataries"],
                                                            "text": params["text"],
                                                            "date": params["date"]})
            else:
                raise ValueError("Incorrect action type")
            
            # move pointer since you have executed the log command 
            self.pend_log.set('current_ptr', current_ptr + 1)

    def CheckLiveness(self, request, context):
        pass

    def Login(self, request, context):
        """
        Logs in user into the platform if the username already exists.

        Parameters
        ----------
        request : User (chat_app.proto)
            User to log in. 

        Returns
        -------
        RequestReply :
            Indicates Success or Failure of the login attempt.
        """
        print(f"Server {self.server_id}: Login")

        if self.is_primary:
            if request.username in self._get_registered_users(): 
                print(f'user login success {request.username}')
                return chat_app_pb2.RequestReply(reply = 'OK', 
                request_status=chat_app_pb2.SUCCESS)
            else: 
                print(f'user login failure {request.username}')
                return chat_app_pb2.RequestReply(reply = 'Failure, username not registered',
                                                 request_status=chat_app_pb2.FAILED)
        else: 
            print(f"\t Rerouting Login to {self.primary_server_id}")
            return chat_app_pb2.RequestReply(reply='OK', request_status=chat_app_pb2.REROUTED,
                                             rerouted=self.primary_server_id)

    def SignUp(self, request, context):
        """
        Sign up new user into the platform (only if the username is not taken).

        Parameters
        ----------
        request : User (chat_app.proto)
            User to sign up. 

        Returns
        -------
        RequestReply :
            Indicates Success or Failure of the signup attempt.
        """
        print(f"Server {self.server_id}: SignUp")
        if self.is_primary:
            if request.username not in self._get_registered_users(): 
                
                # Add to log
                self.pend_log.ladd("log", {"action_type": LogActionType.NEW_USER.value, 
                                    "params": {"username": request.username}})
                last_entry = self.pend_log.get("last_entry")
                self.pend_log.set("last_entry", last_entry + 1)

                # TODO add persistence
                for rep_server in self.replica_stubs:
                    print(f"\tSending replication to server {rep_server}")
                    reply = self.replica_stubs[rep_server].NewUser_StateUpdate(request)
                    # time.sleep(1)
                    # print(reply)
                    # if not reply: 
                    #     print("Liveness check failed: ", e)
                    
                # Add new user to database
                self._execute_log()

                #self.registered_users.users.append(request)
                print(f'user signup success {request.username}')
                return chat_app_pb2.RequestReply(reply = 'Success', 
                                                 request_status=chat_app_pb2.SUCCESS)
            else: 
                print(f'user signup failed {request.username}')
                return chat_app_pb2.RequestReply(reply='Failure, username taken', 
                                                 request_status=chat_app_pb2.FAILED)
        else: 
            print(f"\t Rerouting SignUp to {self.primary_server_id}")
            return chat_app_pb2.RequestReply(reply='OK', request_status=chat_app_pb2.REROUTED,
                                             rerouted=self.primary_server_id)

    def ListAll(self, request, context):
        """
        Sign up new user into the platform (only if the username is not taken).

        Parameters
        ----------
        request : ListAllRequest (chat_app.proto)
            Username Filter based on which to filter users.

        Returns
        -------
        UserList :
            List of all users that match the filter.
        """
        print(f"Server {self.server_id}: ListAll")

        if self.is_primary:
            if request.username_filter:
                filtered_users = [chat_app_pb2.User(username = user) for user in self._get_registered_users() 
                                        if fnmatch.fnmatch(user, request.username_filter) 
                                        and (user != 'root')]
            else:
                filtered_users = [chat_app_pb2.User(username = user) for user in self._get_registered_users() if (user != 'root')]
            
            print("BEFORE RETURN LIST")
            return_list = chat_app_pb2.UserList()
            return_list.users.extend(filtered_users)
            return_list.request_status = chat_app_pb2.SUCCESS
            print("RETURN userlist", return_list)
            return return_list
        
        else: 
            print(f"\t Rerouting ListAll to {self.primary_server_id}")
            # TODO: Response must be of type ListAll NOT RequestReply
            return chat_app_pb2.UserList(users=[], 
                                         request_status = chat_app_pb2.REROUTED,
                                         rerouted=self.primary_server_id)

    def DeleteUser(self, request, context):
        """
        Delete user from the chat app.

        Parameters
        ----------
        request : User (chat_app.proto)
            Username to be removed.

        Returns
        -------
        RequestReply :
            Indicates Success or Failure of the deletion.
        """
        print(f"Server {self.server_id}: DeleteUser")

        if self.is_primary:
            if request.username in self._get_registered_users():

                # TODO : Add to log
                self.pend_log.ladd("log", {"action_type": LogActionType.DELETE_USER.value, 
                                    "params": {"username": request.username}})

                last_entry = self.pend_log.get("last_entry")
                self.pend_log.set("last_entry", last_entry + 1)

                for rep_server in self.replica_stubs:
                    print(f"\tSending replication to server {rep_server}")
                    reply = self.replica_stubs[rep_server].DeleteUser_StateUpdate(request)

                # Remove user from database (TODO: R)
                self._execute_log()

                return chat_app_pb2.RequestReply(reply='OK', 
                request_status=chat_app_pb2.SUCCESS) 
            else: 
                # Error trying to delete a user that doesn't exist
                return chat_app_pb2.RequestReply(reply='OK', 
                request_status=chat_app_pb2.FAILED)
        else: 
            print(f"\t Rerouting DeleteUser to {self.primary_server_id}")
            return chat_app_pb2.RequestReply(reply='OK', request_status=chat_app_pb2.REROUTED,
                                             rerouted=self.primary_server_id)

    def SendMessage(self, request, context):
        """
        Queues message to be received by the specified destinatary. 

        Parameters
        ----------
        request : ChatMessage (chat_app.proto)
            Message to be sent (ChatMessage contains all data).

        Returns
        -------
        RequestReply :
            Indicates Success or Failure.
        """
        print(f"Server {self.server_id}: SendMessage")

        if self.is_primary:

            # TODO: add to log 
            self.pend_log.ladd("log", {"action_type": LogActionType.ENQUEUE_MSG.value, 
                                    "params": {"sender_username": request.sender.username, 
                                    "destinataries": [dest.username for dest in request.destinataries.users], 
                                    "text": request.text, 
                                    "date": request.date.ToDatetime().strftime("%d/%m/%Y, %H:%M")}})

            last_entry = self.pend_log.get("last_entry")
            self.pend_log.set("last_entry", last_entry + 1)

            # Send update to enqueue a message to replicas
            for rep_server in self.replica_stubs:
                print(f"\tSending replication to server {rep_server}")
                reply = self.replica_stubs[rep_server].EnqueueMessage_StateUpdate(request)
           
            self._execute_log()   
            
            return chat_app_pb2.RequestReply(reply='OK', request_status=chat_app_pb2.SUCCESS)
        
        else:
            print(f"\t Rerouting SendMessage to {self.primary_server_id}")
            return chat_app_pb2.RequestReply(reply='OK', request_status=chat_app_pb2.REROUTED,
                                             rerouted=self.primary_server_id)


         
    def ReceiveMessage(self, request, context):
        """
        Retrieves all messages for a given user. 

        Parameters
        ----------
        request : User (chat_app.proto)
            User for which to fetch all of the messages.

        Returns
        -------
        ChatMessage stream:
            Stream of all of the pending messages for the given user.
        """
        print(f"Server {self.server_id}: ReceiveMessage")
        if self.is_primary:

            # Add to pending log here
            self.pend_log.ladd("log", {"action_type": LogActionType.DEQUEUE_MSG.value, 
                                    "params": {"username": request.username}})

            last_entry = self.pend_log.get("last_entry")
            self.pend_log.set("last_entry", last_entry + 1)


            # TODO: handle replication
            for rep_server in self.replica_stubs:
                print(f"\tSending replication to server {rep_server}")
                reply = self.replica_stubs[rep_server].DequeueMessage_StateUpdate(request)

            # Execute actions from log here
            # Empty list of pending messages
            message_list = [] 
            for message in self._get_pending_messages(request.username): 
                message_list.append(dict_to_ChatMessage(message))
                
            self._execute_log()
            return chat_app_pb2.ChatMessageList(messages=message_list, 
                request_status=chat_app_pb2.SUCCESS)
        else: 
            print(f"\t Rerouting ReceiveMessage to {self.primary_server_id}")
            # TODO: Response must be of type ChatMessage NOT RequestReply
            return chat_app_pb2.ChatMessageList(messages=[], 
                request_status=chat_app_pb2.SUCCESS, rerouted=self.primary_server_id)
        
    def NewUser_StateUpdate(self, request, context):
        """

        """
        print(f"Server {self.server_id}: NewUser_StateUpdate")

        if self.is_primary:
            # TODO Error: This should not happen
            raise NotImplementedError('Method not implemented!')
        else :

            # TODO add info to log and respond
            self.pend_log.ladd("log", {"action_type": LogActionType.NEW_USER.value, 
                                    "params": {"username": request.username}})
            last_entry = self.pend_log.get("last_entry")
            self.pend_log.set("last_entry", last_entry + 1)

            self._execute_log()

            return chat_app_pb2.RequestReply(reply='OK', request_status=chat_app_pb2.SUCCESS)

        

    def DeleteUser_StateUpdate(self, request, context):
        """Missing associated documentation comment in .proto file."""
        print(f"Server {self.server_id}: DeleteUser_StateUpdate")

        if self.is_primary:
            # TODO Error: This should not happen
            raise NotImplementedError('Method not implemented!')
        else :
            self.pend_log.ladd("log", {"action_type": LogActionType.DELETE_USER.value, 
                                    "params": {"username": request.username}})

            last_entry = self.pend_log.get("last_entry")
            self.pend_log.set("last_entry", last_entry + 1)
            self._execute_log()
            
            return chat_app_pb2.RequestReply(reply='OK', request_status = chat_app_pb2.SUCCESS)


    def EnqueueMessage_StateUpdate(self, request, context):
        """Request enqueue a message.
        """
        print(f"Server {self.server_id}: EnqueueMessage_StateUpdate")

        if self.is_primary:
            # TODO Error: This should not happen
            raise NotImplementedError('Method not implemented!')
        else :
            self.pend_log.ladd("log", {"action_type": LogActionType.ENQUEUE_MSG.value, 
                                    "params": {"sender_username": request.sender.username, 
                                    "destinataries": [dest.username for dest in request.destinataries.users], 
                                    "text": request.text, 
                                    "date": request.date.ToDatetime().strftime("%d/%m/%Y, %H:%M")}})

            last_entry = self.pend_log.get("last_entry")
            self.pend_log.set("last_entry", last_entry + 1)
            self._execute_log()
            return chat_app_pb2.RequestReply(reply = 'OK', request_status = chat_app_pb2.SUCCESS)


    def DequeueMessage_StateUpdate(self, request, context):
        """Request to dequeue a message.
        """
        print(f"Server {self.server_id}: DequeueMessage_StateUpdate")

        if self.is_primary:
            # TODO Error: This should not happen
            raise NotImplementedError('Method not implemented!')
        else :

            # TODO add info to log and respond
            self.pend_log.ladd("log", {"action_type": LogActionType.DEQUEUE_MSG.value, 
                                    "params": {"username": request.username}})

            last_entry = self.pend_log.get("last_entry")
            self.pend_log.set("last_entry", last_entry + 1)
            self._execute_log()
            return chat_app_pb2.RequestReply(reply = 'OK', request_status = chat_app_pb2.SUCCESS)


def server(server_id, primary_server_id, config):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))

    chat_app_pb2_grpc.add_ChatAppServicer_to_server(
        ChatAppServicer(server_id, primary_server_id, config), server)
    
    host = config[server_id]['host']
    port = config[server_id]['port']
    server.add_insecure_port(f'{host}:{port}')
    server.start()
    server.wait_for_termination()


if __name__ == '__main__':
    if len(sys.argv) != 2: 
        print("Usage: python server.py <arg>")
        sys.exit(1)
    arg = sys.argv[1] 
    config = {
            "rep_server1" : {
                "host": os.environ["REP_SERVER_HOST_1"],
                "port": os.environ["REP_SERVER_PORT_1"],
                "pend_log_file": os.environ["REP_SERVER_PEND_1"],
                "db_file": os.environ["REP_SERVER_DB_FILE_1"],
            },
            "rep_server2" : {
                "host": os.environ["REP_SERVER_HOST_2"],
                "port": os.environ["REP_SERVER_PORT_2"],
                "pend_log_file": os.environ["REP_SERVER_PEND_2"],
                "db_file": os.environ["REP_SERVER_DB_FILE_2"],
            },
            "rep_server3" : {
                "host": os.environ["REP_SERVER_HOST_3"],
                "port": os.environ["REP_SERVER_PORT_3"],
                "pend_log_file": os.environ["REP_SERVER_PEND_3"],
                "db_file": os.environ["REP_SERVER_DB_FILE_3"],
            }
        }

    if arg == '0': 

        primary_server_id = 'rep_server1'

        processes = []
        for rep_server in config:
            p = Process(target=server, args=(rep_server, primary_server_id, config))
            processes.append(p)
        
        for process in processes:
            process.start()
        
        time.sleep(200)

        for process in processes:
            process.kill()

    else: 
        server_id = "rep_server" + arg
        server(server_id, "rep_server1", config)
        # chat_app_pb2_grpc.add_ChatAppServicer_to_server(ChatAppServicer(), server)
        # HOST = os.environ['CHAT_APP_SERVER_HOST']
        # PORT = os.environ['CHAT_APP_SERVER_PORT']
        # server.add_insecure_port(f'{HOST}:{PORT}')
        # server.start()
        # server.wait_for_termination() 





