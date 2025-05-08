import grpc
import threading
import time
import yaml
from node import node_pb2_grpc, node_pb2
from leader import leader_services  # Import LeaderService class

with open('config.yaml', 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)

NODES = config['nodes']
INTERVAL = config.get('heartbeat_interval', 5)

class HeartbeatMonitor(threading.Thread):
    def __init__(self, leader_service):
        super().__init__()
        self.node_status = {node['address']: True for node in NODES}
        self.leader_service = leader_service
        self.failed_nodes = set()

    def run(self):
        while True:
            print("\n[HEARTBEAT] === Checking Node Status ===")
            for node in NODES:
                node_id = node['id']
                node_addr = node['address']
                try:
                    with grpc.insecure_channel(node_addr) as channel:
                        stub = node_pb2_grpc.NodeServiceStub(channel)
                        response = stub.Ping(node_pb2.PingRequest(), timeout=2)
                        self.node_status[node_addr] = True
                        print(f"[✓] {node_id} ({node_addr}) is ALIVE: {response.message}")

                        # Node trở lại sau khi mất kết nối
                        if node_addr in self.failed_nodes:
                            print(f"[RECOVERY] {node_id} has recovered.")
                            self.failed_nodes.remove(node_addr)
                except Exception:
                    if self.node_status[node_addr]:
                        print(f"[✗] {node_id} ({node_addr}) is DOWN!")
                        self.leader_service.replicate_missing_chunks(node_addr)
                        self.failed_nodes.add(node_addr)
                    self.node_status[node_addr] = False

            print("[HEARTBEAT] =============================\n")
            time.sleep(INTERVAL)

    def get_status(self):
        return self.node_status
