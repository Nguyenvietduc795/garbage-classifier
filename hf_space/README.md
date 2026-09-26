---
title: Bỏ vào thùng nào
emoji: ♻️
colorFrom: green
colorTo: blue
sdk: gradio
app_file: app.py
pinned: false
license: mit
short_description: Phân loại ảnh rác thành 7 nhóm và gợi ý cách vứt đúng
---

# Bỏ vào thùng nào?

Phân loại ảnh rác thành 7 nhóm — pin, bìa carton, quần áo, thủy tinh, kim loại,
giấy, nhựa — kèm gợi ý xử lý cho từng loại.

ResNet-18 fine-tune từ ImageNet trên 7.772 ảnh.

## Độ chính xác

| Đo trên | Accuracy |
|---|---|
| Ảnh cùng nguồn dataset (1.672 ảnh) | 94,4% |
| **Ảnh đời thực từ Wikimedia (49 ảnh)** | **57,1%** |

Cột thứ hai mới là con số thật khi bạn đưa ảnh của mình vào. Khoảng cách đến từ
**domain shift**: dữ liệu huấn luyện gần như toàn ảnh một vật trên nền sạch, còn
ảnh đời thường có nhiều vật, nền lộn xộn, ánh sáng bất kỳ.

Khi model không đủ tự tin (dưới 60%), giao diện báo *"Chưa chắc"* và không đưa gợi ý —
sai mà biết ngập ngừng tốt hơn sai mà tự tin.

## Đã thử gì để cải thiện

| Cách | Thay đổi trên ảnh đời thực |
|---|---|
| Augmentation mạnh | 0 điểm (thử 2 lần) |
| Hạ learning rate backbone | +4 điểm (trong sai số) |
| **Thêm 7.922 ảnh từ nguồn khác** | **+12,2 điểm** |

Chỉ dữ liệu đa dạng mới có tác dụng, và phải là dữ liệu *khác kiểu* — thêm ảnh
cùng phong cách studio không giúp gì.

## Giới hạn

- Lớp `nhựa` yếu nhất — chai nhựa trong và chai thủy tinh rất giống nhau
- Bộ test 49 ảnh có sai số khoảng ±7 điểm và thiếu lớp `quần áo`
- Chưa phù hợp để dùng thật; cần bổ sung ảnh chụp trong bối cảnh thực tế
