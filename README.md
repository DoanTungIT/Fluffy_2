# FLUFFY_2 — Distributed Storage System

## Giới thiệu

Hệ thống lưu trữ phân tán hỗ trợ:
- Chia nhỏ (chunking) và phân phối file lên nhiều node.
- Replication (sao lưu) dữ liệu để đảm bảo tính dư thừa.
- Phát hiện và xử lý lỗi node tự động bằng heartbeat.
- Tự động tái replicate chunk nếu node chứa chunk bị chết.

---

## Cấu trúc thư mục

| Thư mục / File         | Mô tả                                                                |
|------------------------|----------------------------------------------------------------------|
| `chunks/`              | Chứa các chunk dữ liệu được lưu trữ trên từng node.                  |
| `leader/`              | Chứa logic của Leader node — quản lý phân phối, tải lên/tải xuống.   |
| `node/`                | Code gRPC cho các node lưu trữ dữ liệu.                              |
| `heartbeat/`           | Theo dõi trạng thái sống/chết của các node (heartbeat).              |
| `storage/`             | Hàm chia nhỏ file và tái tạo lại file (`chunk_file`, `dechunk_file`).|
| `replication/`         | (Có thể mở rộng) để xử lý sao lưu chủ động/phức tạp hơn.             |
| `metadata/`            | (Dự phòng cho mở rộng): lưu trữ thông tin về file/chunk/node.        |
| `tests/`               | Chứa các script test upload, download, mô phỏng lỗi node.            |
| `supernode/`           | (Mở rộng sau) quản lý nhiều cluster, logic RAFT, leader election...  |
| `config.yaml`          | Cấu hình chung: danh sách node, chunk size, replication,...          |

---

## Cấu hình mẫu (`config.yaml`)
```yaml
chunk_size: 1048576             # 1MB per chunk
replication_factor: 2
heartbeat_interval: 5

nodes:
  - id: "Node1"
    address: "localhost:5001"
  - id: "Node2"
    address: "localhost:5002"
  - id: "Node3"
    address: "localhost:5003"
```

---

## Hướng dẫn chạy hệ thống

### Bước 1. Khởi động các node
Mở 3 terminal khác nhau:
```bash
python node/node_server.py --port 5001
python node/node_server.py --port 5002
python node/node_server.py --port 5003
```

### Bước 2. Khởi động Leader + Heartbeat monitor
```bash
python leader/leader_server.py
```

---

## Cách test

### Test bình thường (upload & download)
```bash
python tests/test_upload_download.py
```
- Script sẽ tạo 9MB file, gửi lên hệ thống, rồi tải về file để kiểm tra.

### Test lỗi node (node loss recovery)
1. Chạy các node như bình thường.
2. Upload file: `python tests/test_upload_download.py`
3. Tắt 1 node (Ctrl+C).
4. Download lại file: `python tests/test_upload_download.py`
5. Kiểm tra log: leader sẽ tự động replicate chunk bị mất sang node còn sống.

---

## Vai trò & công việc chính

### ✳ Storage Layer
- Chia file thành các chunk.
- Lưu chunk xuống ổ đĩa.
- Phục hồi lại file từ chunk.

### ✳ Data Distribution
- Sử dụng round-robin để phân phối chunk đều giữa các node.
- Hỗ trợ replication theo cấu hình.

### ✳ Fault Tolerance
- Triển khai heartbeat để phát hiện node chết.
- Tự động replicate lại chunk nếu node chứa chunk bị lỗi.

---

## Ghi chú thêm
- Mã nguồn dễ mở rộng cho các cơ chế load-based distribution, search file,...
- Có thể tích hợp Redis để lưu metadata và mở rộng thành nhiều cluster với supernode.
