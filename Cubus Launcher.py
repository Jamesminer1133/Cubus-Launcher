import minecraft_launcher_lib
import subprocess
import neotkinter as ntk
import os
from tkinter.filedialog import askopenfile as openFile
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

##          INITIALIZE          ##

subprocess.run("cls", shell=True)

print("Initializing application...")

sys.stdout.reconfigure(encoding="utf-8")

if not os.path.exists(
    "C:\\Users\\" + str(os.getlogin()) + "\\AppData\\Roaming\\CubusLauncher"
):
    os.mkdir("C:\\Users\\" + str(os.getlogin()) + "\\AppData\\Roaming\\CubusLauncher")

if not os.path.exists(
    "C:\\Users\\" + str(os.getlogin()) + "\\AppData\\Roaming\\CubusLauncher\\appData"
):
    os.mkdir(
        "C:\\Users\\"
        + str(os.getlogin())
        + "\\AppData\\Roaming\\CubusLauncher\\appData"
    )

path = os.path.join(
    "C:\\Users\\" + str(os.getlogin()) + "\\AppData\\Roaming\\CubusLauncher"
)

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


def login(mode):
    global authCode
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
            print("Automatic login successful! Welcome " + accData["name"])
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
            with open(str(path) + "\\appData\\accountData.json", "w") as f:
                json.dump(accData, f, indent=4)
            print("Saved account data for automatic login.")
        except Exception as e:
            loggedIn = False
            print("Login failed:", e)


def logout():
    global loggedIn
    loggedIn = False
    accData.clear()
    if os.path.exists(str(path) + "\\appData\\accountData.json"):
        os.remove(str(path) + "\\appData\\accountData.json")
    print("Successfully Logged out!")


def selectModLoader(value):
    global modLoader
    modLoader = value.lower()


def setVersionBox(version):
    global versionChoice
    versionChoice = version
    versionMenu.set(version)


def setInstanceBox(instance):
    global instanceChoice
    global modLoader
    global instanceVersion
    instanceChoice = instance
    instancesMenu.set(instance)
    vers = [
        name
        for name in os.listdir(
            str(minecraftDirectory) + "\\instances\\" + instanceChoice + "\\versions\\"
        )
        if os.path.isdir(
            os.path.join(
                str(minecraftDirectory)
                + "\\instances\\"
                + instanceChoice
                + "\\versions\\",
                name,
            )
        )
    ]
    instanceVersion = vers[0]
    if len(vers) > 1:
        if "fabric" in vers[1].lower():
            modLoader = "fabric"
        elif "forge" in vers[1].lower():
            modLoader = "forge"
        elif "neoforge" in vers[1].lower():
            modLoader = "neoforge"


def importMrpack():
    global restart
    global minecraftDirectory
    path = openFile(
        initialdir=str(
            os.path.join("C:\\Users\\" + str(os.getlogin()) + "\\Downloads")
        ),
        title="Select a Modrinth Pack",
        filetypes=[("Modrinth Packs", "*.mrpack")],
    ).name
    name = minecraft_launcher_lib.mrpack.get_mrpack_information(path)["name"]

    callback = {"setStatus": setStatus, "setProgress": setProgress, "setMax": setMax}

    minecraft_launcher_lib.mrpack.install_mrpack(
        path,
        str(minecraftDirectory) + "\\instances\\" + name,
        callback=callback,
        mrpack_install_options=mrpackInstallConfig,
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


def launchGame():
    global demoChoice
    global demoValue
    global versionChoice
    global minecraftDirectory
    global instanceVersion
    global instanceChoice
    global path
    global loggedIn

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
    data["launcherName"] = "CubusLauncher"
    data["jvmArguments"] = ["-Xmx" + ramTextbox.get("0.0", "end-1c") + "G"]

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
            str(instanceVersion), minecraftDirectory, data
        )

    ##          LAUNCH          ##

    print(
        "Launching: "
        + str(instanceChoice)
        + " with game version: "
        + str(instanceVersion)
        + " at the path: "
        + str(minecraftDirectory)
    )
    minecraftDirectory = os.path.join(
        "C:\\Users\\" + str(os.getlogin()) + "\\AppData\\Roaming\\CubusLauncher"
    )
    subprocess.Popen(minecraftCommand, cwd=minecraftDirectory)


def createInstance():
    global versionToInstall
    global versionChoice
    global minecraftDirectory
    global modLoader
    global instances
    global restart

    versionChoice = versionMenu.get()
    minecraftDirectory = os.path.join(
        "C:\\Users\\" + str(os.getlogin()) + "\\AppData\\Roaming\\CubusLauncher"
    )

    if not os.path.exists(str(minecraftDirectory) + "\\instances\\"):
        os.mkdir(str(minecraftDirectory) + "\\instances\\")

    instanceName = instanceTextbox.get("0.0", "end-1c").strip()
    instancePath = os.path.join(minecraftDirectory, "instances", instanceName)

    if os.path.exists(instancePath):
        print(
            "Instance with that name already exists, reinstalling Minecraft Version "
            + versionChoice
            + " to that instance."
        )
        versionsPath = os.path.join(instancePath, "versions")
        if os.path.exists(versionsPath):
            shutil.rmtree(versionsPath)
        os.makedirs(versionsPath, exist_ok=True)
    else:
        os.makedirs(instancePath, exist_ok=True)

    minecraftDirectory = instancePath

    if versionChoice == "latest":
        versionChoice = minecraft_launcher_lib.utils.get_latest_version()["release"]

    if versionChoice == "snapshot":
        versionChoice = minecraft_launcher_lib.utils.get_latest_version()["snapshot"]

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
        + instanceTextbox.get("0.0", "end-1c")
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


##          GUI          ##

app = ntk.NTk()
app.geometry("400x500")
app.title("Cubus Launcher")

ntk.set_appearance_mode("system")

label = ntk.NTkLabel(app, text="Cubus Launcher", fg_color="transparent")
label.pack(pady=0, padx=10)

tabview = ntk.NTkTabview(master=app)
tabview.add("Play")
tabview.add("Create Instance")
tabview.add("Import Instance")
tabview.add("Account")
tabview.pack(padx=20, pady=20)

playTab = ntk.NTkScrollableFrame(tabview.tab("Play"), width=400, height=1000)
playTab.pack(pady=12, padx=10)
createTab = ntk.NTkScrollableFrame(
    tabview.tab("Create Instance"), width=400, height=1000
)
createTab.pack(pady=12, padx=10)
importTab = ntk.NTkScrollableFrame(
    tabview.tab("Import Instance"), width=400, height=1000
)
importTab.pack(pady=12, padx=10)
accountTab = ntk.NTkScrollableFrame(tabview.tab("Account"), width=400, height=1000)
accountTab.pack(pady=12, padx=10)

window = ntk.NTkScrollableFrame(app, width=400, height=1000)

label = ntk.NTkLabel(createTab, text="Instance", fg_color="transparent")
label.pack(pady=0, padx=10)

instanceTextbox = ntk.NTkTextbox(createTab)
instanceTextbox.insert("0.0", "Instance Name")
instanceTextbox.configure(height=20, width=200)
instanceTextbox.pack(pady=12, padx=10)

instancesMenu = ntk.NTkComboBox(playTab, command=setInstanceBox)
instancesMenu.set("Select Instance")
instancesMenu.configure(values=instances)
ntk.NTkScrollableDropdown(
    instancesMenu, values=instances, width=200, command=setInstanceBox
)
instancesMenu.pack(pady=12, padx=10)

label = ntk.NTkLabel(createTab, text="Version", fg_color="transparent")
label.pack(pady=0, padx=10)

versionMenu = ntk.NTkComboBox(createTab, command=setVersionBox)
versionMenu.set("Select Version")
versionList = []
for version in minecraft_launcher_lib.utils.get_version_list():
    versionList.append(version["id"])
versionMenu.configure(values=versionList)
ntk.NTkScrollableDropdown(
    versionMenu, values=versionList, width=200, command=setVersionBox
)
versionMenu.pack(pady=12, padx=10)

label = ntk.NTkLabel(createTab, text="Modloader", fg_color="transparent")
label.pack(pady=0, padx=10)

modLoaderMultiButton = ntk.NTkSegmentedButton(
    createTab, values=["None", "Fabric", "Forge", "NeoForge"], command=selectModLoader
)
modLoaderMultiButton.set("None")
modLoaderMultiButton.pack(pady=12, padx=10)

label = ntk.NTkLabel(playTab, text="R.A.M. Assignment (GB)", fg_color="transparent")
label.pack(pady=0, padx=10)

ramTextbox = ntk.NTkTextbox(playTab)
ramTextbox.insert("0.0", str(ramRecommendation))
ramTextbox.configure(height=20)
ramTextbox.pack(pady=12, padx=10)

launchButton = ntk.NTkButton(playTab, text="Launch Game", command=launchGame)
launchButton.pack(pady=12, padx=10)

importMrpackButton = ntk.NTkButton(
    importTab, text="Import Modrinth Instance (Mrpack)", command=importMrpack
)
importMrpackButton.pack(pady=12, padx=10)

createButton = ntk.NTkButton(createTab, text="Create Instance", command=createInstance)
createButton.pack(pady=12, padx=10)

loginButton = ntk.NTkButton(accountTab, text="Login", command=lambda: login("online"))
loginButton.pack(pady=12, padx=10)

overrideLoginButton = ntk.NTkButton(
    accountTab, text="Logout", command=logout, fg_color="#F55858", hover_color="#FF8787"
)
overrideLoginButton.pack(pady=12, padx=10)


##          AUTOMATIC LOGIN ATTEMPT          ##

login("auto")

if restart == False:
    app.mainloop()

if restart == True:
    subprocess.run([sys.executable, __file__])
