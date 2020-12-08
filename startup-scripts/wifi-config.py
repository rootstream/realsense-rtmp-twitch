import tkinter as tk
import tkinter.font as tkfont
import os

class Application(tk.Frame):
    wifiSSID = str(os.environ['WIFI_CONFIG_SSID'])
    wifiPASSWD = str(os.environ['WIFI_CONFIG_PASSWD'])

    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        self.pack()
        self.create_widgets()

    def create_widgets(self):
        self.wifi_config = tk.Label(self, font=fontStyle, justify=tk.LEFT)
        self.wifi_config["text"] = "The Depth capture kit was unable to detect internet.\n\
Currently broadcasting a wifi hotspot to connect and setup wifi.\n\n\
WIFI NAME = " + self.wifiSSID + "\n\
WIFI PASSWORD = " + self.wifiPASSWD + "\n\n\
Please connect to the wifi address above and follow the prompts on the screen.\n\
Hit the 'QUIT' button to the bottom right of the text when done."
        self.wifi_config.pack(side=tk.TOP, anchor=tk.NW)

        self.quit = tk.Button(self, text="QUIT", fg="red", font=fontStyle,
                              command=self.master.destroy)
        self.quit.pack(side=tk.TOP, anchor=tk.SE)

root = tk.Tk()
fontStyle = tkfont.Font(family="Lucida Grande", size=20)
root.attributes('-fullscreen', True)
app = Application(master=root)
app.mainloop()