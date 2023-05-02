from cgitb import text
from distutils.fancy_getopt import wrap_text
import tkinter as tk
from tkinter import font as tkfont
from tkinter import ttk
import grpc 
import quiplash_pb2
import quiplash_pb2_grpc
from node import QuiplashServicer
from concurrent import futures
import os 
import argparse
import socket
import threading
from tkinter import messagebox
import asyncio

from PIL import Image, ImageDraw, ImageFont, ImageTk

 
# LARGEFONT =("Verdana", 35, "bold")
MEDFONT =("Verdana", 16, "bold")


class tkinterApp(tk.Tk):
     
    # __init__ function for class tkinterApp
    def __init__(self, port, *args, **kwargs):         
        # __init__ function for class Tk
        tk.Tk.__init__(self, *args, **kwargs)

        # creating a container
        container = tk.Frame(self) 
        container.pack(side = "top", fill = "both", expand = True)
  
        container.grid_rowconfigure(0, weight = 1)
        container.grid_columnconfigure(0, weight = 1)
  
        IP = socket.gethostbyname(socket.gethostname())
        self.ip = IP 
        self.port = port 
        self.servicer = QuiplashServicer(IP, port)
        #self.serve_grpc(port)


        # initializing frames to an empty array
        self.frames = {} 
  
        # iterating through a tuple consisting
        # of the different page layouts
        for F in (LandingPage, JoinGamePage, WaitingPage, QuestionPage, VotingPage, LeaderboardPage):
  
            frame = F(container, self, self.servicer)
  
            # initializing frame of that object from
            # startpage, page1, page2 respectively with
            # for loop
            self.frames[F] = frame
  
            frame.grid(row = 0, column = 0, sticky ="nsew")
        self.show_frame(LandingPage)

  
    # to display the current frame passed as
    # parameter
    def show_frame(self, cont):
        frame = self.frames[cont]
        frame.update()
        frame.tkraise()
    
    async def serve_grpc(self):
        #IP = socket.gethostbyname(socket.gethostname())
        #PORT = port
        server = grpc.aio.server()
        #quiplash_servicer = QuiplashServicer(IP, PORT)
        quiplash_pb2_grpc.add_QuiplashServicer_to_server(self.servicer, server)
        # self.servicer = quiplash_servicer
        server.add_insecure_port(f'{self.ip}:{self.port}')

        await server.start() 
        await server.wait_for_termination() 

    async def mainloop(self):
        asyncio.create_task(self.serve_grpc())
        while True: 
            self.update() # replicating main loop functionality tkinter 
            await asyncio.sleep(0.01)         

class LandingPage(tk.Frame):
    def __init__(self, parent, controller, servicer):
        tk.Frame.__init__(self, parent)
        self.servicer = servicer
        self.controller = controller

        self.LARGEFONT = tkfont.Font(family="Verdana", size=50)
        self.MEDFONT = tkfont.Font(family="Verdana", size=16, weight='bold')

        # Load the image file
        image = Image.open("./StartPageWallpaper.jpeg")
        # Convert the image to a Tkinter-compatible format
        # image = image.resize((self.max_width, self.max_height), Image.ANTIALIAS)

        photo = ImageTk.PhotoImage(image)

        # Load the image file and resize it to match the maximum window size
        image = Image.open("./StartPageWallpaper.jpeg")
        photo = ImageTk.PhotoImage(image)
        # Create a label to display the image
        background_label = tk.Label(self, image=photo)
        background_label.image = photo # Keep a reference to the photo to prevent garbage collection
        # Set the label to fill the entire frame
        background_label.place(relx=0, rely=0, relwidth=1, relheight=1)
        background_label.lower()
    

        # label of frame Layout 2
        label = ttk.Label(self, text ="QuiP2Plash!", font = self.LARGEFONT)
        # putting the grid in its place
        label.place(relx=0.5, rely=0.2, anchor="center")

        start_new_game_button = tk.Button(self, text ="Start New Game", 
            borderwidth = 0,  # Add this line
            highlightthickness = 0, relief='flat', height=4, width=20, 
            font=self.MEDFONT, command = self.start_new_game)
        start_new_game_button.place(relx=0.5, rely=0.45, anchor="center")

        join_existing_button = tk.Button(self, text ="Join Game", 
            borderwidth = 0,  # Add this line
            highlightthickness = 0, relief='flat', height=4, width=20, 
            font=self.MEDFONT, command = self.join_game)
        join_existing_button.place(relx=0.5, rely=0.65, anchor="center")

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

    def start_new_game(self): 
        # set this server as the primary server for new game 
        self.servicer.setup_primary()
        self.controller.show_frame(JoinGamePage)

    def join_game(self):        
        self.controller.show_frame(JoinGamePage)
 

# first window frame startpage
class JoinGamePage(tk.Frame):
    def __init__(self, parent, controller, servicer):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        self.servicer = servicer

        self.LARGEFONT = tkfont.Font(family="Verdana", size=50)
        self.MEDFONT = tkfont.Font(family="Verdana", size=16, weight='bold')
        self.SMALLFONT = tkfont.Font(family="Verdana", size=14)

        # label of frame Layout 2
        label = ttk.Label(self, text ="QuiP2Plash!", font = self.LARGEFONT)
        # putting the grid in its place
        label.place(relx=0.5, rely=0.2, anchor="center")

        def show_message():
             messagebox.showinfo("Fail", "Username taken for this game. Enter new name.")

        # widgets for entering game code and username 
        def on_entry_click(event, entry):
            if entry.get() in ['Enter Code Game', 'Enter Username']:
                entry.delete(0, "end") # delete all the text in the entry widget
                entry.insert(0, '') #Insert blank for user input

        def check_fields():
            code = self.code_entry.get().strip()
            username = self.username_entry.get().strip()

            if self.servicer.is_primary and username and username != 'Enter Username': 
                self.servicer.username = username
                self.servicer.add_new_player(username, self.servicer.ip, self.servicer.port)
                self.controller.show_frame(WaitingPage) 
            else: 
                if code and username:
                    if code != 'Enter Code Game' and username != 'Enter Username': 
                        # TODO lOGIC HERE FOR CHECKING GAME CODE 
                        self.servicer.primary_ip, self.servicer.primary_port = code.split(":") 
                        self.servicer.primary_address = code 
                        self.servicer.create_stub(self.servicer.primary_ip, self.servicer.primary_port)

                        print(username, type(username))
                        print("servicer ip ", self.servicer.ip, type(self.servicer.ip))
                        print("servicer port ", self.servicer.port, type(self.servicer.port))
                        user = quiplash_pb2.User(username=username, 
                                         ip_address=self.servicer.ip, 
                                         port=self.servicer.port)
                        # send join game request 
                        stub = self.servicer.stubs[self.servicer.primary_address]
                        # qst_lst = quiplash_pb2.QuestionList(question_list=[quiplash_pb2.Question(question_id='1', question_text='2', topic='test')])
                        reply = stub.JoinGame(user)
                        print("status:", reply.request_status)

                        if reply.request_status == quiplash_pb2.SUCCESS:
                            
                            self.servicer.id = reply.num_players
                            self.servicer.num_players = reply.num_players 
                            self.servicer.username = username
                            print("num players: ", reply.num_players)

                        elif reply.request_status == quiplash_pb2.FAILED:
                            show_message()
                        else: 
                            print("ERROR")
                    else:
                        self.controller.show_frame(WaitingPage) 


        self.code_entry = ttk.Entry(self,width=15, font=self.SMALLFONT)
        self.code_entry.insert(0, "Enter Code Game")
        # Bind the function to the entry widget
        self.code_entry.bind('<FocusIn>', lambda event: on_entry_click(event, self.code_entry))
        self.code_entry.place(relx=0.5, rely=0.4, anchor="center")

        self.username_entry = ttk.Entry(self,width=15, font=self.SMALLFONT)
        self.username_entry.insert(0, "Enter Username")
        # Bind the function to the entry widget
        self.username_entry.bind('<FocusIn>', lambda event: on_entry_click(event, self.username_entry))
        self.username_entry.place(relx=0.5, rely=0.5, anchor="center")


        join_game_button = tk.Button(self, text ="Join Game", 
            borderwidth = 0,  # Add this line
            highlightthickness = 0, relief='flat', height=3, width=10, font=self.MEDFONT,
            command = check_fields)
     
        # putting the button in its place by using grid
        join_game_button.place(relx=0.5, rely=0.7, anchor="center")
  
        # Load the image file
        image = Image.open("./StartPageWallpaper.jpeg")
        photo = ImageTk.PhotoImage(image)

        # Load the image file and resize it to match the maximum window size
        image = Image.open("./StartPageWallpaper.jpeg")
        photo = ImageTk.PhotoImage(image)
        # Create a label to display the image
        background_label = tk.Label(self, image=photo)
        background_label.image = photo # Keep a reference to the photo to prevent garbage collection
        # Set the label to fill the entire frame
        background_label.place(relx=0, rely=0, relwidth=1, relheight=1)
        # background_label.grid(row=0, column=0, sticky='nsew')

        background_label.lower()
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
    
    def lift(self):
        self.update()
        tk.Frame.lift(self)

    def update(self): 
        if self.servicer.is_primary: 
            self.code_entry.delete(0, "end") # delete all the text in the entry widget
            self.code_entry.insert(0, self.servicer.primary_address)
            self.code_entry.config(state= "disabled")
        else: 
            self.code_entry.delete(0, "end") # delete all the text in the entry widget
            self.code_entry.insert(0, "Enter Code Game")
            self.code_entry.config(state= "enabled")
        

    
# second window frame page1
class WaitingPage(tk.Frame):
     
    def __init__(self, parent, controller, servicer):
         
        tk.Frame.__init__(self, parent)
        self.LARGEFONT = tkfont.Font(family="Verdana", size=35)
        self.MEDFONT = tkfont.Font(family="Verdana", size=16, weight='bold')
        self.SMALLFONT = tkfont.Font(family="Verdana", size=14)

        self.controller = controller 
        self.servicer = servicer

        welcome_label = ttk.Label(self, text ="Waiting for other players to join!", font = self.LARGEFONT)
        welcome_label.place(relx=0.5, rely=0.2, anchor="center")

        self.share_code_text = ttk.Label(self, text="", font = self.MEDFONT, wraplength=300, justify="center", anchor="n")
        self.share_code_text.place(relx=0.5, rely=0.3, anchor="center")


        # button to start game 
        start_game_button = tk.Button(self, text ="Start playing",
            borderwidth = 0,  # Add this line
            highlightthickness = 0, relief='flat', height=4, width=20, 
            font=self.MEDFONT, command = self.start_game)
                            
        # putting the button in its place
        # by using grid
        start_game_button.place(relx=0.5, rely=0.5, anchor="center")

        button_explanation= ttk.Label(self, text ="Press the button below to start game once everyone has joined the room.", 
            font = self.SMALLFONT, wraplength=350, justify="center", anchor="n")
        button_explanation.place(relx=0.5, rely=0.7, anchor="center")
    

    def start_game(self): 
        pass

    def update(self): 
        text =f"Share the code with your friends for them to join the game! {self.servicer.primary_address}"
        self.share_code_text.config(text=text)
  

class QuestionPage(tk.Frame):
    def __init__(self, parent, controller, servicer):
        tk.Frame.__init__(self, parent)

        # Create the canvas for the background image
        self.canvas = tk.Canvas(self, width=500, height=500)
        self.canvas.pack(fill="both", expand=True)

        # Load the background image
        image = Image.open("./StartPageWallpaper.jpeg")
        photo = ImageTk.PhotoImage(image)
        self.canvas.background = photo  # Keep a reference to the photo to prevent garbage collection
        self.canvas.create_image(0, 0, image=photo, anchor="nw")
        
        
        # Create the transparent rectangle
        self.canvas.create_rectangle(50, 50, 700, 450, fill="white", outline="")
                
        # Create the text labels and entry widgets
        label1 = tk.Label(self.canvas, text="Question 1: What is the worst thing your dog could say to you?", 
            bg="white", font=MEDFONT, wraplength=400, justify="center", anchor="n")
        label1.place(relx=0.5, rely=0.3, anchor="center")
        entry1 = tk.Entry(self.canvas)
        entry1.place(relx=0.5, rely=0.4, anchor="center")

        label2 = tk.Label(self.canvas, text="Question 2: What would be a much more interesting name for CS262?",
         bg="white", font=MEDFONT,  wraplength=400, justify="center", anchor="n")
        label2.place(relx=0.5, rely=0.5, anchor="center")
        entry2 = tk.Entry(self.canvas)
        entry2.place(relx=0.5, rely=0.6, anchor="center")

        button1 = tk.Button(self.canvas, text="Submit answers!", command=lambda: self.validate_fields(controller, entry1, entry2))
        button1.place(relx=0.5, rely=0.8, anchor="center")

        # Create the countdown label
        self.timer_label = tk.Label(self.canvas, text="00:00", font=MEDFONT, bg="white")
        self.timer_label.place(relx=0.5, rely=0.7, anchor="center")

        # Set the countdown duration in seconds
        self.countdown_duration = 60

        # Start the countdown
        self.start_countdown()

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

    def start_countdown(self):
            # Update the timer label every second
            if self.countdown_duration > 0:
                minutes = self.countdown_duration // 60
                seconds = self.countdown_duration % 60
                self.timer_label.configure(text="{:02d}:{:02d}".format(minutes, seconds))
                self.countdown_duration -= 1
                self.after(1000, self.start_countdown)
            else:
                # Do something when the countdown is over
                pass

    def validate_fields(self, controller, entry1, entry2):
        if entry1.get() and entry2.get():
            controller.show_frame(VotingPage)


class VotingPage(tk.Frame):
    def __init__(self, parent, controller, servicer):
        tk.Frame.__init__(self, parent)

        self.LARGEFONT = tkfont.Font(family="Verdana", size=35)
        self.SMALLFONT = tkfont.Font(family="Verdana", size=14)

        # Create the canvas for the background image
        self.canvas = tk.Canvas(self, width=500, height=500)
        self.canvas.pack(fill="both", expand=True)

        # Load the background image
        image = Image.open("./StartPageWallpaper.jpeg")
        photo = ImageTk.PhotoImage(image)
        self.canvas.background = photo  # Keep a reference to the photo to prevent garbage collection
        self.canvas.create_image(0, 0, image=photo, anchor="nw")
        
        
        # Create the transparent rectangle
        self.canvas.create_rectangle(50, 50, 700, 450, fill="white", outline="")
                
        # Create the text labels and entry widgets
        title_label = tk.Label(self.canvas, text="Time to vote!", 
            bg="white", font=self.LARGEFONT, wraplength=400, justify="center", anchor="n")
        title_label.place(relx=0.5, rely=0.2, anchor="center")

        question = tk.Label(self.canvas, text="What would be a much more interesting name for CS262?",
         bg="white", font=MEDFONT,  wraplength=400, justify="center", anchor="n")
        question.place(relx=0.5, rely=0.4, anchor="center")

        answer1 = tk.Label(self.canvas, text="The Art of Making Things Fail Together", 
            wraplength=120, justify="center", anchor="c", font=self.SMALLFONT)
        answer1.place(relx=0.2, rely=0.5)
        answer2 = tk.Label(self.canvas, text="Making Skynet a Reality, One System at a Time",
            wraplength=120, justify="center", anchor="c", font=self.SMALLFONT)
        answer2.place(relx=0.4, rely=0.5)
        answer3 = tk.Label(self.canvas, text="How to Break the Internet 101", 
            wraplength=120, justify="center", anchor="c", font=self.SMALLFONT)
        answer3.place(relx=0.6, rely=0.5)
        
        button1 = tk.Button(self.canvas, text="Option 1", command=lambda: self.vote(controller, 1), font=self.SMALLFONT)
        button1.place(relx=0.21, rely=0.7)
        button2 = tk.Button(self.canvas, text="Option 2", command=lambda: self.vote(controller, 2), font=self.SMALLFONT)
        button2.place(relx=0.42, rely=0.7)
        button3 = tk.Button(self.canvas, text="Option 3", command=lambda: self.vote(controller, 3), font=self.SMALLFONT)
        button3.place(relx=0.62, rely=0.7)
        
        # Create the countdown label
        self.timer_label = tk.Label(self.canvas, text="00:00", font=MEDFONT, bg="white")
        self.timer_label.place(relx=0.5, rely=0.3, anchor="center")

        # Set the countdown duration in seconds
        self.countdown_duration = 10

        # Start the countdown
        self.start_countdown()

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

    def start_countdown(self):
        # Update the timer label every second
        if self.countdown_duration > 0:
            minutes = self.countdown_duration // 60
            seconds = self.countdown_duration % 60
            self.timer_label.configure(text="{:02d}:{:02d}".format(minutes, seconds))
            self.countdown_duration -= 1
            self.after(1000, self.start_countdown)
        else:
            # Do something when the countdown is over
            pass
    def vote(self, controller, option):
            controller.show_frame(LeaderboardPage)
            print("Vote for option", option)
    
        


class LeaderboardPage(tk.Frame):
    def __init__(self, parent, controller, servicer):
        tk.Frame.__init__(self, parent)

        self.LARGEFONT = tkfont.Font(family="Verdana", size=35)

        # Define the names and scores of the players
        player_names = ['Player 1', 'Player 2', 'Player 3', 'Player 4', 'Player 5', 'Player 6', 'Player 7', 'Player 8']
        player_scores = [100, 200, 300, 400, 500, 600, 700, 800]
        
        # Create the canvas for the background image
        self.canvas = tk.Canvas(self, width=500, height=500)
        self.canvas.pack(fill="both", expand=True)

        # Load the background image
        image = Image.open("./StartPageWallpaper.jpeg")
        photo = ImageTk.PhotoImage(image)
        self.canvas.background = photo  # Keep a reference to the photo to prevent garbage collection
        self.canvas.create_image(0, 0, image=photo, anchor="nw")

        # Create a frame inside the canvas
        self.frame = tk.Frame(self.canvas)
        self.frame.pack(expand=True)

        # Create the title label
        title_label = tk.Label(self.frame, text="Leaderboard", font=self.LARGEFONT)
        title_label.grid(row=0, column=0, columnspan=3, pady=(20, 10))

        # Create a grid of Labels to display the player names and scores
        for i in range(len(player_names)):
            name_label = tk.Label(self.frame, text=player_names[i], font=("Verdana", 16))
            name_label.grid(row=i+1, column=0, padx=20, pady=10)
            
            score_label = tk.Label(self.frame, text=player_scores[i], font=("Verdana", 16))
            score_label.grid(row=i+1, column=1, padx=20, pady=10)

        # Center the frame in the canvas
        self.frame.place(relx=0.5, rely=0.5, anchor="center")




if __name__ == '__main__': 
    parser = argparse.ArgumentParser()
    parser.add_argument("-P", "--port", help="Port of where server will be running", type=str, default=os.environ['QUIPLASH_SERVER_PORT'])

    args = parser.parse_args()  
    app = tkinterApp(args.port)
    app.resizable(False, False)
    asyncio.run(app.mainloop())