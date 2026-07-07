# Sơ đồ Kiến trúc Hệ thống (System Architecture)
## Dự án: Tích hợp Quản lý Khách hàng (CRM) & Quản lý Văn bản trên Odoo 16

Tài liệu này chứa sơ đồ kiến trúc hệ thống 3 lớp tiêu chuẩn và tích hợp dịch vụ ngoài của Odoo. Bạn có thể copy mã nguồn dưới đây dán vào Draw.io (**Arrange -> Insert -> Advanced -> PlantUML... / Mermaid...**) để vẽ tự động.

---

### 1. Sơ đồ dạng Mermaid (Vẽ tự động cực đẹp trên Draw.io hoặc GitHub)

```text
graph TD
    %% Tầng Client
    subgraph Client [Tầng Client / Trình diễn]
        UI[Web Browser<br>Odoo Web UI]
        Mobile[Mobile App<br>Optional]
    end

    %% Tầng Odoo Server
    subgraph AppServer [Odoo Server]
        Framework[Odoo 16 Framework]
        Modules[ERP Modules<br>HRM / CRM / Documents]
    end

    %% Tầng Lưu trữ dữ liệu
    subgraph Storage [Lưu trữ dữ liệu]
        Postgres[(PostgreSQL Database<br>Centralized Data Store)]
        FileStore[File Storage<br>Odoo Attachments / Local / S3]
    end

    %% Lớp tích hợp dịch vụ
    subgraph Integration [Integration Layer]
        Intg[REST API / Webhooks / RPC]
    end

    %% Các dịch vụ tích hợp bên ngoài
    subgraph Services [External Services]
        OCR[OCR Service<br>Text extraction from scanned docs]
        PKI[PKI / Digital Signature Service<br>Signing and verification]
        Notif[Notification Service<br>Email / SMS / In-app notifications]
        Cloud[Cloud Platform<br>AWS / Azure / GCP]
    end

    %% Các kết nối
    UI & Mobile --> AppServer
    AppServer --> Postgres
    AppServer --> FileStore
    AppServer -->|API Calls| Intg
    Postgres & FileStore -.-> Intg
    
    Intg -->|REST API| OCR
    Intg -->|REST API| PKI
    Intg -->|REST API| Notif
    Intg -->|REST API / Queue| Cloud

    %% Định dạng CSS cho đẹp mắt
    style Client fill:#f9f9f9,stroke:#333,stroke-width:1px;
    style AppServer fill:#e1f5fe,stroke:#0288d1,stroke-width:2px;
    style Storage fill:#efebe9,stroke:#5d4037,stroke-width:2px;
    style Integration fill:#ede7f6,stroke:#512da8,stroke-width:2px;
    style Services fill:#f1f8e9,stroke:#558b2f,stroke-width:2px;
    style Postgres fill:#bbdefb,stroke:#1565c0,stroke-width:1px;
    style FileStore fill:#d7ccc8,stroke:#4e342e,stroke-width:1px;
```

---

### 2. Sơ đồ dạng PlantUML (Đặc tả Component chi tiết trên Draw.io)

```text
@startuml
package "Client Layer" {
    [Web Browser\n(Odoo Web UI)] as UI
    [Mobile App\n(optional)] as Mobile
}

package "Odoo Server" {
    [Odoo 16 Framework] as Framework
    [ERP Modules\nHRM / CRM / Documents] as Modules
}

database "PostgreSQL Database\n(Centralized Data Store)" as Postgres
node "File Storage\n(Odoo Attachments)" as FileStore

package "Integration Layer" {
    [REST API / Webhooks / RPC] as Intg
}

package "External Services" {
    [OCR Service\n(Text extraction)] as OCR
    [PKI / Digital Signature Service\n(Signing & verification)] as PKI
    [Notification Service\n(Email / SMS API)] as Notif
    [Cloud Platform\n(AWS / Azure / GCP)] as Cloud
}

' Đường truyền dữ liệu
UI --> Modules
Mobile --> Modules
Modules --> Postgres
Modules --> FileStore
Modules --> Intg : API Calls

Intg --> OCR : REST API
Intg --> PKI : REST API
Intg --> Notif : REST API
Intg --> Cloud : REST API / Queue

Postgres ..> Intg
FileStore ..> Intg
@enduml
```

---

### 3. Giải thích các phân vùng Kiến trúc

1. **Client (Tầng Trình diễn)**: Người dùng cuối truy cập Odoo thông qua Trình duyệt Web (Odoo Web UI) sử dụng các framework UI hiện đại (OWL, JS, CSS).
2. **Odoo Server (Tầng Nghiệp vụ)**: Bộ não của hệ thống chạy trên nền tảng Odoo 16 Framework và Python. Chứa các phân hệ cốt lõi gồm **HRM (Nhân sự)**, **CRM (Khách hàng)**, và **Documents (Quản lý văn bản)**.
3. **Storage (Tầng Lưu trữ)**:
   * **PostgreSQL Database**: Lưu trữ dữ liệu cấu trúc (Metadata, Thông tin khách hàng, cấu hình và lịch sử tương tác).
   * **File Storage**: Lưu trữ các file nhị phân đính kèm (PDF hợp đồng, ảnh CCCD, tệp đính kèm văn bản).
4. **Integration Layer (Lớp Tích hợp)**: Sử dụng các giao thức REST API / Webhooks để gọi các dịch vụ chuyên dụng bên ngoài.
5. **Dịch vụ tích hợp bên ngoài (External Services)**:
   * **OCR Service**: Trích xuất văn bản tự động từ các tài liệu scan (như hóa đơn, hồ sơ).
   * **PKI / Digital Signature Service**: Dịch vụ ký số để xác nhận tính pháp lý của hợp đồng và văn bản đi/đến.
   * **Notification Service**: Tự động gửi Email/SMS thông báo sự kiện cho Khách hàng và Nhân sự.
   * **Cloud Platform (AWS/Azure/GCP)**: Cung cấp tài nguyên hạ tầng, lưu trữ và hàng đợi.
