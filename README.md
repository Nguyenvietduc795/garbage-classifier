# Phân loại rác — 8 loại, 4 nhóm

Pipeline huấn luyện ResNet-18 (PyTorch) phân loại ảnh rác thành 8 loại vật liệu:
`battery`, `cardboard`, `clothes`, `glass`, `metal`, `organic`, `paper`, `plastic`.
Giao diện gộp lại thành **4 nhóm**: hữu cơ, tái chế, không thể tái chế, nguy hại.

Kèm các giao diện sử dụng: web (`frontend/`, Vercel), desktop (PyQt5) và API (Flask).

---

## Model đang chạy trên web (01/10/2026)

`frontend/` chạy **ResNet-18 8 loại ngay trong trình duyệt** (TensorFlow.js, nén uint8,
11 MB) — không cần server, ảnh không rời máy người dùng.

Đo trên 49 ảnh đời thực (`realworld_curated`), tính đúng **theo 4 nhóm**:

| Model | Đúng | Pin (13 ảnh) |
|---|---|---|
| Teachable Machine 4 nhóm (MobileNet, chỉ train phần đầu) | 37/49 | 5 |
| ResNet-18 7 lớp cũ (`new11k`, chưa có hữu cơ) | 43/49 | 9 |
| **ResNet-18 8 lớp (`v2_r18`) ← đang dùng** | **44/49** | **11** |
| MobileNetV3-Large 8 lớp | 40/49 | 5 |
| ResNet-18 / MobileNetV3 + cân bằng lớp | 43/49 · 36/49 | — |
| ResNet-18 trên `dataset_merged` + augmentation mạnh | 38/49 | 6 |

- Dữ liệu: bộ 11.107 ảnh (bộ cho kết quả tốt nhất từ trước) + 1.451 ảnh hữu cơ.
  Train như `new11k`: 15 epoch, batch 32, **không** augmentation mạnh, **không** cân bằng lớp
  — hai thứ này đều làm kết quả trên ảnh thật kém đi.
- Bộ 49 ảnh không có ảnh hữu cơ và quần áo chụp ngoài đời, nên hai nhóm đó **chưa đo được
  trên ảnh thật** (trên ảnh test cùng nguồn: hữu cơ 96%). Chênh 44 với 43 là 1 ảnh — nằm
  trong sai số; đúng hơn là "ngang model cũ, có thêm nhóm hữu cơ".
- Web chọn nhóm theo **loại có xác suất cao nhất**, không cộng xác suất theo nhóm: nhóm tái
  chế gồm 5 loại, cộng lại sẽ lấn át pin (44 đúng so với 42). Ngưỡng "chưa chắc" là 50%.

### Đưa model mới lên web

Cần một môi trường riêng Python 3.11 + `tensorflow-cpu==2.15.1`, `onnx==1.15.0`,
`protobuf==4.25.3`, `onnx2tf==1.19.16` và `tensorflowjs==4.17.0` (hai gói cuối cài
`--no-deps`; `tensorflowjs` cần thêm `tensorflow_hub==0.15.0` và `setuptools<70`, còn
`tensorflow_decision_forests` / `jax` không có bản Windows — tạo module rỗng cùng tên là đủ,
bộ chuyển CNN không dùng tới). Bản TF 2.16+ dùng Keras 3, các công cụ trên không chạy.

```bash
uv run --extra export garbage-export-onnx --checkpoint artifacts/v2_r18/best_model.pt --output r18.onnx
onnx2tf -i r18.onnx -o r18_tf -osd -n
python -m tensorflowjs.converters.converter --input_format=tf_saved_model --output_format=tfjs_graph_model --quantize_uint8="*" r18_tf r18_tfjs
```

`onnx2tf` đòi tải file ảnh mẫu `calibration_image_sample_data_20x128x128x3_float32.npy`
từ một server đã hỏng — tự tạo file đó (20 ảnh 128×128×3, giá trị 0–1) trong thư mục chạy lệnh.

Chép `r18_tfjs/*` vào **thư mục mới** `frontend/models/<tên>/`, thêm `meta.json` (danh sách
lớp đúng thứ tự, mean/std ImageNet), rồi đổi `THU_MUC_MODEL` trong `frontend/index.html`.
Đừng ghi đè thư mục cũ: Vercel cache `models/` 1 năm.

---

## Thử thêm ảnh rác đời thực (24/10/2026) — chưa đưa lên web

Bản nộp Vòng Khu vực được gắn tag `vong-khu-vuc-2026`.

Gộp `dataset_8lop_v2` với hai bộ ảnh chụp thật thành `dataset_8lop_v3` (17.581 ảnh):

- **RealWaste** (UCI, CC BY 4.0): rác thật ở bãi rác, nền xi măng — thêm 3.247 ảnh
  (bìa, hữu cơ, vải, kính, kim loại, giấy, nhựa).
- **Malaysian Trash Annotation** (Hugging Face, CC BY 4.0): ảnh điện thoại ở Đông Nam Á, có
  ảnh chụp tối — cắt từng vật theo bbox, thêm 1.776 ảnh. Phần `test` của bộ này giữ riêng
  làm `realworld_mta_test` (175 ảnh), không dùng để train.
- Lọc trùng bằng dHash, kể cả với các bộ `realworld_*`.
- Đã bỏ **TrashBusters `real_world`**: xem mẫu thì là ảnh sản phẩm/stock trên web, có cả ảnh
  sai nhãn — không phải ảnh rác đời thực như tên gọi.
- `Garbage Classification v2` (Kaggle, sumn2u) chính là `dataset_8lop_v2` — đã có sẵn.

Số ảnh đúng theo 4 nhóm:

| Bộ test | v2 (đang dùng) | v3 | v3 + `--oversample battery=2` |
|---|---|---|---|
| `realworld_curated` (49) | **44** | 42 | 41 |
| `realworld_test` (49) | 22 | **29** | 27 |
| `realworld_test2` (53) | 43 | **45** | 43 |
| Tổng 3 bộ (151) | 109 | **116** | 111 |
| **Pin** trong 3 bộ (27) | **20** | 14 | 16 |
| `realworld_mta_test` (175, cùng nguồn với dữ liệu train) | 146 | 170 | 170 |

v3 đúng nhiều hơn trên ảnh thật nói chung nhưng **nhận pin kém đi** — dữ liệu mới không có
ảnh pin nào, pin bị các lớp khác lấn át. Lấy mẫu pin gấp đôi không chữa được. Vì pin là rác
nguy hại, web giữ v2. Việc cần làm tiếp: tự chụp 200–300 ảnh pin thật (nhiều nền, đèn vàng,
chỗ tối) rồi train lại v3. Vẫn chưa có bộ test ảnh tối nên chưa đo được độ bền ánh sáng.

### Cân bằng độ sáng và ngưỡng tin cậy (web, model v2)

Không train lại, chỉ thêm bước xử lý trước và sau khi chạy model trong `frontend/index.html`:

- **Cân bằng độ sáng:** ảnh có độ sáng trung bình < 0,30 thì nâng gamma cho độ sáng về
  ~0,45; ảnh đủ sáng giữ nguyên. Kết quả hiện thêm "ảnh tối, đã tự tăng sáng".
- **Ngưỡng tin cậy 0,5:** nhóm được chọn có xác suất < 50% thì hiện "Chưa chắc" thay vì đoán.

Chưa có ảnh tối thật, nên làm tối giả 151 ảnh (còn 25% độ sáng). Số ảnh đúng theo 4 nhóm:

| | Không cân bằng | Có cân bằng |
|---|---|---|
| Ảnh gốc — PyTorch | 109 | 109 |
| Ảnh tối giả — PyTorch | 95 | **107** |
| Ảnh gốc — trình duyệt | 107 | 107 |
| Ảnh tối giả — trình duyệt | 100 | **105** |

(Trình duyệt và PyTorch thu nhỏ ảnh hơi khác nhau nên lệch 2 ảnh ở ảnh gốc.)

Ngưỡng tin cậy trên 151 ảnh gốc (PyTorch), đúng – sai – "Chưa chắc":

| Ngưỡng | Đúng | Sai | Chưa chắc |
|---|---|---|---|
| 0,4 | 107 | 33 | 11 |
| **0,5 (đang dùng)** | 104 | 26 | 21 |
| 0,6 | 99 | 16 | 36 |

Giữ 0,5: lên 0,6 bớt 10 lần sai nhưng 5 ảnh đúng bị đổi thành "Chưa chắc", và cứ 4 ảnh
thì 1 ảnh không có câu trả lời.

---

## Kết quả 7 lớp (trước khi thêm hữu cơ) — đọc kỹ cả hai cột

| Model | Dữ liệu train | Ảnh cùng nguồn dataset | **Ảnh từ nguồn khác** |
|---|---|---|---|
| `full` | 980 | 90,0% | 53,1% |
| `big` | 2.890 | 94,4% | 44,9% |
| `gentle` | 2.890, backbone LR 3e-6 | 90,1% | 49,0% |
| `aug` | 2.890 + augmentation mạnh | 96,0% | 44,9% |
| **`new11k`** | **7.772** | 94,4% | **57,1%** ← tốt nhất thực tế |
| `merged` | 8.435 + augmentation mạnh | **96,0%** | 51,0% |

**Cột bên phải mới là con số thật.** Nó đo trên 49 ảnh rác lấy từ Wikimedia Commons —
ảnh chụp ngoài đời, không thuộc bất kỳ bộ dữ liệu huấn luyện nào.

Model tốt nhất đạt **96% trên ảnh dataset nhưng chỉ 57% trên ảnh đời thực**.
Cứ 10 tấm ảnh bạn tự chụp thì sai hơn 4 tấm. Đây là giới hạn thật của dự án, không phải
con số đem giấu đi.

## Vì sao có khoảng cách đó

Dữ liệu huấn luyện gần như toàn **ảnh chụp studio: một vật, nền trắng, ánh sáng đều**.
Ảnh đời thực có nhiều vật trong khung, nền lộn xộn, ánh sáng bất kỳ — model chưa từng thấy.
Hiện tượng này gọi là **domain shift**.

Kiểm chứng trong quá trình làm:

- Bộ `archive` (4.133 ảnh) thực chất **chính là TrashNet** — đối chiếu md5 thấy 86,7% ảnh
  giống nhau từng byte. TrashNet nổi tiếng vì chụp mỗi vật trên một tấm bìa trắng.
- Bộ `dataset_sach_zip` (1.400 ảnh) là **tập con** của `archive`, giống hệt từng byte.

Tức là ba bộ dữ liệu ban đầu thực ra chỉ là **một nguồn duy nhất**.

## Đã thử gì để chữa

| Cách | Thay đổi trên ảnh đời thực |
|---|---|
| Augmentation mạnh (TrivialAugmentWide, crop 0.3–1.0, blur, random erasing) | **0 điểm** — thử 2 lần, kể cả khi train đủ 43 epoch |
| Hạ learning rate của backbone xuống 10 lần | +4 điểm (nằm trong sai số ±7) |
| **Thêm 7.922 ảnh từ nguồn khác** | **+12,2 điểm** ← cách duy nhất có tác dụng |
| Thêm 948 ảnh cùng kiểu studio | 0 điểm |

Kết luận: **chỉ dữ liệu đa dạng mới chữa được, và phải là dữ liệu KHÁC KIỂU.**
Thêm ảnh cùng phong cách không giúp gì.

Muốn cải thiện tiếp, việc đáng làm nhất là bổ sung ảnh chụp bằng điện thoại trong
bối cảnh thật — nhiều vật một khung, trong thùng rác, ánh sáng trong nhà.

---

## Cấu trúc

```
garbage_classifier/        Pipeline train + đánh giá (phần chính)
  src/garbage_classifier/
    data.py                Chia tập, augmentation
    model.py               ResNet-18 + lưu/nạp checkpoint
    engine.py              Vòng train và đánh giá
    train.py               Lệnh train
    evaluate.py            Lệnh đánh giá
    predict.py             Dự đoán 1 ảnh
  artifacts/               Checkpoint + số liệu (không đẩy lên git)

trash_ai_ui/               Giao diện sử dụng
  giao_dien_pyqt.py        Desktop PyQt5
  phan_loai_rac.py         Logic AI dùng chung
  app.py                   API Flask
  index.html + tfjs_model/ Web chạy trong trình duyệt
  garbage_resnet18.pt      Model đang triển khai
```

## Cài đặt

Cần [uv](https://docs.astral.sh/uv/). Từ thư mục `garbage_classifier`:

```bash
uv sync
```

**Về GPU:** `pyproject.toml` đã trỏ sang index CUDA 13.0 của PyTorch. Mặc định PyPI chỉ
có bản torch **CPU-only** cho Windows — cài nhầm bản đó thì train chậm hơn khoảng **20 lần**
(72 phút so với 3 phút cho cùng một lần train). Kiểm tra bằng:

```bash
uv run python -c "import torch; print(torch.__version__, torch.cuda.is_available())"
```

Phải ra `2.14.0+cu130 True`. Nếu ra `+cpu` thì GPU đang không được dùng.

## Sử dụng

Kiểm tra dataset:

```bash
uv run garbage-data --data-dir "duong/dan/toi/dataset"
```

Train:

```bash
uv run garbage-train --data-dir "duong/dan/toi/dataset" --output-dir "artifacts/lan1" --epochs 20 --batch-size 64 --num-workers 8
```

Tham số quan trọng: `--strong-augment` (augmentation mạnh), `--freeze-epochs` (số epoch
đóng băng backbone), `--patience` (dừng sớm), `--backbone-learning-rate`.

Đánh giá lại:

```bash
uv run garbage-evaluate --data-dir "duong/dan/toi/dataset" --checkpoint "artifacts/lan1/best_model.pt" --output "artifacts/lan1/evaluation.json"
```

Dự đoán một ảnh:

```bash
uv run garbage-predict "anh.jpg" --checkpoint "artifacts/lan1/best_model.pt"
```

## Giao diện desktop và API

**Desktop (PyQt5)** — từ `trash_ai_ui`, cần `pip install -r requirements.txt`:

```bash
python giao_dien_pyqt.py
```

**API (Flask)** — từ `trash_ai_ui`:

```bash
python app.py
```

Gửi `POST /predict` kèm file ảnh, trả về JSON có `class`, `ten`, `confidence`, `chac_chan`,
`goi_y_xu_ly`, `all_scores`.

**Web `frontend/`, desktop, API và `backend/` cùng dùng ResNet-18 8 loại** (xem đầu file),
gộp thành 4 nhóm theo cùng một cách, nên cho cùng kết quả. Riêng `trash_ai_ui/index.html`
còn dùng model Teachable Machine cũ (37/49).

---

## Những chỗ cần biết trước khi dùng

**Ngưỡng tin cậy 60%.** Dưới mức này giao diện báo "không chắc chắn" và không đưa gợi ý
xử lý. Đây là thiết kế có chủ đích: khi model sai, nó thường sai ở vùng 25–50%, nên chặn lại
tốt hơn là khuyên bừa.

**Model Teachable Machine thì ngược lại.** Cùng tấm ảnh kiện giấy phế liệu, nó trả về
`Glass 99,5%` — sai nhưng tự tin, vượt ngưỡng nên vẫn đưa lời khuyên sai. Model ResNet-18
trên cùng ảnh đó trả 40,8% và bị chặn. Với ứng dụng khuyên người ta vứt rác, **sai mà tự tin
nguy hiểm hơn sai mà biết ngập ngừng**.

**Lớp yếu nhất là `plastic`** (86,7% ngay cả trên ảnh dataset). Chai nhựa trong và chai
thủy tinh trông rất giống nhau.

**Bộ test 49 ảnh là thước đo yếu.** Sai số khoảng ±7 điểm, và không có lớp `clothes`
(tìm mãi không ra ảnh quần áo cũ hợp lệ trên Wikimedia). Chỉ nên tin những chênh lệch
lớn hơn 10 điểm.

## Nguồn dữ liệu

Dataset không đẩy lên git vì dung lượng. Các bộ đã dùng:

- **TrashNet** — [github.com/garythung/trashnet](https://github.com/garythung/trashnet)
- **Garbage Classification (Kaggle)** — bản mở rộng của TrashNet, thêm `battery` và `clothes`
- **Bộ 11.107 ảnh** — đa dạng hơn, có ảnh chụp trong nhà thật
- **49 ảnh test đời thực** — Wikimedia Commons, giấy phép tự do, nguồn và tác giả ghi
  trong `realworld_curated/manifest.json`

## Ghi chú

Phần `trash_ai_ui/` ban đầu do một thành viên khác viết cho model Teachable Machine.
Ở đây đã được chuyển sang dùng model ResNet-18; hai file gốc giữ lại dưới dạng `.bak`.
