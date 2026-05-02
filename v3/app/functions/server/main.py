import socket as socket_module
import threading
from config import PORT_AUDIO, PORT_CONTROL


    
class Serveur:
    def __init__(self):
        self.socket = socket_module.socket(
            socket_module.AF_INET, socket_module.SOCK_STREAM, proto=socket_module.IPPROTO_TCP)
        self.socket_audio_recv = socket_module.socket(
            socket_module.AF_INET, socket_module.SOCK_DGRAM, proto=socket_module.IPPROTO_UDP)
        self.socket_audio_send = socket_module.socket(
            socket_module.AF_INET, socket_module.SOCK_DGRAM, proto=socket_module.IPPROTO_UDP)
        self.socket_audio_send.setsockopt(socket_module.SOL_SOCKET, socket_module.SO_BROADCAST, 1)
        self.port_control = PORT_CONTROL
        self.port_audio = PORT_AUDIO
        self.clients = []
        self.clients_demandes_parole = []
        self.speaker_id = None
        self.client_id_counter = 0
        self.lock = threading.Lock()
        self.client_addresses = {}
        self.client_udp_addresses = {}
        self.host_is_speaking = False
        self.audio_buffer = {}

    def demarrer_serveur(self):
        self.socket_audio_recv.bind(("0.0.0.0", self.port_audio))
        self.socket.bind(("0.0.0.0", self.port_control))
        self.socket.listen(5)
        threading.Thread(target=self._handle_audio_relay, daemon=True).start()
        while True:
            try:
                conn, addr = self.socket.accept()
                print(f"Connexion reçue de {addr}")
                threading.Thread(target=self._handle_client,
                                 args=(conn, addr), daemon=True).start()
            except Exception as e:
                print(f"Erreur lors de l'acceptation: {e}")


    def _handle_audio_relay(self):
        while True:
            try:
                data, addr = self.socket_audio_recv.recvfrom(1024)
                if not data:
                    continue
                client_id = self._get_client_id_by_addr(addr)
                if client_id == self.speaker_id and not self.host_is_speaking:
                    self.socket_audio_send.sendto(data, ("127.0.0.1", 5002))
            except Exception as e:
                print(f"Erreur relay audio: {e}")

    def _get_client_id_by_addr(self, addr):
        with self.lock:
            for c, a, cid, p in self.clients:
                if a == addr:
                    return cid
        return None

    def _handle_client(self, conn, addr):
        client_id = None
        prenom = None
        try:
            data = conn.recv(1024).decode()
            print(f"Message reçu: {data}")

            if data.startswith("PRENOM:"):
                prenom = data.split(":")[1]
                with self.lock:
                    client_id = self.client_id_counter
                    self.client_id_counter += 1
                    self.clients.append((conn, addr, client_id, prenom))
                    self.client_addresses[client_id] = addr
                print(f"Client {client_id} connecté: {prenom}")
                try:
                    conn.send(f"CLIENT_ID:{client_id}".encode())
                except:
                    pass
            else:
                conn.close()
                return

            while True:
                data = conn.recv(1024).decode()
                if not data:
                    break
                print(f"Message reçu de {prenom}: {data}")

                if data == "REQUEST_TO_SPEAK":
                    self.on_demande_la_parole(client_id, prenom)
        except Exception as e:
            print(f"Erreur client: {e}")
        finally:
            with self.lock:
                if client_id is not None:
                    self.clients = [(c, a, cid, p)
                                    for c, a, cid, p in self.clients if a != addr]
                    self.clients_demandes_parole = [
                        (c, p) for c, p in self.clients_demandes_parole if c != client_id]
                    if client_id in self.client_addresses:
                        del self.client_addresses[client_id]
            conn.close()


    def on_demande_la_parole(self, client_id, prenom):
        with self.lock:
            self.clients_demandes_parole.append((client_id, prenom))
        print(f"{prenom} demande la parole")

    def accepter_parole(self, id_client):
        with self.lock:
            for conn, addr, cid, prenom in self.clients:
                if cid == id_client:
                    message = "SPEAK_ACCEPTED".encode()
                    try:
                        conn.send(message)
                        print(f"Message 'SPEAK_ACCEPTED' envoyé à {prenom}")
                    except:
                        pass
                    break

        self.donner_la_parole(id_client)

    def refuser_parole(self, id_client):
        with self.lock:
            for conn, addr, cid, prenom in self.clients:
                if cid == id_client:
                    message = "SPEAK_REJECTED".encode()
                    try:
                        conn.send(message)
                        print(f"Message 'SPEAK_REJECTED' envoyé à {prenom}")
                    except:
                        pass
                    self.clients_demandes_parole = [
                        (c, p) for c, p in self.clients_demandes_parole if c != id_client]
                    break

    def reset_speak(self):
        with self.lock:
            for conn, addr, cid, prenom in self.clients:
                message = "RESET_SPEAK".encode()
                try:
                    conn.send(message)
                    print(f"Message 'RESET_SPEAK' envoyé à {prenom}")
                except:
                    pass
            self.speaker_id = None

    def retirer_la_parole(self, id_client):
        with self.lock:
            for conn, addr, cid, prenom in self.clients:
                if cid == id_client:
                    message = "SPEAKER:0".encode()
                    try:
                        conn.send(message)
                        print(f"Message 'SPEAKER:0' envoyé à {prenom}")
                    except:
                        pass
                    break
            if self.speaker_id == id_client:
                self.speaker_id = None

    def donner_la_parole(self, id_client):
        with self.lock:
            if self.speaker_id is not None and self.speaker_id != id_client:
                for conn, addr, cid, prenom in self.clients:
                    if cid == self.speaker_id:
                        message = "SPEAKER:0".encode()
                        try:
                            conn.send(message)
                        except:
                            pass
                        break

            for conn, addr, cid, prenom in self.clients:
                if cid == id_client:
                    message = "SPEAKER:1".encode()
                    try:
                        conn.send(message)
                        print(f"Message 'SPEAKER:1' envoyé à {prenom}")
                    except:
                        pass
                    break

            self.speaker_id = id_client
            self.clients_demandes_parole = [
                (c, p) for c, p in self.clients_demandes_parole if c != id_client]

    def host_start_speaking(self):
        with self.lock:
            self.host_is_speaking = True
            if self.speaker_id is not None:
                for conn, addr, cid, prenom in self.clients:
                    if cid == self.speaker_id:
                        message = "SPEAKER:0".encode()
                        try:
                            conn.send(message)
                        except:
                            pass
                        break
                self.speaker_id = None

    def host_stop_speaking(self):
        with self.lock:
            self.host_is_speaking = False
