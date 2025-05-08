import grpc
import os
from leader import leader_pb2
from leader import leader_pb2_grpc

def download_file_partial(file_name, save_path):
    channel = grpc.insecure_channel('localhost:6000')
    stub = leader_pb2_grpc.LeaderServiceStub(channel)

    response_iterator = stub.DownloadFile(
        leader_pb2.DownloadFileRequest(file_name=file_name)
    )

    with open(save_path, 'wb') as f:
        total_chunks = 0
        for response in response_iterator:
            if response.file_end:
                break
            total_chunks += 1
            f.write(response.chunk_data)

    print(f"[DOWNLOAD] Downloaded chunks: {total_chunks}")
    print(f"[DOWNLOAD] Saved to: {save_path}")

if __name__ == "__main__":
    os.makedirs('tests', exist_ok=True)
    download_file_partial('sample_big.txt', 'tests/test_missing_chunk.txt')
