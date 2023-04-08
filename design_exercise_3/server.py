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
        for rep_server in self.rep_servers_config:
            if rep_server != self.server_id:
                channel = grpc.insecure_channel(f"{self.rep_servers_config[rep_server]['host']}:{self.rep_servers_config[rep_server]['port']}")
                self.rep_servers_config[rep_server]['stub'] = chat_app_pb2_grpc.ChatAppStub(channel)




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
        self.db.set('root', [])

        # print(self._get_registered_users())
        # print(self._get_pending_messages())
        # self.db.ladd('root', {"dest": "javi", 
        #          "content":"hello javi third"})
        # print(self._get_pending_messages())


    def _get_pending_messages(self, username):
        """extracts list of pending messages from db"""
        # TODO: 
        return self.db.get(username)

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
        print(f"Server {self.server_id}: Login")

        if self.is_primary:
            if request.username in self._get_registered_users(): 
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
        print(f"Server {self.server_id}: SignUp")
        if self.is_primary:
            if request.username not in self._get_registered_users(): 
                
                # TODO add persistence
                # for rep_server in self.rep_servers_config:
                #     reply = self.rep_servers_config[rep_server]['stub'].NewUser_StateUpdate(request)

                # Add new user to database
                self.db.set(request.username, [])

                #self.registered_users.users.append(request)
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
            return return_list
        
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
        print(f"Server {self.server_id}: DeleteUser")

        if self.is_primary:
            if request.username in self._get_registered_users():
                
                # TODO: handle persistence
                self.db.rem(request.username)
                return chat_app_pb2.RequestReply(request_status = 0) 
            else: 
                # Error trying to delete a user that doesn't exist
                return chat_app_pb2.RequestReply(request_status = 1)
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
        print(f"Server {self.server_id}: SendMessage")

        if self.is_primary:
            destinataries = request.destinataries.users
            request.ClearField('destinataries')
            for destinatary in destinataries:
                if destinatary.username in self._get_registered_users():
                    self.db.ladd(destinatary.username, request)
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
        print(f"Server {self.server_id}: ReceiveMessage")
        if self.is_primary:

            for message in self._get_pending_messages(request.username): 
                yield message
            
            # TODO: handle replication
            self.db.set(request.username, [])
        
        else: 
            # TODO Reroute request to primary
            pass
        
    def NewUser_StateUpdate(self, request, context):
        """

        """
        print(f"Server {self.server_id}: NewUser_StateUpdate")

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

    processes = []
    for rep_server in config:
        p = Process(target=server, args=(rep_server, primary_server_id, config))
        processes.append(p)
    
    for process in processes:
        process.start()
    
    time.sleep(40)

    for process in processes:
        process.kill()





