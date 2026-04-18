import sys
from program.client import Client


if __name__ == '__main__':
    # Récupérer l'adresse IP passée en argument ou utiliser localhost par défaut
    target_ip = sys.argv[1] if len(sys.argv) > 1 else '192.168.1.156'
    app = Client(target_ip)
    app.run()
