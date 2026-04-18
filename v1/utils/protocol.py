import struct
from config import STRUCTURE_PROTOCOL


def _encode_data(data):
    """Convertit les données en bytes si nécessaire."""
    return data.encode() if isinstance(data, str) else data


def _read_exact(sock, n):
    """Lit exactement n bytes depuis le socket."""
    buffer = b''
    while len(buffer) < n:
        chunk = sock.recv(n - len(buffer))
        if not chunk:
            return None
        buffer += chunk
    return buffer


def send_message(sock, ptype, data):
    """Envoie un message structuré: [type:1 byte][length:4 bytes][data]."""
    data = _encode_data(data)
    sock.sendall(struct.pack(STRUCTURE_PROTOCOL, ptype, len(data)) + data)


def recv_message(sock):
    """Reçoit un message structuré et retourne (type, data)."""
    header = _read_exact(sock, 5)
    if not header:
        return None, None
    ptype, length = struct.unpack(STRUCTURE_PROTOCOL, header)
    payload = _read_exact(sock, length)
    return (ptype, payload) if payload is not None else (None, None)
