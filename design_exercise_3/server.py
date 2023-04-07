"""Chat App - GRPC ChatAppServicer Class

This script defines the GRPC ChatAppServicer class that implements the Wire Protocol (as defined in `chat_app.proto`)

This file can be imported as a module and can ALSO be run to spawn a running server.
"""

from concurrent import futures
import grpc
import chat_app_pb2
import chat_app_pb2_grpc
from collections import defaultdict
import fnmatch 
import os
import pickledb
import pickle

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

    def _initialize_storage(self, dir=os.getcwd()):
        print(f"Server {self.server_id}: Initializing storage")

        # Delete previous pending log
        pend_log_filename = self.rep_servers_config[self.server_id]['pend_log_file']
        if pend_log_filename in os.listdir(dir):
            os.remove(pend_log_filename)

        # Create a new empty log file
        empty_file = open(pend_log_filename, "x")
        empty_file.close()


        # Delete previous database
        db_filename = self.rep_servers_config[self.server_id]['db_file']
        if db_filename in os.listdir(dir):
            os.remove(db_filename)

        # Create a new empty db file
        # empty_file = open(db_filename, "x")
        # empty_file.close()

        
        # Create pickledb db instance, auto_dump is set to True, 
        # because we are manually handling the dumps to the database
        self.db = pickledb.load(db_filename, True)

        # Add ROOT user to database
        self.db.set('root', [
                {"dest": "javi", 
                 "content":"hello javi"},
                {"dest": "javi", 
                 "content":"hello javi twice"}
            ])

        print(self._get_registered_users())
        print(self._get_pending_messages())
        self.db.ladd('root', {"dest": "javi", 
                 "content":"hello javi third"})
        print(self._get_pending_messages())


    def _get_pending_messages(self, ):
        """extracts list of pending messages from db"""
        # TODO: 
        return self.db.get('root')

    def _get_registered_users(self):
        """extracts list of pending messages from db"""
        return self.db.getall()

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
        if self.is_primary:
            if request in self.registered_users.users: 
                print(f'user login success {request.username}')
                return chat_app_pb2.RequestReply(reply = 'Success', request_status = 1)
            else: 
                print(f'user login failure {request.username}')
                return chat_app_pb2.RequestReply(reply = 'Failure, username not registered',
                request_status = 0)
        else: 
            # TODO Reroute request to primary
            pass

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
        if self.is_primary:
            if request not in self.registered_users.users: 
                self.registered_users.users.append(request)
                print(f'user signup success {request.username}')
                return chat_app_pb2.RequestReply(reply = 'Success', request_status = 1)
            else: 
                print(f'user signup failed {request.username}')
                return chat_app_pb2.RequestReply(reply = 'Failure, username taken', request_status = 0)
        else: 
            # TODO Reroute request to primary
            pass

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
        if self.is_primary:
            filtered_users = chat_app_pb2.UserList()
            if request.username_filter:
                filtered_users.users.extend([user for user in self.registered_users.users 
                                        if fnmatch.fnmatch(user.username, request.username_filter) 
                                        and (user.username != 'root')])
            else:
                filtered_users.users.extend([user for user in self.registered_users.users if (user.username != 'root')])
                
            return filtered_users
        
        else: 
            # TODO Reroute request to primary
            pass

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
        if self.is_primary:

            updated_registered_users = chat_app_pb2.UserList()
            for user in self.registered_users.users:
                if user.username != request.username: 
                    updated_registered_users.users.append(user)
            if len(self.registered_users.users) - 1 == len(updated_registered_users.users): 
                self.registered_users = updated_registered_users
                return chat_app_pb2.RequestReply(request_status = 1)
            else: 
                return chat_app_pb2.RequestReply(request_status = 0)
        else: 
            # TODO Reroute request to primary
            pass

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
        if self.is_primary:
            destinataries = request.destinataries.users
            request.ClearField('destinataries')
            for destinatary in destinataries:
                if destinatary in self.registered_users.users: 
                    self.pending_messages[destinatary.username].append(request)
            return chat_app_pb2.RequestReply(request_status = 1)
        
        else:
            # TODO Reroute request to primary
            pass

         
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
        if self.is_primary:
            for message in self.pending_messages[request.username]: 
                yield message
            
            del self.pending_messages[request.username] 
        
        else: 
            # TODO Reroute request to primary
            pass
        
    def NewUser_StateUpdate(self, request, context):
        """

        """
        if self.is_primary:
            # TODO Error: This should not happen
            raise NotImplementedError('Method not implemented!')
        else :
            # TODO add info to log and respond
            raise NotImplementedError('Method not implemented!')

        

    def DeleteUser_StateUpdate(self, request, context):
        """Missing associated documentation comment in .proto file."""
        if self.is_primary:
            # TODO Error: This should not happen
            raise NotImplementedError('Method not implemented!')
        else :
            # TODO add info to log and respond
            raise NotImplementedError('Method not implemented!')


    def EnqueueMessage_StateUpdate(self, request, context):
        """Request enqueue a message.
        """
        if self.is_primary:
            # TODO Error: This should not happen
            raise NotImplementedError('Method not implemented!')
        else :
            # TODO add info to log and respond
            raise NotImplementedError('Method not implemented!')


    def DequeueMessage_StateUpdate(self, request, context):
        """Request to dequeue a message.
        """
        if self.is_primary:
            # TODO Error: This should not happen
            raise NotImplementedError('Method not implemented!')
        else :
            # TODO add info to log and respond
            raise NotImplementedError('Method not implemented!')


if __name__ == '__main__':
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
            "db_file": os.environ["REP_SERVER_DB_FILE_2"],
        }
    }
    primary_server_id = 'rep_server1'

    for server_id in config:
        server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))

        chat_app_pb2_grpc.add_ChatAppServicer_to_server(
            ChatAppServicer(server_id, primary_server_id, config), server)
        
        host = config[server_id]['host']
        port = config[server_id]['port']
        server.add_insecure_port(f'{host}:{port}')
        server.start()
        # TODO: Threading for each server
        server.wait_for_termination()



