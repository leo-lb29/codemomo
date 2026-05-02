import sys
from app.main.client.main import Client

if __name__ == '__main__':
    ip_du_serveur = sys.argv[1] if len(sys.argv) > 1 else '192.168.1.156'
    app = Client(ip_du_serveur)
    app.run()