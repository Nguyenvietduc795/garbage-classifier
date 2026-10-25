# Bảng lệch số liệu – Vòng 2 (sau khi sửa)

Hai agent mới làm độc lập, không đọc kết quả vòng 1:
- **Agent Kiểm kê:** `audit/round2/numbers_ledger.json`, 454 mục.
- **Agent Đối chiếu:** `audit/round2/numbers_in_docs.csv` (315 dòng) và `audit/round2/internal_consistency.md`.
- **Chạy lại bằng `realworld.py` gốc**, dùng để phân xử khi hai script cho số khác nhau: `audit/round2/crosscheck_main.log`.

Chuẩn: v5_r18 seed 42, ngưỡng pin 0,5. Cột v2 đo bằng `realworld.py --nguong-pin 0.3`.

**Kết luận: CHƯA đạt 0 dòng lệch.** Còn 1 ô chưa phân xử được, 1 định nghĩa phải chốt, 10 chỗ ngoài phần đã sửa và 5 câu không kiểm được bằng dữ liệu hiện có. Theo yêu cầu, tôi không tự lặp thêm.

## A. Các bảng chính trong docx: khớp ledger

- **Bảng 3.1, 3.2, 3.3:** Bower 596 (59 ảnh pin), BDWaste 980, tổng v4 19.157, v5 19.657. Ba bộ realworld có 144 ảnh, 95 ảnh khác nhau, pin 14. rw5 1.642, Bower 313, 11 ảnh pin.
- **Bảng 4.5, cả ba cột:** khớp `realworld.py`.
  - Script riêng của agent vòng 2 lệch 1 ảnh ở cột v2: 102 ảnh cũ 66 thay vì 65, rw5 1.426 thay vì 1.427.
  - Chạy lại `realworld.py` gốc ra 65 và 1.427, khớp tài liệu.
- **Bảng 4.6:** khớp. Seed 2 tổng 8 bộ = 2.291 theo `realworld.py`; script agent ra 2.292.
- **Bảng 5.2, Bảng 5.4 (v5), Bảng 5.5 (v5 40/49, pin 10/13):** khớp.
- **Mục 5.6, Mục 6.1, Kết luận:** khớp. Các số gồm 126/166, 97, 31/43, 19 so với 20, 91,3% và 91,2%.

## B. Còn lệch

| # | Vị trí | Chỉ số | Đang ghi | Đúng (ledger) | Nguồn | Đề xuất sửa |
|---|---|---|---|---|---|---|
| 1 | docx Bảng 4.4, cột v2 (102 ảnh; rw5) | v2, luật argmax | 65; 1.425 (86,8%) | Vòng 1: 65; 1.425. Vòng 2: **66; 1.424 (86,7%)** | ledger v1 `luat_backend` / ledger r2 mục 6 | **Chưa phân xử được**: chưa có script chuẩn cho luật argmax. Đề xuất viết 1 lệnh chuẩn (`realworld.py --nguong-pin 1.01 --khong-tang-sang`, hoặc chạy `backend/app.py`) rồi chốt. |
| 2 | docx Bảng 4.5, hàng "Tổng báo nhầm thành pin", cột v2; Mục 4.6, 5.6.1, Kết luận; README:20, :276 | phạm vi tổng báo nhầm | 47 (v2) so với 45 (v5) | Gồm MTA (102 + rw5 + Bower + MTA): **v2 47, v5 45**. Chỉ 3 bộ có cột báo nhầm (102 + rw5 + Bower): **v2 45, v5 45** | ledger r2 mục 5 | **Cần bạn chốt định nghĩa.** (a) Giữ 47 và thêm "(gồm 2 lần ở MTA)" vào nhãn hàng; ô MTA đổi thành "144 · nhầm 2" để bảng cộng được. (b) Đổi thành 45, khi đó câu so sánh thành "45 so với 45". |
| 3 | frontend/models/r18-8lop-v5/meta.json | tổng pin v5 | "129/166" | **126/166** | ledger r2 mục 5 | Sửa thành 126/166 (vòng 1 bỏ sót file này) |
| 4 | README:246 | số ảnh pin Bower | "53 ảnh" | **59** (v3 → v4 thêm 59 ảnh pin `bower_`) | ledger r2 mục 1 | 59 |
| 5 | README:190 (bảng độ sáng, hàng "+ ưu tiên pin (web hiện tại)") | v2 + pin 0,3 trên 102 ảnh cũ | 66 · 11 · 4 | **65 · 10 · 4** | crosscheck_main.log | 65 · 10 · 4; đổi "web hiện tại" thành "web lúc đó (v2)" |
| 6 | README:205-209 | bảng ngưỡng tin cậy trên 102 ảnh | 65/28/9 · 64/23/15 · 61/16/25, nhãn "(đang dùng)" | Số v5 (đang chạy trên web): **67/20/15 · 64/19/19 · 59/13/30**. Số cũ không tái hiện được với v2. | ledger r2 mục 7 | Ghi rõ đây là nhật ký của giai đoạn v2, hoặc thay bằng số v5 |
| 7 | README:190, 194, 268 | nhãn "web hiện tại" gắn với v2 | v2 | Web hiện chạy v5 | ledger r2 mục 8 | Đổi thành "web lúc đó (v2)" |
| 8 | README:438 | lớp yếu nhất | plastic 86,7% | v5 test nội bộ: **cardboard 250/291 = 85,9%**, plastic 516/592 = 87,2% (khớp Bảng 5.1) | ledger v1 `v5_r18.test_noi_bo.*.accuracy` | Thêm "(model v2)", hoặc đổi sang số v5 |
| 9 | docx Danh mục bảng (mục lục), dòng Bảng 5.4 | tên bảng | "(102 ảnh, đã có luật pin)" | Chú thích thật: "(mô hình v5, 102 ảnh cũ, luật pin 0,5)" | internal_consistency A13 | Cập nhật trường mục lục trong Word (F9), hoặc sửa tay có track changes |
| 10 | trash_ai_ui/README:75, 101 | ngưỡng tin cậy | 60% | 0,50 (app.py:34; cũng là dòng 21 của chính file đó) | internal_consistency A5 | 50% |
| 11 | trash_ai_ui/README | "desktop cùng model với frontend" | cùng model | Desktop: `garbage_resnet18.pt` = v2. Frontend: v5. | ledger r2 mục 8 + model_identity | "desktop dùng v2" |
| 12 | backend/app.py:3 (docstring); :52, :57 (ví dụ "ắc quy", "khẩu trang"); trash_ai_ui/README:8-9 | mô tả API; ví dụ giao diện | "Cung model va cung cach gop nhom voi trang web"; ắc quy, khẩu trang | API = v2, argmax, không có luật pin. Bảng 1.1 ghi ắc quy và khẩu trang là "Chưa" nhận diện. | ledger r2 mục 8 | **Để nguyên theo yêu cầu "chưa đụng code"**, chỉ ghi nhận. Sửa khi bạn cho phép đụng backend. |

## C. Không kiểm được bằng dữ liệu/model hiện có

Các mục này thuộc giai đoạn 1 (7 lớp) hoặc thiếu định nghĩa trong repo.

| # | Vị trí | Vấn đề |
|---|---|---|
| 13 | docx Mục 3.1; README:300 | "96% cùng nguồn / 57% đời thực" ghép số của 2 cấu hình khác nhau trong Bảng 4.2 |
| 14 | docx Mục 4.3; README:324 | "7.922 ảnh → +12,2 điểm", "948 ảnh studio": không suy ra được từ Bảng 4.2 |
| 15 | docx Bảng 3.1 (12.055) và Bảng 4.2 (8.435) | Hai số cho bộ merged; Bảng 4.2 có vẻ là phần train nhưng không ghi |
| 16 | docx Bảng 3.3, cột "Nguồn" | Tỉ lệ tách 20% / 15% / 20%, trong khi tính theo số ảnh ra 34,4% / 16,7% / 22,0% (không rõ đơn vị tính) |
| 17 | docx Mục 4.6; index.html:163-167 | "Nửa A/B: pin 52 → 64/80, báo nhầm 22 → 22; 0,3 → 52": repo không có định nghĩa nửa A/B |
| — | README (±7 điểm) và docx 2.8 (≈ 2 điểm/ảnh) | Hai cách nói sai số của bộ 49 ảnh; cùng kết luận ngưỡng 10 điểm, không phải lệch số |

## D. Phát hiện mới của vòng 2 (không phải lệch số, để bạn cân nhắc)

- 7 ảnh bị loại vào `realworld_loai_bo` đều là quần áo và v5 sai cả 7. Bỏ chúng làm số test/test2 trông tốt hơn: 67/95 thay vì 67/102. Docx Mục 3.4 đã ghi việc loại 7 ảnh nhưng chưa nêu điểm này.
- Với v5 trên curated, chọn nhóm theo tổng xác suất nhóm đúng **44/49**, còn chọn theo loại cao nhất (cách web đang dùng) chỉ đúng **40/49**. Lý do thiết kế trong Mục 5.3 dựa trên số của v2.
- Bảng 5.4 theo v5: ngưỡng 0,4 tốt hơn 0,5 (thêm 3 ảnh đúng, chỉ thêm 1 ảnh sai). Hiện web vẫn để 0,5.

## E. Đã sửa sau vòng 2 (theo quyết định của bạn)

| # | Đã làm |
|---|---|
| 2 | Giữ 47 so với 45. docx Bảng 4.5: hàng MTA đổi thành "MTA (175): đúng · báo nhầm pin" với 144 · 2 / 165 · 0 / 165 · 0; nhãn hàng tổng ghi "(102 ảnh cũ, rw5, Bower, MTA)". Cộng lại: v2 4 + 21 + 20 + 2 = 47 ✓; v5 t = 0,5: 5 + 35 + 5 + 0 = 45 ✓; v5 t = 0,7: 1 + 8 + 2 + 0 = 11 ✓. Mục 5.6.2 ghi thêm MTA. Sửa tương tự README:274, :276. |
| 3 | meta.json: 129/166 → 126/166; ghi phạm vi báo nhầm; rw5 91% → 91,2% |
| 4 | README:246: 53 → 59 ảnh pin train. README:221 ("438 box pin nằm trong 53 ảnh") vẫn để nguyên, vì câu đó nói về ảnh gốc có box, không phải số ảnh train. |
| 5 | README:190: 65 · 10 · 4, nhãn "web lúc đó, v2" |
| 6 | README bảng ngưỡng tin cậy: ghi rõ là số của giai đoạn v2, chưa tái hiện được; thêm số v5 |
| 7 | README:100, 155, 190, 194, 268: "đang dùng / web hiện tại" → "web lúc đó (v2)" |
| 8 | README:438: ghi rõ là v2; thêm số v5 (cardboard 85,9%, plastic 87,2%) |
| 9 | docx Danh mục bảng, dòng Bảng 5.4: sửa bằng track changes cho khớp chú thích |
| 10 | trash_ai_ui/README:71, 92: 60% → 50% (khớp `NGUONG_TIN_CAY = 0.5` trong giao_dien_pyqt.py và app.py) |
| 11 | trash_ai_ui/README:12, 29: ghi rõ desktop/API dùng v2, web dùng v5 |
| 1, 12 | Chưa xử lý: #1 cần script chuẩn cho luật argmax; #12 (app.py, trash_ai_ui/README:8-9) để sau theo yêu cầu |

Bản trước khi sửa: `audit/round2/*.truoc_sua*`.
