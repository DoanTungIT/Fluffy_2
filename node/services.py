from node import node_pb2
from node import node_pb2_grpc
import os

# Đường dẫn thư mục chứa các chunk
CHUNKS_DIR = 'chunks'


class NodeService(node_pb2_grpc.NodeServiceServicer):
    def __init__(self):
        os.makedirs(CHUNKS_DIR, exist_ok=True)

    def StoreChunk(self, request, context):
        chunk_id = request.chunk_id
        chunk_data = request.chunk_data

        chunk_path = os.path.join(CHUNKS_DIR, chunk_id)
        with open(chunk_path, 'wb') as f:
            f.write(chunk_data)

        print(f"[NODE] Stored chunk at {chunk_path}")

        return node_pb2.StoreChunkResponse(status="OK")

    def RetrieveChunk(self, request, context):
        chunk_id = request.chunk_id
        chunk_path = os.path.join(CHUNKS_DIR, chunk_id)

        print("[DEBUG] RetrieveChunk called:", chunk_id)

        if os.path.exists(chunk_path):
            with open(chunk_path, 'rb') as f:
                chunk_data = f.read()
            return node_pb2.RetrieveChunkResponse(chunk_data=chunk_data, found=True)
        else:
            return node_pb2.RetrieveChunkResponse(chunk_data=b'', found=False)
        
        


    def DeleteChunk(self, request, context):
        chunk_id = request.chunk_id
        chunk_path = os.path.join(CHUNKS_DIR, chunk_id)

        if os.path.exists(chunk_path):
            os.remove(chunk_path)
            return node_pb2.DeleteChunkResponse(status="Deleted")
        else:
            return node_pb2.DeleteChunkResponse(status="NotFound")
        

    def Ping(self, request, context):
        return node_pb2.PingResponse(message="Alive")
