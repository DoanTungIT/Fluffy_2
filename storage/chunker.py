CHUNK_SIZE = 4 * 1024 * 1024  # 4MB mặc định

def chunk_file(file_path):
    chunks = []
    with open(file_path, 'rb') as f:
        while True:
            chunk = f.read(CHUNK_SIZE)
            if not chunk:
                break
            chunks.append(chunk)
    return chunks

def dechunk_file(chunks, output_path):
    with open(output_path, 'wb') as f:
        for chunk in chunks:
            f.write(chunk)
