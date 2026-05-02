import socket
import pyaudio

# Client UDP
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, proto=socket.IPPROTO_UDP)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock.bind(("0.0.0.0", 5002))
print("Client UDP en attente sur 0.0.0.0:5002")

audio = pyaudio.PyAudio()
stream = audio.open(format=pyaudio.paInt16, channels=1,
                    rate=44100, output=True, frames_per_buffer=1024)

while True:
    try:
        data, addr = sock.recvfrom(1024)
        if not data:
            break
        stream.write(data)
    except KeyboardInterrupt:
        break

sock.close()
stream.stop_stream()
stream.close()
audio.terminate()
