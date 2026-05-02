import queue
import threading
import pyaudio


CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
PYAUDIO_INSTANCE = pyaudio.PyAudio()
STRUCTURE_PROTOCOL = "!BI"
HAUT_PARLEUR = threading.Lock()
QUEUE_AUDIO = queue.Queue()
PORT_CONTROL = 5000
PORT_AUDIO_OUT = 5002
PORT_AUDIO_IN = 5003
BROADCAST_ADDR = "192.168.1.255"