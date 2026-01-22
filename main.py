from network.p2p import P2PNetwork

HOST = "0.0.0.0"
PORT = 5000


if __name__ == "__main__":
    server = P2PNetwork(HOST, PORT)
    server.start_server()

