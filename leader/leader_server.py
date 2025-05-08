import grpc
from concurrent import futures
import time
from leader.leader_services import LeaderService
from leader import leader_pb2_grpc
from heartbeat.heartbeat_monitor import HeartbeatMonitor

PORT = 6000

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))

    # Tạo LeaderService instance trước
    leader_service = LeaderService()

    # Tạo monitor và gắn vào LeaderService
    monitor = HeartbeatMonitor(leader_service)
    leader_service.set_monitor(monitor)

    # Đăng ký gRPC service
    leader_pb2_grpc.add_LeaderServiceServicer_to_server(leader_service, server)
    server.add_insecure_port(f'[::]:{PORT}')
    server.start()
    print(f"Leader Server started on port {PORT}")

    # Bắt đầu Heartbeat
    monitor.daemon = True
    monitor.start()

    try:
        while True:
            time.sleep(86400)
    except KeyboardInterrupt:
        server.stop(0)

if __name__ == '__main__':
    serve()
