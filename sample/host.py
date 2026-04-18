"""
HOST - Serveur de parole
Usage : python host.py

Commandes console :
  0, 1, 2 ...  → donne la parole au client N
  h            → l'host parle (Entrée pour s'arrêter)
  l            → liste les clients
"""

import socket
import threading
import struct
import queue
import pyaudio

# ── Audio ──────────────────────────────────────────────────────────────────────
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100

pa = pyaudio.PyAudio()

# ── État global ────────────────────────────────────────────────────────────────
clients = []        # [(socket, adresse, client_id), ...]
clients_lock = threading.Lock()
speaker_id = None      # None=personne  -1=host  N=client_id
speaker_lock = threading.Lock()
audio_q = queue.Queue()   # Audio reçu → lecture locale host
host_stop_event = threading.Event()  # Signal pour arrêter host_speak()


# ── Protocole : [1B type][4B longueur][data] ───────────────────────────────────
# type 0x01 = contrôle (texte)   type 0x02 = audio (bytes bruts)

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


# ── Broadcast audio ────────────────────────────────────────────────────────────

def broadcast(data, exclude_id=None):
    """Envoie un chunk audio à tous les clients sauf l'émetteur."""
    pkt = struct.pack('!BI', 0x02, len(data)) + data
    with clients_lock:
        for sock, _, cid in clients:
            if cid != exclude_id:
                try:
                    sock.sendall(pkt)
                except Exception:
                    pass


def notify_speaker(new_id):
    """Informe chaque client s'il est speaker ou non."""
    with clients_lock:
        for sock, _, cid in clients:
            try:
                send(sock, 0x01, "SPEAKER:1" if cid == new_id else "SPEAKER:0")
            except Exception:
                pass


def set_speaker(new_id):
    global speaker_id

    # Si le host parlait, arrêter son micro
    if speaker_id == -1 and new_id != -1:
        host_stop_event.set()

    with speaker_lock:
        speaker_id = new_id
    notify_speaker(new_id)
    if new_id == -1:
        print("\n🎤 ═══════════════════════════════════════════════════════")
        print("🔴 [HOST] MICRO OUVERT - Vous parlez maintenant")
        print("   Appuyez sur Entrée pour terminer")
        print("═══════════════════════════════════════════════════════\n")
    elif new_id is None:
        print("⏹️  [*] Micro fermé - Plus de speaker")
    else:
        with clients_lock:
            found = next((f"{a}" for s, a, c in clients if c == new_id), "?")
        print(f"[+] Client {new_id} ({found}) peut parler")


# ── Gestion d'un client ────────────────────────────────────────────────────────

def handle_client(sock, addr, cid):
    try:
        while True:
            ptype, data = recv(sock)
            if ptype is None:
                break
            if ptype == 0x02:               # chunk audio reçu
                with speaker_lock:
                    if speaker_id == cid:   # n'accepter que si c'est son tour
                        broadcast(data, exclude_id=cid)
                        audio_q.put(data)   # l'host entend aussi
    except Exception:
        pass
    finally:
        with clients_lock:
            clients[:] = [(s, a, i) for s, a, i in clients if i != cid]
        sock.close()
        print(f"[-] Client {cid} ({addr}) déconnecté")


# ── Lecture audio côté host ────────────────────────────────────────────────────

def playback_worker():
    stream = pa.open(format=FORMAT, channels=CHANNELS, rate=RATE,
                     output=True, frames_per_buffer=CHUNK)
    while True:
        data = audio_q.get()
        if data is None:
            break
        stream.write(data)
    stream.stop_stream()
    stream.close()


# ── L'host parle ──────────────────────────────────────────────────────────────

def host_speak():
    stream = pa.open(format=FORMAT, channels=CHANNELS, rate=RATE,
                     input=True, frames_per_buffer=CHUNK)
    try:
        while not host_stop_event.is_set():
            with speaker_lock:
                if speaker_id != -1:    # quelqu'un a repris la main
                    break
            data = stream.read(CHUNK, exception_on_overflow=False)
            broadcast(data)             # envoie à tous les clients
    finally:
        stream.stop_stream()
        stream.close()
        host_stop_event.clear()  # réinitialiser pour la prochaine fois


# ── Console de l'host ─────────────────────────────────────────────────────────

def console():
    print("Commandes : [numéro] donner parole · [h] parler · [l] lister\n")
    host_speak_thread = None

    while True:
        try:
            prompt = ">>> "
            with speaker_lock:
                if speaker_id == -1:
                    prompt = "🎤 >>> "
                elif speaker_id is not None:
                    prompt = f"📢 [{speaker_id}] >>> "
            cmd = input(prompt).strip()
        except EOFError:
            break

        if cmd == 'h':
            if host_speak_thread is None or not host_speak_thread.is_alive():
                set_speaker(-1)
                host_stop_event.clear()
                host_speak_thread = threading.Thread(
                    target=host_speak, daemon=True)
                host_speak_thread.start()
            else:
                print("[*] Host parle déjà")

        elif cmd == '' and host_speak_thread and host_speak_thread.is_alive():
            # Entrée seule quand le host parle → arrêter le micro
            host_stop_event.set()
            host_speak_thread.join(timeout=0.5)
            set_speaker(None)
            host_speak_thread = None
            print("")

        elif cmd == 'l':
            with clients_lock:
                if not clients:
                    print("  (aucun client)")
                for i, (_, addr, cid) in enumerate(clients):
                    tag = " ← parle" if speaker_id == cid else ""
                    print(f"  [{i}] Client {cid}  {addr}{tag}")

        elif cmd.isdigit():
            idx = int(cmd)
            with clients_lock:
                if idx < len(clients):
                    cid = clients[idx][2]
                else:
                    print(f"[!] Index {idx} invalide")
                    continue
            set_speaker(cid)

        elif cmd != '':
            print("[!] Commande inconnue")


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(('0.0.0.0', 5001))
    server.listen(10)
    print("[*] HOST démarré sur le port 5001\n")

    threading.Thread(target=playback_worker, daemon=True).start()
    threading.Thread(target=console,         daemon=True).start()

    client_id_counter = 0
    try:
        while True:
            sock, addr = server.accept()

            # Handshake : attendre "coucou"
            ptype, data = recv(sock)
            if ptype != 0x01 or data.decode() != "coucou":  # type: ignore
                sock.close()
                continue

            cid = client_id_counter
            client_id_counter += 1

            with clients_lock:
                clients.append((sock, addr, cid))

            send(sock, 0x01, f"ID:{cid}")
            print(f"[+] Client {cid} connecté depuis {addr}")

            threading.Thread(target=handle_client, args=(sock, addr, cid),
                             daemon=True).start()

    except KeyboardInterrupt:
        print("\n[*] Arrêt du serveur")
    finally:
        audio_q.put(None)
        server.close()


if __name__ == '__main__':
    main()
