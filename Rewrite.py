import minecraft_launcher_lib
import subprocess
import neotkinter as ntk
import os
import shutil
import json
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs
import threading
import webbrowser
from time import sleep as wait
from dotenv import find_dotenv, load_dotenv
import psutil
import requests
from PIL import Image as image

##          INITIALIZE          ##

subprocess.run("cls", shell=True)

print("Initializing application...")

sys.stdout.reconfigure(encoding="utf-8")

path = os.path.join("C:\\Users\\" + str(os.getlogin()) + "\\AppData\\Roaming")

cbsFolder = os.path.join(path, "CubusLauncher")
os.makedirs(cbsFolder, exist_ok=True)

path = os.path.join(
    "C:\\Users\\" + str(os.getlogin()) + "\\AppData\\Roaming\\CubusLauncher"
)

tempFolder = os.path.join(path, "temp")
os.makedirs(tempFolder, exist_ok=True)

dataFolder = os.path.join(path, "appData")
os.makedirs(dataFolder, exist_ok=True)

minecraftDirectory = path
minecraftDirectory = str(minecraftDirectory).lower()
instanceVersion = 1.0
instanceChoice = ""
restart = False

##          R.A.M. RECOMMENDATION          ##
ramGB = psutil.virtual_memory().total / (1024**3)
ramRecommendation = round(ramGB / 4)

if not os.path.exists(str(minecraftDirectory) + "\\instances\\"):
    os.mkdir(str(minecraftDirectory) + "\\instances\\")

versionChoice = "1.0"
modLoader = "none"
authCode = None
loggedIn = False
accData = {}
minecraftProcess = None
accountName = ""
instancesOpen = 0

instances = [
    name
    for name in os.listdir(str(path) + "\\instances\\")
    if os.path.isdir(os.path.join(str(path) + "\\instances\\", name))
]

mrpackInstallConfig = {"optionalFiles": [], "skipDependenciesInstall": False}


class OAuthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global authCode, loggedIn
        query = parse_qs(urlparse(self.path).query)
        if "code" in query:
            authCode = query["code"][0]
            loggedIn = True
            print("OAuth login received!")
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Login successful!")
            threading.Thread(target=self.server.shutdown).start()
        else:
            self.send_response(400)
            self.end_headers()

    def log_message(self, format, *args):
        return


def startServer():
    server = HTTPServer(("localhost", 8080), OAuthHandler)
    server.serve_forever()


def downloadModrinthPack():
    global restart
    global minecraftDirectory

    # TODO: REWRITE INTO NEW G.U.I. FORMAT
    # query = downloadMRTextbox.get("0.0", "end-1c").strip()
    # wantedVersion = downloadMRVersionTextbox.get("0.0", "end-1c").strip()
    print("Searching Modrinth...")
    response = requests.get(
        "https://api.modrinth.com/v2/search",
    #    params={"query": query, "facets": '[["project_type:modpack"]]'},
    )
    response.raise_for_status()
    hits = response.json()["hits"]
    if not hits:
        print("No modpack found.")
        return
    project = None
    for pack in hits:
        # TODO: REWRITE INTO NEW G.U.I. FORMAT
        #    if pack["title"].lower() == query.lower():
        project = pack
        break
    if project is None:
        project = hits[0]
    print("Selected:", project["title"])
    versions = requests.get(
        f"https://api.modrinth.com/v2/project/{project['project_id']}/version"
    )
    versions.raise_for_status()
    versions = versions.json()
    if not versions:
        print("No versions available.")
        return
    selectedVersion = None
    # TODO: REWRITE INTO NEW G.U.I. FORMAT
    # Version override
    # if wantedVersion != "":
    # for version in versions:
    # if wantedVersion in version["game_versions"]:
    # selectedVersion = version
    # break
    # if selectedVersion is None:
    # print("Couldn't find that Minecraft version.")
    # return
    # else:
    # selectedVersion = versions[0]
    file = selectedVersion["files"][0]
    print("Downloading:", file["filename"])
    download = requests.get(file["url"])
    download.raise_for_status()
    savePath = os.path.join(tempFolder, file["filename"])
    with open(savePath, "wb") as f:
        f.write(download.content)
    print("Download complete.")

    print("Installing modpack...")

    ##        INSTALL        ##

    path = os.path.join(tempFolder, file["filename"])
    if not path:
        print("No file selected.")
        return
    name = minecraft_launcher_lib.mrpack.get_mrpack_information(path)["name"]

    callback = {"setStatus": setStatus, "setProgress": setProgress, "setMax": setMax}

    minecraft_launcher_lib.mrpack.install_mrpack(
        path,
        str(minecraftDirectory) + "\\instances\\" + name,
        callback=callback,
        mrpack_install_options=mrpackInstallConfig,
    )

    if os.path.exists(path):
        os.remove(path)

    ##          RESTART          ##

    msg = ntk.NTkMessageBox(
        title="Installation Complete",
        message="The instance: "
        + name
        + " has been installed successfully! Launcher restart required to see changes.",
        icon="check",
        option_1="Restart Now",
        option_2="Restart Later",
    )
    response = msg.get()
    if response == "Restart Now":
        restart = True
        app.destroy()


def login(mode):
    global authCode
    global accountName
    global accData
    global loggedIn

    load_dotenv(
        os.path.join(sys._MEIPASS, ".env")
        if getattr(sys, "frozen", False)
        else find_dotenv()
    )

    authCode = None
    clientID = os.getenv("Client_ID")
    clientSecret = os.getenv("Client_Secret")
    redirectURL = "http://localhost:8080/callback"

    if mode == "auto":
        try:
            print("Attempting automatic login...")
            with open(str(path) + "\\appData\\accountData.json", "r") as f:
                accData = json.load(f)
            accData = minecraft_launcher_lib.microsoft_account.complete_refresh(
                clientID, clientSecret, redirectURL, accData["refresh_token"]
            )
            loggedIn = True
            print(f"Automatic login successful! Welcome {accData['name']}")
            accountName = accData["name"]
            refreshAccountDetails()
            return
        except Exception as e:
            if "[Errno 2]" in str(e):
                print(
                    "Login failed: user has not logged in before, please login under the ACCOUNT tab."
                )
            else:
                print("Automatic login failed:", e)
            loggedIn = False
            return
    else:
        try:
            loginUrl = minecraft_launcher_lib.microsoft_account.get_login_url(
                clientID, redirectURL
            )
            threading.Thread(target=startServer, daemon=True).start()
            webbrowser.open(loginUrl)
            print("Waiting for Microsoft login...")
            while authCode is None:
                wait(0.1)
            print("Authorization code received.")
            print("Exchanging access token...")
            accData = minecraft_launcher_lib.microsoft_account.complete_login(
                clientID, clientSecret, redirectURL, authCode
            )
            loggedIn = True
            print("Login successful! Welcome " + accData["name"])
            accountName = accData["name"]
            refreshAccountDetails()
            with open(str(path) + "\\appData\\accountData.json", "w") as f:
                json.dump(accData, f, indent=4)
            print("Saved account data for automatic login.")
        except Exception as e:
            loggedIn = False


def logout():
    global loggedIn
    global accountName

    loggedIn = False
    accData.clear()
    if os.path.exists(str(path) + "\\appData\\accountData.json"):
        os.remove(str(path) + "\\appData\\accountData.json")
    print("Successfully Logged out!")
    accountName = ""
    refreshAccountDetails()

def importMrpack():
    global restart
    global minecraftDirectory
    path = ntk.filedialog.askopenfile(
        initialdir=str(
            os.path.join("C:\\Users\\" + str(os.getlogin()) + "\\Downloads")
        ),
        title="Select a Modrinth Pack",
        filetypes=[("Modrinth Packs", "*.mrpack")],
    ).name
    if not path or path == None:
        print("No file selected.")
        return
    name = minecraft_launcher_lib.mrpack.get_mrpack_information(path)["name"]

    callback = {"setStatus": setStatus, "setProgress": setProgress, "setMax": setMax}

    minecraft_launcher_lib.mrpack.install_mrpack(
        path,
        str(minecraftDirectory) + "\\instances\\" + name,
        callback=callback,
        mrpack_install_options=mrpackInstallConfig,
    )
    updateInstances()
    CreateNewInstanceMenu1Close()


def launchGame(instanceChoice : str, versionChoice : str):
    try:
        global instancesOpen
        global minecraftDirectory
        global path
        global loggedIn
        global minecraftProcess

        minecraftDirectory = path

        if not os.path.exists(str(minecraftDirectory) + "\\instances\\"):
            os.mkdir(str(minecraftDirectory) + "\\instances\\")

        if not os.path.exists(str(minecraftDirectory) + "\\instances\\" + instanceChoice):
            os.mkdir(str(minecraftDirectory) + "\\instances\\" + instanceChoice)
            minecraftDirectory = str(minecraftDirectory) + "\\instances\\" + instanceChoice
        else:
            minecraftDirectory = str(minecraftDirectory) + "\\instances\\" + instanceChoice

        if versionChoice == "latest":
            versionChoice = minecraft_launcher_lib.utils.get_latest_version()["release"]

        if versionChoice == "snapshot":
            versionChoice = minecraft_launcher_lib.utils.get_latest_version()["snapshot"]

        if loggedIn != True:
            print("Not logged in, please log in to launch the game.")
            return
        else:
            data = {
                "username": accData["name"],
                "uuid": accData["id"],
                "token": accData["access_token"],
            }
        if instancesOpen >= 1:
            data["username"] = accData["name"] + "_" + str(instancesOpen)
        instancesOpen += 1
        data["launcherName"] = "CubusLauncher"
        # TODO: REWRITE INTO NEW G.U.I. FORMAT
        # data["jvmArguments"] = ["-Xmx" + ramTextbox.get("0.0", "end-1c") + "G"]
        data["jvmArguments"] = ["-Xmx" + "8" + "G"]

        vers = [
            name
            for name in os.listdir(str(minecraftDirectory) + "\\versions\\")
            if os.path.isdir(os.path.join(str(minecraftDirectory) + "\\versions\\", name))
        ]
        if len(vers) > 1:
            moddedInstanceVersion = vers[1]
            minecraftCommand = minecraft_launcher_lib.command.get_minecraft_command(
                str(moddedInstanceVersion), minecraftDirectory, data
            )
        else:
            minecraftCommand = minecraft_launcher_lib.command.get_minecraft_command(
                str(versionChoice), minecraftDirectory, data
            )

        ##          LAUNCH          ##

        print(
            "Launching: "
            + str(instanceChoice)
            + " with game version: "
            + str(versionChoice)
            + " at the path: "
            + str(minecraftDirectory)
        )
        minecraftDirectory = os.path.join(
            "C:\\Users\\" + str(os.getlogin()) + "\\AppData\\Roaming\\CubusLauncher"
        )
        minecraftProcess = subprocess.Popen(minecraftCommand, cwd=minecraftDirectory)
    except Exception as e:
        print(f"Launch failed: {e}")
        print("Attempting to close all instances open.")
        for i in range(instancesOpen-1):
            quitGame()
        ntk.NTkMessageBox(
            title="Launch Failed",
            message="The instance: "
            + instanceChoice
            + " failed to launch.",
            icon="cancel",
            option_1="Ok",
        )

def quitGame():
    global minecraftProcess

    if minecraftProcess is None:
        print("No game is running, cannot close.")
        return

    if minecraftProcess.poll() is None:  # Still running
        try:
            minecraftProcess.terminate()
            minecraftProcess.wait(timeout=10)
        except subprocess.TimeoutExpired:
            minecraftProcess.kill()
            minecraftProcess.wait()

    minecraftProcess = None


def monitorMinecraft(entry):
    global instancesOpen
    global minecraftProcess

    if minecraftProcess is None:
        return

    # Wait until Minecraft exits
    minecraftProcess.wait()

    minecraftProcess = None

    app.after(0, entry.onGameClosed)
    print("Minecraft has been closed")
    instancesOpen -= 1

def createInstance(version: str, modLoader: str, name: str):
    global minecraftDirectory
    global instances
    global restart

    minecraftDirectory = os.path.join(
        "C:\\Users\\" + str(os.getlogin()) + "\\AppData\\Roaming\\CubusLauncher"
    )

    if not os.path.exists(str(minecraftDirectory) + "\\instances\\"):
        os.mkdir(str(minecraftDirectory) + "\\instances\\")

        instancePath = os.path.join(minecraftDirectory, "instances", name)

        if os.path.exists(instancePath):
            print(
                "Instance with that name already exists, reinstalling Minecraft Version "
                + version
                + " to that instance."
            )
            versionsPath = os.path.join(instancePath, "versions")
            if os.path.exists(versionsPath):
                shutil.rmtree(versionsPath)
            os.makedirs(versionsPath, exist_ok=True)
        else:
            os.makedirs(instancePath, exist_ok=True)

        minecraftDirectory = instancePath

    if modLoader != "none":
        modLoader = minecraft_launcher_lib.mod_loader.get_mod_loader(modLoader)

    callback = {"setStatus": setStatus, "setProgress": setProgress, "setMax": setMax}

    ##          INSTALL          ##

    if modLoader != "none":
        versionToInstall = modLoader.install(
            versionChoice, minecraftDirectory, callback=callback
        )
    else:
        minecraft_launcher_lib.install.install_minecraft_version(
            versionChoice, minecraftDirectory, callback=callback
        )

    ##          RESTART          ##

    msg = ntk.NTkMessageBox(
        title="Installation Complete",
        message="The instance: "
            + name
            + " has been installed successfully! Launcher restart required to see changes.",
            icon="check",
            option_1="Restart Now",
            option_2="Restart Later",
    )
    response = msg.get()
    if response == "Restart Now":
        restart = True
        app.destroy()


installProgressMax = 0

def setStatus(status: str):
    print(status)

def setProgress(progress: int):
    if installProgressMax != 0:
        print(f"{progress}/{installProgressMax}")

def setMax(new_max: int):
    global installProgressMax
    installProgressMax = new_max

####----                GUI                ----####

textMainColor = ("#111214", "#ffffff")
textSubColor = ("#555555", "#aaaaaa")

bgMainColor = ("#f4f5f7", "#161719")
bgSidebarColor = ("#eaecef", "#111214")
bgCardColor = ("#ebeeef", "#111214")
bgButtonColor = ("#dcdfe3", "#1c1d21")
bgHoverColor = ("#cfd2d6", "#24262b")

accentColor = "#1bd96a"
accentHover = "#14a952"
borderColor = ("#dcdfe3", "#24262b")

app = ntk.NTk()
app.geometry("960x540")
app.minsize(960, 540)
app.title("Cubus Launcher")
ntk.set_appearance_mode("dark")
ntk.set_default_color_theme("purple")
app.configure(fg_color=bgMainColor)

app.grid_columnconfigure(1, weight=1)
app.grid_rowconfigure(0, weight=1)

try:
    fontFamily = "Minecraft"
except Exception:
    pass

def refreshAccountDetails():
    global accountName

    if accountName == "":
        accountNameLabel.configure(text = "You are not logged in.")
    else:
        accountNameLabel.configure(text = f"You are logged in as: {accountName}")

class sidebarButton():
    def __init__(self, name: str):
        self.name = name
        self.button = ntk.NTkButton(sidebar, text=name, font=ntk.NTkFont(family=fontFamily, size=13, weight="bold"), fg_color="transparent", hover_color=bgButtonColor, text_color=textSubColor, command=self.changeTab)
        self.button.pack(pady=10, padx=20, anchor="center", fill="x")
        self.tab = mainContentFrame.add(name)

    def changeTab(self):
        mainContentFrame.set(name=self.name)


def updateInstances():
    # Remove existing entries
    for widget in instanceMenu.winfo_children():
        widget.destroy()
    instancesPath = os.path.join(minecraftDirectory, "instances")
    if not os.path.exists(instancesPath):
        return
    for instanceName in sorted(os.listdir(instancesPath)):
        instancePath = os.path.join(instancesPath, instanceName)
        if not os.path.isdir(instancePath):
            continue
        icon = (
            os.path.exists(instancePath + "\\icon.png")
            or os.path.exists(instancePath + "\\icon.jpg")
            or os.path.exists(instancePath + "\\icon.jpeg")
            or os.path.exists(instancePath + "\\icon.bmp")
            or os.path.exists(instancePath + "\\icon.ico")
            or os.path.exists(instancePath + "\\icon.icns")
            or os.path.exists(instancePath + "\\icon.gif")
        )

        versionsPath = os.path.join(instancePath, "versions")
        version = "Unknown"
        loader = "Vanilla"
        if os.path.exists(versionsPath):
            versions = [v for v in os.listdir(versionsPath) if os.path.isdir(os.path.join(versionsPath, v))]
            if versions:
                version = versions[0]
                for v in versions:
                    lower = v.lower()
                    if "fabric" in lower:
                        loader = "Fabric"
                        version = lower.replace("fabric-loader-", "")
                        break
                    elif "forge" in lower:
                        loader = "Forge"
                        break
                    elif "neoforge" in lower:
                        loader = "NeoForge"
                        break
        LibraryEntry(instanceMenu, instanceName, f"{loader} {version}", version, icon, instancePath)


class LibraryEntry:

    def __init__(self, parent, name: str, details: str, versionLaunched: str, icon: bool, instancePath: str):
        # Card
        self.frame = ntk.NTkFrame(parent,height=90,corner_radius=8,border_width=1,border_color=("#dcdfe3", "#24262b"), fg_color=("#1c1d21"))
        self.frame.pack(fill="x", padx=5, pady=6)
        self.frame.pack_propagate(False)

        # Icon
        self.iconFrame = ntk.NTkFrame(self.frame,width=64,height=64,corner_radius=6,fg_color=("#dcdfe3", "#1c1d21"))
        self.iconFrame.pack(side="left", padx=14, pady=13)
        self.iconFrame.pack_propagate(False)

        self.iconLabel = ntk.NTkLabel(self.iconFrame,text=name[:2].upper(),font=ntk.NTkFont(family=fontFamily, size=18, weight="bold"))
        self.iconLabel.place(relx=0.5, rely=0.5, anchor="center")

        if icon == True:
            for ext in [".png", ".jpg", ".jpeg", ".bmp", ".ico", ".icns", ".gif"]:
                path = os.path.join(instancePath, "icon" + ext)
                if os.path.exists(path):
                    iconPath = path
                    break
            if not "gif" in iconPath:
                self.iconLabel.configure(text = "",image=ntk.NTkImage(image.open(iconPath), size=(64, 64)))
            else:
                self.gifImage = ntk.NTkAnimatedImage(light_image=image.open(iconPath), dark_image=image.open(iconPath), size=(64, 64))
                self.iconLabel.configure(text="", image=self.gifImage)
                self.gifImage.start_animation()

        # Middle section
        self.infoFrame = ntk.NTkFrame(self.frame, fg_color="transparent")
        self.infoFrame.pack(side="left", fill="both", expand=True, padx=(4, 10), pady=12)

        self.titleLabel = ntk.NTkLabel(self.infoFrame,text=name,font=ntk.NTkFont(family=fontFamily, size=14, weight="bold"),anchor="w")
        self.titleLabel.pack(fill="x")

        self.detailsLabel = ntk.NTkLabel(self.infoFrame, text=details, font=ntk.NTkFont(family=fontFamily, size=11), anchor="w")
        self.detailsLabel.pack(fill="x", pady=(2, 6))

        if "Unknown" in details:
            try:
                self.detailsLabel.configure(
                    font=ntk.NTkFont(family="Standard Galactic Alpha Regular", size=11)
                )
            except Exception:
                self.detailsLabel.configure(font=ntk.NTkFont(family=fontFamily, size=11))
                pass
            self.detailsLabel.configure(text_color = "#b12525")

        # Right section
        self.actionFrame = ntk.NTkFrame(self.frame, width=120, fg_color="transparent")
        self.actionFrame.pack(side="right", fill="y", padx=14)
        self.actionFrame.pack_propagate(False)

        def playButtonCommand(name, versionLaunched):
            launchGame(name, versionLaunched)
            self.quitButton.pack(anchor="ne", pady=(12, 0))
            self.playButton.forget()
            threading.Thread(target=monitorMinecraft, args=(self,), daemon=True).start()

        self.playButton = ntk.NTkButton(self.actionFrame, text="Play", width=80, height=30,fg_color=accentColor, text_color="#111214", hover_color=accentHover, font=ntk.NTkFont(family=fontFamily, size=11, weight="bold"), command=lambda: playButtonCommand(name, versionLaunched))
        self.playButton.pack(anchor="ne", pady=(12, 0))

        def quitButtonCommand():
            quitGame()
            self.playButton.pack(anchor="ne", pady=(12, 0))
            self.quitButton.forget()

        self.quitButton = ntk.NTkButton(self.actionFrame, text="Quit", width=80, height=30,fg_color="#b12525", text_color="#111214", hover_color="#a14949", font=ntk.NTkFont(family=fontFamily, size=11, weight="bold"), command=lambda: quitButtonCommand())

        self.versionLabel = ntk.NTkLabel(self.actionFrame, text=details, font=ntk.NTkFont(family=fontFamily, size=10))
        self.versionLabel.pack(side="bottom", anchor="se", pady=(0, 8))
        if "Unknown" in details:
            self.versionLabel.configure(text_color="#b12525", text = "No version installed.")

    def onGameClosed(self):
        self.quitButton.forget()
        self.playButton.pack(anchor="ne", pady=(12, 0))


class InstallOption:
    def __init__(self, parent, title: str, desc: str, action=None):
        self.frame = ntk.NTkButton(parent, height=75, corner_radius=8, fg_color=("#1c1d21"), hover_color=("#1c1d21"))
        self.frame.pack(fill="x", padx=24, pady=6)
        self.frame.pack_propagate(False)

        # Icon placeholder
        self.iconFrame = ntk.NTkFrame(self.frame,width=28,height=28,fg_color=("#dcdfe3", "#2d3035"),corner_radius=6)
        self.iconFrame.pack(side="left", padx=16, pady=22)
        self.iconFrame.pack_propagate(False)

        # Text container
        self.textFrame = ntk.NTkFrame(self.frame, fg_color="transparent")
        self.textFrame.pack(side="left", fill="both", expand=True, padx=(16, 10), pady=12)

        self.titleLabel = ntk.NTkLabel(self.textFrame,text=title,font=ntk.NTkFont(family=fontFamily, size=13, weight="bold"),text_color=("#111214", "#ffffff"),anchor="w",)
        self.titleLabel.pack(fill="x")

        self.descriptionLabel = ntk.NTkLabel(self.textFrame,text=desc,font=ntk.NTkFont(family=fontFamily, size=11),text_color=("#555555", "#aaaaaa"),anchor="w",)
        self.descriptionLabel.pack(fill="x", pady=(2, 0))

        # Make whole card clickable
        if action:
            self.frame.bind("<Button-1>", lambda e: action())
            self.iconFrame.bind("<Button-1>", lambda e: action())
            self.textFrame.bind("<Button-1>", lambda e: action())
            self.titleLabel.bind("<Button-1>", lambda e: action())
            self.descriptionLabel.bind("<Button-1>", lambda e: action())


def CreateNewInstanceMenu1Open():
    createInstanceFrame1.place(relx=0.5, rely=0.5, relwidth=0.75, relheight=0.85, anchor="center")

def CreateNewInstanceMenu1Close():
    createInstanceFrame1.place_forget()

sidebar = ntk.NTkFrame(app, corner_radius=0, fg_color=bgSidebarColor, width=144)
sidebar.grid(row=0, column=0, sticky="ns")

title = ntk.NTkLabel(sidebar, text="Cubus Launcher", font=ntk.NTkFont(family=fontFamily, size=24, weight="bold"), fg_color="transparent", text_color=textMainColor)
title.pack(pady=10, padx=20, anchor="center", fill="x")

mainContentFrame = ntk.NTkTabview(app,fg_color="transparent",segmented_button_fg_color=bgSidebarColor,segmented_button_selected_color=accentColor,segmented_button_selected_hover_color=accentHover,)
mainContentFrame.grid(row=0, column=1, sticky="nsew", padx=10, pady=20)

sidebarLibraryButton = sidebarButton("Library")
sidebarExploreButton = sidebarButton("Explore")
sidebarAccountButton = sidebarButton("Account")
sidebarSettingsButton = sidebarButton("Settings")

for tab in ["Library", "Explore", "Account", "Settings"]:
    mainContentFrame.tab(tab).configure(fg_color=bgMainColor)

placeholder2 = ntk.NTkLabel(mainContentFrame.tab("Explore"), text="Explore Content", font=ntk.NTkFont(family=fontFamily, size=14), fg_color="transparent")
placeholder4 = ntk.NTkLabel(mainContentFrame.tab("Settings"), text="Settings Content", font=ntk.NTkFont(family=fontFamily, size=14), fg_color="transparent")
placeholder2.pack(pady=10, padx=20, anchor="center", fill="x")
placeholder4.pack(pady=10, padx=20, anchor="center", fill="x")

createInstanceButton = ntk.NTkButton(sidebarLibraryButton.tab, text="+", width=30, height=30, font=ntk.NTkFont(family=fontFamily, size=20, weight="bold"), command = CreateNewInstanceMenu1Open)
createInstanceButton.pack(pady=10, padx=20, anchor="ne")

instanceMenu = ntk.NTkScrollableFrame(sidebarLibraryButton.tab, corner_radius=0, fg_color="transparent")
instanceMenu.pack(pady=10, padx=20, anchor="center", fill="both", expand=True)
updateInstances()

accountMenu = ntk.NTkScrollableFrame(sidebarAccountButton.tab, corner_radius=0, fg_color="transparent")
accountMenu.pack(pady=10, padx=20, anchor="center", fill="both", expand=True)

accountNameLabel = ntk.NTkLabel(accountMenu, text = "You are not logged in.", font=ntk.NTkFont(family=fontFamily))
accountNameLabel.pack(pady=10, padx=20, anchor="center", fill="x")

loginButton = ntk.NTkButton(accountMenu, text="Login", command=lambda: login("online"), font=ntk.NTkFont(family=fontFamily))
loginButton.pack(pady=12, padx=10)

logoutButton = ntk.NTkButton(accountMenu, text="Logout", command=logout, fg_color="#F55858", hover_color="#FF8787",font=ntk.NTkFont(family=fontFamily))
logoutButton.pack(pady=12, padx=10)

mainContentFrame._segmented_button.grid_remove()

createInstanceFrame1 = ntk.NTkFrame(app, fg_color=bgCardColor, border_width=1, border_color=borderColor, corner_radius=12)

closeCreateNewInstanceMenu1Button = ntk.NTkButton(createInstanceFrame1, text="x", width=30, height=30, font=ntk.NTkFont(family=fontFamily, size=20, weight="bold"),fg_color = "transparent",hover_color = "#696969", command = CreateNewInstanceMenu1Close)
closeCreateNewInstanceMenu1Button.pack(pady=10, padx=20, anchor="ne")

createInstanceFrame1Header = ntk.NTkLabel(createInstanceFrame1, text="Create instance", font=ntk.NTkFont(family=fontFamily, size=18, weight="bold"))
createInstanceFrame1Header.pack(side="top")

customSetupButton = InstallOption(createInstanceFrame1, "Custom setup", "Start from scratch by picking a loader and game version.", lambda: print("Custom"))
modpackSetupButton = InstallOption(
    createInstanceFrame1,
    "Install modpack",
    "Browse modpacks on Modrinth.",
    lambda: (sidebarExploreButton.changeTab(), CreateNewInstanceMenu1Close()),
)
importButton = InstallOption(createInstanceFrame1, "Import instance", "Import an instance from a \".mrpack\" file.", importMrpack)

##          AUTOMATIC LOGIN ATTEMPT          ##

login("auto")

if restart == False:
    app.mainloop()

if restart == True:
    subprocess.run([sys.executable, __file__])
