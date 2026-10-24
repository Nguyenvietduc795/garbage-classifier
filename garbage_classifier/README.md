# Garbage Classifier — PyTorch

Pipeline hiện đại để huấn luyện mô hình phân loại ảnh rác thành 7 lớp: `Battery`, `Cardboard`, `Clothes`, `Glass`, `Metal`, `Paper`, `Plastic`.

## Plan và kiến trúc

1. Kiểm tra 1.400 ảnh trong `../dataset_sach_zip`.
2. Chia cân bằng từng lớp theo tỷ lệ 70/15/15: 140 train, 30 validation, 30 test.
3. Dùng augmentation chỉ trên train; validation/test dùng preprocessing cố định.
4. Fine-tune ResNet-18 pretrained trên ImageNet: đóng băng backbone 2 epoch đầu, sau đó mở toàn bộ mạng.
5. Dùng AdamW, cosine learning-rate schedule, label smoothing, mixed precision trên CUDA và early stopping.
6. Lưu `best_model.pt`, `last_model.pt`, lịch sử, metrics và confusion matrix dạng JSON.
7. Đánh giá độc lập và dự đoán một ảnh bằng checkpoint tốt nhất.

```text
Ảnh theo thư mục lớp
  -> split cân bằng 70/15/15
  -> augmentation + normalize
  -> ResNet-18 transfer learning
  -> validation chọn model tốt nhất
  -> test + confusion matrix
  -> predict ảnh mới
```

## Cài môi trường

Yêu cầu: Windows, `uv`, NVIDIA driver mới nếu dùng GPU. Từ thư mục này:

```powershell
uv sync
```

Lệnh trên tạo `.venv` và cài đúng các version trong `pyproject.toml`. Lần train pretrained đầu tiên, TorchVision tải trọng số ResNet-18 chính thức về máy.

## 1. Kiểm tra dataset

```powershell
uv run garbage-data --data-dir "../dataset_sach_zip"
```

Lệnh phải báo 980 train, 210 validation, 210 test và không có ảnh lỗi.

## 2. Smoke test nhanh

Kiểm tra toàn pipeline trên một phần nhỏ dữ liệu, không tải pretrained weights:

```powershell
uv run garbage-train --data-dir "../dataset_sach_zip" --output-dir "artifacts/smoke" --epochs 2 --freeze-epochs 0 --max-images-per-class 12 --no-pretrained --num-workers 0
```

Accuracy của smoke test không có ý nghĩa; mục tiêu chỉ là xác nhận code, GPU và checkpoint hoạt động.

## 3. Train đầy đủ

```powershell
uv run garbage-train --data-dir "../dataset_sach_zip" --output-dir "artifacts/full" --epochs 20 --batch-size 32
```

Với RTX 4060 Laptop 8GB, hãy bắt đầu bằng batch 32. Nếu thiếu VRAM, giảm xuống `--batch-size 16`. Nếu muốn ép dùng CPU, thêm `--device cpu`.

Artifacts:

- `artifacts/full/best_model.pt`: model có validation accuracy cao nhất.
- `artifacts/full/last_model.pt`: trạng thái epoch cuối.
- `artifacts/full/dataset_split.json`: số lượng ảnh của từng split/lớp.
- `artifacts/full/history.json`: loss, accuracy và thời gian từng epoch.
- `artifacts/full/metrics.json`: test accuracy, per-class accuracy và confusion matrix.

## 4. Đánh giá lại

```powershell
uv run garbage-evaluate --data-dir "../dataset_sach_zip" --checkpoint "artifacts/full/best_model.pt" --output "artifacts/full/evaluation.json"
```

Confusion matrix dùng hàng là nhãn thật, cột là nhãn dự đoán; thứ tự lớp nằm trong trường `classes`.

## 5. Dự đoán một ảnh

```powershell
uv run garbage-predict "../dataset_sach_zip/Plastic/plastic1.jpg" --checkpoint "artifacts/full/best_model.pt"
```

Đổi đường dẫn đầu tiên thành ảnh cần nhận diện. Kết quả gồm top 3 lớp và xác suất.

## Tuỳ chọn quan trọng

```text
--epochs 20                 số epoch tối đa
--patience 5                dừng sớm nếu validation không cải thiện
--freeze-epochs 2           chỉ train classifier trong 2 epoch đầu
--batch-size 32             số ảnh mỗi batch
--num-workers 4             tiến trình đọc ảnh
--device auto|cuda|cpu      thiết bị tính toán
--no-pretrained             không tải trọng số ImageNet
--max-images-per-class N    giới hạn dữ liệu để smoke test
```

## Nguồn kỹ thuật

- [PyTorch — Get Started](https://pytorch.org/get-started/locally/)
- [TorchVision documentation](https://pytorch.org/vision/stable/)

Nội dung kỹ thuật từ tài liệu được diễn giải lại để tuân thủ yêu cầu cấp phép.

## Tuỳ chọn thêm (01/10/2026)

- `--arch resnet18 | mobilenet_v3_large` — chọn kiến trúc. MobileNetV3 nhẹ hơn (~4 MB khi nén)
  nhưng trên ảnh đời thực kém hơn ResNet-18 rõ rệt (40/49 so với 44/49).
- `--balance-classes` — lấy mẫu mỗi lớp ngang nhau khi train. Đã thử: không giúp, còn làm kém đi.
- `--oversample battery=2` — chỉ lấy mẫu một lớp nhiều hơn N lần, các lớp khác giữ tỉ lệ tự
  nhiên; lặp lại được cho nhiều lớp. Đã thử với pin trên `dataset_8lop_v3`: chỉ +2/27 ảnh pin.
- `garbage-export-onnx` (cần `uv sync --extra export`) — xuất checkpoint sang ONNX để chuyển
  tiếp sang TF.js. Các bước còn lại xem README ở thư mục gốc.
