# Phân loại rác — 8 loại, 4 nhóm

Pipeline huấn luyện ResNet-18 (PyTorch) phân loại ảnh rác thành 8 loại vật liệu:
`battery`, `cardboard`, `clothes`, `glass`, `metal`, `organic`, `paper`, `plastic`.
Giao diện gộp lại thành **4 nhóm**: hữu cơ, tái chế, không thể tái chế, nguy hại.

Kèm các giao diện sử dụng: web (`frontend/`, Vercel), desktop (PyQt5) và API (Flask).

---

## Model đang chạy trên web: v5 (24/10/2026)

`frontend/models/r18-8lop-v5` — ResNet-18 train trên `dataset_8lop_v5` (19.657 ảnh, thêm ảnh
pin thật). Luật pin: xác suất pin ≥ 50% thì báo nguy hại, dưới 50% thì chọn loại cao nhất
trong 7 loại còn lại (bỏ luật "có thể là pin" ở 30% của bản v2). Số đo xem mục **v5** bên dưới.

| | Trước (v2 + luật pin 30%) | Sau (v5 + luật pin 50%) |
|---|---|---|
| Nhận ra pin | cứ 10 pin bỏ sót 4 | cứ 10 pin bỏ sót 2 |
| Báo nhầm thành pin | 47 lần | 45 lần |
| Đúng nhóm, 1.642 ảnh rác chụp thật | 86,9% | 91,2% |
| Hữu cơ (/300) | 250 | 250 |
| Quần áo chụp thật | — | 31/43 (bộ test mới, xem mục **v6**) |

Dòng "quần áo sai hết" trước đây là do bộ test: phần lớn ảnh "quần áo" trong đó không có
quần áo (thùng thu gom, logo chữ…). Đã lọc lại — xem mục **v6**.

Bản v2 vẫn giữ ở `frontend/models/r18-8lop-v1`; muốn quay lại thì đổi `THU_MUC_MODEL` và
khôi phục luật pin cũ (commit `d364ddf`).

## v6: bộ test quần áo mới + thêm quần áo cũ thật (24/10/2026) — chưa đưa lên web

**Bộ test quần áo cũ đo sai.** 7/10 ảnh "quần áo" không có quần áo làm vật chính (cây treo
vải, thùng thu gom quần áo, xe tải chở kiện vải, hộp điện, logo chữ). Đã chuyển sang
`realworld_loai_bo/` (lý do ghi trong `manifest.json`), còn lại 1 ảnh ở `realworld_test` và
2 ảnh ở `realworld_mta_test`.

**Bộ test mới `realworld_clothes_test`** (43 ảnh): Wikimedia Commons, lọc tay từng ảnh — giày
cũ vứt trên vỉa hè/cỏ/bùn, quần áo đổ đống bên đường, giẻ treo, áo bỏ trên cầu thang. Bỏ ảnh
người mặc, ảnh sản phẩm, tranh vẽ. Lọc trùng dHash với train (gần nhất cách 10 bit). Mới lọc
420/1.103 ảnh ứng viên (Commons giới hạn tốc độ tải); phần lớn là giày, ít quần áo.

**Dữ liệu train thêm** (đều là đồ cũ thật chụp trải phẳng trên nền trắng, không có bối cảnh rác):

- `dataset_8lop_v6a` = v5 + **1.000 ảnh RISE** "Clothing Dataset for Second-Hand Fashion"
  (CC BY 4.0, bản front-only trên Hugging Face): chọn `usage = Recycle` hoặc `condition ≤ 2`,
  ưu tiên đồ thủng/bẩn, mỗi loại đồ ≤ 15%, cắt sát món đồ.
- `dataset_8lop_v6b` = v6a + **575 ảnh Na Uy** "Norway post-consumer garment data" (CC BY-SA
  4.0, Zenodo, chỉ tải khu F 8,3 GB): chỉ lấy món `Sorted_as = T_waste` (đồ vứt bỏ), bỏ ảnh
  nhãn mác/thẻ số, cắt theo vùng vật lớn nhất.
- Train giống hệt v5 (15 epoch, batch 32, không augmentation mạnh). Lớp `clothes`: 3.656 →
  4.656 (v6a) → 5.231 (v6b).

Đo bằng `uv run python -m garbage_classifier.realworld` (đúng luật web: tăng sáng ảnh tối, pin
≥ 50%, đúng theo 4 nhóm, bỏ trùng MD5). Bộ test cũ đã bỏ 7 ảnh nên số khác bảng trước.

| | v5 (web) | v6a | v6b |
|---|---|---|---|
| **Quần áo thật** `realworld_clothes_test` (43) | **31** | 30 | 29 |
| `realworld_test` (43) · `test2` (52) · `curated` (49) | 28 · 39 · 40 | 26 · 42 · 41 | 27 · **43** · **43** |
| MTA (175) · Bower (313) · BDWaste (196) | 165 · 281 · 196 | 168 · 282 · 195 | 166 · 282 · 196 |
| rw5 (1.642) | 1.498 (91%) | 1.498 (91%) | **1.512 (92%)** |
| **Tổng đúng nhóm, 8 bộ (2.513)** | 2.278 | 2.282 | **2.298** |
| Báo nhầm thành pin (8 bộ) | 47 | 50 | **35** |
| Báo nhầm thành quần áo (8 bộ) | 75 | 78 | **69** |
| `realworld_pin_test` (141) | 107 | **112** | 111 |

- **Quần áo chụp trải phẳng không giúp nhận quần áo trong rác**: 31 → 30 → 29/43 (chênh trong
  sai số). Ảnh còn sai là giày nhỏ giữa vỉa hè/cỏ, quần áo đổ đống lẫn rác, mũ/áo nhàu —
  model đoán giấy/nhựa/kim loại. Thứ còn thiếu là ảnh đồ **trong bối cảnh rác**, không phải
  thêm ảnh đồ cũ.
- Nền trắng của RISE/Na Uy **không** làm model đoán bừa sang quần áo (báo nhầm 75 → 69).
- v6b nhỉnh hơn v5 ở lần train đầu (+20 ảnh, ít báo nhầm pin hơn), nhưng **train lại 3 seed
  thì hết chênh** (seed đổi cả cách chia train/val) — nên **giữ v5 trên web**:

  | 3 lần train (seed 42 · 1 · 2) | v5 | v6b |
  |---|---|---|
  | Quần áo thật (/43) | 31 · 29 · 29 (TB 29,7) | 29 · 31 · 27 (TB 29,0) |
  | Tổng đúng nhóm, 8 bộ (/2.513) | 2.278 · 2.278 · 2.291 (TB 2.282) | 2.298 · 2.265 · 2.290 (TB 2.284) |
  | Báo nhầm thành pin | 47 · 47 · 41 | 35 · 74 · 39 |
  | Báo nhầm thành quần áo | 75 · 72 · 74 | 69 · 70 · 70 |
  | `realworld_pin_test` (/141) | 107 · 111 · 110 | 111 · 114 · 115 |

  Cùng một dataset, chỉ đổi seed đã lệch tới 33 ảnh tổng và 39 lần báo nhầm pin (v6b seed 1)
  — mọi chênh lệch nhỏ hơn thế giữa hai model đơn lẻ đều không đáng tin.
- Số v5 đo lại bằng script mới lệch README cũ 1 ảnh ở MTA (165 so với 166) và 3 ảnh ở
  `realworld_pin_test` (107 so với 110).

## Model v2 (01/10/2026) — chạy trên web tới 24/10/2026

`frontend/` chạy **ResNet-18 8 loại ngay trong trình duyệt** (TensorFlow.js, nén uint8,
11 MB) — không cần server, ảnh không rời máy người dùng.

Đo trên 49 ảnh đời thực (`realworld_curated`), tính đúng **theo 4 nhóm**:

| Model | Đúng | Pin (13 ảnh) |
|---|---|---|
| Teachable Machine 4 nhóm (MobileNet, chỉ train phần đầu) | 37/49 | 5 |
| ResNet-18 7 lớp cũ (`new11k`, chưa có hữu cơ) | 43/49 | 9 |
| **ResNet-18 8 lớp (`v2_r18`) ← web lúc đó** | **44/49** | **11** |
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

| Bộ test | v2 (web lúc đó) | v3 | v3 + `--oversample battery=2` |
|---|---|---|---|
| `realworld_curated` (49) | **44** | 42 | 41 |
| `realworld_test` (49, bộ cũ trước khi bỏ 6 ảnh) | 22 | **29** | 27 |
| `realworld_test2` (53, bộ cũ trước khi bỏ 1 ảnh) | 43 | **45** | 43 |
| **3 bộ, bỏ ảnh trùng (102)** | 65 (64%) | **74 (73%)** | — |
| **Pin**, bỏ ảnh trùng (14) | **10** | 7 | — |
| `realworld_mta_test` (175, cùng nguồn với dữ liệu train) | 146 | 170 | 170 |

**Ba bộ `realworld_*` trùng ảnh nhau:** `realworld_curated` lấy lại ảnh từ hai bộ kia, nên
151 ảnh chỉ có 102 ảnh khác nhau (so MD5), pin 27 ảnh chỉ có 14. Cộng thẳng 3 bộ (109 / 116,
pin 20 / 14) là đếm một ảnh hai lần — mọi con số "151 ảnh" cũ nên đọc theo dòng 102.

v3 đúng nhiều hơn trên ảnh thật nói chung nhưng **nhận pin kém đi** — dữ liệu mới không có
ảnh pin nào, pin bị các lớp khác lấn át. Lấy mẫu pin gấp đôi không chữa được. Vì pin là rác
nguy hại, web giữ v2. Việc cần làm tiếp: tự chụp 200–300 ảnh pin thật (nhiều nền, đèn vàng,
chỗ tối) rồi train lại v3. Vẫn chưa có bộ test ảnh tối nên chưa đo được độ bền ánh sáng.

### Xử lý thêm trên web, không train lại (model v2)

Ba bước thêm trước và sau khi chạy model trong `frontend/index.html`:

- **Cân bằng độ sáng:** ảnh có độ sáng trung bình < 0,30 thì nâng gamma cho độ sáng về
  ~0,45; ảnh đủ sáng giữ nguyên. Kết quả hiện thêm "ảnh tối, đã tự tăng sáng".
- **Ngưỡng tin cậy 0,5:** nhóm được chọn có xác suất < 50% thì hiện "Chưa chắc" thay vì đoán.
- **Ưu tiên pin:** xác suất pin ≥ 30% thì hiện "Có thể là rác nguy hại", kể cả khi pin không
  phải lớp cao nhất. Pin là rác nguy hại nên bỏ sót tệ hơn báo nhầm.

Đo trên 102 ảnh không trùng (PyTorch), số ảnh đúng theo 4 nhóm. Chưa có ảnh tối thật nên làm
tối giả (còn 25% độ sáng):

| | Đúng nhóm | Pin đúng (/14) | Báo nhầm thành pin |
|---|---|---|---|
| v2 gốc | 65 | 10 | 4 |
| + cân bằng độ sáng | 65 | 10 | 4 |
| + ưu tiên pin 30% (**web lúc đó, v2**) | **65** | **10** | 4 |
| Ảnh tối giả, v2 gốc | 58 | 7 | 6 |
| Ảnh tối giả, + cân bằng độ sáng | 68 | 8 | 3 |

Trên trình duyệt (web lúc đó, v2): 63/102 đúng nhóm, pin 11/14, báo nhầm pin 5; ảnh tối giả
66/102. Lệch vài ảnh so với PyTorch vì trình duyệt thu nhỏ ảnh hơi khác.

**Ưu tiên pin chỉ sửa được 1 ảnh** (pin AA rò rỉ, xác suất pin 34%, trước bị đoán thủy tinh),
và ngưỡng 30% được chọn trên chính bộ test này — đây là quy tắc an toàn, không phải model tốt
hơn. Hạ xuống 20% không nhận thêm pin nào mà báo nhầm tăng từ 4 lên 8. 3 ảnh pin v2 vẫn sai:
vỉ pin còn bao bì giấy (đoán bìa), pin nhỏ nằm ở mép trên ảnh mạch điện (bị cắt mất khi lấy
phần giữa ảnh), và ảnh *thùng thu gom pin* — ảnh này không có pin, không nên tính là lỗi.

Ngưỡng tin cậy (đã có ưu tiên pin), đúng – sai – "Chưa chắc" trên 102 ảnh — số đo ở giai đoạn v2,
chưa tái hiện được bằng script hiện tại; số của v5 (đang chạy) xem bảng 5.4 trong báo cáo:
0,4 → 67-20-15; 0,5 → 64-19-19; 0,6 → 59-13-30.

| Ngưỡng | Đúng | Sai | Chưa chắc |
|---|---|---|---|
| 0,4 | 65 | 28 | 9 |
| **0,5 (chọn ở giai đoạn v2)** | 64 | 23 | 15 |
| 0,6 | 61 | 16 | 25 |

Giữ 0,5: lên 0,6 bớt 7 lần sai nhưng 3 ảnh đúng bị đổi thành "Chưa chắc", và cứ 4 ảnh thì
1 ảnh không có câu trả lời.

---

## Thêm pin chụp thật + rác Nam Á (24/10/2026) — chưa đưa lên web

`dataset_8lop_v4` (19.157 ảnh) = v3 + hai bộ mới, train y như v3 (15 epoch, batch 32):

- **Bower waste annotations** (Hugging Face, MIT): ảnh điện thoại, pin cũ đổ đống trên bàn,
  sàn, trong lọ, còn trong vỉ. 438 box pin nhưng **chỉ nằm trong 53 ảnh**, box nhỏ (cạnh ngắn
  trung vị 35 px) — mỗi ảnh lấy 1 mẫu là cả cụm pin, thêm box pin riêng ≥ 80 px. Lấy cả vật
  không phải pin của Bower để model không học "nền Bower = pin". 20% số ảnh giữ làm
  `realworld_bower_test`. Thêm được **59 ảnh pin** train.
- **BDWaste** (Mendeley, CC BY 4.0): ảnh điện thoại ở Dhaka — vỏ trái cây, vỏ trứng, cơm,
  nilon, gói snack, chai PET, ly giấy, mảnh kính. 649 ảnh là bản xoay/lật của ảnh khác (bộ gốc
  có augmentation) → bỏ. Thêm 980 ảnh train, 15% giữ làm `realworld_bdw_test`.
- **Real-World Waste 5 class** (Kaggle `tuhanasinan`, CC BY 4.0): 1.647 ảnh (1.642 sau khi bỏ 5 ảnh trùng MD5) tự chụp ở khuôn
  viên trường, **chỉ dùng để test** → `realworld_rw5_test`. Đây là bộ test ảnh thật lớn nhất
  hiện có, nguồn khác hẳn dữ liệu train; có 300 ảnh hữu cơ thật.

Số ảnh đúng theo 4 nhóm (bỏ ảnh trùng MD5 trong từng bộ):

| Bộ test | v2 (web) | v3 | v4 |
|---|---|---|---|
| 102 ảnh cũ | 65 | **74** | 71 |
| — pin (/14) | **10** | 7 | 6 |
| `realworld_rw5_test` (1.642) | 1.425 (87%) | 1.522 (93%) | **1.534 (93%)** |
| — hữu cơ (/300) | 250 | 226 | **251** |
| `realworld_bower_test` (313, pin 11) | 254, pin 10 | 280, pin 9 | **281, pin 11** |
| `realworld_bdw_test` (196) | 153 | 166 | 196 ⚠ |
| `realworld_mta_test` (175) | 146 | **170** | 167 |

- **Hữu cơ thật khá lên rõ** (226 → 251/300 trên bộ độc lập), nhờ BDWaste.
- **Pin vẫn chưa chữa được:** đúng 11/11 trên ảnh Bower nhưng chỉ 6/14 trên 102 ảnh cũ —
  59 ảnh pin train từ một nguồn là quá ít; model học được "đống pin kiểu Bower", chưa học được pin nói
  chung. Web vẫn giữ v2.
- `realworld_bdw_test` 100% là **không đáng tin**: ảnh cùng một người chụp, cùng nền, chỉ
  khác góc — dHash không bắt được hết các ảnh gần giống đó. Đừng dùng bộ này để so model.
- Cả ba model đều sai **8/8 ảnh quần áo** trong 102 ảnh cũ (không phải bộ `realworld_clothes_test`).

## v5: thêm ~500 ảnh pin thật (24/10/2026) — pin tốt hơn mà không bị đổi chác

`dataset_8lop_v5` = v4 + ảnh pin **lọc tay từng ảnh**:

- **Open Images V7** (nhãn ảnh "Battery" do người kiểm, ảnh Flickr CC BY 2.0): 428 ảnh, tải
  được 363, giữ 245 — bỏ khoang máy ô tô, màn hình hiện biểu tượng pin, kệ siêu thị.
- **Wikimedia Commons** (các mục pin AA/AAA, cúc áo, sạc dự phòng, pin điện thoại/máy ảnh, pin
  rỉ sét, thùng thu gom…): 1.124 ảnh, giữ 703. Bỏ 11 ảnh đã có trong bộ test.
- Lọc trùng dHash (cả bản xoay/lật) với v4 và mọi bộ test → thêm 500 ảnh pin train
  (pin 815 → 1.315). 20% ảnh pin mới giữ làm `realworld_pin_test` (141 ảnh).

v5 nhận pin tốt hẳn nhưng **báo nhầm thành pin nhiều hơn** (lon, chai kim loại → pin). Chữa
bằng ngưỡng: pin chỉ khi P(pin) ≥ t, không thì lấy lớp cao nhất **không tính pin**. Chọn t
trên một nửa các bộ test (chia theo MD5), nửa còn lại để báo cáo — không chỉnh trên chính
số liệu báo cáo.

| | v2 + ưu tiên pin 30% (**web lúc đó**) | v5, t = 0,5 | v5, t = 0,7 |
|---|---|---|---|
| 102 ảnh cũ: đúng nhóm · pin /14 · báo nhầm | 65 · 10 · 4 | 67 · 10 · 5 | **70** · 9 · **1** |
| `realworld_pin_test` (141 pin) | 77 (54,6%) | **107 (75,9%)** | 95 (67,4%) |
| `realworld_rw5_test` (1.642): đúng · báo nhầm | 86,9% · 21 | 91,2% · 35 | **92,8% · 8** |
| `realworld_bower_test` (313): đúng · pin /11 · nhầm | 250 · 10 · 20 | 281 · 9 · 5 | **283** · 8 · **2** |
| `realworld_mta_test` (175): đúng · báo nhầm | 144 · 2 | **165** · 0 | **165** · 0 |
| **Tổng pin nhận đúng (/166)** | 97 | **126** | 112 |
| **Tổng báo nhầm thành pin** (102 ảnh cũ + rw5 + Bower + MTA) | 47 | 45 | **11** |

- **v5 + t = 0,5 đúng nhóm cao hơn v2 ở mọi bộ test**, nhận đúng thêm 29 ảnh pin, báo nhầm
  thành pin tương đương (45 so với 47). Cột v2 đo lại bằng `realworld.py --nguong-pin 0.3`. t = 0,7 gần như hết báo nhầm nhưng bỏ sót pin nhiều hơn t = 0,5.
- `realworld_pin_test` cùng nguồn (Open Images, Commons) với ảnh pin train nên con số 75,9% là
  lạc quan. Trên 14 + 11 pin của các bộ khác, v5 ngang v2 (19 so với 20, trong sai số).
- 8 ảnh quần áo trong 102 ảnh cũ vẫn sai cả 8 (bộ quần áo mới 43 ảnh: 31/43, xem mục **v6**).

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
có bản torch **CPU-only** cho Windows — cài nhầm bản đó thì train chậm hơn khoảng **24 lần**
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

**Web `frontend/` chạy v5** (luật pin 50%, tăng sáng ảnh tối). **API `backend/` và giao diện
desktop vẫn dùng v2** (`backend/model.pt`, `trash_ai_ui/garbage_resnet18.pt`), chọn loại cao nhất
trong 8 loại, chưa có luật pin, nên kết quả có thể khác web. Riêng `trash_ai_ui/index.html`
còn dùng model Teachable Machine cũ (37/49).

---

## Những chỗ cần biết trước khi dùng

**Ngưỡng tin cậy 50%.** Dưới mức này giao diện báo "không chắc chắn" và không đưa gợi ý
xử lý. Đây là thiết kế có chủ đích: khi model sai, nó thường sai ở vùng 25–50%, nên chặn lại
tốt hơn là khuyên bừa.

**Model Teachable Machine thì ngược lại.** Cùng tấm ảnh kiện giấy phế liệu, nó trả về
`Glass 99,5%` — sai nhưng tự tin, vượt ngưỡng nên vẫn đưa lời khuyên sai. Model ResNet-18
trên cùng ảnh đó trả 40,8% và bị chặn. Với ứng dụng khuyên người ta vứt rác, **sai mà tự tin
nguy hiểm hơn sai mà biết ngập ngừng**.

**Lớp yếu nhất của v2 là `plastic`** (86,7% ngay cả trên ảnh dataset; ở v5 là `cardboard` 85,9%, `plastic` 87,2%). Chai nhựa trong và chai
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
- **Bower waste annotations** (MIT) — [huggingface.co/datasets/BowerApp/bower-waste-annotations](https://huggingface.co/datasets/BowerApp/bower-waste-annotations)
- **BDWaste** (CC BY 4.0) — [data.mendeley.com/datasets/96g5pgfnfw](https://data.mendeley.com/datasets/96g5pgfnfw)
- **Clothing Dataset for Second-Hand Fashion** (RISE, CC BY 4.0) — [zenodo.org/records/12518734](https://zenodo.org/records/12518734), bản front-only [huggingface.co/datasets/fnauman/fashion-second-hand-front-only-rgb](https://huggingface.co/datasets/fnauman/fashion-second-hand-front-only-rgb)
- **Norway post-consumer garment data and images** (CC BY-SA 4.0) — [zenodo.org/records/20440761](https://zenodo.org/records/20440761)
- **Bộ test quần áo** `realworld_clothes_test` — Wikimedia Commons, nguồn, giấy phép, tác giả
  trong `realworld_clothes_test/manifest.json`
- **Real-World Waste 5 class** (CC BY 4.0, chỉ để test) — [kaggle.com/datasets/tuhanasinan/real-world-waste-classification-dataset-5-class](https://www.kaggle.com/datasets/tuhanasinan/real-world-waste-classification-dataset-5-class)

## Ghi chú

Phần `trash_ai_ui/` ban đầu do một thành viên khác viết cho model Teachable Machine.
Ở đây đã được chuyển sang dùng model ResNet-18; hai file gốc giữ lại dưới dạng `.bak`.
