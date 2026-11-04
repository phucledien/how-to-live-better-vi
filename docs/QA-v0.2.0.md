# Kiểm tra bản phát hành v0.2.0

Ngày 05-11-2026. Nguồn vẫn ghim tại `d2de3fc8da8c109f082b3551d4d26e0fbb01641d`.

## Nội dung và cách đọc

Đã đọc tiêu đề, chi phí và phần giải thích chính của toàn bộ 772 mục, phần mở đầu các chương và chín phụ lục. Phần nghiên cứu và lưu ý được rà thêm theo các điểm cần làm rõ; không tuyên bố đã viết lại từng câu trong toàn bộ dẫn chứng dài. So với v0.1.0, bỏ qua việc đổi tên nhãn, 521 mục có sửa tiêu đề, câu chữ hoặc dẫn chiếu; 317 phần ý chính, 192 phần chi phí, 59 phần giải thích chi tiết và 120 phần lưu ý có thay đổi. Nội dung các dòng trích dẫn và mức bằng chứng không đổi.

Hồ sơ biên tập: [01–12](../editorial/READABILITY-01-12.md), [13](../editorial/READABILITY-13.md), [14–24 và A1–A3](../editorial/READABILITY-14-24-A1-A3.md), [25–34](../editorial/READABILITY-25-34.md), [A4–A9](../editorial/READABILITY-A4-A9.md).

Trang mục lục xuất hiện sau bìa EPUB. Các số mục trong lời dẫn và dẫn chiếu trong bài có liên kết nội bộ; đã làm rõ những dẫn chiếu dễ nhầm sang chương hiện tại. Nghiên cứu và ghi chú Việt Nam dùng footnote gốc của Apple Books; lưu ý an toàn và đính chính luôn hiện trực tiếp. PDF trình bày đầy đủ mọi phần, với cỡ chữ nhỏ hơn cho phần bổ sung. Xem [lý do thiết kế và nguồn tham khảo](READING-DESIGN.md).

## Kết quả kiểm tra

| Phạm vi | Kết quả |
| --- | --- |
| Nội dung | 34 chương, 772 mục, 9 phụ lục |
| Trường sau chuyển đổi | Đủ 4.632 trường; không có dấu giữ chỗ |
| Đối chiếu cấu trúc | Đúng số mục, đủ trường, mức bằng chứng và URL nguồn |
| EPUBCheck 5.4.0 | 0 lỗi nghiêm trọng, 0 lỗi, 0 cảnh báo |
| Liên kết EPUB | 4.477 liên kết nội bộ đều có đích; 795 liên kết mở ghi chú có đích footnote hợp lệ |
| Bố cục EPUB | 48 tài liệu × 2 chiều rộng 320/768 px × 2 cỡ chữ 100%/150%: 192 trường hợp đạt, không tràn ngang |
| Tương tác và màu | 15 kiểm tra đạt: mục lục → chương, số (1) → mục thắt dây an toàn, liên kết giữa chương, ghi chú và đường quay lại, bốn trang ở chế độ sáng/tối |
| Kiểm tra hồi quy | 5 bài kiểm tra đạt: số mục, dải số, dẫn chiếu đảo thứ tự, bảo toàn nguồn và tách ghi chú an toàn |
| PDF | 1.317 trang, 170 × 240 mm; không có trang trắng hoặc chữ vượt biên trang |
| Nội dung PDF | Mọi đoạn văn và mục danh sách trong EPUB đều tìm được trong văn bản trích xuất PDF |
| Điều hướng PDF | 2.069 liên kết nội bộ có đích hợp lệ; không phát hiện tiêu đề mục nằm riêng cuối trang |
| Phông | Nhúng Noto Serif thường/đậm với tên riêng và phông CJK dự phòng; không thiếu ký tự cần dùng |
| Kiểm tra hình ảnh | Render toàn bộ PDF thành 21 bảng trang thu nhỏ; xem mẫu đầu/giữa/cuối sách và trang ở cỡ đọc, kiểm tra lại vùng sửa cuối |

## Phạm vi kiểm chứng Apple Books

Đã nhập EPUB thử vào Apple Books trên macOS và xem bố cục thực tế, chữ đậm/thường và liên kết điều hướng ở đầu trang. Công cụ thao tác trả lỗi cửa sổ không có focus, kể cả sau bước khôi phục cửa sổ, nên **chưa kiểm chứng trực tiếp thao tác mở pop-up trong Books**. Không dùng kết quả Chrome để thay cho tuyên bố đã thử pop-up gốc. Markup được kiểm theo tài liệu Apple; liên kết, đích footnote và đường quay lại đã được kiểm tự động, thao tác qua trình duyệt cũng đạt.

Vị trí ngắt trang EPUB tùy ứng dụng, cỡ chữ và màn hình. Ứng dụng không hỗ trợ pop-up có thể hiện ghi chú trực tiếp. PDF cho đoạn dài nối sang trang sau, giữ tiêu đề cùng văn bản tiếp theo và kiểm soát dòng lẻ; không ép một mục dài vào một trang.

## Giới hạn biên tập

Còn 37 cảnh báo so sánh số viết trực tiếp, giống danh sách v0.1.0 đã đọc đối chiếu; không có cảnh báo mới. Các trường hợp gồm cách viết bằng chữ, phân nhóm chữ số hoặc đổi đơn vị. Kiểm tra này không chứng minh mọi phép diễn giải số liệu đều đúng. Bản thảo chưa có thẩm định y khoa/pháp lý độc lập toàn bộ; [các ưu tiên rà soát tiếp](../editorial/REVIEW_PRIORITIES.md) vẫn áp dụng.

Dấu kiểm nguồn, đầu vào và ba file xuất khớp báo cáo build. `SHA256SUMS.txt` ở bản phát hành chứa dấu kiểm tải về. Các file xuất, cache và ảnh QA được giữ ở thư mục cục bộ dưới `Library/Developer`, không nằm trong iCloud hoặc Git.
