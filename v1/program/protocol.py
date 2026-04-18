from utils.protocol import recv_message, send_message


class Protocol:
    @staticmethod
    def send(sock, ptype, data):
        send_message(sock, ptype, data)

    @staticmethod
    def recv(sock):
        return recv_message(sock)
