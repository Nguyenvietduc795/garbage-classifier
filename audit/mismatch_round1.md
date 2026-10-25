# Bảng lệch số liệu – Vòng 1

Nguồn "Đúng":
- `audit/numbers_ledger.json` (Agent Kiểm kê, 3.313 mục).
- `audit/join_extra.json`: các số tổng hợp, tính từ `audit/eval_realworld/*_probs.json` bằng `audit/scripts/join_extra.py`.

Nguồn "Đang ghi": `audit/numbers_in_docs.csv` (Agent Đối chiếu, 667 dòng) và `audit/internal_consistency.md`.

Quy ước:
- Luật web: Resize 256 + CenterCrop 224, tăng sáng ảnh tối, P(pin) ≥ t thì báo nguy hại, tính đúng theo 4 nhóm, bỏ ảnh trùng MD5 trong từng bộ.
- % = tử/mẫu, làm tròn 1 chữ số thập phân.
- Chưa sửa file nào.

## 0. Cần bạn chốt trước khi sửa (nhiều phiên bản)

| Câu hỏi | Bằng chứng | Đề xuất |
|---|---|---|
| Model chuẩn của báo cáo là bản nào? | Web nạp `models/r18-8lop-v5` (`frontend/index.html:150`); lớp fc khớp `v5_r18/best_model.pt` (seed 42). Docx gọi v5 là "triển khai". | **v5_r18 seed 42, ngưỡng pin 0,5** |
| Backend/API dùng bản nào? | `backend/model.pt` trùng hoàn toàn state_dict với **v2_r18** (`audit/model_identity.json`), và dùng argmax 8 lớp, không có luật pin (`backend/app.py:118`). | Hoặc thay `model.pt` bằng v5 và thêm luật pin, hoặc sửa docx Mục 6.1 và README:420-421 để nói rõ API vẫn là v2. **Đây là sửa code, không chỉ sửa số.** |
| Bộ test 43/52 hay 49/53? | Hiện tại: `realworld_test` 43 ảnh, `test2` 52 ảnh. 7 ảnh đã chuyển sang `realworld_loai_bo` (6 + 1). Bộ cũ 49 + 53 = 102 = 43 + 52 + 7. | Dùng 43/52 cho số hiện tại; số đo trên 49/53 ghi là "bộ cũ". |

## 1. Lệch so với dữ liệu/model thật

| # | Vị trí | Chỉ số | Đang ghi | Đúng (ledger) | Nguồn | Đề xuất sửa |
|---|---|---|---|---|---|---|
| 1 | docx Bảng 4.5 (tr.18), cột "v5, t = 0,5" | realworld_pin_test, pin đúng | 110 (78%) | **107/141 = 75,9%** | ledger `realworld_pin_test.v5_r18.nguong0.5.pin_dung`; khớp stdout của realworld.py gốc | 107 (75,9%) |
| 2 | docx Mục 5.6.2 P345 (tr.24) | % pin_test v5 | "78%" | **75,9%** | như #1 | "75,9%" |
| 3 | docx Bảng 4.5, MTA, cột v5 t = 0,5 | MTA đúng nhóm | 166 | **165/175 = 94,3%** | `realworld_mta_test.v5_r18.nguong0.5.dung_4nhom` | 165 |
| 4 | docx Bảng 4.5, MTA, cột v5 t = 0,7 | MTA đúng nhóm | 166 | **165/175** | join_extra `v5 t=0.7 realworld_mta_test` | 165 |
| 5 | docx Bảng 4.5, "Tổng pin nhận đúng (/166)", cột v5 t = 0,5 | 10 (102 ảnh cũ) + 107 (pin_test) + 9 (Bower) | 129 | **126/166 = 75,9%** | join_extra | 126 |
| 6 | docx Bảng 4.5, pin_test, cột v5 t = 0,7 | pin đúng | 97 (69%) | **95/141 = 67,4%** | join_extra `v5 t=0.7 realworld_pin_test` | 95 (67,4%) |
| 7 | docx Bảng 4.5, Tổng pin, cột v5 t = 0,7 | 9 + 95 + 8 | 114 | **112/166** | join_extra | 112 |
| 8 | docx Bảng 4.5, rw5, cột v5 t = 0,7 | đúng % · báo nhầm | 93% · 8 | 1524/1642 = **92,8%** · 8 | join_extra | "92,8% · 8" (nếu làm tròn số nguyên thì vẫn là 93%) |
| 9 | docx Kết luận P375 (tr.29) | tổng pin v5 | "129/166 … (mô hình cũ: 103)" | **126/166**; số của model cũ không tái hiện được (xem #22) | như #5 | "126/166". Đổi luôn số của model cũ sau khi chốt #22. |
| 10 | README:86-87 | ghi chú "đo lại lệch 165 so với 166, 107 so với 110" | đúng là lệch | ledger xác nhận 165 và 107 | – | Giữ ghi chú nhưng bỏ số cũ khỏi docx. Docx không có ghi chú này. |
| 11 | docx Bảng 3.2 hàng 7 (tr.10) | số ảnh Bower thêm vào v4 | "+59 ảnh pin và vật khác" | **+596 ảnh**, trong đó 59 pin; còn lại 143 bìa, 129 thủy tinh, 87 kim loại, 43 giấy, 132 nhựa, 3 quần áo | `dataset_8lop_v4.tong.nguon[Bower].so_anh` = 596; `…battery.nguon[Bower]` = 59 | "+596 ảnh (59 pin)" |
| 12 | docx Bảng 3.1 hàng v4 (tr.10) | thành phần v4 | "+ Bower (pin chụp thật) + BDWaste (980)" | Bower **596**, BDWaste 980; 17.581 + 596 + 980 = 19.157 ✓ | ledger | "+ Bower (596) + BDWaste (980)" |
| 13 | docx Mục 5.6.2 P344 (tr.24) | quần áo v5 | "≈ 30/43" | **31/43 = 72,1%** | `realworld_clothes_test.v5_r18.nguong0.5.dung_4nhom` | "31/43" |
| 14 | README:158-159 | kích thước bộ | `realworld_test` (49), `test2` (53) | hiện tại **43 / 52** (49 = 43 + 6, 53 = 52 + 1 ảnh bị loại) | ledger `so_anh_sau_bo_trung` | Thêm "(bộ cũ, trước khi bỏ 7 ảnh)", hoặc đo lại v2/v3/v3os trên 43/52 |
| 15 | docx Bảng 3.3 (tr.12) "3 bộ chỉ có 102 ảnh khác nhau"; Mục 3.4 P244 "151 ảnh chỉ có 102" | số ảnh cộng thẳng / khác nhau | 151 / 102 | Hiện tại 49 + 43 + 52 = **144** ảnh, **95** ảnh khác nhau (curated = 15 ảnh test + 34 ảnh test2). Pin vẫn 27 → 14 ✓ | Agent Kiểm kê, điểm bất thường 4 | Sửa thành "144 / 95". Hoặc giữ 151/102 nhưng ghi rõ là bộ cũ, vì các Bảng 4.4, 4.5, 5.3, 5.4 dùng 102 ảnh cũ. |
| 16 | docx Bảng 4.4, 4.5, 5.3, 5.4 | tên tập "102 ảnh" | không nói đây là tập cũ | 102 = 43 + 52 + 7 ảnh trong `realworld_loai_bo` (v5 t = 0,5: 67 · 10 · 5 ✓) | join_extra `v5 t=0.5 102cu` | Thêm chú thích: "102 ảnh = realworld_test + test2 trước khi loại 7 ảnh" |
| 17 | docx Bảng 4.6 / Bảng 5.2 "Tổng 8 bộ (2.513)"; "Báo nhầm thành pin 47" | tổng đếm trùng | 2.278 / 2.513; 47 | Số tái hiện **khớp** (2.278; 47), **nhưng** 49 ảnh curated đã nằm sẵn trong test/test2 nên bị đếm 2 lần. Không đếm trùng: **2.238/2.464 = 90,8%**, báo nhầm **45** | join_extra `v5_r18 8bo khong trung curated` | Ghi rõ "có đếm trùng curated", hoặc dùng 7 bộ: 2.238/2.464, báo nhầm 45. Seed 1: 2.237 · 45; seed 2: 2.247 · 40. |
| 18 | README:22 | rw5 hữu cơ (/300), cột v5 | 238 | **250/300 = 83,3%** (v5 t = 0,5; t = 0,3 cũng 250) | `realworld_rw5_test.v5_r18.nguong0.5.organic.dung_4nhom` | 250. Khi đó v2 và v5 bằng nhau ở hữu cơ (250 – 250). |
| 19 | README:228 | số ảnh rw5 | 1.647 | 1.647 ảnh thô, **1.642** sau bỏ 5 bản trùng MD5 | ledger rw5 `so_anh_truoc/sau_bo_trung` | "1.647 ảnh (1.642 sau bỏ trùng)" |
| 20 | index.html:151-152 | ngưỡng tin cậy trên "49 ảnh": 0,5 → 41/3/5; 0,6 → 38/2/9 | 41·3·5 / 38·2·9 | **Không tái hiện được.** Curated 49 ảnh, v5, luật web: 0,5 → **39·4·6**; 0,6 → **35·3·11**. v2: 42·5·2 / 40·3·6. | join_extra `conf * curated49` (độ chắc = tổng xác suất nhóm, như `index.html:178`) | Xóa comment cũ (thuộc model trước v2), hoặc thay bằng số v5 trên 43/52. |
| 21 | docx Bảng 5.4 (tr.22); index.html:155-156 | ngưỡng tin cậy trên 102 ảnh: 65-28-9 / 64-23-15 / 61-16-25 | như trên | **Không tái hiện chính xác.** v5 t = 0,5: **67-20-15 / 64-19-19 / 59-13-30**; v2 + pin 0,3: 64-28-10 / 62-22-18 / 59-15-28 | join_extra | Đo lại bằng v5 rồi thay cả bảng; ghi rõ model và tập. Kết luận "giữ 0,5" vẫn đứng được. |
| 22 | docx Bảng 4.5, cột "v2 + pin 30% (cũ)"; Kết luận "103", "55" | v2 với luật pin 0,3 | 102: 66·11·4; pin_test 82 (58%); rw5 87%·27; Bower 250·10·22; MTA 146; tổng pin 103; báo nhầm 55 | Luật hiện tại (realworld.py, t = 0,3) cho: 102: **65·10·4**; pin_test **77 (54,6%)**; rw5 **86,9%·21**; Bower **250·10·20**; MTA **144**; tổng pin **97**; báo nhầm **45**. Thử thêm biến thể (không tăng sáng, chọn theo tổng nhóm) cũng không ra đúng bộ số đang ghi. | join_extra `v2 pin0.3 *` | Đo lại cột v2 bằng realworld.py (`--nguong-pin 0.3`) rồi thay. Khi đó câu "ít báo nhầm hơn (45 so với 55)" ở Kết luận thành **45 so với 45**, tức không còn ít hơn. Câu này phải viết lại. |
| 23 | docx Bảng 4.5, cột v2: các dòng báo nhầm 4 + 27 + 22 = 53 | tổng | 55 | Nội bộ không cộng khớp (53); theo ledger là 4 + 21 + 20 (+ MTA 2) = 45 hoặc 47 | internal_consistency.md | Sửa theo số đo lại ở #22 |
| 24 | docx Mục 5.6.2 P345 | "19 so với 21 trên 25 ảnh" pin ngoài nguồn | 19 vs 21 | v5: 10 + 9 = **19** ✓; v2 t = 0,3: 10 + 10 = **20** | join_extra | "19 so với 20" (sau khi chốt #22) |
| 25 | index.html:175, backend/app.py:117 | "44 đúng so với 42 / 49" | 44 vs 42 | Đây là số của v2 trên curated (v2 luật backend = 44/49 ✓). Web hiện chạy v5: chọn theo loại **40/49**, theo tổng nhóm chưa đo. | ledger `realworld_curated.v2_r18.luat_backend` | Ghi "(đo với v2)", hoặc đo lại bằng v5 |
| 26 | index.html:166-167 | "nửa A/B: pin 52 → 64/80, báo nhầm 22 → 22; 0,3 → 52" | – | **Không kiểm được**: repo không có định nghĩa nửa A/B | – | Bỏ, hoặc trỏ tới script/split đã dùng |
| 27 | docx Kết luận P375 | accuracy test nội bộ v5 | 91,34% | 2699/2955 = **91,3%** ✓ (91,34% cũng đúng nếu giữ 2 chữ số thập phân) | `v5_r18.test_noi_bo.accuracy` | Đổi thành "91,3%" cho thống nhất cách làm tròn 1 chữ số |

## 2. Lệch nội bộ / diễn đạt (không cần ledger)

| # | Vị trí | Vấn đề | Đề xuất |
|---|---|---|---|
| 28 | index.html:189, 195; app.py:52, 57; trash_ai_ui/README:8-9 | Ví dụ giao diện ghi "Pin, ắc quy" và "Quần áo, dép, khẩu trang", trong khi Bảng 1.1, Mục 1.4 và 5.6.2 nói chưa nhận diện ắc quy và khẩu trang | "Pin (pin tiểu, pin cúc…)" và "Quần áo, giày dép"; bỏ "ắc quy" và "khẩu trang" |
| 29 | README:428; trash_ai_ui/README:71, 92 | Ngưỡng tin cậy ghi 60%; code (`index.html:157`, `app.py:34`) dùng 0,50 | 50% |
| 30 | docx Mục 6.1; README:420-421 | Nói API "cùng quy tắc / cùng kết quả" với web, nhưng API là v2 và chọn argmax, không có luật pin, không tăng sáng | Tùy quyết định ở mục 0 |
| 31 | docx Bảng 5.5 | Cột ghi số của v2 (44/49, 11/13), nhưng hàng "Kiểm soát đầu ra" ghi "Luật pin 50%" (của v5) | Dùng số v5 (curated 40/49, pin 10/13), hoặc ghi luật pin 30% cho v2 |
| 32 | README:250, 282 vs README:23 | "Sai 8/8 quần áo" (8 ảnh trong bộ 102 cũ) lẫn với 31/43 (bộ quần áo mới) | Ghi rõ tên bộ ở cả hai chỗ |
| 33 | docx Mục 3.1 và README:300 "96% cùng nguồn, 57% đời thực" | Ghép 2 model khác nhau (aug/merged và new11k) | Nêu tên model cho mỗi số |
| 34 | docx Mục 4.3 và README:324 "7.922 ảnh → +12,2 điểm" | 7.922 là merged − bộ gốc, còn +12,2 là new11k − big | Viết lại cho cùng một cặp |
| 35 | docx Bảng 3.1 (12.055) vs Bảng 4.2 (8.435) | Bảng 4.2 dùng số ảnh train (≈70%) mà không nói rõ | Thêm "(tập train)" |
| 36 | README:84 | "lệch 35 lần báo nhầm pin" nhưng max − min của 3 seed v6b = 39 | Đo lại hoặc sửa thành 39 |
| 37 | README:365 | "≈20 lần" nhưng 72/3 = 24 | "≈ 24 lần" |
| 38 | frontend/models/r18-8lop-v1 | Thư mục tên "v1" nhưng chứa model v2 (meta.json); docx gọi "v1" là một model khác | Đổi tên thư mục, hoặc ghi chú trong README |

## 3. Đã khớp (không cần sửa)

- **Dataset:** tổng v1 13.506, v2 12.558, v3 17.581, v4 19.157, v5 19.657; v3 thêm RealWaste 3.247 và MTA 1.776; v4 thêm BDWaste 980; v5 thêm +500 pin (815 → 1.315).
- **Kích thước bộ test:** 1.642 / 175 / 313 / 196 / 141 / 43 / 49.
- **Bảng 5.2 (v5, t = 0,5):** rw5 1.498 (91,2%), MTA 165 (94,3%), Bower 281 (89,8%), BDWaste 196, curated 40 (81,6%), test 28 (65,1%), test2 39 (75,0%), quần áo 31 (72,1%), pin 107 (75,9%), tổng 2.278 (90,6%).
- **Bảng 4.4:** đo bằng argmax (luật backend). Các số v2 và v4 khớp: rw5 1.425 / 1.534, MTA 146 / 167, Bower 254·10 / 281·11, 102 ảnh 65 / 71, pin 10 / 6. Cần thêm chú thích "không có luật pin". Cột v3 chưa đối chiếu.
- **Bảng 4.5, các ô v5 khác:** t = 0,5: 102 ảnh 67·10·5, rw5 91%·35, Bower 281·9·5, báo nhầm 45. t = 0,7: 102 ảnh 70·9·1, Bower 283·8·2, báo nhầm 11.
- **Bảng 4.6:** seed 42 / 1 / 2: pin 107 / 111 / 110, quần áo 31 / 29 / 29, tổng 2.278 / 2.278 / 2.291, báo nhầm 47 / 47 / 41.

## 4. Phát hiện phụ của Agent Kiểm kê (ngoài phạm vi số trong tài liệu)

- `realworld.py --output` lưu JSON theo tên thư mục cuối, nên `realworld_loai_bo/realworld_test` ghi đè `realworld_test`. Số in ra màn hình vẫn đúng.
- Tập test v5 có 3/2.955 ảnh trùng MD5 với tập train (organic, tiền tố `gam_`). Ảnh hưởng tối đa ±0,1 điểm.
- Tiền tố `gam_` (1.451 ảnh hữu cơ) chưa rõ nguồn gốc.
