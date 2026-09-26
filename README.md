# Phân loại rác — 7 lớp

Pipeline huấn luyện ResNet-18 (PyTorch) phân loại ảnh rác thành 7 nhóm:
`battery`, `cardboard`, `clothes`, `glass`, `metal`, `paper`, `plastic`.

Kèm ba giao diện sử dụng: desktop (PyQt5), web (Gradio + TensorFlow.js), và API (Flask).

---

## Kết quả — đọc kỹ cả hai cột

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
  app.py                   Web demo Gradio
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

## Ba giao diện

**Web (Gradio)** — từ `garbage_classifier`:

```bash
uv run python app.py
```

Mở `http://127.0.0.1:7860`.

**Desktop (PyQt5)** — từ `trash_ai_ui`, cần `pip install -r requirements.txt`:

```bash
python giao_dien_pyqt.py
```

**API (Flask)** — từ `trash_ai_ui`:

```bash
python app.py
```

Gửi `POST /predict` kèm file ảnh, trả về JSON có `class`, `confidence`, `chac_chan`,
`goi_y_xu_ly`, `all_scores`.

Desktop và API dùng chung `phan_loai_rac.py` nên **luôn cho cùng kết quả**.
Riêng `index.html` vẫn chạy model Teachable Machine cũ nên kết quả lệch.

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
