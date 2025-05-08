import grpc
import os
import yaml
import threading
from leader import leader_pb2
from leader import leader_pb2_grpc
from node import node_pb2_grpc
from node import node_pb2

from storage.chunker import chunk_file, dechunk_file

# Đọc config
with open('config.yaml', 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)

NODES = config['nodes']  # Danh sách nodes
print("[DEBUG] NODES from config:", NODES)

class LeaderService(leader_pb2_grpc.LeaderServiceServicer):
    def __init__(self):
        self.file_metadata = {}  # file_name -> list of (chunk_id, node_address)
        self.monitor = None
        print("[DEBUG] Current file_metadata:", self.file_metadata)

    def set_monitor(self, monitor):
        self.monitor = monitor

    def UploadFile(self, request_iterator, context):
        file_name = None
        assigned_nodes = []
        idx = 0

        replication_factor = config.get('replication_factor', 2)
        total_nodes = len(NODES)

        for request in request_iterator:
            if file_name is None:
                file_name = request.file_name

            chunk_id = f"{file_name}_chunk_{idx}"
            primary_index = idx % total_nodes
            replica_indices = [(primary_index + i) % total_nodes for i in range(replication_factor)]

            replica_addresses = []

            for i, node_idx in enumerate(replica_indices):
                node_info = NODES[node_idx]
                try:
                    with grpc.insecure_channel(node_info['address']) as channel:
                        stub = node_pb2_grpc.NodeServiceStub(channel)
                        stub.StoreChunk(node_pb2.StoreChunkRequest(
                            chunk_id=chunk_id,
                            chunk_data=request.chunk_data
                        ))
                    role = "Primary" if i == 0 else "Replica"
                    print(f"[LEADER] Sent {chunk_id} to {node_info['id']} ({role})")
                    replica_addresses.append(node_info['address'])
                except Exception as e:
                    print(f"[LEADER] Failed to store {chunk_id} to {node_info['id']}: {e}")

            assigned_nodes.append((chunk_id, replica_addresses))
            idx += 1

        self.file_metadata[file_name] = assigned_nodes

        return leader_pb2.UploadFileResponse(status="Upload Successful")

    def DownloadFile(self, request, context):
        file_name = request.file_name

        if file_name not in self.file_metadata:
            yield leader_pb2.DownloadFileResponse(chunk_data=b'', file_end=True)
            return

        chunks_info = self.file_metadata[file_name]

        for chunk_id, node_addresses in chunks_info:
            success = False

            # Lọc chỉ những node còn sống
            alive_nodes = [
                addr for addr in node_addresses
                if self.monitor and self.monitor.node_status.get(addr, False)
            ]

            if not alive_nodes:
                print(f"[ERROR] All replicas DEAD for chunk {chunk_id}")
                continue  # Skip chunk này

            for node_address in alive_nodes:
                try:
                    with grpc.insecure_channel(node_address) as channel:
                        stub = node_pb2_grpc.NodeServiceStub(channel)
                        response = stub.RetrieveChunk(node_pb2.RetrieveChunkRequest(chunk_id=chunk_id))
                        if response.found:
                            yield leader_pb2.DownloadFileResponse(chunk_data=response.chunk_data, file_end=False)
                            success = True
                            break
                except Exception as e:
                    print(f"Failed to retrieve chunk {chunk_id} from {node_address}: {e}")

            if not success:
                print(f"[ERROR] Failed to retrieve chunk {chunk_id} from all live replicas")

        yield leader_pb2.DownloadFileResponse(chunk_data=b'', file_end=True)

    def replicate_missing_chunks(self, dead_node_addr):
        print(f"[RECOVERY] Handling failure for: {dead_node_addr}")
        for file_name, chunks in self.file_metadata.items():
            for idx, (chunk_id, node_list) in enumerate(chunks):
                if dead_node_addr in node_list:
                    print(f"[RECOVERY] Chunk {chunk_id} lost from {dead_node_addr}")
                    source_nodes = [addr for addr in node_list if addr != dead_node_addr and self.monitor.node_status.get(addr, False)]
                    if not source_nodes:
                        print(f"[ERROR] No available replica for {chunk_id}")
                        continue

                    live_targets = [node['address'] for node in NODES if node['address'] not in node_list and self.monitor.node_status.get(node['address'], False)]
                    if not live_targets:
                        print(f"[WARN] No live node to replicate {chunk_id}")
                        continue

                    source_addr = source_nodes[0]
                    new_target = live_targets[0]

                    try:
                        with grpc.insecure_channel(source_addr) as chan:
                            stub = node_pb2_grpc.NodeServiceStub(chan)
                            resp = stub.RetrieveChunk(node_pb2.RetrieveChunkRequest(chunk_id=chunk_id))
                            if not resp.found:
                                print(f"[ERROR] Replica {chunk_id} not found on {source_addr}")
                                continue

                        with grpc.insecure_channel(new_target) as chan:
                            stub = node_pb2_grpc.NodeServiceStub(chan)
                            stub.StoreChunk(node_pb2.StoreChunkRequest(chunk_id=chunk_id, chunk_data=resp.chunk_data))

                        node_list.remove(dead_node_addr)
                        node_list.append(new_target)

                        print(f"[RECOVERY] Chunk {chunk_id} replicated to {new_target}")
                    except Exception as e:
                        print(f"[ERROR] Failed to replicate {chunk_id}: {e}")
