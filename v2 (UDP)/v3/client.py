import socket
import pyaudio

# Client UDP
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock.bind(("127.0.0.1", 5000))

audio = pyaudio.PyAudio()
stream = audio.open(format=pyaudio.paInt16, channels=1,
                    rate=44100, output=True, frames_per_buffer=1024)

while True:
    try:
        data, addr = sock.recvfrom(1024)
        stream.write(data)
    except KeyboardInterrupt:
        break

sock.close()
stream.stop_stream()
stream.close()
audio.terminate()
