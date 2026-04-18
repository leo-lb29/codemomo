import socket
import struct
import threading
import queue
from config import CHANNELS, CHUNK, FORMAT, PYAUDIO_INSTANCE, STRUCTURE_PROTOCOL, RATE, HAUT_PARLEUR, QUEUE_AUDIO
from utils.protocol import send_message, recv_message
from utils.log import _log_error, _log_grey, _log_info, _log_success

# ── État global du HOST ────────────────────────────────────────────────────────
HOST_CLIENTS = []
HOST_CLIENTS_LOCK = threading.Lock()
# Utiliser un dict pour pouvoir modifier sans global
HOST_SPEAKER_STATE: dict = {"id": None}
HOST_SPEAKER_LOCK = threading.Lock()
HOST_AUDIO_QUEUE = queue.Queue()
HOST_STOP_EVENT = threading.Event()


def _create_input_stream():
    return PYAUDIO_INSTANCE.open(
        format=FORMAT, channels=CHANNELS, rate=RATE,
        input=True, frames_per_buffer=CHUNK
    )


def _create_output_stream():
    return PYAUDIO_INSTANCE.open(
        format=FORMAT, channels=CHANNELS, rate=RATE,
        output=True, frames_per_buffer=CHUNK
    )


def _close_stream(stream):
    try:
        stream.stop_stream()
        stream.close()
    except Exception:
        pass


def _update_speaker_status(app, is_speaker):
    with HAUT_PARLEUR:
        app.is_speaker = is_speaker
    app.call_from_thread(app.update_status, is_speaker)


def _handle_control_message(app, msg):
    if msg == "SPEAKER:1":
        _update_speaker_status(app, True)
        _log_success(app, "C'est votre tour de parler !")
    elif msg == "SPEAKER:0":
        _update_speaker_status(app, False)
        _log_grey(app, "En écoute...")


def _handle_audio_message(data):
    QUEUE_AUDIO.put(data)



def mic_worker(sock, app):
    stream = _create_input_stream()
    try:
        while True:
            data = stream.read(CHUNK, exception_on_overflow=False)

            with HAUT_PARLEUR:
                if app.is_speaker:
                    try:
                        send_message(sock, 0x02, data)
                    except Exception:
                        break
    except Exception:
        print("Erreur avec le worker micro")
    finally:
        _close_stream(stream)


def playback_worker():
    stream = _create_output_stream()
    try:
        while True:
            data = QUEUE_AUDIO.get()
            if data is None:
                break
            stream.write(data)
    except Exception:
        print("Erreur avec le worker playback")
    finally:
        _close_stream(stream)


def receive_loop(sock, app):
    try:
        while True:
            ptype, data = recv_message(sock)
            if ptype is None:
                _log_error(app, "Connexion perdue avec le host")
                break

            if ptype == 0x01:
                if data is None:
                    continue
                msg = data.decode()
                _handle_control_message(app, msg)

            elif ptype == 0x02:
                _handle_audio_message(data)

    except Exception as e:
        _log_error(app, f"Erreur de réception : {e}")
    finally:
        QUEUE_AUDIO.put(None)


def _connect_to_host(sock, host_addr, app):
    try:
        sock.connect((host_addr, 5001))
        _log_info(app, f"Connecté à {host_addr}:5001")
        return True
    except ConnectionRefusedError:
        _log_error(app, f"Impossible de se connecter à {host_addr}:5001")
        return False


def _perform_handshake(sock, app):
    """Effectue le handshake avec le host."""
    send_message(sock, 0x01, "coucou")
    ptype, data = recv_message(sock)
    if ptype is not None and data:
        client_id = int(data.decode().split(':')[1])
        _log_success(app, f"Vous êtes le Client {client_id}")
        _log_info(app, "En attente que l'host vous donne la parole...\n")
        return True
    return False


def _start_audio_workers(sock, app):
    threading.Thread(target=playback_worker, daemon=True).start()
    threading.Thread(target=mic_worker, args=(sock, app), daemon=True).start()


def connect_and_run(app, host_addr):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        if not _connect_to_host(sock, host_addr, app):
            return

        if not _perform_handshake(sock, app):
            return

        _start_audio_workers(sock, app)
        receive_loop(sock, app)

    except Exception as e:
        _log_error(app, f"Erreur lors du handshake: {e}")
    finally:
        sock.close()


# ── Fonctions HOST ────────────────────────────────────────────────────────────

def broadcast(data, exclude_id=None):
    """Diffuse les données audio à tous les clients sauf un."""
    pkt = struct.pack(STRUCTURE_PROTOCOL, 0x02, len(data)) + data
    with HOST_CLIENTS_LOCK:
        for sock, _, cid in HOST_CLIENTS:
            if cid != exclude_id:
                try:
                    sock.sendall(pkt)
                except Exception:
                    pass


def notify_speaker(new_id):
    """Notifie tous les clients du changement de speaker."""
    with HOST_CLIENTS_LOCK:
        for sock, _, cid in HOST_CLIENTS:
            try:
                send_message(sock, 0x01, "SPEAKER:1" if cid ==
                             new_id else "SPEAKER:0")
            except Exception:
                pass


def set_speaker_host(new_id, app):
    """Change le speaker actuel et notifie les clients."""
    if HOST_SPEAKER_STATE["id"] == -1 and new_id != -1:
        HOST_STOP_EVENT.set()

    with HOST_SPEAKER_LOCK:
        HOST_SPEAKER_STATE["id"] = new_id

    notify_speaker(new_id)

    if new_id == -1:
        app.add_log("[bold red]🔴 MICRO HOST OUVERT[/]")
    elif new_id is None:
        app.add_log("[bold grey]⏹️ Micro fermé[/]")
    else:
        app.add_log(f"[bold green][+] La parole est au Client {new_id}[/]")

    app.refresh_clients_table()


def handle_client(sock, addr, cid, app):
    """Gère un client connecté."""
    try:
        while True:
            ptype, data = recv_message(sock)
            if ptype is None:
                break
            if ptype == 0x02:
                with HOST_SPEAKER_LOCK:
                    if HOST_SPEAKER_STATE["id"] == cid:
                        broadcast(data, exclude_id=cid)
                        HOST_AUDIO_QUEUE.put(data)
    except Exception:
        pass
    finally:
        with HOST_CLIENTS_LOCK:
            HOST_CLIENTS[:] = [(s, a, i)
                               for s, a, i in HOST_CLIENTS if i != cid]
        sock.close()
        app.call_from_thread(
            app.add_log, f"[bold yellow][-] Client {cid} déconnecté[/]")
        app.call_from_thread(app.refresh_clients_table)


def playback_worker_host():
    """Joue les chunks audio reçus depuis le speaker."""
    stream = PYAUDIO_INSTANCE.open(
        format=FORMAT, channels=CHANNELS, rate=RATE,
        output=True, frames_per_buffer=CHUNK
    )
    try:
        while True:
            data = HOST_AUDIO_QUEUE.get()
            if data is None:
                break
            stream.write(data)
    finally:
        _close_stream(stream)


def host_speak(app):
    """Permet au host de parler et diffuse son audio."""
    stream = _create_input_stream()
    try:
        while not HOST_STOP_EVENT.is_set():
            with HOST_SPEAKER_LOCK:
                if HOST_SPEAKER_STATE["id"] != -1:
                    break
            data = stream.read(CHUNK, exception_on_overflow=False)
            broadcast(data)
    finally:
        _close_stream(stream)
        HOST_STOP_EVENT.clear()
        app.call_from_thread(app.add_log, "[bold grey]Micro host arrêté.[/]")


def server_main(app):
    """Boucle principale du serveur socket."""
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(('0.0.0.0', 5001))
    server.listen(10)
    app.call_from_thread(
        app.add_log, "[bold cyan][*] HOST démarré sur le port 5001[/]")

    client_id_counter = 0
    try:
        while True:
            sock, addr = server.accept()
            ptype, data = recv_message(sock)
            if ptype != 0x01 or data is None or data.decode() != "coucou":
                sock.close()
                continue

            cid = client_id_counter
            client_id_counter += 1

            with HOST_CLIENTS_LOCK:
                HOST_CLIENTS.append((sock, addr, cid))

            send_message(sock, 0x01, f"ID:{cid}")
            app.call_from_thread(
                app.add_log, f"[bold green][+] Client {cid} connecté depuis {addr[0]}[/]")
            app.call_from_thread(app.refresh_clients_table)

            threading.Thread(target=handle_client, args=(
                sock, addr, cid, app), daemon=True).start()
    except Exception as e:
        app.call_from_thread(app.add_log, f"[bold red]Erreur serveur: {e}[/]")
    finally:
        server.close()
