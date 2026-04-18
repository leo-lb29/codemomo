"""
CLIENT - Rejoindre une session de parole
Usage : python client.py [adresse_host]
        python client.py 192.168.1.10
"""

import socket
import threading
import struct
import queue
import sys
import pyaudio

# ── Audio ──────────────────────────────────────────────────────────────────────
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100

pa = pyaudio.PyAudio()

# ── État global ────────────────────────────────────────────────────────────────
is_speaker = False
speaker_lock = threading.Lock()
audio_q = queue.Queue()
client_id = None


# ── Protocole identique au host ────────────────────────────────────────────────

def send(sock, ptype, data):
    if isinstance(data, str):
        data = data.encode()
    sock.sendall(struct.pack('!BI', ptype, len(data)) + data)


def recv(sock):
    def exact(n):
        buf = b''
        while len(buf) < n:
            chunk = sock.recv(n - len(buf))
            if not chunk:
                return None
            buf += chunk
        return buf
    header = exact(5)
    if not header:
        return None, None
    ptype, length = struct.unpack('!BI', header)
    return ptype, exact(length)


# ── Capture micro ──────────────────────────────────────────────────────────────

def mic_worker(sock):
    """Capture le micro en continu et envoie si c'est notre tour."""
    stream = pa.open(format=FORMAT, channels=CHANNELS, rate=RATE,
                     input=True, frames_per_buffer=CHUNK)
    try:
        while True:
            data = stream.read(CHUNK, exception_on_overflow=False)
            with speaker_lock:
                if is_speaker:
                    try:
                        send(sock, 0x02, data)
                    except Exception:
                        break
    except Exception:
        pass
    finally:
        stream.stop_stream()
        stream.close()


# ── Lecture audio reçu ────────────────────────────────────────────────────────

def playback_worker():
    """Joue les chunks audio reçus du host."""
    stream = pa.open(format=FORMAT, channels=CHANNELS, rate=RATE,
                     output=True, frames_per_buffer=CHUNK)
    try:
        while True:
            data = audio_q.get()
            if data is None:
                break
            stream.write(data)
    finally:
        stream.stop_stream()
        stream.close()


# ── Réception des messages du host ────────────────────────────────────────────

def receive_loop(sock):
    """Reçoit les messages du host : contrôle ou audio."""
    global is_speaker
    try:
        while True:
            ptype, data = recv(sock)
            if ptype is None:
                print("\n[!] Connexion perdue avec le host")
                break

            if ptype == 0x01:                       # message de contrôle
                msg = data.decode()  # type: ignore
                if msg == "SPEAKER:1":
                    with speaker_lock:
                        is_speaker = True
                    print("\n[+] C'est votre tour de parler !")
                elif msg == "SPEAKER:0":
                    with speaker_lock:
                        is_speaker = False
                    print("\n[-] En écoute...")

            elif ptype == 0x02:                     # chunk audio
                # Le host ne nous envoie pas notre propre audio,
                # donc on joue tout ce qu'on reçoit.
                audio_q.put(data)

    except Exception as e:
        print(f"\n[!] Erreur : {e}")
    finally:
        audio_q.put(None)


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    host_addr = sys.argv[1] if len(sys.argv) > 1 else '127.0.0.1'

    # Connexion au host
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect((host_addr, 5001))
    except ConnectionRefusedError:
        print(f"[!] Impossible de se connecter à {host_addr}:5001")
        return

    print(f"[*] Connecté à {host_addr}:5001")

    # Handshake
    send(sock, 0x01, "coucou")
    ptype, data = recv(sock)
    client_id = int(data.decode().split(':')[1])  # type: ignore
    print(f"[+] Vous êtes le Client {client_id}")
    print("[*] En attente que l'host vous donne la parole...\n")

    # Démarrer les threads
    threading.Thread(target=playback_worker,        daemon=True).start()
    threading.Thread(target=mic_worker, args=(sock,), daemon=True).start()

    try:
        receive_loop(sock)          # bloquant jusqu'à déconnexion
    except KeyboardInterrupt:
        pass
    finally:
        sock.close()
        print("[-] Déconnecté")


if __name__ == '__main__':
    main()
