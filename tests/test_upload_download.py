import grpc
from leader import leader_pb2
from leader import leader_pb2_grpc

import os

def upload_file(file_path):
    channel = grpc.insecure_channel('localhost:6000')
    stub = leader_pb2_grpc.LeaderServiceStub(channel)

    def request_generator():
        with open(file_path, 'rb') as f:
            while True:
                chunk = f.read(1024 * 1024)  # 1MB mỗi chunk gửi lên Leader
                if not chunk:
                    break
                yield leader_pb2.UploadFileRequest(
                    file_name=os.path.basename(file_path),
                    chunk_data=chunk
                )

    print(f"[DEBUG] File size: {os.path.getsize(file_path)} bytes")

    def request_generator():
        with open(file_path, 'rb') as f:
            i = 0
            while True:
                chunk = f.read(1024 * 1024)
                if not chunk:
                    break
                print(f"[CLIENT] Sending chunk #{i}, size: {len(chunk)}")
                i += 1
                yield leader_pb2.UploadFileRequest(
                    file_name=os.path.basename(file_path),
                    chunk_data=chunk
                )

    response = stub.UploadFile(request_generator())
    print(f"[UPLOAD] Upload status: {response.status}")

def download_file(file_name, save_path):
    channel = grpc.insecure_channel('localhost:6000')
    stub = leader_pb2_grpc.LeaderServiceStub(channel)

    response_iterator = stub.DownloadFile(
        leader_pb2.DownloadFileRequest(file_name=file_name)
    )

    with open(save_path, 'wb') as f:
        for response in response_iterator:
            if response.file_end:
                break
            f.write(response.chunk_data)

    print(f"[DOWNLOAD] File saved to: {save_path}")

if __name__ == "__main__":
    # Đảm bảo có thư mục tests/ và file sample.txt
    os.makedirs('tests', exist_ok=True)
    with open('tests/sample_big.txt', 'wb') as f:
        f.write(b'x' * (1048576 * 9))  # 9MB dữ liệu nhị phân

    # Upload file lên Leader
    upload_file('tests/sample_big.txt')

    # Download file về lại
    download_file('sample_big.txt', 'tests/output_sample_big.txt')
