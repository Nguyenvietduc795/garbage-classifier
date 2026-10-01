"""
FILE TEST - gửi thử 1 ảnh tới API để xem kết quả trả về
----------------------------------------------------------------
Cài thư viện: pip install requests
Chạy sau khi app.py đã chạy ở cửa sổ terminal khác:
    python test_client.py duong_dan_toi_anh.jpg
"""

import json
import sys

import requests

# Console Windows mac dinh dung cp1252, khong in duoc tieng Viet co dau
# -> ep stdout sang UTF-8 de khong bi UnicodeEncodeError.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

if len(sys.argv) < 2:
    print("Cách dùng: python test_client.py duong_dan_toi_anh.jpg")
    sys.exit(1)

image_path = sys.argv[1]

try:
    with open(image_path, "rb") as f:
        response = requests.post(
            "http://127.0.0.1:5000/predict",
            files={"image": f},
            timeout=30,
        )
except FileNotFoundError:
    print(f"Không tìm thấy ảnh: {image_path}")
    sys.exit(1)
except requests.exceptions.ConnectionError:
    print("Không kết nối được tới http://127.0.0.1:5000 — app.py đã chạy chưa?")
    sys.exit(1)

if response.status_code != 200:
    print(f"Lỗi {response.status_code}:", response.text)
    sys.exit(1)

result = response.json()
print(f"Kết quả: {result['ten']} ({result['confidence']}%)")
print(f"Chắc chắn: {'có' if result['chac_chan'] else 'không'}")
print(f"Gợi ý xử lý: {result['goi_y_xu_ly']}")
print("Chi tiết:", json.dumps(result["all_scores"], ensure_ascii=False))
