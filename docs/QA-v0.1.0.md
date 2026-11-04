# Kiểm tra bản phát hành v0.1.0

Bản thảo tiếng Việt đầu tiên, ngày 04-11-2026. Nguồn ghim tại `d2de3fc8da8c109f082b3551d4d26e0fbb01641d`.

| Phạm vi | Kết quả |
| --- | --- |
| Nội dung | 34 chương, 772 mục, 9 bài bổ sung |
| Trường nội dung sau chuyển đổi | Đủ 4.632 trường, hiển thị thành từng mục riêng |
| Đối chiếu cấu trúc | Đủ số mục, trường, mức bằng chứng và URL nguồn; không có dấu giữ chỗ |
| Dấu kiểm | Nguồn, đầu vào bản dịch và ba file xuất khớp báo cáo build |
| EPUBCheck 5.4.0 | 0 lỗi nghiêm trọng, 0 lỗi, 0 cảnh báo |
| Bố cục EPUB | 47 tài liệu × 2 chiều rộng (320/768 px) × 2 cỡ chữ (100%/150%): 188 trường hợp đạt; không tràn ngang, phông tải đủ |
| PDF | 1.004 trang, khổ 170 × 240 mm; không phát hiện chữ vượt trang hoặc trang trắng |
| Nội dung PDF | Các đoạn và mục danh sách trong EPUB đều tìm thấy trong văn bản trích xuất PDF |
| Kiểm tra hình ảnh | Render toàn bộ PDF; xem các trang thu nhỏ và trang mẫu ở cỡ đọc, kiểm tra lại vùng bị ảnh hưởng sau sửa bố cục |

Đã sửa mục lục để không còn một mục đứng riêng trên trang cuối, sửa cách chuyển Markdown để nhãn nguồn và mức bằng chứng không dính vào đoạn trước, kiểm tra các ghi chú, dấu tiếng Việt, liên kết và phần phụ lục. Bảng rộng được dàn thành từng nhóm thông tin trong EPUB/PDF.

## Giới hạn của kết quả

- Kiểm tra EPUB ở đây dùng Chrome để thử nội dung XHTML và CSS; không phải kiểm tra thực tế trên mọi mẫu máy đọc sách. Vị trí ngắt trang EPUB phụ thuộc ứng dụng, màn hình và cỡ chữ.
- Còn 37 cảnh báo so sánh số viết trực tiếp; đã đọc đối chiếu các trường hợp này. Nhiều cảnh báo xuất phát từ cách viết số bằng chữ, khoảng trắng phân nhóm hoặc đổi đơn vị Trung Quốc sang triệu. Chúng không được tính là lỗi cấu trúc và cũng không chứng minh mọi phép diễn giải số liệu đều đúng.
- Mỗi chương có hồ sơ tự đối chiếu trong `editorial/`; chương 9 và 12 có thêm lượt đối chiếu độc lập. Chưa có thẩm định chuyên môn y khoa/pháp lý độc lập toàn bộ.
- Đọc [ưu tiên rà soát tiếp](../editorial/REVIEW_PRIORITIES.md) để biết những vấn đề của nguyên tác và phần bản dịch cần tiếp tục biên tập.

Dấu kiểm của các file tải về nằm trong `SHA256SUMS.txt` ở bản phát hành. Cách chạy lại kiểm tra: [BUILD.md](BUILD.md).
