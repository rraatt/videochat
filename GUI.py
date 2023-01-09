import ipaddress
import re
import socket
import tkinter as tk
from time import sleep
from tkinter import ttk

import client
import client as vid

LARGEFONT = ("Verdana", 35)
VID_CLIENT: client.VideoChat


class tkinterApp(tk.Tk):

    # __init__ function for class tkinterApp
    def __init__(self, *args, **kwargs):
        # __init__ function for class Tk
        tk.Tk.__init__(self, *args, **kwargs)

        # creating a container
        container = tk.Frame(self)
        container.pack(side="top", fill="both", expand=True)

        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        # initializing frames to an empty array
        self.frames = {}

        # iterating through a tuple consisting
        # of the different page layouts
        for F in (StartPage, Chat):
            frame = F(container, self)

            # initializing frame of that object from
            # startpage, page1, page2 respectively with
            # for loop
            self.frames[F] = frame

            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame(Chat)

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
        label.grid(row=0, column=1, padx=10, pady=10)

        button1 = ttk.Button(self, text="Accept connection",
                             command=self.accept_connection)

        # putting the button in its place by
        # using grid
        button1.grid(row=1, column=1, padx=10, pady=10)

        ## button to show frame 2 with text layout2
        button2 = ttk.Button(self, text="Connect",
                             command=self.con_popup)

        # putting the button in its place by
        # using grid
        button2.grid(row=2, column=1, padx=10, pady=10)

    def accept_connection(self):
        global VID_CLIENT
        VID_CLIENT = vid.ClientPassive()
        try:
            VID_CLIENT.start_chat()
        except socket.timeout:
            error = tk.Toplevel()
            error.wm_title('Error')
            error_msg = tk.Label(error, text='No connection')
            error_msg.grid(row=0, column=0)
            ok_butt = ttk.Button(error, text="Ok",
                                 command=lambda: [error.destroy(), self.controller.show_frame(StartPage)])
            ok_butt.grid(row=1, column=0)

    def con_popup(self):
        win = tk.Toplevel()
        win.wm_title("Connect to user")

        l = tk.Label(win, text="IP address")
        l.grid(row=0, column=0, padx=10, pady=10)

        user_input = tk.StringVar(win)
        entry = ttk.Entry(win, textvariable=user_input)
        entry.grid(row=0, column=1, padx=10, pady=10)

        b = ttk.Button(win, text="Connect", command=lambda: self.create_connection(user_input.get(), win))
        b.grid(row=1, column=0, padx=10, pady=10)

    def create_connection(self, inp, popup):
        global VID_CLIENT
        try:
            ipaddress.ip_address(inp)
            VID_CLIENT = vid.ClientActive(inp)
            popup.destroy()
            VID_CLIENT.start_chat()
        except socket.timeout:
            error = tk.Toplevel()
            error.wm_title('Error')
            error_msg = tk.Label(error, text='No connection')
            error_msg.grid(row=0, column=0)
            ok_butt = ttk.Button(error, text="Ok",
                                 command=lambda: [error.destroy(), self.controller.show_frame(StartPage)])
            ok_butt.grid(row=1, column=0)
        except ValueError:
            error = tk.Toplevel()
            error.wm_title('Error')
            error_msg = tk.Label(error, text='Incorrect IP address')
            error_msg.grid(row=0, column=0, padx=10, pady=10)
            ok_butt = ttk.Button(error, text="Ok", command=error.destroy)
            ok_butt.grid(row=1, column=0, padx=10, pady=10)


# third window frame page2
class Chat(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        lable1 = ttk.Label(self, text="Welcome", padding=10)
        lable1.grid(row=0)

        GUI_out = tk.Text(self, width=60)
        GUI_out.grid(row=1, column=0, columnspan=2)

        scrollbar = tk.Scrollbar(GUI_out)
        scrollbar.place(relheight=1, relx=0.974)

        e = tk.Entry(self, width=55)
        e.grid(row=2, column=0)

        send = tk.Button(self, text='send')
        send.grid(row=2, column=1)

# Driver Code
app = tkinterApp()
app.mainloop()
