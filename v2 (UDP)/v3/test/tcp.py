import socket
import pyaudio
import threading

# Serveur TCP qui accepte les connexions
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.bind(("127.0.0.1", 5000))
server_socket.listen(1)

capture_micro = pyaudio.PyAudio()
stream = capture_micro.open(
    format=pyaudio.paInt16,
    channels=1,
    rate=44100,
    input=True,
    frames_per_buffer=1024
)

client_socket = None

def envoyer_audio():
    global client_socket
    while True:
        if client_socket is None:
            client_socket, addr = server_socket.accept()
        try:
            data = stream.read(1024, exception_on_overflow=False)
            client_socket.sendall(data)
        except (BrokenPipeError, ConnectionResetError):
            client_socket = None

threading.Thread(target=envoyer_audio, daemon=True).start()
threading.Event().wait()