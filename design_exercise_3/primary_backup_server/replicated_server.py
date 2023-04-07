"""Chat App - GRPC ChatAppServicer Class

This script defines the GRPC ChatAppServicer class that implements the Wire Protocol (as defined in `chat_app.proto`)

This file can be imported as a module and can ALSO be run to spawn a running server.
"""

from concurrent import futures
import grpc
import primary_backup_server_pb2
import primary_backup_server_pb2_grpc
from collections import defaultdict
import fnmatch 
import os
import pickledb
CHAT_APP_CONFIG = {

}


REP_SERVER_CONFIG = {
    "rep_server1" : {
        "host": os.environ["REP_SERVER_HOST_1"],
        "port": os.environ["REP_SERVER_PORT_1"],
        "pend_log_file": os.environ["REP_SERVER_LOG_FILE_1"],
        "db_file": os.environ["REP_SERVER_DB_FILE_1"],
    },
    "rep_server2" : {
        "host": os.environ["REP_SERVER_HOST_2"],
        "port": os.environ["REP_SERVER_PORT_2"],
        "pend_log_file": os.environ["REP_SERVER_LOG_FILE_2"],
        "db_file": os.environ["REP_SERVER_DB_FILE_2"],
    },
    "rep_server3" : {
        "host": os.environ["REP_SERVER_HOST_3"],
        "port": os.environ["REP_SERVER_PORT_3"],
        "pend_log_file": os.environ["REP_SERVER_LOG_FILE_2"],
        "db_file": os.environ["REP_SERVER_DB_FILE_2"],
    }
}

class ReplicatedServer(primary_backup_server_pb2_grpc.PrimaryBackupServerServicer):
    """Interface exported by the server."""
    def __init__(self, 
                 server_id, 
                 primary_server_id, 
                 rep_servers_config = REP_SERVER_CONFIG):
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

        # Delete previous pending log
        pend_log_filename = self.rep_servers_config[self.server_id]['pend_log_file']
        if pend_log_filename in os.listdir(dir):
            os.remove(pend_log_filename)

        # Create a new empty log file
        empty_file = open(pend_log_filename, "x")
        empty_file.close()

        # Delete previous commit log
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
        

        # Create 

        


        	


            





    def NewUser(self, request, context):
        """
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def DeleteUser(self, request, context):
        """
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def EnqueueMessage(self, request, context):
        """Request enqueue a message.
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def DequeueMessage(self, request, context):
        """Request to dequeue a message.
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!') 
        
        


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    chat_app_pb2_grpc.add_ChatAppServicer_to_server(ChatAppServicer(), server)
    HOST = os.environ['CHAT_APP_SERVER_HOST']
    PORT = os.environ['CHAT_APP_SERVER_PORT']
    server.add_insecure_port(f'{HOST}:{PORT}')
    server.start()
    server.wait_for_termination()

if __name__ == '__main__':
    serve()

