import socket
import pyaudio
import threading

socket_signal = socket.socket(
    socket.AF_INET, socket.SOCK_DGRAM, proto=socket.IPPROTO_UDP)
socket_signal.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
capture_micro = pyaudio.PyAudio()
stream = capture_micro.open(
    format=pyaudio.paInt16,
    channels=1,
    rate=44100,
    input=True,
    frames_per_buffer=1024
)


def envoyer_audio():
    while True:
        data = stream.read(512, exception_on_overflow=False)
        socket_signal.sendto(data, ("192.168.1.255", 5001))


threading.Thread(target=envoyer_audio, daemon=True).start()
threading.Event().wait()