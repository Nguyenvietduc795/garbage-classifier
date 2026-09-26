# Hướng dẫn dự án phân loại rác
Model 7 loại: **Battery, Cardboard, Clothes, Glass, Metal, Paper, Plastic**

> **Đã đổi model (26/09/2026).** Phần A và C giờ dùng **ResNet-18 / PyTorch**
> (`garbage_resnet18.pt`) thay cho Teachable Machine. Không còn cần TensorFlow,
> nên chạy được Python 3.9–3.14. Hai file gốc vẫn giữ nguyên nếu cần quay lại:
> `phan_loai_rac_TEACHABLEMACHINE_goc.py.bak` và `app_TEACHABLEMACHINE_goc.py.bak`.
>
> **Độ chính xác của model mới, đo thật:**
>
> | Đo trên | Accuracy |
> |---|---|
> | Ảnh cùng nguồn dataset (626 ảnh) | 96,0% |
> | Ảnh từ nguồn khác, Wikimedia (49 ảnh) | 44,9% |
>
> Con số thứ hai mới là con số thật khi đưa ảnh đời thường vào. Dataset huấn
> luyện gần như toàn ảnh chụp studio nền trắng. Khi model không chắc, giao diện
> hiện màu cam và không đưa gợi ý — đừng tin kết quả lúc đó.

Dự án có 3 phần, dùng cho 2 mục đích khác nhau:

| Phần | File | Model | Dùng khi nào |
|---|---|---|---|
| A. Giao diện Desktop (PyQt5) | `giao_dien_pyqt.py` + `phan_loai_rac.py` | ResNet-18 | **Chính** — demo hackathon dạng ứng dụng desktop, giao diện đẹp |
| B. Web demo | `index.html` + `tfjs_model/` | Teachable Machine (cũ) | Demo hackathon dạng web, không cần cài Python |
| C. API | `app.py`, `test_client.py` | ResNet-18 | Khi cần gọi model qua API |

Lưu ý: phần B vẫn chạy model Teachable Machine cũ, nên **kết quả của nó khác
phần A và C**. Phần A và C dùng chung một model nên luôn khớp nhau.

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

Nếu muốn tự tạo venv mới: Python 3.9–3.14 đều được (đã bỏ TensorFlow nên
không còn giới hạn ≤ 3.11 như trước).

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
- Thanh % cho từng loại rác, và hộp gợi ý xử lý (đổi màu cam khi chưa chắc chắn, xanh khi tự tin).

### 5. Tùy chỉnh
- Đổi nội dung gợi ý xử lý từng loại rác → sửa dict `GOI_Y_XU_LY` trong file `phan_loai_rac.py` (dùng chung cho cả giao diện lẫn logic AI).
- Đổi màu sắc/giao diện → sửa các biến `MAU_...` và chuỗi `STYLESHEET` ở đầu file `giao_dien_pyqt.py`.
- Đổi ngưỡng độ tin cậy hiển thị gợi ý (mặc định 60%) → sửa biến `NGUONG_TIN_CAY` trong `giao_dien_pyqt.py`.

---

## B. Chạy web demo (không cần Python)

1. Đảm bảo `index.html` và thư mục `tfjs_model/` nằm **cùng thư mục**.
2. **Không mở trực tiếp bằng double-click** — trình duyệt sẽ chặn webcam. Dùng 1 trong 2 cách:
   - Extension **Live Server** trong VS Code (chuột phải `index.html` → "Open with Live Server").
   - Hoặc: mở terminal tại thư mục này, chạy `python -m http.server 8000`, mở trình duyệt vào `http://localhost:8000`.
3. Bấm **"Bắt đầu Camera"**, cho phép quyền webcam.
4. Sửa gợi ý xử lý → tìm biến `GOI_Y` trong thẻ `<script>` của `index.html`.

---

## C. API bằng Flask (tùy chọn nâng cao)

Chạy `app.py`, terminal hiện `Running on http://127.0.0.1:5000`.
Test bằng: `python test_client.py duong_dan_anh.jpg`

API trả về JSON gồm: `class`, `confidence`, `chac_chan` (có vượt ngưỡng 60%
không), `goi_y_xu_ly`, và `all_scores` cho cả 7 loại. Dùng chung model và
tiền xử lý với `phan_loai_rac.py` nên **kết quả luôn khớp giao diện desktop**.

---

## Lỗi thường gặp
- **ModuleNotFoundError: No module named 'PyQt5' / 'torch' / 'cv2'** → chưa chọn đúng interpreter (phải là `.venv311`), hoặc quên `pip install -r requirements.txt`.
- **No Python at 'C:\Users\ACER\...'** → đang dùng nhầm thư mục `.venv` hỏng. Chọn lại interpreter sang `.venv311` (xem mục A.2).
- **FileNotFoundError: garbage_resnet18.pt** → file model (44,8 MB) phải nằm cùng thư mục với `phan_loai_rac.py`.
- **UnicodeEncodeError khi chạy `test_client.py`** → đã sửa sẵn (ép stdout sang UTF-8). Nếu vẫn gặp ở file khác, thêm `sys.stdout.reconfigure(encoding="utf-8")`.
- **Không mở được webcam (PyQt5)** → kiểm tra không có ứng dụng khác (Zoom, OBS...) đang chiếm webcam; thử đổi `cv2.VideoCapture(0)` thành `(1)` trong `phan_loai_rac.py` nếu máy có nhiều camera.
- **Webcam web demo không hoạt động** → phải chạy qua local server, không mở file trực tiếp (xem phần B).
- **Port 5000 đang được dùng (Flask)** → đổi `port=5000` thành `port=5001` trong `app.py`.
