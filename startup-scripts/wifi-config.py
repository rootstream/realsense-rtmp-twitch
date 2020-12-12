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
        self.description = tk.Label(self, font=fontStyle, justify=tk.LEFT)
        self.description["text"] = "The Raspberry Capture Kit was unable to detect internet.\n\
Currently broadcasting a wifi hotspot to setup wifi.\n\n"
        self.description.pack(side=tk.TOP, anchor=tk.NW)
        self.wifi_config = tk.Label(self, font=wifiStyle, justify=tk.LEFT)
        self.wifi_config["text"]= "WIFI NAME = " + self.wifiSSID + "\n\
WIFI PASSWORD = " + self.wifiPASSWD + "\n"
        self.wifi_config.pack(side=tk.TOP, anchor=tk.NW)
        self.exit = tk.Label(self, font=fontStyle, justify=tk.LEFT)
        self.exit["text"]= "\
1. Connect to the wifi name above with your device\n\
2. Follow the prompts\n\
3. Hit Connect\n\
4. Tap 'NEXT' to close this screen"
        self.exit.pack(side=tk.TOP, anchor=tk.NW)

        self.quit = tk.Button(self, text="NEXT", fg="red", font=buttonStyle,
                              command=self.master.destroy)
        self.quit.pack(side=tk.TOP, anchor=tk.NE)

root = tk.Tk()
fontStyle = tkfont.Font(family="Lucida Grande", size=33)
wifiStyle = tkfont.Font(family="Lucida Grande", size=44)
buttonStyle = tkfont.Font(family="Lucida Grande", size=85)
root.attributes('-fullscreen', True)
app = Application(master=root)
app.mainloop()
