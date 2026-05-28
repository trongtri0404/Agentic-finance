# 🧪 Test Cases — DJIA Financial Agent

## SQL Route — Truy vấn cơ sở dữ liệu

### 1. Giá đóng cửa cụ thể (1 công ty, 1 ngày)
```
What was the closing price of Apple on 2023-10-20?
```
> **Kỳ vọng:** Trả về giá đóng cửa AAPL ngày 2023-10-20, route = `sql`

### 2. Giá cổ phiếu gần nhất
```
Show me the latest 5 closing prices of Microsoft
```
> **Kỳ vọng:** 5 dòng gần nhất từ bảng `prices` với ticker = MSFT

### 3. Thông tin sector công ty
```
Which sector does Boeing belong to?
```
> **Kỳ vọng:** Trả về sector của BA (Industrials)

### 4. Danh sách công ty theo sector
```
Which companies in DJIA belong to Technology sector?
```
> **Kỳ vọng:** Liệt kê các công ty có sector = Technology (AAPL, MSFT, CRM, CSCO...)

### 5. So sánh giá 2 công ty
```
Compare the closing price of Apple and Microsoft on 2024-01-15
```
> **Kỳ vọng:** Trả về giá close của AAPL và MSFT cùng ngày

### 6. Giá cao nhất
```
What was the highest price of Boeing in 2024?
```
> **Kỳ vọng:** MAX(high) từ bảng prices cho BA trong năm 2024

### 7. Khối lượng giao dịch công ty cụ thể
```
What was the trading volume of Visa on 2024-03-01?
```
> **Kỳ vọng:** Volume từ bảng prices cho ticker V

### 8. Tổng hợp nhiều sector
```
How many companies are in each sector?
```
> **Kỳ vọng:** GROUP BY sector, COUNT

---

## SQL Fallback Route — Test các chức năng dự phòng khi LLM quá tải

### 9. Top 1 công ty có Khối lượng (Volume) thấp nhất
```
công ty nào có volumn thấp nhất
```
> **Kỳ vọng:** Bắt đúng keyword "thấp nhất" và "volumn" (sai lỗi chính tả), tự động tìm trên toàn database và trả về 1 dòng tên công ty.

### 10. Top 1 công ty có Khối lượng (Volume) cao nhất
```
công ty nào có volumn cao nhất
```
> **Kỳ vọng:** Bắt đúng keyword "cao nhất" & "volumn", và thu gọn định dạng kết quả chỉ còn một chuỗi văn bản (VD: `Apple Inc.`).

### 11. Top công ty có Giá (Price) cao nhất 
```
công ty nào có giá cao nhất
```
> **Kỳ vọng:** Trả về 1 dòng công ty có giá cổ phiếu từng đạt mức cao nhất.

### 12. Top công ty có Giá thấp nhất kèm Năm
```
công ty nào có giá thấp nhất năm 2024
```
> **Kỳ vọng:** Script tự extract năm `2024` rồi cho vào câu query SQL và trả về 1 công ty.

---

## RAG Route — Tìm kiếm báo cáo thường niên

### 13. Rủi ro kinh doanh
```
What risks does Boeing mention in its annual report?
```
> **Kỳ vọng:** Nội dung từ section "Risk Factors" của Boeing, route = `rag`

### 14. Mô hình kinh doanh
```
What business model does Coca-Cola describe?
```
> **Kỳ vọng:** Nội dung từ section "Business" của Coca-Cola

### 15. Phân khúc kinh doanh
```
What are Microsoft's business segments?
```
> **Kỳ vọng:** Thông tin segments từ tài liệu Microsoft

### 16. Sản phẩm và dịch vụ
```
What products and services does Apple describe?
```
> **Kỳ vọng:** Nội dung về iPhone, iPad, Mac... từ section "Business"

### 17. Chiến lược kinh doanh
```
What is Apple's business strategy?
```
> **Kỳ vọng:** Thông tin chiến lược từ tài liệu Apple

### 18. Nguồn doanh thu
```
What are the main revenue sources of Microsoft?
```
> **Kỳ vọng:** Thông tin từ section Business/MD&A của Microsoft

---

## Greeting Route & Edge Cases 

### 19. Câu hỏi tiếng Việt chuẩn RAG 
```
Boeing đề cập những rủi ro gì trong báo cáo thường niên?
```
> **Kỳ vọng:** Fallback router vẫn có thể routing vào đúng RAG nhờ keyword tiếng Việt "rủi ro", "báo cáo". 

### 20. Chào hỏi thông thường
```
chào
```
> **Kỳ vọng:** Không gọi database, trả lời trực tiếp một câu chào thân thiện qua `Greeting Route`.

### 21. Công ty không có tài liệu RAG
```
What are Nike's risk factors?
```
> **Kỳ vọng:** Thông báo không tìm thấy tài liệu (Nike không có trong 4 công ty RAG)

### 22. Câu hỏi mơ hồ
```
Tell me about Apple
```
> **Kỳ vọng:** Trả về thông tin cơ bản từ SQL hoặc RAG

---

## Checklist kết quả test

| # | Câu hỏi | Route | Kết quả | ✅/❌ |
|---|---------|-------|---------|------|
| 1 | Closing price Apple 2023-10-20 | SQL | | |
| 2 | Latest 5 prices Microsoft | SQL | | |
| 3 | Sector Boeing | SQL | | |
| 4 | Technology sector companies | SQL | | |
| 5 | Compare Apple vs Microsoft | SQL | | |
| 6 | Highest price Boeing 2024 | SQL | | |
| 7 | Volume Visa 2024-03-01 | SQL | | |
| 8 | Companies per sector | SQL | | |
| 9 | Volumn thấp nhất | SQL (Fallback) | | |
| 10| Volumn cao nhất | SQL (Fallback) | | |
| 11| Giá cao nhất | SQL (Fallback) | | |
| 12| Giá thấp nhất 2024 | SQL (Fallback) | | |
| 13| Boeing risks | RAG | | |
| 14| Coca-Cola business model | RAG | | |
| 15| Microsoft segments | RAG | | |
| 16| Apple products | RAG | | |
| 17| Apple strategy | RAG | | |
| 18| Microsoft revenue | RAG | | |
| 19| Tiếng Việt RAG | RAG | | |
| 20| Lời chào ("chào") | Greeting | | |
| 21| Nike risks (no docs) | RAG | | |
| 22| Câu hỏi mơ hồ | ? | | |
