# Thiết kế bản đọc v0.2.0

Mục tiêu là giúp mắt theo được nội dung chính, đồng thời vẫn tìm được nguồn và giới hạn của từng lời khuyên. Không dùng màu sắc làm dấu hiệu duy nhất: mỗi phần có nhãn và kiểu trình bày riêng.

## Phân cấp nội dung

| Thành phần | EPUB | PDF |
| --- | --- | --- |
| Ý chính | Đứng đầu mục, không lặp nhãn | 11,2 pt, giãn dòng 18 pt |
| Chi phí | Nhỏ hơn phần chính | 9,2 pt, giãn dòng 14 pt |
| Lưu ý | Khối có dấu `!`, viền màu hổ phách | 9,4 pt, khung riêng, vẫn hiện trực tiếp |
| Chi tiết và cơ sở, mức bằng chứng, dẫn chứng | Mở qua `i Chi tiết và dẫn chứng` | Hiện sau nội dung chính; 9,4 pt cho giải thích, 8,3 pt cho dẫn chứng |
| Ghi chú Việt Nam | Liên kết mở ghi chú, đặt sau đoạn liên quan | 9 pt, viền xanh trầm, sau nội dung liên quan |
| Đính chính an toàn | Luôn hiện trực tiếp | Luôn hiện trực tiếp |

Phông Noto Serif được nhúng với tên nội bộ riêng cho kiểu thường và đậm. EPUB cho phép ứng dụng và người đọc đổi cỡ chữ; màu có biến thể cho giao diện tối. PDF dùng khổ 170 × 240 mm, lề thoáng, tiêu đề đi cùng phần văn tiếp theo, kiểm soát dòng lẻ khi ngắt trang. Đoạn quá dài vẫn phải tiếp sang trang sau; không ép cả mục vào một khối khiến trang trước bỏ trống.

## Điều hướng

Trang mục lục hiện ngay sau bìa. Mục lục chuẩn EPUB chứa cả chương lẫn 772 mục; đầu mỗi chương có đường về mục lục sách và danh sách mục trong chương. Số trong lời dẫn như “Thắt dây an toàn (1)” và dẫn chiếu “chương 13, mục 3” được liên kết tới ID ổn định. Bản Markdown ghép và PDF cũng có liên kết nội bộ.

Ghi chú bổ sung trong EPUB dùng `epub:type="noteref"` và `aside epub:type="footnote"`, theo [hướng dẫn pop-up footnotes của Apple Books](https://help.apple.com/itc/booksassetguide/en.lproj/itccf8ecf5c8.html). Cách này để Books điều khiển cửa sổ ghi chú; không dùng JavaScript hoặc mặc định rằng mọi máy đọc sách hỗ trợ HTML `details`. Các ứng dụng khác có thể hiện ghi chú trực tiếp. PDF hiển thị đầy đủ nội dung, không giả lập cơ chế thu gọn.

## Tài liệu tham khảo về trình bày

- [Apple Books: Designing great book layouts and interiors](https://authors.apple.com/support/3975-designing-great-book-layouts-interiors): dùng hệ thống tiêu đề rõ ràng và điều hướng phù hợp sách điện tử.
- [O’Reilly Atlas: Writing](https://docs.atlas.oreilly.com/atlas/writing.html): phân biệt ghi chú, cảnh báo và nội dung bên lề bằng khối có nhãn.
- [Manning: chương mẫu *DSLs in Boo*](https://manning-content.s3.amazonaws.com/download/e/903a650-a948-4697-b8d8-603321078874/Sample1.pdf), trang sách 3: nhãn NOTE, thụt lề và khoảng trắng giúp tách phần bổ sung khỏi văn chính. Đã xem trang PDF mẫu khi thiết kế.

Đây là các điểm tham khảo về phân cấp thị giác. Khổ trang, phông, màu và thông số giãn dòng của bản dịch được chọn riêng, không phải thông số chính thức của các nhà xuất bản.
