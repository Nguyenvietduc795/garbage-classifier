# Đối chiếu nội bộ các con số trong tài liệu — "Bỏ vào thùng nào?"

Phạm vi: chỉ đọc văn bản (docx báo cáo + PDF để lấy số trang, README.md bản trên đĩa gồm thay đổi chưa commit, frontend/index.html, backend/app.py, garbage_classifier/README.md + src/*.py, trash_ai_ui/README.md, frontend/models/*/meta.json). Không đếm ảnh, không chạy model. Mọi phép tính dưới đây chỉ dùng số đã ghi trong tài liệu.

- Danh sách đầy đủ các con số (667 dòng): `audit/numbers_in_docs.csv`.
- Số trang = số in ở chân trang PDF (trang 1 = "CHƯƠNG 1"). Trong docx không có track changes (`w:ins`/`w:del` = 0) và không có comment.
- Hình ảnh (Hình 3.1, 4.1, 5.1, 5.2…) là ảnh nhúng nên số liệu bên trong hình không được đối chiếu; chỉ đối chiếu chú thích hình.

---

## A. Các điểm người dùng nghi lệch

### A1. realworld_pin_test, báo nhầm thành pin, MTA: XÁC NHẬN có lệch

Có hai bộ số khác nhau cho **cùng một mô hình** (v5, ngưỡng pin 0,5, bản triển khai = seed 42):

| Chỉ số | Bảng 4.5 (Mục 4.6, tr. 18) cột "v5, t = 0,5" | Bảng 4.6 (Mục 4.7, tr. 19) cột "Seed 42 (triển khai)" | Bảng 5.2 (Mục 5.2, tr. 21) | Mục 5.6.2 (tr. 24) | Kết luận 1 (tr. 29) |
|---|---|---|---|---|---|
| realworld_pin_test | "110 (78%)" | "107" | "107 / 75,9%" | "con số 78% trên bộ pin_test" | (gián tiếp: 129/166 = 10+110+9) |
| Báo nhầm thành pin | "Tổng báo nhầm thành pin: 45" | "Báo nhầm thành pin: 47" | — | "≈ 45 lần trên các bộ test" | "45 so với 55" |
| MTA (175) | "166" | — | "165 / 94,3%" | — | — |

- 107/141 = 75,9% (đúng với Bảng 5.2); 110/141 = 78,0% (đúng với Bảng 4.5). Mỗi bảng tự khớp, nhưng hai bảng không khớp với nhau.
- Phạm vi "báo nhầm" cũng khác nhau: Bảng 4.5 cộng 102 ảnh cũ + rw5 + Bower (5+35+5 = 45); Bảng 4.6 tính trên "8 bộ" (47). Docx không nói rõ điều này.
- Lý do chỉ có trong README:86-87 (không có trong docx): "Số v5 đo lại bằng script mới lệch README cũ 1 ảnh ở MTA (165 so với 166) và 3 ảnh ở `realworld_pin_test` (107 so với 110)."
- Hệ quả: "129/166", "+26 ảnh pin" (Mục 4.6 P298, 5.6.1, Kết luận) và "78%" (5.6.2) dựa trên số cũ 110. Nếu lấy 107 thì tổng pin là 126/166 và chênh so với mô hình cũ là +23.
- Các chỗ khác cũng dùng số cũ: README:20, 271, 274-276; meta.json v5 ("pin 129/166, bao nham pin 45").

### A2. Bảng 3.1 / 3.2 không cộng khớp ở v4 (Bower): XÁC NHẬN

- Bảng 3.1 (Mục 3.1, tr. 10), hàng v4: "+ Bower (pin chụp thật) + BDWaste (980) | 19.157". Hàng này **không ghi số ảnh Bower**.
- Phép tính: 19.157 − 17.581 (v3) − 980 (BDWaste) = **596** ảnh Bower.
- Bảng 3.2 (Mục 3.2, tr. 10), hàng 7: "Bower waste annotations | +59 ảnh pin và vật khác". Ghi 59 cho cả "pin và vật khác", không khớp 596.
- README:224 ghi: "Thêm được **59 ảnh pin** train". Như vậy 59 chỉ là số ảnh pin; các vật khác của Bower (≈ 537 = 596 − 59) không được ghi ở đâu.
- Các hàng còn lại đều khớp: v1 12.055+1.451 = 13.506 ✓; v2 11.107+1.451 = 12.558 ✓; v3 12.558+3.247+1.776 = 17.581 ✓; v5 19.157+500 = 19.657 ✓; pin 815+500 = 1.315 ✓.

### A3. Mục 5.6.2 "≈30/43" so với "31/43": XÁC NHẬN

- Mục 5.6.2 P344 (tr. 24): "Quần áo trong bối cảnh rác còn yếu (≈ 30/43): …"
- Bảng 4.6 hàng "Quần áo thật (/43)", seed 42 (tr. 19): "31". Bảng 5.2 hàng "Quần áo thật (43)" (tr. 21): "31 | 72,1%". README:23 và README:59: "31/43".
- Con số "≈30" chỉ gần với trung bình 3 seed (31·29·29, TB 29,7, ghi ở README:78), nhưng docx không nói là trung bình.

### A4. Kích thước realworld_test/test2: 43/52 so với 49/53: XÁC NHẬN, có giải thích một phần

- Docx Bảng 3.3 hàng "realworld_test / test2" (tr. 11): "43 / 52". Bảng 5.2 (tr. 21): "realworld_test (43)", "realworld_test2 (52)". README:60 (mục v6): "(43) · test2 (52)".
- README:158-159 (bảng v2/v3): "`realworld_test` (49)", "`realworld_test2` (53)".
- README:55 giải thích: "Bộ test cũ đã bỏ 7 ảnh nên số khác bảng trước." Kiểm tra: (49+53) − (43+52) = 7 ✓.
- **Lệch còn lại trong docx**: Bảng 3.3 ghi "43 / 52 … 3 bộ chỉ có 102 ảnh khác nhau", và Mục 3.4 P244 ghi "151 ảnh chỉ có 102 ảnh khác nhau". Nhưng 49+43+52 = **144**, không phải 151; con số 151 = 49+49+53 là kích thước trước khi bỏ 7 ảnh. Bảng 4.4, 4.5, 5.3, 5.4 dùng "102 ảnh" (tức tập trước khi bỏ ảnh), còn Bảng 5.2 dùng 43/52 (tập sau khi bỏ). Docx không nói hai tập này khác nhau.

### A5. index.html dòng 151–153 còn số cũ trên 49 ảnh: XÁC NHẬN

- index.html:151-153: `// Do tren 49 anh that: nguong 0,5 -> 41 dung / 3 sai / 5 "chua chac"; // nguong 0,6 -> 38 dung / 2 sai / 9 "chua chac"` (đặt cạnh `THU_MUC_MODEL = "models/r18-8lop-v5"`).
- Comment không ghi model và không khớp số nào trong tài liệu: v2 = 44/49 (Bảng 4.3, 5.5); v5 trên curated = 40/49 (Bảng 5.2). Comment này đứng ngay trên phép đo mới trên 102 ảnh (index.html:154-156, khớp Bảng 5.4).
- index.html:175 cũng dùng số của v2 trong code v5: "do tren 49 anh that: 44 dung so voi 42". backend/app.py:117 cũng vậy.

### A6. Giao diện ghi "ắc quy", "khẩu trang" trong khi Bảng 1.1 nói chưa nhận diện: XÁC NHẬN

- index.html:189: `viDu: "Pin, ắc quy"` (nhóm "Rác nguy hại"); index.html:195: `viDu: "Quần áo, dép, khẩu trang"` (nhóm "Rác không thể tái chế"). Khi có kết quả, giao diện hiển thị "Gồm: " + viDu (index.html:386).
- Giống hệt ở backend/app.py:52 và :57, trash_ai_ui/README.md:8-9.
- Docx Bảng 1.1 (tr. 2-3): hàng "Đồ điện – điện tử | Ắc quy, cục sạc, dây sạc | … | Chưa"; hàng "Rác khác | Sành sứ, nilon bẩn, khẩu trang | … | Chưa". Mục 1.4 P169: "chưa nhận diện … khẩu trang, tã". Mục 5.6.2 P347: "chưa nhận diện rác điện tử, sành sứ, khẩu trang".
- Chính trash_ai_ui/README.md:16 cũng ghi: "Khẩu trang và dép chưa có ảnh train — model chưa nhận được". "Dép" trên giao diện cũng không khớp: Bảng 1.1 ghi quần áo/vải gồm "giày dép" là "Có".
- Phụ: Bảng 1.1 xếp "nilon bẩn" vào nhóm "Chưa" nhận diện, trong khi Bảng 3.1 v4 ghi BDWaste bổ sung "nilon ở Nam Á".

---

## B. Các lệch nội bộ quan trọng khác

1. **API không có luật pin.** backend/app.py:118 chọn nhóm bằng `max(range(len(classes)), …)` trên cả 8 lớp, không có NGUONG_PIN. Web (index.html:168, 287) và realworld.py:40 dùng luật P(pin) ≥ 0,5. Trong khi đó docx Mục 6.1 P352 ghi "API Flask … dùng cùng mô hình và cùng quy tắc gộp nhóm", và README:420-421 ghi "gộp thành 4 nhóm theo cùng một cách, nên cho cùng kết quả". Tài liệu cũng không ghi backend/model.pt là phiên bản nào.
2. **Ngưỡng tin cậy 60% và 50%.** README:428: "**Ngưỡng tin cậy 60%.**" Các chỗ sau ghi 0,5: README:112, :179, :208; index.html:157; app.py:34; docx Mục 2.6, Bảng 5.4, 5.5, 6.2. Trong trash_ai_ui/README.md, dòng 18 ghi "dưới 50%" nhưng dòng 71 ("mặc định 60%") và dòng 92 ("ngưỡng 60%") ghi 60%.
3. **"96% cùng nguồn nhưng 57% đời thực" ghép hai model khác nhau.** Mục 3.1 P226 (tr. 10): "mô hình đạt 96% trên ảnh cùng nguồn nhưng chỉ 57% trên ảnh đời thực"; README:300 ghi tương tự. Theo Bảng 4.2, 96,0% là của aug/merged (đời thực 44,9% / 51,0%), còn 57,1% là của new11k (cùng nguồn 94,4%). Không có model nào đạt cả 96% và 57%.
4. **Mục 4.3 P277: "Bổ sung 7.922 ảnh từ nguồn khác kiểu cải thiện 12,2 điểm"** (README:324 ghi giống). +12,2 = 57,1 − 44,9 (new11k − big). Nhưng new11k − big chỉ chênh 11.107 − 4.133 = 6.974 ảnh (tổng) hoặc 7.772 − 2.890 = 4.882 (cột Bảng 4.2). Con số 7.922 bằng 12.055 − 4.133 (merged − bộ gốc). "948 ảnh studio" = 12.055 − 11.107 ✓.
5. **Bảng 3.1 và Bảng 4.2 dùng hai đơn vị khác nhau cho cùng một bộ.** "merged" ghi 12.055 ảnh ở Bảng 3.1 nhưng 8.435 ảnh ở Bảng 4.2 (≈ 70% của 12.055). Tương tự new11k 7.772 ≈ 0,7×11.107, big 2.890 ≈ 0,7×4.133, full 980 = 0,7×1.400. Tiêu đề cột Bảng 4.2 ("Dữ liệu huấn luyện") không nói đây là số ảnh train sau khi chia.
6. **Tên thư mục và phiên bản bị lẫn.** frontend/models/r18-8lop-v1/meta.json chứa `"nguon": "…artifacts/v2_r18/best_model.pt…"`, tức model v2; README:28 cũng viết "Bản v2 vẫn giữ ở `frontend/models/r18-8lop-v1`". Trong khi docx Bảng 3.1/4.3 gọi "v1" là một model khác (bộ merged + hữu cơ, 38/49). README:103 gọi chính model 38/49 này là "ResNet-18 trên `dataset_merged` + augmentation mạnh" chứ không gọi là v1.
7. **README tự mâu thuẫn về quần áo.** README:282 (mục v5): "Quần áo chụp thật vẫn sai 8/8" và README:250: "Cả ba model đều sai **8/8 ảnh quần áo**". Nhưng README:23 (đã sửa) ghi v5 đúng 31/43 trên bộ mới, và README:25 ghi "quần áo sai hết" là do bộ test.
8. **Số ảnh rw5: 1.647 và 1.642.** README:228: "1.647 ảnh tự chụp", còn mọi bảng (docx Bảng 3.3/4.4/4.5/5.2, README:238/272) ghi 1.642. Không có chỗ nào giải thích 5 ảnh chênh lệch (có thể do bỏ trùng MD5, nhưng tài liệu không ghi).
9. **Tổng báo nhầm của v2 trong Bảng 4.5 không cộng khớp từ các hàng hiển thị.** v2: 4 (102 ảnh) + 27 (rw5) + 22 (Bower) = **53**, nhưng hàng tổng ghi **55**. Hai cột v5 thì khớp: 5+35+5 = 45 ✓, 1+8+2 = 11 ✓. Chênh 2 có thể đến từ MTA (bảng không có cột báo nhầm cho MTA); README:270-276 có cùng vấn đề.
10. **Bảng 5.5 ghép dữ liệu của v2 với luật của v5.** Cột "ResNet-18 của nhóm" ghi "44/49 (89,8%) – v2", "11/13 – v2", nhưng hàng "Kiểm soát đầu ra" của cùng cột lại ghi "Luật pin 50%". Theo Mục 4.6 và README:180, v2 dùng luật pin 30%, còn 50% là của v5.
11. **README:84: "35 lần báo nhầm pin (v6b seed 1)".** Ba seed v6b có báo nhầm 35 · 74 · 39, nên max − min = 39; con số 35 chỉ là seed1 − seed2. "33 ảnh tổng" = 2.298 − 2.265 ✓.
12. **README:365: "chậm hơn khoảng 20 lần (72 phút so với 3 phút)"**, trong khi 72/3 = 24.
13. **README:437: "Lớp yếu nhất là `plastic` (86,7%…)"** không ghi model. Với v5 (docx Bảng 5.1), nhựa đạt 87,2% và lớp yếu nhất là bìa carton (85,9%).
14. **Mục 5.4 / Bảng 5.4 (ngưỡng tin cậy, 102 ảnh) và câu "(44 so với 42 ảnh đúng trên 49 ảnh)" (P330)** không ghi model. Theo README:203 và :112 thì đó là v2 + ưu tiên pin 30%, nhưng docx trình bày chúng như thông số của hệ thống hiện tại (v5).
15. **Mức "chênh có ý nghĩa" không thống nhất.** README:440 ghi sai số "±7 điểm" trên 49 ảnh; docx Mục 2.8 ghi "mỗi ảnh ≈ 2 điểm %, chênh dưới 10 điểm không có ý nghĩa". Hai cách nói này không mâu thuẫn trực tiếp, nhưng README:323 lại dùng "±7".
16. **Số epoch mặc định trong code khác tài liệu.** train.py:30 có `--epochs` mặc định 20, README:385 ví dụ `--epochs 20 --batch-size 64`, còn tài liệu ghi các bản v2–v6 train 15 epoch, batch 32. Đây không phải lỗi, nhưng số 15 không có trong code (do truyền qua tham số).

---

## C. Kiểm tra cộng khớp bảng (docx)

| Bảng | Phép kiểm | Kết quả |
|---|---|---|
| 3.1 | v1..v5 cộng dồn | Khớp, trừ v4: Bower không ghi số (suy ra 596) và mâu thuẫn "+59" ở Bảng 3.2 |
| 3.2 | 10 nguồn (hàng 1–10, trừ ImageNet) | Khớp với "10 nguồn" (Mục 1.6, 5.6.1, Kết luận) |
| 3.3 | 49+43+52+1.642+175+313+196+141+43 | = 2.654 ✓ (Mục 1.6 "2.654"; "hơn 2.600" ✓). Lưu ý 2.654 cộng cả ảnh trùng giữa curated/test/test2 |
| 3.4 | Mọi hàng: train+val+test = tổng; mọi cột cộng = hàng Tổng | Khớp hoàn toàn (13.757 / 2.945 / 2.955 / 19.657) |
| 3.4 với 5.1 | Cột Kiểm thử Bảng 3.4 = cột "Số ảnh test" Bảng 5.1 | Khớp từng lớp |
| 5.1 | Trung bình có trọng số các lớp | 91,344% → "91,34%" ✓ |
| 1.1 với 5.1 | % từng lớp | Khớp cả 8 lớp |
| 4.4 | % rw5: 1.425/1.642 = 86,8 → 87; 1.522 → 92,7 → 93; 1.534 → 93,4 → 93 | ✓ |
| 4.5 | Pin /166 = 14+141+11; 11+82+10 = 103; 10+110+9 = 129; 9+97+8 = 114 | ✓ |
| 4.5 | Báo nhầm: v2 4+27+22 = 53 nhưng ghi 55; v5 0,5: 45 ✓; 0,7: 11 ✓ | **Lệch 2 ở cột v2** |
| 4.5 | % pin_test: 82/141 = 58,2; 110/141 = 78,0; 97/141 = 68,8 → 69 | ✓ |
| 4.5 với 5.6.2 | "19 so với 21 trên 25 ảnh" = 10+9 so với 11+10, 25 = 14+11 | ✓ (nhưng câu không nói 25 ảnh lấy từ đâu) |
| 4.6 | Lệch seed: 2.291−2.278 = 13 ✓; 111−107 = 4 ✓ | ✓ |
| 5.2 | Tổng 8 bộ: các số ảnh cộng = 2.513 ✓; số đúng cộng = 2.278 ✓; 2.278/2.513 = 90,65 → "90,6%" ✓ | ✓ |
| 5.2 | % từng hàng (91,2 / 94,3 / 89,8 / 100 / 81,6 / 65,1 / 75,0 / 72,1 / 75,9) | Tất cả đúng với tử/mẫu |
| 5.2 với 4.6 | 2.278 = seed 42; pin 107 = seed 42; quần áo 31 = seed 42 | ✓ (vậy Bảng 5.2 = seed 42, còn Bảng 4.5 là lần đo cũ) |
| 5.3 / 5.4 | Câu dẫn: 58→68 ✓; 0,4→0,5 giảm 5 sai, mất 1 đúng ✓; 0,6: 25/102 ≈ 1/4 ✓ | ✓ |
| 5.5 | 37/49 = 75,5% ✓; 44/49 = 89,8% ✓ | ✓ |
| README v6 | v5 31+28+39+40+165+281+196+1.498 = 2.278 ✓; v6a = 2.282 ✓; v6b = 2.298 ✓; 1.512/1.642 = 92,1 → 92% ✓; TB 29,7 / 2.282 / 29,0 / 2.284 ✓ | ✓ |
| README v6 | clothes 3.656 + 1.000 = 4.656 ✓; + 575 = 5.231 ✓ | ✓ |
| README:160 | 65/102 = 63,7 → "64%" ✓; 74/102 = 72,5 → "73%" ✓ | ✓ |
| garbage_classifier/README | 7 lớp × (140/30/30) = 980/210/210 ✓ = 1.400 ✓ | ✓ |

## D. % ghi sai so với tử/mẫu

Không tìm thấy % nào sai khi tính lại từ chính tử/mẫu ghi cạnh nó. Các % "lệch" ở mục A1 đều là do dùng hai tử số khác nhau (110 và 107) cho cùng một chỉ số.

## E. Câu có số nhưng không ghi rõ lấy từ bộ ảnh / model nào

- Mục 5.6.2 P345: "19 so với 21 trên 25 ảnh": không nói 25 = 14 pin trong 102 ảnh Wikimedia + 11 pin Bower.
- Mục 5.6.2 P346: "≈ 45 lần trên các bộ test": không nói là những bộ nào (Bảng 4.5 = 102+rw5+Bower; Bảng 4.6 "8 bộ" = 47).
- Mục 4.6 P294: "pin nhận đúng 52 → 64/80, báo nhầm pin giữ nguyên 22; t = 0,3 … 52": nửa B gồm những bộ nào, 80 pin lấy từ đâu thì không ghi.
- Mục 5.3 P330: "(44 so với 42 ảnh đúng trên 49 ảnh)": không ghi model (v2).
- Bảng 5.4: không ghi model (v2 + luật pin 30% theo README).
- Mục 3.1 P226: "96% … 57%": không ghi model (hai cấu hình khác nhau).
- Mục 2.1.2 P189: "58 lên 68/102": không ghi model trong câu (Bảng 5.3 ghi là v2).
- Mục 5.1 P307: "v2 (94,6% trên 1.891 ảnh)": tập test v2 không xuất hiện ở bảng nào khác.
- index.html:151-153: "49 anh that … 41/3/5": không ghi model.
- README:22: "Hữu cơ (/300) 250 → 238": số 238 của v5 không có trong docx (docx chỉ nói BDWaste giúp hữu cơ, 226 → 251 ở v4).
- README:228: "1.647" và các bảng ghi "1.642": không giải thích.

## F. Các phiên bản model/dataset mà tài liệu nhắc tới

- **Dataset**: dataset_sach_zip (1.400), archive/Kaggle 7 lớp (4.133), TrashNet (2.527), bộ 11.107 (Garbage Classification v2), merged (12.055 / 8.435 train), dataset_8lop_v1 (13.506), v2 (12.558), v3 (17.581), v4 (19.157), v5 (19.657), v6a (v5 + 1.000 RISE), v6b (v6a + 575 Na Uy).
- **Model giai đoạn 1 (7 lớp)**: full, big, gentle, aug, new11k, merged.
- **Model 8 loại**: ResNet-18 v1 (38/49), v2 (`v2_r18`, 44/49, chạy web 01/10–24/10/2026), ResNet-18 + cân bằng lớp, MobileNetV3-Large (+ cân bằng lớp), Teachable Machine (cơ sở), v3, v3 + `--oversample battery=2`, v4, v5 (`v5_r18`, seed 42 / 1 / 2; ngưỡng pin t = 0,3 / 0,5 / 0,7; đang chạy web từ 24/10/2026), v6a, v6b (seed 42 / 1 / 2).
- **Thư mục / tệp**: `frontend/models/r18-8lop-v1` (chứa **v2**), `frontend/models/r18-8lop-v5` (v5); `backend/model.pt` (không ghi phiên bản); `trash_ai_ui/garbage_resnet18.pt` (README trash_ai_ui ghi "đổi model 01/10/2026", 44/49, tức v2); `trash_ai_ui/tfjs_model` (Teachable Machine); tag git `vong-khu-vuc-2026`.
- **Chỗ lẫn phiên bản**: index.html:151-153 và :175, app.py:117 (số của v2/không rõ, nằm trong code v5); Bảng 5.5 (dữ liệu v2 + luật pin 50% của v5); Bảng 5.4 / P330 (v2 nhưng không ghi); thư mục r18-8lop-v1 chứa v2; Bảng 4.5 và Bảng 4.6/5.2 cùng là v5 nhưng là hai lần đo khác nhau.
