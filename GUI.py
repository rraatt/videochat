import ipaddress
import os
import threading
import tkinter as tk
from time import sleep
from tkinter import ttk

import client
import client as vid

LARGEFONT = ("Verdana", 35)
VID_CLIENT: client.VideoChat
TIMEOUT_FLAG = False


def custom_hook(args):
    global TIMEOUT_FLAG, VID_CLIENT
    if args.exc_type == TimeoutError:
        error = tk.Toplevel()
        error.wm_title('Error')
        error_msg = tk.Label(error, text='No connection', font=LARGEFONT)
        error_msg.grid(row=0, column=0)
        ok_butt = ttk.Button(error, text="Ok", command=error.destroy)
        ok_butt.grid(row=1, column=0)
        TIMEOUT_FLAG = True
        VID_CLIENT.__del__()


class TkinterApp(tk.Tk):

    # __init__ function for class tkinterApp
    def __init__(self, *args, **kwargs):
        # __init__ function for class Tk
        tk.Tk.__init__(self, *args, **kwargs)

        # creating a container
        container = ttk.Frame(self)
        container.pack(side="top", fill="both", expand=True)

        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        # initializing frames to an empty array
        self.frames = {}

        # iterating through a tuple consisting
        # of the different page layouts
        for F in (StartPage, Chat, Connection):
            frame = F(container, self)

            # initializing frame of that object from
            # startpage, page1, page2 respectively with
            # for loop
            self.frames[F] = frame

            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame(StartPage)

    def show_frame(self, cont):
        frame = self.frames[cont]
        frame.tkraise()


class StartPage(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller

        # label of frame Layout 2
        label = ttk.Label(self, text="Videochat app", font=LARGEFONT)

        # putting the grid in its place by using
        # grid
        label.grid(row=0, column=2, padx=10, pady=10)

        button1 = ttk.Button(self, text="Accept connection",
                             command=self.accept_connection)

        # putting the button in its place by
        # using grid
        button1.grid(row=1, column=2, padx=10, pady=10)

        ## button to show frame 2 with text layout2
        button2 = ttk.Button(self, text="Connect",
                             command=self.con_popup)

        # putting the button in its place by
        # using grid
        button2.grid(row=2, column=2, padx=10, pady=10)

    def con_popup(self):
        win = tk.Toplevel()
        win.wm_title("Connect to user")

        l = ttk.Label(win, text="IP address")
        l.grid(row=0, column=0, padx=10, pady=10)

        user_input = tk.StringVar(win)
        entry = ttk.Entry(win, textvariable=user_input)
        entry.grid(row=0, column=1, padx=10, pady=10)

        b = ttk.Button(win, text="Connect", command=lambda: self.create_connection(user_input.get(), win))
        b.grid(row=1, column=0, padx=10, pady=10)

    def accept_connection(self):
        global VID_CLIENT
        VID_CLIENT = vid.ClientPassive()
        self.chat()

    def create_connection(self, inp, popup):
        global VID_CLIENT
        try:
            ipaddress.ip_address(inp)
            VID_CLIENT = vid.ClientActive(inp)
            popup.destroy()
            self.chat()
        except ValueError:
            error = tk.Toplevel()
            error.wm_title('Error')
            error_msg = tk.Label(error, text='Incorrect IP address')
            error_msg.grid(row=0, column=0, padx=10, pady=10)
            ok_butt = ttk.Button(error, text="Ok", command=error.destroy)
            ok_butt.grid(row=1, column=0, padx=10, pady=10)

    def chat(self):
        t1 = threading.Thread(target=VID_CLIENT.start_chat, args=())
        threading.excepthook = custom_hook
        t1.daemon = True
        t1.start()
        self.controller.show_frame(Connection)
        t2 = threading.Thread(target=self.con_ok, args=())
        t2.start()

    def con_ok(self):
        global VID_CLIENT
        while not VID_CLIENT.connected and not TIMEOUT_FLAG:
            sleep(1)
        if TIMEOUT_FLAG:
            self.controller.show_frame(StartPage)
        elif VID_CLIENT.connected:
            self.controller.show_frame(Chat)
            t1 = threading.Thread(target=VID_CLIENT.start_video(), args=())
            t1.start()


class Connection(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        label = ttk.Label(self, text="Waiting for\nconnection", font=LARGEFONT)
        label.pack()


# third window frame page2
class Chat(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        # label of frame Layout 2
        label = ttk.Label(self, text="Access text chat\nin console", font=LARGEFONT)

        # putting the grid in its place by using
        # grid
        label.grid(row=0, column=1, padx=10, pady=10)

        ## button to show frame 2 with text layout2
        button2 = ttk.Button(self, text="End conversation", command=self.close)

        # putting the button in its place by
        # using grid
        button2.grid(row=2, column=1, padx=10, pady=10)

    def close(self):
        global VID_CLIENT
        VID_CLIENT.__del__()
        self.controller.show_frame(StartPage)
        clear = lambda: os.system('cls')
        clear()


# Driver Code
app = TkinterApp()
app.mainloop()
