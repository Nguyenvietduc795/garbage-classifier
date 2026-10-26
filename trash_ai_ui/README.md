# Hướng dẫn dự án phân loại rác
Model phân **4 nhóm rác**:

| Nhóm | Gồm |
|---|---|
| Rác hữu cơ | Thức ăn thừa, rau củ quả |
| Rác tái chế | Carton, thủy tinh, nhựa, giấy, kim loại |
| Rác không thể tái chế | Quần áo, giày dép, hộp xốp, vỏ bánh kẹo, giấy ăn, ống hút |
| Rác nguy hại | Pin AA/AAA, pin cúc áo, pin điện thoại |

> **Đã đổi model (26/10/2026).** Phần A và C dùng **ResNet-18 10 loại v6**
> (`garbage_resnet18.pt`, PyTorch) — cùng model với trang web `frontend/`. Model phân
> 10 loại vật liệu (thêm `shoes`, `trash`) rồi gộp thành 4 nhóm. Xác suất pin ≥ 50% thì
> báo rác nguy hại; dưới mức đó chọn nhóm theo loại có xác suất cao nhất trong các loại còn lại.
> Số đo trên ảnh chụp thật xem README gốc, mục v6.
>
> Khi model không chắc (dưới 50%), giao diện hiện màu cam và không đưa gợi ý — đừng tin kết quả lúc đó.

Dự án có 3 phần:

| Phần | File | Dùng khi nào |
|---|---|---|
| A. Giao diện Desktop (PyQt5) | `giao_dien_pyqt.py` + `phan_loai_rac.py` | **Chính** — demo dạng ứng dụng desktop |
| B. Web demo | `index.html` + `tfjs_model/` | Demo dạng web, không cần cài Python — **vẫn là model Teachable Machine cũ**, nên dùng trang `frontend/` thay thế |
| C. API | `app.py`, `test_client.py` | Khi cần gọi model qua API |

Phần A, C và trang `frontend/` dùng chung model và tiền xử lý (cạnh ngắn về 256 → cắt giữa
224×224 → tăng sáng nếu ảnh tối → chuẩn hóa ImageNet) và cùng luật pin 50%, nên cho cùng kết quả.

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

Nếu muốn tự tạo venv mới: Python 3.9–3.14 đều được (không cần TensorFlow).

### 3. Cài thư viện
Nếu dùng `.venv311` có sẵn thì **bỏ qua bước này**. Nếu tự tạo venv mới, mở
Terminal trong PyCharm và chạy:
```
pip install -r requirements.txt
```
(gồm `torch`, `torchvision`, `PyQt5`, `opencv-python`, `pillow`, `numpy`, `flask`, `requests`)

### 4. Chạy giao diện
Mở file `giao_dien_pyqt.py` → chuột phải → **Run**.

Giao diện gồm:
- Nút **"Mở ảnh"** — chọn ảnh từ máy để phân loại.
- Nút **"Bật Webcam"** — nhận diện trực tiếp qua camera (bấm lại để tắt).
- Thanh % cho từng nhóm rác, và hộp gợi ý xử lý tô màu theo nhóm (xanh lá: hữu cơ, xanh dương: tái chế, xám: không thể tái chế, đỏ: nguy hại, cam: chưa chắc chắn).

### 5. Tùy chỉnh
- Đổi tên nhóm, ví dụ vật thể, hướng dẫn xử lý → sửa dict `NHOM_RAC` trong file `phan_loai_rac.py` (dùng chung cho cả giao diện lẫn API). Loại vật liệu nào thuộc nhóm nào → `LOAI_VAO_NHOM`.
- Đổi màu sắc/giao diện → sửa các biến `MAU_...` và chuỗi `STYLESHEET` ở đầu file `giao_dien_pyqt.py`.
- Đổi ngưỡng độ tin cậy hiển thị gợi ý (mặc định 50%) → sửa biến `NGUONG_TIN_CAY` trong `giao_dien_pyqt.py`.

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

API trả về JSON gồm: `class` (khóa nhóm: `huu-co`, `tai-che`…), `ten` (tên nhóm tiếng Việt),
`vi_du`, `confidence`, `chac_chan` (có vượt ngưỡng 50% không), `goi_y_xu_ly`, và
`all_scores` cho cả 4 nhóm. Dùng chung model và
tiền xử lý với `phan_loai_rac.py` nên **kết quả luôn khớp giao diện desktop**.

---

## Lỗi thường gặp
- **ModuleNotFoundError: No module named 'PyQt5' / 'torch' / 'cv2'** → chưa chọn đúng interpreter (phải là `.venv311`), hoặc quên `pip install -r requirements.txt`.
- **No Python at 'C:\Users\ACER\...'** → đang dùng nhầm thư mục `.venv` hỏng. Chọn lại interpreter sang `.venv311` (xem mục A.2).
- **FileNotFoundError: garbage_resnet18.pt** → file model (44,8 MB) phải nằm cùng thư mục với `phan_loai_rac.py`.
- **OSError: [WinError 1114] ... c10.dll** → `phan_loai_rac` (kéo theo torch) phải được import trước PyQt5 — đừng đổi thứ tự import trong `giao_dien_pyqt.py`.
- **UnicodeEncodeError khi chạy `test_client.py`** → đã sửa sẵn (ép stdout sang UTF-8). Nếu vẫn gặp ở file khác, thêm `sys.stdout.reconfigure(encoding="utf-8")`.
- **Không mở được webcam (PyQt5)** → kiểm tra không có ứng dụng khác (Zoom, OBS...) đang chiếm webcam; thử đổi `cv2.VideoCapture(0)` thành `(1)` trong `phan_loai_rac.py` nếu máy có nhiều camera.
- **Webcam web demo không hoạt động** → phải chạy qua local server, không mở file trực tiếp (xem phần B).
- **Port 5000 đang được dùng (Flask)** → đổi `port=5000` thành `port=5001` trong `app.py`.
