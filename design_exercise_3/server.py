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
import threading
import argparse
from config import CONFIG
REBOOT_TIME = 20

class LogActionType(Enum):
    """Action types to be used in log"""
    NEW_USER = 'new_user'
    DEL_USER = 'del_user'
    ENQUEUE_MSG = 'enqueue_msg'
    DEQUEUE_MSG = 'dequeue_msg'

log_action_type_to_grpc = {
    LogActionType.NEW_USER: chat_app_pb2.Log.NEW_USER,
    LogActionType.DEL_USER: chat_app_pb2.Log.DEL_USER,
    LogActionType.ENQUEUE_MSG: chat_app_pb2.Log.ENQUEUE_MSG,
    LogActionType.DEQUEUE_MSG: chat_app_pb2.Log.DEQUEUE_MSG
}
grpc_to_log_action_type = {value:key for key, value in log_action_type_to_grpc.items()}

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

def liveness_check_thread(instance):
    while True:
        for rep_server in instance.rep_servers_config: 
            if rep_server != instance.server_id: 
                stub = instance.replica_stubs[rep_server]
                try:
                    response = stub.CheckLiveness(chat_app_pb2.LivenessRequest(), timeout=0.5)
                    instance.replica_is_alive[rep_server] = True
                except grpc.RpcError as e:
                    instance.replica_is_alive[rep_server] = False
                    print(f"Liveness check failed between {instance.server_id} and {rep_server}: ")

                    if rep_server == instance.primary_server_id: 
                       instance.primary_server_id = min([rep for rep in instance.rep_servers_config if instance.replica_is_alive[rep]])
                       instance.is_primary = instance.primary_server_id == instance.server_id 
                       print(f"primary server changed to {instance.primary_server_id}")
        time.sleep(3)

class ChatAppServicer(chat_app_pb2_grpc.ChatAppServicer):
    """Interface exported by the server."""
    def __init__(self, 
                 server_id, 
                 primary_server_id, 
                 rep_servers_config,
                 reboot=False):
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
        self.rebooted = reboot

        self._initialize_replica_stubs()
        self._initialize_storage()

    
    def _initialize_replica_stubs(self):
        """ Initialize stubs to communicate with the other server replicas"""
        self.replica_stubs = {}
        self.channels = {} 
        self.replica_is_alive = {} 
        
        for rep_server in self.rep_servers_config:
            self.replica_is_alive[rep_server] = True
            if rep_server != self.server_id:
                channel = grpc.insecure_channel(f"{self.rep_servers_config[rep_server]['host']}:{self.rep_servers_config[rep_server]['port']}")
                self.channels[rep_server] = channel
                self.replica_stubs[rep_server] = chat_app_pb2_grpc.ChatAppStub(self.channels[rep_server])


    def _initialize_storage(self, dir=os.getcwd()):
        """
        Helper function to initialize disk storage files.
        Sets up all pending log files and db files.

        If the server is rebooting, it will reuse the existing 
        file instead of creating a new one.
        """
        print(f"Server {self.server_id}: Initializing storage" + (" with REBOOT" if self.rebooted else "")  )
        pend_log_filename = self.rep_servers_config[self.server_id]['pend_log_file']
        db_filename = self.rep_servers_config[self.server_id]['db_file']
        if not self.rebooted:
            # Delete previous pending log
            if pend_log_filename in os.listdir(dir):
                os.remove(pend_log_filename)

        # Create pickledb db instance, auto_dump is set to True, 
        # because we are manually handling the dumps to the database
        self.pend_log = pickledb.load(pend_log_filename, True)

        if not self.rebooted:
            self.pend_log.set('last_entry', 0)
            self.pend_log.set('current_ptr', 0)
            self.pend_log.set('log', [])

            # Delete previous database
            if db_filename in os.listdir(dir):
                os.remove(db_filename)

        # Create pickledb db instance, auto_dump is set to True, 
        # because we are manually handling the dumps to the database
        self.db = pickledb.load(db_filename, True)

        if not self.rebooted:
            # Add ROOT user to database
            self.db.set('root', [])

    def _get_pending_messages(self, username):
        """
        Extracts list of pending messages from db for a given user
        """
        return self.db.get(username)

    def _get_registered_users(self):
        """
        Extracts list of pending messages from db
        """
        return self.db.getall()

    def _execute_log(self):
        """
        Function to write actions from the pending log into the disk database
        This is the ONLY part of the code that directly writes to db files.

        Function executes all the entries that are pending in the log (keeps track using pointer)
        """
        # Function that loops through unexecuted lines in the log and adds them
        current_ptr = self.pend_log.get('current_ptr')
        last_entry = self.pend_log.get('last_entry')
        log = self.pend_log.get("log")
        
        for entry in log[current_ptr:]:

            params = entry['params']
            if entry['action_type'] == LogActionType.NEW_USER.value:
                self.db.set(params['username'], [])

            elif entry['action_type'] == LogActionType.DEL_USER.value:
                self.db.rem(params['username'])

            elif entry['action_type'] == LogActionType.DEQUEUE_MSG.value:
                self.db.set(params['username'], [])

            elif entry['action_type'] == LogActionType.ENQUEUE_MSG.value:
                destinataries = params['destinataries']
                for destinatary in destinataries:
                    if destinatary in self._get_registered_users():

                        # Add message to database
                        self.db.ladd(destinatary, {"sender": params["sender"],
                                                    "destinataries": params["destinataries"],
                                                            "text": params["text"],
                                                            "date": params["date"]})
            else:
                raise ValueError("Incorrect action type")
            
            # move pointer since you have executed the log command 
            self.pend_log.set('current_ptr', self.pend_log.get('current_ptr') + 1)



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
                print(f'Login success {request.username}')
                return chat_app_pb2.RequestReply(reply = 'OK', 
                request_status=chat_app_pb2.SUCCESS)
            else: 
                print(f'Login failure {request.username}')
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

                for rep_server in self.replica_stubs:
                    try: 
                        reply = self.replica_stubs[rep_server].NewUser_StateUpdate(request, timeout=0.5)
                    except grpc.RpcError as e:
                        self.replica_is_alive[rep_server] = False
                        print(f"\t\t Exception: {rep_server} not alive")
                    
                # Execute pending log entries
                self._execute_log()

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
            
            return_list = chat_app_pb2.UserList()
            return_list.users.extend(filtered_users)
            return_list.request_status = chat_app_pb2.SUCCESS
            return return_list
        
        else: 
            print(f"\t Rerouting ListAll to {self.primary_server_id}")
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
                # Add to log
                self.pend_log.ladd("log", {"action_type": LogActionType.DEL_USER.value, 
                                    "params": {"username": request.username}})

                last_entry = self.pend_log.get("last_entry")
                self.pend_log.set("last_entry", last_entry + 1)
                for rep_server in self.replica_stubs:
                    print(f"\tSending replication to server {rep_server}")
                    try: 
                        reply = self.replica_stubs[rep_server].DeleteUser_StateUpdate(request, timeout=0.5)
                    except grpc.RpcError as e: 
                        self.replica_is_alive[rep_server] = False
                        print(f"\t\t Exception: {rep_server} not alive")

                # Execute pending log entries
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
            self.pend_log.ladd("log", {"action_type": LogActionType.ENQUEUE_MSG.value, 
                                    "params": {"sender": request.sender.username, 
                                    "destinataries": [dest.username for dest in request.destinataries.users], 
                                    "text": request.text, 
                                    "date": request.date.ToDatetime().strftime("%d/%m/%Y, %H:%M")}})

            last_entry = self.pend_log.get("last_entry")
            self.pend_log.set("last_entry", last_entry + 1)

            # Send update to enqueue a message to replicas
            for rep_server in self.replica_stubs:
                print(f"\tSending replication to server {rep_server}")
                try: 
                    reply = self.replica_stubs[rep_server].EnqueueMessage_StateUpdate(request, timeout=0.5)
                except grpc.RpcError as e: 
                    self.replica_is_alive[rep_server] = False
                    print(f"\t\t Exception: {rep_server} not alive")
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

            # Send Status update to other replicas
            for rep_server in self.replica_stubs:
                print(f"\tSending replication to server {rep_server}")
                try:
                    reply = self.replica_stubs[rep_server].DequeueMessage_StateUpdate(request, timeout=0.5)
                except grpc.RpcError as e: 
                    self.replica_is_alive[rep_server] = False
                    print(f"\t\t Exception: {rep_server} not alive")

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
            return chat_app_pb2.ChatMessageList(messages=[], 
                request_status=chat_app_pb2.SUCCESS, rerouted=self.primary_server_id)
        
    def NewUser_StateUpdate(self, request, context):
        """"""
        print(f"Server {self.server_id}: NewUser_StateUpdate")

        if self.is_primary:
            raise NotImplementedError('Method not implemented!')
        else :
            self.pend_log.ladd("log", {"action_type": LogActionType.NEW_USER.value, 
                                    "params": {"username": request.username}})
            last_entry = self.pend_log.get("last_entry")
            self.pend_log.set("last_entry", last_entry + 1)
            
            # Execute pending log entries
            self._execute_log()
            return chat_app_pb2.RequestReply(reply='OK', request_status=chat_app_pb2.SUCCESS)

        

    def DeleteUser_StateUpdate(self, request, context):
        """"""
        print(f"Server {self.server_id}: DeleteUser_StateUpdate")

        if self.is_primary:
            # Error: This should not happen
            raise NotImplementedError('Method not implemented!')
        else :
            self.pend_log.ladd("log", {"action_type": LogActionType.DELETE_USER.value, 
                                    "params": {"username": request.username}})

            last_entry = self.pend_log.get("last_entry")
            self.pend_log.set("last_entry", last_entry + 1)
            self._execute_log()
            
            return chat_app_pb2.RequestReply(reply='OK', request_status = chat_app_pb2.SUCCESS)


    def EnqueueMessage_StateUpdate(self, request, context):
        """Request enqueue a message."""
        print(f"Server {self.server_id}: EnqueueMessage_StateUpdate")

        if self.is_primary:
            # Error: This should not happen
            raise NotImplementedError('Method not implemented!')
        else :
            self.pend_log.ladd("log", {"action_type": LogActionType.ENQUEUE_MSG.value, 
                                    "params": {"sender": request.sender.username, 
                                    "destinataries": [dest.username for dest in request.destinataries.users], 
                                    "text": request.text, 
                                    "date": request.date.ToDatetime().strftime("%d/%m/%Y, %H:%M")}})

            last_entry = self.pend_log.get("last_entry")
            self.pend_log.set("last_entry", last_entry + 1)
            self._execute_log()
            return chat_app_pb2.RequestReply(reply = 'OK', request_status = chat_app_pb2.SUCCESS)


    def DequeueMessage_StateUpdate(self, request, context):
        """Request to dequeue a message. """
        print(f"Server {self.server_id}: DequeueMessage_StateUpdate")

        if self.is_primary:
            # Error: This should not happen
            raise NotImplementedError('Method not implemented!')
        else :

            # Add info to log 
            self.pend_log.ladd("log", {"action_type": LogActionType.DEQUEUE_MSG.value, 
                                       "params": {"username": request.username}})

            last_entry = self.pend_log.get("last_entry")
            self.pend_log.set("last_entry", last_entry + 1)
            self._execute_log()
            return chat_app_pb2.RequestReply(reply = 'OK', request_status = chat_app_pb2.SUCCESS)
    
    def CheckLiveness(self, request, context):
        return chat_app_pb2.LivenessResponse(status='OK')
    
    def RebootPush(self, request, context):
        print(f"Server {self.server_id}: RebootPush")
        assert (request.last_entry >= self.pend_log.get('last_entry'))
        for log_entry in request.log_diff:
            if log_entry.action == chat_app_pb2.Log.ENQUEUE_MSG:
                self.pend_log.ladd("log", {"action_type": LogActionType.ENQUEUE_MSG.value, 
                                    "params": {"sender": log_entry.chat_message.sender.username, 
                                    "destinataries": [dest.username for dest in log_entry.chat_message.destinataries.users], 
                                    "text": log_entry.chat_message.text, 
                                    "date": log_entry.chat_message.date.ToDatetime().strftime("%d/%m/%Y, %H:%M")}})
            else:
                self.pend_log.ladd("log", {"action_type": grpc_to_log_action_type[log_entry.action].value, 
                                           "params": {"username": log_entry.user.username}})
            
            last_entry = self.pend_log.get("last_entry")
            self.pend_log.set("last_entry", last_entry + 1)

        assert (self.pend_log.get("last_entry") == request.last_entry), "Log was not updated to correct size"
        return chat_app_pb2.RequestReply(reply = 'OK', request_status = chat_app_pb2.SUCCESS)
    

    def RebootPull(self, request, context):
        print(f"Server {self.server_id}: RebootPull")
        last_entry = self.pend_log.get('last_entry')
        reboot_response = chat_app_pb2.RebootResponse(last_entry=last_entry)
        return reboot_response

        
def server(server_id, primary_server_id, config, reboot):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    chat_app_servicer = ChatAppServicer(server_id, primary_server_id, config, reboot)
    chat_app_pb2_grpc.add_ChatAppServicer_to_server(chat_app_servicer, server)
    
    host = config[server_id]['host']
    port = config[server_id]['port']
    server.add_insecure_port(f'{host}:{port}')
    server.start()

    # Start the liveness check thread with the existing gRPC channel and stub
    liveness_thread = threading.Thread(target=liveness_check_thread, args=(chat_app_servicer,))
    liveness_thread.start()

    # ---------------
    # Code to handle rebooting
    # ---------------
    if chat_app_servicer.rebooted:
        print(f"Waiting for {REBOOT_TIME} seconds before rebooting")
        time.sleep(REBOOT_TIME)
        print("Rebooting...\n")

        # Retrieve all log diffs from all replicas
        if chat_app_servicer.is_primary:
            last_entries = {}
            last_entries[server_id] = chat_app_servicer.pend_log.get('last_entry')
            max_entry = last_entries[server_id]
            max_rep_server = server_id
            max_log_diff = None
            for rep_server in chat_app_servicer.replica_stubs:
                print(f"\tGet log from {rep_server}")
                if chat_app_servicer.replica_is_alive[rep_server]:
                    reboot_request = chat_app_pb2.RebootRequest(last_entry=last_entries[server_id])
                    reply = chat_app_servicer.replica_stubs[rep_server].RebootPull(reboot_request)
                    last_entries[rep_server] = reply.last_entry

                    if reply.last_entry > max_entry:
                        max_entry = reply.last_entry
                        max_log_diff = reply.log_diff
                        max_rep_server = rep_server

            # Updating Primary server to have the latest logs
            if chat_app_servicer.server_id != max_rep_server: 
                # Update primary log
                for entry in max_log_diff:
                    print(entry)
            
            # Update all remaining replicas from the new version of the primary
            for rep_server in chat_app_servicer.replica_stubs:
                if (chat_app_servicer.replica_is_alive[rep_server] and
                    last_entries[rep_server] != chat_app_servicer.pend_log.get('last_entry') and
                    rep_server != max_rep_server):

                    # compute diff between updated primary and third placed
                    ptr_diff = last_entries[rep_server] - chat_app_servicer.pend_log.get('last_entry')
                    print(f"\tUpdate {rep_server} with diff of {ptr_diff}")
                    log_diff = chat_app_servicer.pend_log.get('log')[ptr_diff:]
                    assert len(log_diff) == -ptr_diff, f"Length mismatch log_diff {len(log_diff)} vs {-ptr_diff}"

                    grpc_log_list = []
                    for log_entry in chat_app_servicer.pend_log.get('log')[ptr_diff:]:
                        action = log_action_type_to_grpc[LogActionType(log_entry['action_type'])]

                        if LogActionType(log_entry['action_type']) == LogActionType.ENQUEUE_MSG:
                            gen_msg = dict_to_ChatMessage(log_entry['params'])
                            grpc_log = chat_app_pb2.Log(action=action, chat_message=gen_msg)
                        else:
                            grpc_user = chat_app_pb2.User(username=log_entry['params']['username'])
                            grpc_log = chat_app_pb2.Log(action=action, user=grpc_user)
                        
                        grpc_log_list.append(grpc_log)
                    
                    grpc_reboot_resp = chat_app_pb2.RebootResponse(last_entry=max_entry,
                                                                   log_diff=grpc_log_list)

                    reply = chat_app_servicer.replica_stubs[rep_server].RebootPush(grpc_reboot_resp)
                    
    server.wait_for_termination()


if __name__ == '__main__':
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--server", "-s", help="Server id to boot", type=int, choices=[0, 1, 2, 3], default=0)
    parser.add_argument("-p", "--primary", help="Id of primary server", choices=CONFIG.keys(), default="rep_server1")
    parser.add_argument("-r", "--reboot", help="Flag to reboot", action='count', default=0)
    args = parser.parse_args()
    
    if args.server == 0: 
        print(f"Running all servers with primary of {args.primary}")
        processes = []
        for rep_server in CONFIG:
            p = Process(target=server, args=(rep_server, args.primary, CONFIG, bool(args.reboot)))
            processes.append(p)
        for process in processes:
            process.start()
        time.sleep(200)
        for process in processes:
            process.kill()
    else: 
        server_id = "rep_server" + str(args.server)
        print(f"Running server {server_id} with primary of {args.primary}")
        server(server_id, args.primary, CONFIG, bool(args.reboot))





