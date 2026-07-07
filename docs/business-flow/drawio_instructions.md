# Hướng dẫn vẽ sơ đồ End-to-End: Số hóa hồ sơ khách hàng bằng lệnh trên Draw.io

Để tạo sơ đồ quy trình một cách nhanh chóng và chuyên nghiệp nhất trên Draw.io mà không cần kéo thả tay thủ công, bạn có thể sử dụng tính năng **Insert từ mã nguồn (PlantUML hoặc Mermaid)**.

---

### Cách thực hiện trên Draw.io:
1. Truy cập trang web: [draw.io (diagrams.net)](https://app.diagrams.net/).
2. Chọn **Create New Diagram** (hoặc mở file trống).
3. Trên thanh công cụ trên cùng, chọn menu: **Arrange** -> **Insert** -> **Advanced** -> **PlantUML...** (hoặc **Mermaid...**).
4. Copy toàn bộ đoạn mã code tương ứng dưới đây và dán vào ô văn bản.
5. Bấm **Insert** (Chèn). Hệ thống sẽ tự động vẽ sơ đồ luồng hoàn hảo cho bạn!

---

### MÃ 1: Định dạng PlantUML (Khuyên dùng - Vẽ dạng Sequence Diagram)

```text
@startuml
skinparam handwritten false
skinparam monochrome false
skinparam packageStyle rect
skinparam defaultFontName "Segoe UI"
skinparam roundcorner 10

title Quy trình End-to-End: Số hóa hồ sơ khách hàng

actor "Nhân viên CRM" as NV
actor "Trưởng phòng" as TP
database "Hệ thống Odoo (DB)" as HT
actor "Khách hàng" as KH

== Bước 1: Tiếp cận & Số hóa Hồ sơ Pháp lý ==
NV -> HT: Tạo Khách hàng tiềm năng (Lead)
NV -> HT: Đính kèm Hồ sơ pháp lý (ảnh/PDF ĐKKD, CCCD...)
note right of NV: Lưu vào bảng 'tai_lieu_phap_ly'\nLiên kết với nhân viên phụ trách (HRM)

== Bước 2: Thẩm định & Chuyển đổi Khách hàng ==
NV -> TP: Trình duyệt hồ sơ tiềm năng
TP -> HT: Phê duyệt -> Chuyển giai đoạn "Ký hợp đồng" (Giai đoạn 3)
HT -> HT: [TỰ ĐỘNG HÓA 1] Sinh Khách hàng chính thức (khach_hang)

== Bước 3: Ký kết Hợp đồng Giao dịch ==
NV -> HT: Nhấn nút "Ký hợp đồng" trên giao diện Khách hàng
HT -> HT: [TỰ ĐỘNG HÓA 2] Tạo Hợp đồng mới (hop_dong)\nTrạng thái: "Đang thực hiện"

== Bước 4: Số hóa Văn bản & Quyết định ==
NV -> HT: Soạn thảo/Nhập văn bản ký kết (quan_ly_van_ban)\nLiên kết với Khách hàng & Tệp đính kèm
NV -> TP: Trình ký văn bản
TP -> HT: Phê duyệt & Ký/Ban hành (da_ky / hoan_tat)
HT -> HT: [TỰ ĐỘNG HÓA 3] Ghi nhận Lịch sử tương tác (lich_su_tuong_tac)\nvới chi tiết Số hiệu và Trích yếu văn bản

== Bước 5: Hoàn tất & Chăm sóc ==
HT -> KH: Tự động gửi Email thông tin hợp đồng & File đính kèm
@enduml
```

---

### MÃ 2: Định dạng Mermaid (Vẽ dạng Flowchart quy trình từng bước)

```text
graph TD
    Start([Bắt đầu]) --> Step1[Nhân viên: Tạo Lead & Tải lên Hồ sơ pháp lý PDF/Ảnh]
    Step1 --> Step2[Trưởng phòng: Thẩm định hồ sơ tiềm năng]
    Step2 --> Step3[Hệ thống: Tự động chuyển đổi thành Khách hàng chính thức]
    Step3 --> Step4[Nhân viên: Bấm nút Ký hợp đồng trên Form Khách hàng]
    Step4 --> Step5[Hệ thống: Tự động sinh Hợp đồng chính thức]
    Step5 --> Step6[Nhân viên: Nhập Văn bản liên quan & Trình phê duyệt]
    Step6 --> Step7[Trưởng phòng: Phê duyệt & Ký ban hành Văn bản]
    Step7 --> Step8[Hệ thống: Tự động ghi nhận Lịch sử tương tác của khách hàng]
    Step8 --> Step9[Hệ thống: Tự động gửi Email hợp đồng cho Khách hàng]
    Step9 --> End([Hoàn tất Số hóa])

    style Step3 fill:#d4edda,stroke:#28a745,stroke-width:2px;
    style Step5 fill:#d4edda,stroke:#28a745,stroke-width:2px;
    style Step8 fill:#d4edda,stroke:#28a745,stroke-width:2px;
    style Step9 fill:#d4edda,stroke:#28a745,stroke-width:2px;
```
