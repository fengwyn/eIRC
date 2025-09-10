###
# Win32 GUI for eIRC client (pywin32)

# This file provides a native Win32 GUI wrapper around the existing Client class
# in src/client/client.py. It asks the user for username, allows connecting to
# either the default tracker or a custom tracker, displays chat, lets the user
# send messages (including whispers), and shows a side list of servers/users.

# Run from project root (Windows only):
#     python -m src.client.windows.wingui

# Required package(s):
#     pip install pywin32

# Notes:
#  - This GUI uses the Client class with use_queue=True 
#    so GUI pushes commands into client.command_queue (from Client model)
#  - The GUI is only for Windows.
###

import os
import sys
import threading
import queue

# pywin32 APIs and configs
from src.client.windows.config import *
from src.client.client import Client


# In essence, we're wrapping up our pre-existing Client model API with
# pywin's API, 
class IRCClientGUI:

    def __init__(self):

        self.windowhandler = None
        self.client = None
        self.username = None
        self.connected = False
        self.message_queue = queue.Queue() # <-- How the magic happens, GUI text
        self.list_items = []
        self.default_host = 'localhost'
        self.default_port = 8888
        self.current_server = None

        # control handles
        self.chat_display = None
        self.chat_input = None
        self.list_box = None
        self.whisper_user = None
        self.whisper_msg = None
        self.status_bar = None

        # dialog handle refs
        self.username_dlg = None
        self.connect_dlg = None



    # ----- Registration and Creation -----

    def register_classes(self):

        hInstance = win32api.GetModuleHandle(None)

        # Main window
        wc = win32gui.WNDCLASS()
        wc.style = win32con.CS_HREDRAW | win32con.CS_VREDRAW
        wc.lpfnWndProc = self.main_wnd_proc
        wc.hInstance = hInstance
        wc.hCursor = win32gui.LoadCursor(0, win32con.IDC_ARROW)
        wc.hIcon = win32gui.LoadIcon(0, win32con.IDI_APPLICATION)
        wc.hbrBackground = win32con.COLOR_WINDOW + 1
        wc.lpszClassName = MAIN_WINDOW_CLASS
        win32gui.RegisterClass(wc)

        # Username dialog
        wc2 = win32gui.WNDCLASS()
        wc2.style = win32con.CS_DBLCLKS
        wc2.lpfnWndProc = self.username_dialog_proc
        wc2.hInstance = hInstance
        wc2.hCursor = win32gui.LoadCursor(0, win32con.IDC_ARROW)
        wc2.hbrBackground = win32con.COLOR_BTNFACE + 1
        wc2.lpszClassName = USERNAME_DIALOG_CLASS
        win32gui.RegisterClass(wc2)

        # Connect dialog
        wc3 = win32gui.WNDCLASS()
        wc3.style = win32con.CS_DBLCLKS
        wc3.lpfnWndProc = self.connect_dialog_proc
        wc3.hInstance = hInstance
        wc3.hCursor = win32gui.LoadCursor(0, win32con.IDC_ARROW)
        wc3.hbrBackground = win32con.COLOR_BTNFACE + 1
        wc3.lpszClassName = CONNECT_DIALOG_CLASS
        win32gui.RegisterClass(wc3)


    def create_main_window(self):

        hInstance = win32api.GetModuleHandle(None)

        self.windowhandler = win32gui.CreateWindowEx(
            0,
            MAIN_WINDOW_CLASS,
            "eIRC - Win32 GUI",
            win32con.WS_OVERLAPPEDWINDOW,
            win32con.CW_USEDEFAULT,
            win32con.CW_USEDEFAULT,
            1000,
            600,
            0,
            0,
            hInstance,
            None,
        )


        # Menu
        menu = win32gui.CreateMenu()
        file_menu = win32gui.CreatePopupMenu()
        win32gui.AppendMenu(file_menu, win32con.MF_STRING, ID_FILE_CONNECT, "&Connect...")
        win32gui.AppendMenu(file_menu, win32con.MF_STRING, ID_FILE_DISCONNECT, "&Disconnect")
        win32gui.AppendMenu(file_menu, win32con.MF_SEPARATOR, 0, "")
        win32gui.AppendMenu(file_menu, win32con.MF_STRING, ID_FILE_EXIT, "E&xit")
        win32gui.AppendMenu(menu, win32con.MF_POPUP, file_menu, "&File")

        help_menu = win32gui.CreatePopupMenu()
        win32gui.AppendMenu(help_menu, win32con.MF_STRING, ID_HELP_ABOUT, "&About")
        win32gui.AppendMenu(menu, win32con.MF_POPUP, help_menu, "&Help")

        win32gui.SetMenu(self.windowhandler, menu)

        self.create_controls()

        win32gui.ShowWindow(self.windowhandler, win32con.SW_SHOW)
        win32gui.UpdateWindow(self.windowhandler)



    def create_controls(self):

        hInstance = win32api.GetModuleHandle(None)

        # Chat display (read-only multi-line edit)
        self.chat_display = win32gui.CreateWindowEx(
            win32con.WS_EX_CLIENTEDGE,
            "EDIT",
            "",
            win32con.WS_CHILD | win32con.WS_VISIBLE | win32con.ES_MULTILINE |
            win32con.ES_AUTOVSCROLL | win32con.ES_READONLY | win32con.WS_VSCROLL,
            10,
            10,
            700,
            420,
            self.windowhandler,
            ID_CHAT_DISPLAY,
            hInstance,
            None,
        )

        # Chat input
        self.chat_input = win32gui.CreateWindowEx(
            win32con.WS_EX_CLIENTEDGE,
            "EDIT",
            "",
            win32con.WS_CHILD | win32con.WS_VISIBLE | win32con.ES_AUTOVSCROLL | win32con.WS_VSCROLL,
            10,
            440,
            600,
            100,
            self.windowhandler,
            ID_CHAT_INPUT,
            hInstance,
            None,
        )

        # Send button
        win32gui.CreateWindow(
            "BUTTON",
            "Send",
            win32con.WS_CHILD | win32con.WS_VISIBLE | win32con.BS_PUSHBUTTON,
            620,
            440,
            90,
            30,
            self.windowhandler,
            ID_SEND_BUTTON,
            hInstance,
            None,
        )

        # List box label
        win32gui.CreateWindow(
            "STATIC",
            "Servers/Users:",
            win32con.WS_CHILD | win32con.WS_VISIBLE,
            720,
            10,
            120,
            20,
            self.windowhandler,
            -1,
            hInstance,
            None,
        )

        # List box
        self.list_box = win32gui.CreateWindowEx(
            win32con.WS_EX_CLIENTEDGE,
            "LISTBOX",
            "",
            win32con.WS_CHILD | win32con.WS_VISIBLE | win32con.WS_VSCROLL | win32con.LBS_NOTIFY,
            720,
            35,
            240,
            220,
            self.windowhandler,
            ID_LIST_BOX,
            hInstance,
            None,
        )

        # Whisper
        win32gui.CreateWindow(
            "STATIC",
            "Whisper to:",
            win32con.WS_CHILD | win32con.WS_VISIBLE,
            720,
            265,
            240,
            20,
            self.windowhandler,
            -1,
            hInstance,
            None,
        )

        self.whisper_user = win32gui.CreateWindowEx(
            win32con.WS_EX_CLIENTEDGE,
            "EDIT",
            "",
            win32con.WS_CHILD | win32con.WS_VISIBLE,
            720,
            290,
            240,
            24,
            self.windowhandler,
            ID_WHISPER_USER,
            hInstance,
            None,
        )

        self.whisper_msg = win32gui.CreateWindowEx(
            win32con.WS_EX_CLIENTEDGE,
            "EDIT",
            "",
            win32con.WS_CHILD | win32con.WS_VISIBLE | win32con.ES_MULTILINE | win32con.ES_AUTOVSCROLL,
            720,
            320,
            240,
            80,
            self.windowhandler,
            ID_WHISPER_MSG,
            hInstance,
            None,
        )

        win32gui.CreateWindow(
            "BUTTON",
            "Send Whisper",
            win32con.WS_CHILD | win32con.WS_VISIBLE | win32con.BS_PUSHBUTTON,
            720,
            410,
            240,
            30,
            self.windowhandler,
            ID_WHISPER_SEND,
            hInstance,
            None,
        )

        # Status bar (simple static)
        self.status_bar = win32gui.CreateWindow(
            "STATIC",
            "Not connected",
            win32con.WS_CHILD | win32con.WS_VISIBLE | win32con.SS_SUNKEN,
            0,
            540,
            1000,
            20,
            self.windowhandler,
            ID_STATUS_BAR,
            hInstance,
            None,
        )



    # ------ Dialogs -------

    def show_username_dialog(self):

        hInstance = win32api.GetModuleHandle(None)
        width, height = 360, 140
        left, top = 150, 150

        self.username_dlg = win32gui.CreateWindowEx(
            win32con.WS_EX_DLGMODALFRAME,
            USERNAME_DIALOG_CLASS,
            "Enter Username",
            win32con.WS_OVERLAPPED | win32con.WS_CAPTION | win32con.WS_SYSMENU,
            left,
            top,
            width,
            height,
            self.windowhandler,
            0,
            hInstance,
            None,
        )


        # Static + edit + buttons
        win32gui.CreateWindow("STATIC", "Username:", win32con.WS_CHILD | win32con.WS_VISIBLE, 20, 20, 80, 20, self.username_dlg, -1, hInstance, None)

        self.username_edit = win32gui.CreateWindowEx(win32con.WS_EX_CLIENTEDGE, "EDIT", "", 
        win32con.WS_CHILD | win32con.WS_VISIBLE, 110, 18, 220, 22, self.username_dlg, ID_USERNAME_EDIT, hInstance, None)

        win32gui.CreateWindow("BUTTON", "OK", win32con.WS_CHILD | win32con.WS_VISIBLE | win32con.BS_DEFPUSHBUTTON, 
        70, 60, 80, 28, self.username_dlg, ID_USERNAME_OK, hInstance, None)

        win32gui.CreateWindow("BUTTON", "Cancel", win32con.WS_CHILD | win32con.WS_VISIBLE | win32con.BS_PUSHBUTTON, 
        170, 60, 80, 28, self.username_dlg, ID_USERNAME_CANCEL, hInstance, None)

        win32gui.ShowWindow(self.username_dlg, win32con.SW_SHOW)
        win32gui.EnableWindow(self.windowhandler, False)

   
    def show_connect_dialog(self):

        hInstance = win32api.GetModuleHandle(None)
        width, height = 420, 220
        left, top = 160, 160

        self.connect_dlg = win32gui.CreateWindowEx(
            win32con.WS_EX_DLGMODALFRAME,
            CONNECT_DIALOG_CLASS,
            "Connect to Server",
            win32con.WS_OVERLAPPED | win32con.WS_CAPTION | win32con.WS_SYSMENU,
            left,
            top,
            width,
            height,
            self.windowhandler,
            0,
            hInstance,
            None,
        )

        # Radio buttons
        self.radio_default = win32gui.CreateWindow("BUTTON", f"Default Server ({self.default_host}:{self.default_port})",
                                                 win32con.WS_CHILD | win32con.WS_VISIBLE | win32con.BS_AUTORADIOBUTTON | win32con.WS_GROUP,
                                                 20, 20, 360, 22, self.connect_dlg, ID_CONNECT_DEFAULT, hInstance, None)

        win32gui.CreateWindow("BUTTON", "Custom Server:", win32con.WS_CHILD | win32con.WS_VISIBLE | win32con.BS_AUTORADIOBUTTON, 
        20, 48, 120, 22, self.connect_dlg, ID_CONNECT_CUSTOM, hInstance, None)


        # Host / Port
        win32gui.CreateWindow("STATIC", "Host:", win32con.WS_CHILD | win32con.WS_VISIBLE, 40, 80, 40, 20, self.connect_dlg, -1, hInstance, None)

        self.host_edit = win32gui.CreateWindowEx(win32con.WS_EX_CLIENTEDGE, "EDIT", 
        self.default_host, win32con.WS_CHILD | win32con.WS_VISIBLE, 90, 78, 240, 22, self.connect_dlg, ID_CONNECT_HOST, hInstance, None)

        win32gui.CreateWindow("STATIC", "Port:", win32con.WS_CHILD | win32con.WS_VISIBLE, 40, 110, 40, 20, self.connect_dlg, -1, hInstance, None)

        self.port_edit = win32gui.CreateWindowEx(win32con.WS_EX_CLIENTEDGE, "EDIT", str(self.default_port), 
        win32con.WS_CHILD | win32con.WS_VISIBLE, 90, 108, 100, 22, self.connect_dlg, ID_CONNECT_PORT, hInstance, None)


        # Buttons
        win32gui.CreateWindow("BUTTON", "Connect", win32con.WS_CHILD | win32con.WS_VISIBLE | win32con.BS_DEFPUSHBUTTON, 
        80, 150, 100, 28, self.connect_dlg, ID_CONNECT_OK, hInstance, None)

        win32gui.CreateWindow("BUTTON", "Cancel", win32con.WS_CHILD | win32con.WS_VISIBLE | win32con.BS_PUSHBUTTON, 
        220, 150, 100, 28, self.connect_dlg, ID_CONNECT_CANCEL, hInstance, None)

        # default selection
        win32gui.SendMessage(self.radio_default, win32con.BM_SETCHECK, 1, 0)

        win32gui.ShowWindow(self.connect_dlg, win32con.SW_SHOW)
        win32gui.EnableWindow(self.windowhandler, False)



    # ------- Window procs --------

    def username_dialog_proc(self, windowhandler, msg, wParam, lParam):

        if msg == win32con.WM_COMMAND:

            cmd = win32api.LOWORD(wParam)

            if cmd == ID_USERNAME_OK:

                length = win32gui.GetWindowTextLength(self.username_edit)

                if length > 0:
                    self.username = win32gui.GetWindowText(self.username_edit)
                    # close dialog and show connect
                    win32gui.DestroyWindow(windowhandler)
                    self.username_dlg = None
                    win32gui.EnableWindow(self.windowhandler, True)
                    # show connect dialog next
                    self.show_connect_dialog()

                else:
                    win32api.MessageBox(windowhandler, "Username cannot be empty!", "Error", win32con.MB_OK | win32con.MB_ICONERROR)

            elif cmd == ID_USERNAME_CANCEL:

                win32gui.DestroyWindow(windowhandler)
                win32gui.PostQuitMessage(0)

        elif msg == win32con.WM_CLOSE:

            win32gui.DestroyWindow(windowhandler)
            win32gui.PostQuitMessage(0)


        return win32gui.DefWindowProc(windowhandler, msg, wParam, lParam)



    def connect_dialog_proc(self, windowhandler, msg, wParam, lParam):

        if msg == win32con.WM_COMMAND:

            cmd = win32api.LOWORD(wParam)

            if cmd == ID_CONNECT_OK:
                # choose default or custom
                if win32gui.SendMessage(self.radio_default, win32con.BM_GETCHECK, 0, 0):
                    host = self.default_host
                    port = self.default_port

                else:
                    host = win32gui.GetWindowText(self.host_edit)

                    try:
                        port = int(win32gui.GetWindowText(self.port_edit))

                    except ValueError:
                        win32api.MessageBox(windowhandler, "Invalid port number!", "Error", win32con.MB_OK | win32con.MB_ICONERROR)
                        return 0
                # eoif3


                win32gui.DestroyWindow(windowhandler)
                self.connect_dlg = None
                win32gui.EnableWindow(self.windowhandler, True)
                # perform connection
                self.connect_to_server(host, port)


            elif cmd == ID_CONNECT_CANCEL:
                win32gui.DestroyWindow(windowhandler)
                self.connect_dlg = None
                win32gui.EnableWindow(self.windowhandler, True)
            # eoif2

        elif msg == win32con.WM_CLOSE:
            win32gui.DestroyWindow(windowhandler)
            self.connect_dlg = None
            win32gui.EnableWindow(self.windowhandler, True)
        # eoif1

        return win32gui.DefWindowProc(windowhandler, msg, wParam, lParam)



    def main_wnd_proc(self, windowhandler, msg, wParam, lParam):

        if msg == win32con.WM_CREATE:
            return 0

        elif msg == win32con.WM_SIZE:
            width = win32api.LOWORD(lParam)
            height = win32api.HIWORD(lParam)

            # reposition/resize controls simply
            try:
                if self.chat_display:
                    win32gui.MoveWindow(self.chat_display, 10, 10, width - 360, height - 180, True)
                if self.chat_input:
                    win32gui.MoveWindow(self.chat_input, 10, height - 140, width - 360, 100, True)
                if self.status_bar:
                    win32gui.MoveWindow(self.status_bar, 0, height - 20, width, 20, True)
                if self.list_box:
                    win32gui.MoveWindow(self.list_box, width - 260, 35, 240, height - 220, True)

            except Exception:
                pass


        elif msg == win32con.WM_COMMAND:

            cmd = win32api.LOWORD(wParam)
            if cmd == ID_SEND_BUTTON:
                self.send_message()

            elif cmd == ID_WHISPER_SEND:
                self.send_whisper()

            elif cmd == ID_FILE_CONNECT:

                if not self.connected:
                    if not self.username:
                        self.show_username_dialog()
                    else:
                        self.show_connect_dialog()

            elif cmd == ID_FILE_DISCONNECT:
                self.disconnect()

            elif cmd == ID_FILE_EXIT:
                win32gui.DestroyWindow(windowhandler)

            elif cmd == ID_HELP_ABOUT:
                win32api.MessageBox(windowhandler, "eIRC GUI - pywin32\n", "About", win32con.MB_OK | win32con.MB_ICONINFORMATION)


        elif msg == WM_UPDATE_CHAT:

            # flush queue into chat display
            try:
                while not self.message_queue.empty():
                    text = self.message_queue.get_nowait()
                    self.append_chat(text)
            except queue.Empty:
                pass


        elif msg == WM_UPDATE_LIST:

            # repopulate list box
            try:
                win32gui.SendMessage(self.list_box, win32con.LB_RESETCONTENT, 0, 0)

                for item in self.list_items:
                    win32gui.SendMessage(self.list_box, win32con.LB_ADDSTRING, 0, item)

            except Exception:
                pass


        elif msg == WM_UPDATE_STATUS:

            status_text = f"Connected to: {self.current_server}" if self.connected else "Not connected"
            win32gui.SetWindowText(self.status_bar, status_text)

        
        elif msg == win32con.WM_DESTROY:

            if self.client:
                try:
                    self.client.stop()
                except Exception:
                    pass
            
            win32gui.PostQuitMessage(0)
            return 0

        return win32gui.DefWindowProc(windowhandler, msg, wParam, lParam)



    # ------ Helpers ---------

    def append_chat(self, text):

        try:
            # get current length
            length = win32gui.GetWindowTextLength(self.chat_display)
            # set selection at the end and replace
            win32gui.SendMessage(self.chat_display, win32con.EM_SETSEL, length, length)
            win32gui.SendMessage(self.chat_display, win32con.EM_REPLACESEL, False, text + "\r\n")
            # scroll to bottom
            win32gui.SendMessage(self.chat_display, win32con.WM_VSCROLL, win32con.SB_BOTTOM, 0)
        
        except Exception:
            pass


    def send_message(self):

        if not self.connected or not self.client:
            win32api.MessageBox(self.windowhandler, "Not connected to server!", "Error", win32con.MB_OK | win32con.MB_ICONERROR)
            return
        
        text = win32gui.GetWindowText(self.chat_input)
        
        if text and text.strip():
            # push to client's queue; client.write will build packet
            self.client.command_queue.put(text)
            win32gui.SetWindowText(self.chat_input, "")



    def send_whisper(self):

        if not self.connected or not self.client:
            win32api.MessageBox(self.windowhandler, "Not connected to server!", "Error", win32con.MB_OK | win32con.MB_ICONERROR)
            return

        user = win32gui.GetWindowText(self.whisper_user).strip()
        msg = win32gui.GetWindowText(self.whisper_msg).strip()
        
        if user and msg:
            cmd = f"/whisper {user} {msg}"
            self.client.command_queue.put(cmd)
            win32gui.SetWindowText(self.whisper_msg, "")
            self.append_chat(f"[Whisper to {user}]: {msg}")



    def connect_to_server(self, host, port):
        
        try:
            # instantiate client using queue mode
            self.client = Client(host, port, self.username, use_queue=True)
            # perform initial connect
            self.client.connect(host, port)

            # start receive thread which will post messages back to GUI
            t_recv = threading.Thread(target=self.receive_with_gui, daemon=True)
            t_recv.start()

            # start writer thread
            t_write = threading.Thread(target=self.client.write, daemon=True)
            t_write.start()

            self.connected = True
            self.current_server = f"{host}:{port}"
            win32gui.PostMessage(self.windowhandler, WM_UPDATE_STATUS, 0, 0)
            self.message_queue.put(f"Connected to {host}:{port}")
            win32gui.PostMessage(self.windowhandler, WM_UPDATE_CHAT, 0, 0)

        except Exception as e:
            win32api.MessageBox(self.windowhandler, f"Failed to connect: {e}", "Connection Error", win32con.MB_OK | win32con.MB_ICONERROR)


    def disconnect(self):
        
        if self.client:
            try:
                self.client.stop()
            except Exception:
                pass
        
        self.client = None
        self.connected = False
        self.current_server = None
        win32gui.PostMessage(self.windowhandler, WM_UPDATE_STATUS, 0, 0)
        self.message_queue.put("Disconnected")
        win32gui.PostMessage(self.windowhandler, WM_UPDATE_CHAT, 0, 0)



    # ------ Receiving loop ----------

    def receive_with_gui(self):

        # Uses the underlying client.socket to recv and translates into GUI updates
        while self.client and self.client.running:

            try:
                packet = self.client.client.recv(4096)
                if not packet:
                    self.message_queue.put("Server closed the connection.")
                    win32gui.PostMessage(self.windowhandler, WM_UPDATE_CHAT, 0, 0)
                    break

                # handshake prompt
                if packet == b'USER':
                    # server expects username bytes
                    try:
                        self.client.client.send(self.username.encode('ascii'))
                    except Exception:
                        pass
                    continue

                # try structured packet
                try:
                    from src.utils.packet import unpack_packet

                    p = unpack_packet(packet)
                    sender = p.get('header')
                    body = p.get('body')
                    date = p.get('date')
                    self.message_queue.put(f"[{date}] {sender}: {body}")
                    win32gui.PostMessage(self.windowhandler, WM_UPDATE_CHAT, 0, 0)

                    # special commands handled client-side
                    if sender == 'CREATED':
                        # body: "<room> <host> <port>"
                        room, host, port_s = body.split()
                        port = int(port_s)
                        self.message_queue.put(f"Hopping into new node `{room}` @ {host}:{port}...")
                        win32gui.PostMessage(self.windowhandler, WM_UPDATE_CHAT, 0, 0)
                        # reconnect low-level socket
                        self.client.connect(host, port)
                        self.current_server = f"{host}:{port}"
                        win32gui.PostMessage(self.windowhandler, WM_UPDATE_STATUS, 0, 0)


                    elif sender == 'WHISPER':
                        self.message_queue.put(f"[WHISPER] {body}")
                        win32gui.PostMessage(self.windowhandler, WM_UPDATE_CHAT, 0, 0)


                    elif sender == 'JOIN':
                        ip, port_s = body.split(':')
                        port = int(port_s)
                        self.message_queue.put(f"Joining node server @{body}")
                        win32gui.PostMessage(self.windowhandler, WM_UPDATE_CHAT, 0, 0)
                        self.client.connect(ip, port)
                        self.current_server = f"{ip}:{port}"
                        win32gui.PostMessage(self.windowhandler, WM_UPDATE_STATUS, 0, 0)


                    elif sender == 'LEAVE':
                        self.message_queue.put('Leaving node room...')
                        win32gui.PostMessage(self.windowhandler, WM_UPDATE_CHAT, 0, 0)
                        # we'll now hop back to tracker
                        self.client.connect(self.client.tracker_addr, self.client.tracker_port)
                        self.current_server = f"{self.client.tracker_addr}:{self.client.tracker_port}"
                        win32gui.PostMessage(self.windowhandler, WM_UPDATE_STATUS, 0, 0)


                    elif sender == 'EXIT':
                        self.message_queue.put('Server requested exit. Disconnecting...')
                        win32gui.PostMessage(self.windowhandler, WM_UPDATE_CHAT, 0, 0)
                        self.client.stop()
                        break


                except Exception:
                    # fallback to plain text
                    try:
                        text = packet.decode('ascii', errors='ignore').strip()
                        if text:
                            self.message_queue.put(text)
                            win32gui.PostMessage(self.windowhandler, WM_UPDATE_CHAT, 0, 0)
                    
                    except Exception:
                        pass

            except Exception as e:
                # network errors
                self.message_queue.put(f"Receive error: {e}")
                win32gui.PostMessage(self.windowhandler, WM_UPDATE_CHAT, 0, 0)
                break



        # clean up
        try:
            if self.client:
                self.client.stop()
        except Exception:
            pass
        
        self.connected = False
        win32gui.PostMessage(self.windowhandler, WM_UPDATE_STATUS, 0, 0)



    # ------- Run/loop ---------

    def run(self):

        self.register_classes()
        self.create_main_window()

        # show username dialog first
        self.show_username_dialog()

        # standard Win32 message loop
        while True:
            rc, msg = win32gui.GetMessage(None, 0, 0)
            if rc == 0:  # WM_QUIT
                break
            elif rc == -1:
                break  # error
            else:
                win32gui.TranslateMessage(msg)
                win32gui.DispatchMessage(msg)



def main():
    # Must be run on Windows
    if os.name != 'nt':
        print('This GUI requires Windows (pywin32).')
        return

    gui = IRCClientGUI()
    gui.run()


if __name__ == '__main__':
    main()
