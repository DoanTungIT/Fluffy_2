import grpc
from concurrent import futures
import time
import argparse

from node import node_pb2_grpc
from node import services


def serve():
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=50051)
    args = parser.parse_args()

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    node_pb2_grpc.add_NodeServiceServicer_to_server(services.NodeService(), server)
    server.add_insecure_port(f'[::]:{args.port}')
    server.start()
    print(f"Node Server started on port {args.port}")

    try:
        while True:
            time.sleep(86400)
    except KeyboardInterrupt:
        server.stop(0)

if __name__ == '__main__':
    serve()
