# Hướng dẫn dự án phân loại rác
Model phân **4 nhóm rác**:

| Nhóm | Gồm |
|---|---|
| Rác hữu cơ | Thức ăn thừa, rau củ quả |
| Rác tái chế | Carton, thủy tinh, chai nhựa, giấy, kim loại |
| Rác không thể tái chế | Quần áo, dép, khẩu trang |
| Rác nguy hại | Pin, ắc quy |

> **Đã đổi model (01/10/2026).** Cả 3 phần A, B, C giờ dùng chung model
> **Teachable Machine 4 nhóm** (MobileNet): `keras_model.h5` + `labels.txt` cho
> Python, `tfjs_model/` cho web. Bản ResNet-18 7 loại trước đó vẫn còn trong
> lịch sử git nếu cần quay lại.
>
> Khẩu trang và dép chưa có ảnh train — model chưa nhận được, sẽ bổ sung sau.
> Model chưa được đo trên ảnh đời thực; khi model không chắc (dưới 60%),
> giao diện hiện màu cam và không đưa gợi ý — đừng tin kết quả lúc đó.

Dự án có 3 phần:

| Phần | File | Dùng khi nào |
|---|---|---|
| A. Giao diện Desktop (PyQt5) | `giao_dien_pyqt.py` + `phan_loai_rac.py` | **Chính** — demo dạng ứng dụng desktop |
| B. Web demo | `index.html` + `tfjs_model/` | Demo dạng web, không cần cài Python |
| C. API | `app.py`, `test_client.py` | Khi cần gọi model qua API |

Cả 3 phần dùng cùng một model và cùng tiền xử lý của Teachable Machine
(cắt vuông giữa ảnh → 224×224), nên kết quả khớp nhau.

---

## A. Giao diện Desktop bằng PyQt5 (khuyến nghị dùng chính)

### 1. Giải nén & mở project bằng PyCharm
Giải nén zip, mở thư mục bằng PyCharm (**File → Open**).

### 2. Chọn Python Interpreter
Thư mục này đã có sẵn venv cài đủ thư viện: **`.venv311`**.

**File → Settings → Project → Python Interpreter → Add Interpreter →
Add Local Interpreter → Existing**, trỏ tới:
```
.venv311\Scripts\python.exe
```

⚠️ **Đừng chọn thư mục `.venv`** — nó được đóng gói kèm từ máy khác
(`C:\Users\ACER\...`) và đã hỏng, không chạy được. Xóa đi cũng không sao.

Nếu muốn tự tạo venv mới: **phải dùng Python 3.9–3.11** — TensorFlow 2.15
không có bản cho Python mới hơn.

### 3. Cài thư viện
Nếu dùng `.venv311` có sẵn thì **bỏ qua bước này**. Nếu tự tạo venv mới, mở
Terminal trong PyCharm và chạy:
```
pip install -r requirements.txt
```
(gồm `tensorflow`, `PyQt5`, `opencv-python`, `pillow`, `numpy`, `flask`, `requests`)

### 4. Chạy giao diện
Mở file `giao_dien_pyqt.py` → chuột phải → **Run**.

Giao diện gồm:
- Nút **"Mở ảnh"** — chọn ảnh từ máy để phân loại.
- Nút **"Bật Webcam"** — nhận diện trực tiếp qua camera (bấm lại để tắt).
- Thanh % cho từng nhóm rác, và hộp gợi ý xử lý tô màu theo nhóm (xanh lá: hữu cơ, xanh dương: tái chế, xám: không thể tái chế, đỏ: nguy hại, cam: chưa chắc chắn).

### 5. Tùy chỉnh
- Đổi tên nhóm, ví dụ vật thể, hướng dẫn xử lý → sửa dict `NHOM_RAC` trong file `phan_loai_rac.py` (dùng chung cho cả giao diện lẫn API).
- Đổi màu sắc/giao diện → sửa các biến `MAU_...` và chuỗi `STYLESHEET` ở đầu file `giao_dien_pyqt.py`.
- Đổi ngưỡng độ tin cậy hiển thị gợi ý (mặc định 60%) → sửa biến `NGUONG_TIN_CAY` trong `giao_dien_pyqt.py`.

---

## B. Chạy web demo (không cần Python)

1. Đảm bảo `index.html` và thư mục `tfjs_model/` nằm **cùng thư mục**.
2. **Không mở trực tiếp bằng double-click** — trình duyệt sẽ chặn webcam. Dùng 1 trong 2 cách:
   - Extension **Live Server** trong VS Code (chuột phải `index.html` → "Open with Live Server").
   - Hoặc: mở terminal tại thư mục này, chạy `python -m http.server 8000`, mở trình duyệt vào `http://localhost:8000`.
3. Bấm **"Bắt đầu Camera"**, cho phép quyền webcam.
4. Sửa tên nhóm / hướng dẫn xử lý → tìm biến `NHOM_RAC` trong thẻ `<script>` của `index.html`.

---

## C. API bằng Flask (tùy chọn nâng cao)

Chạy `app.py`, terminal hiện `Running on http://127.0.0.1:5000`.
Test bằng: `python test_client.py duong_dan_anh.jpg`

API trả về JSON gồm: `class` (nhãn gốc của model), `ten` (tên nhóm tiếng Việt),
`vi_du`, `confidence`, `chac_chan` (có vượt ngưỡng 60% không), `goi_y_xu_ly`, và
`all_scores` cho cả 4 nhóm. Dùng chung model và
tiền xử lý với `phan_loai_rac.py` nên **kết quả luôn khớp giao diện desktop**.

---

## Lỗi thường gặp
- **ModuleNotFoundError: No module named 'PyQt5' / 'tensorflow' / 'cv2'** → chưa chọn đúng interpreter (phải là `.venv311`), hoặc quên `pip install -r requirements.txt`.
- **No Python at 'C:\Users\ACER\...'** → đang dùng nhầm thư mục `.venv` hỏng. Chọn lại interpreter sang `.venv311` (xem mục A.2).
- **No matching distribution found for tensorflow** → đang dùng Python 3.12 trở lên. Tạo venv bằng Python 3.11.
- **FileNotFoundError: keras_model.h5 / labels.txt** → hai file này phải nằm cùng thư mục với `phan_loai_rac.py`.
- **UnicodeEncodeError khi chạy `test_client.py`** → đã sửa sẵn (ép stdout sang UTF-8). Nếu vẫn gặp ở file khác, thêm `sys.stdout.reconfigure(encoding="utf-8")`.
- **Không mở được webcam (PyQt5)** → kiểm tra không có ứng dụng khác (Zoom, OBS...) đang chiếm webcam; thử đổi `cv2.VideoCapture(0)` thành `(1)` trong `phan_loai_rac.py` nếu máy có nhiều camera.
- **Webcam web demo không hoạt động** → phải chạy qua local server, không mở file trực tiếp (xem phần B).
- **Port 5000 đang được dùng (Flask)** → đổi `port=5000` thành `port=5001` trong `app.py`.
