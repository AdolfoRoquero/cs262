# Engineering Notebook - Chat App 

## Planning 

v0 - working solution in Python meeting all of the specs, console as the UI. 
v1 - re-implementing v0 using gRPC and protocol buffers 
v2 - layering UI with Flask on top of v0 and/or v1 

## Design Decisions 

### Wire protocol 
	TODO 
### Functionality/Usability  
	- Login or Signup: 
		- One user can login from different clients, and therefore hold multiple different client connections. This represents a user logging in from different devices, for instance. Under this scenario, any message directed to this user (by username), is sent to all of the logged in devices. 
		- When a login or signup fail, the socket is disconnected and the connection is closed. In v0, to attempt another login or signup, the user must re-run client.py which prompts the creation of a new socket. 

	- Delete: 
		- A user must be logged in in order to perform a delete user call. Furthermore, a user can only delete themselves. 
		- Once a user successfully deletes themselves, the connection is closed. 
		- All the pending messages sent by that user also gets deleted (i.e. if user x sends a message to user y which cannot be delivered immediately as user y is not logged in, and user x deletes their account before user y logs in, then these messages will be deleted and will not be received by user y upon their login). 

	- Sending messages: 
		- Invalid usernames can be passed as destinataries to a message, and the server will simply ignore those invalid usernames. These messages are not stored by the server, which implies that if user x requests a message to be sent to a user with username y which is not a registered user according to the server, then even if in the future a user signups with username y, they will not receive the message sent by user x. 

	- Receiving messages: 
		- When a user logs in, they receive all of the messages that were sent to them since their last active session, including from users who have since deleted their accounts. 

### Technical details 
 	- Classes for the server and the client 
		- To facilitate unit testing [...] - TODO 
	- Non-blocking IO instead of threads - TODO 
	- Abstracting common functions, wire protocol and configuration 
		- Files shared by both client and server: utils.py, protocol.py, ... TODO 
## Problems Encountered/Debugging steps 
	TODO 
## Limitations and other considerations 

	TODO 