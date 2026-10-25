# Đối chiếu nội bộ (vòng 2, agent B)

Nguồn: docx đã chấp nhận track changes (bỏ w:del, giữ w:ins), README.md, frontend/index.html, backend/app.py, garbage_classifier/src/garbage_classifier/*.py, trash_ai_ui/README.md, frontend/models/*/meta.json.
Chỉ kiểm cộng/chia trên các số đã ghi. Không đếm ảnh, không chạy model. Bảng số đầy đủ ở `numbers_in_docs.csv` (315 dòng).

## A. Lệch giá trị giữa các nguồn (cùng chỉ số)

| # | Chỉ số | A ghi | B ghi | Mức |
|---|---|---|---|---|
| A1 | tong_pin_166.v5_t05 | docx Bảng 4.5 R6, Mục 4.6, Kết luận; README dòng 275: **126**/166 | `frontend/models/r18-8lop-v5/meta.json`: "voi NGUONG_PIN 0,5: pin **129/166**, bao nham pin 45" | Cao |
| A2 | Số ảnh pin Bower | docx Bảng 3.1 R4, Bảng 3.2 R7: "59 ảnh pin"; docx Mục 4.5: "Pin Bower chỉ từ **59 ảnh** một nguồn" | README dòng 246: "**53 ảnh** từ một nguồn là quá ít" (README dòng 221-224 lại ghi 53 ảnh gốc chứa box, 59 mẫu pin train) | Trung bình (README tự lẫn 53 ảnh gốc / 59 mẫu) |
| A3 | rw102.v2 + luật pin 30% | docx Bảng 4.5 R1 cột v2: "65 · 10 · 4"; README dòng 270 cũng 65 · 10 · 4 | README dòng 190: "+ ưu tiên pin (**web hiện tại**) | **66** | **11** | 4" | Trung bình. README dòng 279 giải thích cột v2 "đo lại bằng realworld.py --nguong-pin 0.3", nhưng dòng 190 không ghi đó là phép đo cũ |
| A4 | Bảng ngưỡng tin cậy (102 ảnh) | docx Bảng 5.4 và index.html dòng 154-157 (model v5): 67/20/15; 64/19/19; 59/13/30 | README dòng 205-209 (model v2 + ưu tiên pin): 65/28/9; 64/23/15; 61/16/25, kèm nhãn "0,5 (đang dùng)" | Trung bình. Khác model nên số khác là đúng, nhưng README không có bảng v5 và vẫn gắn "đang dùng" cho bảng v2 |
| A5 | Ngưỡng tin cậy desktop / API trash_ai_ui | docx 2.6, Bảng 5.5, Bảng 6.2; README dòng 112, 429; index.html; backend/app.py: **0,5 / 50%** | trash_ai_ui/README.md dòng 75: "(mặc định **60%**)"; dòng 101: "vượt ngưỡng **60%**"; cùng file đó dòng 21 lại ghi "dưới 50%" | Trung bình |
| A6 | Model của API | docx Mục 6.1: "hiện API vẫn chạy mô hình v2 và chọn loại có xác suất cao nhất trong 8 loại (chưa có luật pin…)"; README dòng 420-422 cũng vậy; code app.py dòng 118-119 chọn top-1, không có NGUONG_PIN | backend/app.py dòng 3 (docstring): "Cung model va cung cach gop nhom voi trang web (frontend/) va giao dien desktop." | Cao (comment trái với code và báo cáo) |
| A7 | Model desktop so với web | docx 6.1 và README dòng 420: web v5, desktop v2 | trash_ai_ui/README.md dòng 14-15: "ResNet-18 8 loại (`garbage_resnet18.pt`) — **cùng model với trang web `frontend/`**"; dòng 31-32: "kết quả luôn khớp nhau và khớp trang frontend/" | Trung bình (đúng lúc 01/10, đã cũ) |
| A8 | Nhãn "web hiện tại" | README dòng 11: web chạy v5 | README dòng 190 "+ ưu tiên pin (**web hiện tại**)", dòng 194 "Trên trình duyệt (web hiện tại)", dòng 268 cột "v2 + ưu tiên pin 30% (**web hiện tại**)", dòng 238/240 "v2 (web)" | Thấp-TB (README tự mâu thuẫn) |
| A9 | Lớp yếu nhất trên tập cùng nguồn | docx Bảng 5.1 (v5): plastic 87,2%, yếu nhất là **cardboard 85,9%** | README dòng 438: "Lớp yếu nhất là `plastic` (**86,7%** ngay cả trên ảnh dataset)", không ghi model | Thấp (khả năng là số của model cũ; cần ghi model) |
| A10 | Khoảng cách 96% / 57% | docx Bảng 4.2: cấu hình 96,0% cùng nguồn (aug, merged) có 44,9% / 51,0% đời thực; cấu hình 57,1% (new11k) có 94,4% cùng nguồn | docx Mục 3.1: "mô hình đạt 96% trên ảnh cùng nguồn nhưng chỉ 57% trên ảnh đời thực"; README dòng 300: "Model tốt nhất đạt 96% … nhưng chỉ 57%" | Trung bình (ghép hai mô hình khác nhau thành "một mô hình") |
| A11 | Sai số bộ 49 ảnh | docx Mục 2.8: "mỗi ảnh ≈ 2 điểm phần trăm nên chênh lệch dưới 10 điểm không được coi là có ý nghĩa" | README dòng 323, 441: "sai số ±7" | Thấp (cùng kết luận 10 điểm, khác cách nói) |
| A12 | Phạm vi ví dụ so với Bảng 1.1 | docx Bảng 1.1: "Đồ điện – điện tử (Ắc quy, cục sạc…) – **Chưa**"; "Rác khác (…khẩu trang) – **Chưa**"; Mục 1.4 cũng ghi chưa nhận diện khẩu trang | backend/app.py dòng 52: ví dụ nguy hại "Pin, **ắc quy**"; dòng 57: ví dụ không tái chế "Quần áo, dép, **khẩu trang**" (API trả về trường `vi_du`); trash_ai_ui/README.md dòng 9-12 cũng vậy (dòng 18 tự ghi "Khẩu trang và dép chưa có ảnh train") | Trung bình. frontend/index.html dòng 190, 196 KHÔNG bị lỗi này ("Pin AA/AAA, pin cúc áo, pin điện thoại"; "Quần áo, giày dép") |
| A13 | Danh mục bảng so với chú thích | docx Bảng 5.4 chú thích: "Lựa chọn ngưỡng tin cậy (mô hình v5, 102 ảnh cũ, luật pin 0,5)" | docx DANH MỤC BẢNG: "Bảng 5.4. Lựa chọn ngưỡng tin cậy (102 ảnh, đã có luật pin)" | Thấp (cần cập nhật trường mục lục) |
| A14 | Kích thước bộ merged | docx Bảng 3.1 R1: "Bộ merged của giai đoạn 1 (**12.055** ảnh, 7 lớp)" | docx Bảng 4.2 R6 và README dòng 295: "merged | **8.435** ảnh" | Thấp-TB. 12.055 × 0,7 ≈ 8.438, nên Bảng 4.2 nhiều khả năng ghi phần train, nhưng cột chỉ ghi "Dữ liệu huấn luyện", không nói rõ |

## B. Bảng / dòng tổng không cộng khớp

| # | Vị trí | Phép tính | Kết quả |
|---|---|---|---|
| B1 | docx Bảng 4.5 R7 cột "v2 + pin 30%" (và README dòng 276) | Tổng báo nhầm = 102 ảnh cũ 4 + rw5 21 + Bower 20 = **45** | Bảng ghi **47** → lệch 2. Cột v5 t=0,5: 5+35+5=45 khớp ghi 45; cột t=0,7: 1+8+2=11 khớp. Bảng không có cột báo nhầm cho MTA, mà Mục 5.6.2 định nghĩa phạm vi là "102 ảnh cũ, rw5 và Bower". Hệ quả: câu "45 so với 47" ở Mục 4.6, 5.6.1, Kết luận và README dòng 20, 278 so hai phạm vi khác nhau, hoặc số 47 sai. (Lưu ý thêm: Bảng 4.6 / README dòng 64 cũng có một con số 47 cho v5 seed 42, "8 bộ", dễ bị nhầm.) |
| B2 | docx Mục 4.3 bullet 2; README dòng 324 | "Bổ sung 7.922 ảnh từ nguồn khác … cải thiện 12,2 điểm" | 12,2 = 57,1 (new11k) − 44,9 (big). Nhưng 7.772 (new11k) − 2.890 (big) = 4.882 ≠ 7.922. Không suy ra được 7.922 từ Bảng 4.2 |
| B3 | docx Mục 4.3 bullet 2; README dòng 325 | "thêm 948 ảnh cùng phong cách studio không cải thiện gì" | Không cặp nào trong Bảng 4.2 chênh nhau 948 ảnh (980→2.890 là +1.910). Không kiểm được |
| B4 | docx Bảng 3.3 R5-R7 (tỉ lệ tách test) | Bower: 313/(596+313) = 34,4% (ghi "20%"); BDWaste: 196/(980+196) = 16,7% (ghi "15%"); pin: 141/(500+141) = 22,0% (ghi "20%") | Có thể % tính trên ảnh gốc trước khi cắt / lọc trùng (Bower cắt nhiều mẫu mỗi ảnh), nhưng bảng không nói rõ đơn vị |

Các bảng khác cộng khớp: Bảng 3.1 (12.558; 17.581; 19.157; 19.657; 13.506), Bảng 3.4 (từng hàng và các cột tổng 13.757 / 2.945 / 2.955 / 19.657), Bảng 4.5 R6 (97 / 126 / 112 = 14+141+11 thành phần), Bảng 5.2 R9 (tổng 8 bộ 2.278; mẫu 2.513), Bảng 5.4 (mỗi hàng = 102), Bảng 3.3 (tổng 9 bộ = 2.654 = Mục 1.6), Bảng 4.6 (lệch 13 và 4 đúng), README v6 (2.278 / 2.282 / 2.298; TB seed 29,7 / 2.282 / 29,0 / 2.284), index.html dòng 151-153 (39+4+6 = 35+3+11 = 49).

## C. Phần trăm so với tử/mẫu

Mọi % 1 chữ số trong docx khớp tử/mẫu (Bảng 4.4: 86,8 / 92,7 / 93,4; Bảng 4.5: 54,6 / 75,9 / 67,4; Bảng 5.2: 91,2 / 94,3 / 89,8 / 81,6 / 65,1 / 75,0 / 72,1 / 90,6 / 75,9; Bảng 5.5: 75,5 / 81,6; Mục 5.1: 2.699/2.955 = 91,3).
Quy tắc làm tròn không thống nhất giữa các nguồn: docx dùng 1 chữ số thập phân; README dùng số nguyên ở nhiều bảng (dòng 62 "91%", "92%"; dòng 160 "64%", "73%"; dòng 238 "87%", "93%"); meta.json v5 "91%". Giá trị đều đúng khi làm tròn, chỉ khác số chữ số.

## D. Câu thiếu nguồn bộ ảnh hoặc model

1. docx Mục 3.1: "mô hình đạt 96% … nhưng chỉ 57%": không nêu cấu hình nào (thực ra là hai cấu hình, xem A10).
2. docx Mục 2.1.2: "nâng số ảnh xếp đúng nhóm từ 58 lên 68/102": không nêu model (v2) và không nói là ảnh tối giả của bộ 102 ảnh cũ (có ở Bảng 5.3).
3. docx Bảng 6.2 R3: "Bổ sung 6 nguồn ảnh rác chụp thật": không nêu 6 nguồn nào (Bảng 3.2 có 10 nguồn).
4. docx Mục 4.6, 5.6.1, Kết luận: "45 so với 47": phạm vi bộ ảnh không ghi tại chỗ, và cột v2 không cộng ra 47 (B1).
5. README dòng 19: "cứ 10 pin bỏ sót 4 / 2": không ghi bộ (97/166 → 4,2; 126/166 → 2,4).
6. README dòng 20-22 (bảng đầu): "Báo nhầm thành pin 47/45", "Hữu cơ (/300) 250/250": không ghi bộ / phạm vi. Số hữu cơ v5 = 250 không có trong docx.
7. README dòng 429-431: "khi model sai, nó thường sai ở vùng 25–50%": không ghi model, không ghi tập.
8. README dòng 435: "Model ResNet-18 trên cùng ảnh đó trả 40,8%": không ghi phiên bản (v2 hay v5).
9. README dòng 438: "plastic 86,7%": không ghi model.
10. backend/app.py dòng 117: "(44 dung so voi 42 / 49 anh that)": không ghi model (index.html dòng 176 có ghi "model v2").
11. backend/app.py dòng 33 và index.html dòng 152-153: "xac suat hiem khi vuot 90%": không có số đo, không ghi model / tập.
12. meta.json v5: "pin 129/166, bao nham pin 45": không ghi các bộ cấu thành, và lệch docx (A1).
13. garbage_classifier/model.py dòng 15: "~45 MB / ~17 MB": là kích thước checkpoint float32, không nói rõ; khác 11 MB (uint8) trong docx / README. Không mâu thuẫn nhưng dễ nhầm.

## E. Mô tả model / luật giữa docx, README và code

- Web: docx (2.6, 5.5, 6.2, 6.3), README dòng 11-15 và index.html (THU_MUC_MODEL = r18-8lop-v5; NGUONG_PIN 0.50; NGUONG_TIN_CAY 0.50; NGUONG_TOI 0.30; DO_SANG_DICH 0.45; gamma ≥ 0,35; CHU_KY_MS 250 ≈ 4 lần/giây) khớp nhau. realworld.py dùng cùng hằng số (0,30 / 0,45 / 0,35; --nguong-pin mặc định 0.5).
- API: code và docx 6.1 / README 420 khớp nhau (v2, top-1, không luật pin, không tăng sáng, ngưỡng 0,5, 10 MB, 512 MB). Chỉ docstring dòng 3 sai (A6).
- Desktop: docx không nói về desktop. README dòng 420 ghi v2. trash_ai_ui/README ghi "cùng model với frontend" (A7) và ngưỡng 60% (A5).
- Bảng 4.5 so sánh "v2 + pin 30% (cũ)" là mô hình web cũ, khớp README dòng 268-276. Bảng 4.4 v2 (top-1, không luật pin) khác Bảng 4.5 v2 ở rw5 (86,8% so với 86,9%), MTA (146 so với 144), Bower (254 so với 250). Hai bảng ghi rõ cấu hình nên không coi là lệch.
