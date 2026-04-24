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
