import socket
import threading
import struct
import queue
import pyaudio
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Header, Footer, Button, DataTable, RichLog

# ── Audio (Identique) ──────────────────────────────────────────────────────────
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
pa = pyaudio.PyAudio()

# ── État global (Identique) ────────────────────────────────────────────────────
clients = []        # [(sock, addr, cid)]
clients_lock = threading.Lock()
speaker_id = None
speaker_lock = threading.Lock()
audio_q = queue.Queue()
host_stop_event = threading.Event()

# ── Fonctions Réseau (Identiques) ──────────────────────────────────────────────


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


def broadcast(data, exclude_id=None):
    pkt = struct.pack('!BI', 0x02, len(data)) + data
    with clients_lock:
        for sock, _, cid in clients:
            if cid != exclude_id:
                try:
                    sock.sendall(pkt)
                except:
                    pass


def notify_speaker(new_id):
    with clients_lock:
        for sock, _, cid in clients:
            try:
                send(sock, 0x01, "SPEAKER:1" if cid == new_id else "SPEAKER:0")
            except:
                pass

# ── Modifications Backend pour communiquer avec l'UI ──────────────────────────


def set_speaker(new_id, app):
    global speaker_id
    if speaker_id == -1 and new_id != -1:
        host_stop_event.set()

    with speaker_lock:
        speaker_id = new_id
    notify_speaker(new_id)

    # 💡 CORRECTION : Plus de call_from_thread ici !
    # Nous sommes déjà dans le thread de l'UI quand on clique sur un bouton.
    if new_id == -1:
        app.add_log("[bold red]🔴 MICRO HOST OUVERT[/]")
    elif new_id is None:
        app.add_log("[bold grey]⏹️ Micro fermé[/]")
    else:
        app.add_log(f"[bold green][+] La parole est au Client {new_id}[/]")

    app.refresh_clients_table()


def handle_client(sock, addr, cid, app):
    try:
        while True:
            ptype, data = recv(sock)
            if ptype is None:
                break
            if ptype == 0x02:
                with speaker_lock:
                    if speaker_id == cid:
                        broadcast(data, exclude_id=cid)
                        audio_q.put(data)
    except Exception:
        pass
    finally:
        with clients_lock:
            clients[:] = [(s, a, i) for s, a, i in clients if i != cid]
        sock.close()
        app.call_from_thread(
            app.add_log, f"[bold yellow][-] Client {cid} déconnecté[/]")
        app.call_from_thread(app.refresh_clients_table)


def playback_worker():
    stream = pa.open(format=FORMAT, channels=CHANNELS,
                     rate=RATE, output=True, frames_per_buffer=CHUNK)
    while True:
        data = audio_q.get()
        if data is None:
            break
        stream.write(data)
    stream.stop_stream()
    stream.close()


def host_speak(app):
    stream = pa.open(format=FORMAT, channels=CHANNELS,
                     rate=RATE, input=True, frames_per_buffer=CHUNK)
    try:
        while not host_stop_event.is_set():
            with speaker_lock:
                if speaker_id != -1:
                    break
            data = stream.read(CHUNK, exception_on_overflow=False)
            broadcast(data)
    finally:
        stream.stop_stream()
        stream.close()
        host_stop_event.clear()
        app.call_from_thread(app.add_log, "[bold grey]Micro host arrêté.[/]")


def server_main(app):
    """Boucle principale du serveur socket, lancée dans un thread séparé."""
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
            ptype, data = recv(sock)
            if ptype != 0x01 or data.decode() != "coucou":
                sock.close()
                continue

            cid = client_id_counter
            client_id_counter += 1

            with clients_lock:
                clients.append((sock, addr, cid))

            send(sock, 0x01, f"ID:{cid}")
            app.call_from_thread(
                app.add_log, f"[bold green][+] Client {cid} connecté depuis {addr[0]}[/]")
            app.call_from_thread(app.refresh_clients_table)

            threading.Thread(target=handle_client, args=(
                sock, addr, cid, app), daemon=True).start()
    except Exception as e:
        app.call_from_thread(app.add_log, f"[bold red]Erreur serveur: {e}[/]")
    finally:
        server.close()

# ── Interface Textual ──────────────────────────────────────────────────────────


class HostDashboard(App):
    TITLE = "PRJ1401"
    SUB_TITLE = "Host"
    
    CSS = """
    #layout-principal { layout: horizontal; }
    #menu-gauche { width: 25%; padding: 1 2 ; }
    #zone-droite { width: 75%; layout: vertical; }
    #liste-clients { height: 70%;}
    #zone-logs { height: 30%; }
    Button { width: 100%; margin-bottom: 1; }
    """

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal(id="layout-principal"):
            with Vertical(id="menu-gauche"):

                yield Button("Prendre la parole", id="btn_host_speak")
                yield Button("Couper le micros", id="btn_mute_all")

            with Vertical(id="zone-droite"):
                yield DataTable(id="liste-clients")
                yield RichLog(id="zone-logs", highlight=True, markup=True)
        yield Footer()

    def on_mount(self) -> None:
        # Configurer la table
        table = self.query_one(DataTable)
        table.cursor_type = "row"
        table.add_columns("ID Clients", "Adresse IP", "Statut (Micro)")

        # Lancer les threads d'arrière-plan en passant l'instance `self` (l'app)
        threading.Thread(target=playback_worker, daemon=True).start()
        threading.Thread(target=server_main, args=(self,), daemon=True).start()

    # --- Fonctions pour mettre à jour l'UI (appelées depuis les threads) ---
    def add_log(self, text: str):
        self.query_one(RichLog).write(text)

    def refresh_clients_table(self):
        table = self.query_one(DataTable)
        table.clear()
        with clients_lock:
            for _, addr, cid in clients:
                status = "[+] le client parle" if speaker_id == cid else "[-] le client est en écoute"
                table.add_row(str(cid), str(addr[0]), status, key=str(cid))

    # --- Événements UI ---
    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn_host_speak":
            if speaker_id == -1:
                # Arrêter de parler
                host_stop_event.set()
                set_speaker(None, self)
                self.query_one("#btn_host_speak", Button).variant = "default"
                self.query_one("#btn_host_speak",
                               Button).label = "Prendre la parole"
                set_speaker(None, self)
            else:
                # Commencer à parler
                set_speaker(-1, self)
                self.query_one("#btn_host_speak", Button).variant = "success"
                self.query_one("#btn_host_speak",
                               Button).label = "Arreter de parler"
                host_stop_event.clear()
                threading.Thread(target=host_speak, args=(
                    self,), daemon=True).start()

        elif event.button.id == "btn_mute_all":
            self.query_one("#btn_host_speak", Button).variant = "default"
            self.query_one("#btn_host_speak",
                           Button).label = "Prendre la parole"
            host_stop_event.set()
            set_speaker(None, self)

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        self.query_one("#btn_host_speak", Button).variant = "default"
        self.query_one("#btn_host_speak",
                       Button).label = "Prendre la parole"
        # Quand on clique sur une ligne du tableau, on donne la parole à ce client
        cid = int(event.row_key.value)  # type: ignore
        set_speaker(cid, self)


if __name__ == '__main__':
    app = HostDashboard()
    app.run()
