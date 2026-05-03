import queue
import threading
import pyaudio


CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
PYAUDIO_INSTANCE = pyaudio.PyAudio()
HAUT_PARLEUR = threading.Lock()
QUEUE_AUDIO = queue.Queue()
PORT_CONTROL = 5000
PORT_AUDIO_BROADCAST = 5001
PORT_AUDIO_CLIENT = 5002
BROADCAST_ADDR = "192.168.1.255"

TITLE_CLIENT = "PRJ1401"
SUB_TITLE_CLIENT = "Client"
CSS_CLIENT = """
    #status-box {
        height: 75%;
        content-align: center middle;
        background: $boost;
        border: solid $surface;
        text-style: bold;
    }
    .status-listening {
        color: gray;
        border: solid gray;
    }
    .status-speaking {
        color: #00ff00;
        background: rgba(0, 255, 0, 0.1);
        border: solid #00ff00;
    }
    .status-disconnected {
        color: red;
        border: solid red;
    }
        #layout-principal { layout: horizontal; }
        #menu-gauche { width: 25%; padding: 1 2 ; }
        #zone-droite { width: 75%; layout: vertical; }
        #zone-logs { height: 100%; }
        Button { width: 100%; margin-bottom: 1; }
        #container-prenom { layout: vertical; align: center middle; border: solid $primary; padding: 2 4; }
        #label-prenom { margin-bottom: 1;  text-align: center; }
        #prenom-input { margin-bottom: 1; width: 100%; }
        #error-prenom { color: $error; margin-bottom: 1; text-align: center; }
        #container-main { display: none; }
    """


TITLE_HOST = "PRJ1401"
SUB_TITLE_HOST = "Maître de conférence"
CSS_HOST = """
        #layout-principal { layout: horizontal; }
        #layout-liste { layout: horizontal; height: 70%; }
        #menu-gauche { width: 25%; padding: 1 2 ; }
        #zone-droite { width: 75%; layout: vertical; }
        #zone-gauche { width: 50%; layout: vertical; }
        #zone-droite-droite { width: 50%; layout: vertical; }
        #label-clients { height: 1; text-align: center; }
        #label-demandes { height: 1; text-align: center; }
        #liste-clients { height: 1fr; }
        #liste-demandes { height: 1fr; }
        #zone-logs { height: 30%; }
        Button { width: 100%; margin-bottom: 1; }
        """


CSS_CONFIRM_SPEAK_SCREEN = """
    Screen {
        align: center middle;
    }

    #dialog {
        width: 60;
        height: 10;
        border: solid $primary;
        background: $panel;
        layout: vertical;
    }

    #dialog-title {
        text-align: center;
        margin-bottom: 1;
    }

    #dialog-buttons {
        layout: horizontal;
        height: 3;
        align: center middle;
    }

    .dialog-btn {
        width: 20;
        margin: 0 1;
    }
    """
