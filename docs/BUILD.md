# Tự xuất sách và kiểm tra

Cần Python 3.10 trở lên. Chạy các lệnh dưới đây từ thư mục repo. Dùng thư mục cục bộ cho môi trường Python, phông, cache và bản xuất; không đặt chúng trong iCloud, Desktop hay Documents.

## Cài đặt

Trên macOS:

```sh
export HLTB_BUILD_ROOT="$HOME/Library/Developer/CodexBuilds/HowToLiveBetter-vi"
mkdir -p "$HLTB_BUILD_ROOT"
python3 -m venv "$HLTB_BUILD_ROOT/venv"
"$HLTB_BUILD_ROOT/venv/bin/pip" install -r tools/requirements.txt
```

Trên Linux, có thể đặt `HLTB_BUILD_ROOT` thành một đường dẫn cục bộ như `$HOME/.cache/how-to-live-better-vi`; các lệnh còn lại giữ nguyên. Lần đầu build cần Internet để tải phông Noto từ Google Fonts. Các lần sau dùng cache. Giấy phép phông nằm trong `assets/OFL-*.txt` và được nhúng vào EPUB.

## Xuất sách

```sh
"$HLTB_BUILD_ROOT/venv/bin/python" tools/build.py
```

Ba file trong `$HLTB_BUILD_ROOT/exports/`:

- `Song-tot-hon-vi-ban-nhap.md`: bản ghép, có mục lục và liên kết nội bộ.
- `Song-tot-hon-vi-ban-nhap.epub`: EPUB 3, mục lục chương/mục, phông tiếng Việt và phông dự phòng CJK.
- `Song-tot-hon-vi-ban-nhap.pdf`: khổ 170 × 240 mm, mục lục số trang, bookmark và số trang.

Có thể dùng `--out /duong/dan/cuc/bo` cho cả build và validate. Công cụ build giải symlink và từ chối các đường dẫn đồng bộ thường gặp. Mặc định cache cũng ở `HLTB_BUILD_ROOT`, không nằm cạnh mã nguồn.

## Đối chiếu nguồn và kiểm tra

Clone bản tiếng Trung vào thư mục riêng cạnh repo này, rồi ghim đúng commit:

```sh
git clone https://github.com/eternity4719/HowToLiveBetter.git ../HowToLiveBetter
git -C ../HowToLiveBetter checkout d2de3fc8da8c109f082b3551d4d26e0fbb01641d
"$HLTB_BUILD_ROOT/venv/bin/python" tools/validate.py
```

Nếu đã có bản nguồn ở nơi khác, dùng `--source /duong/dan/HowToLiveBetter`. Không chuyển phiên bản trong một bản clone đang có thay đổi chưa lưu; hãy dùng clone riêng cho việc đối chiếu.

Validator kiểm tra số mục, đủ trường, mức bằng chứng, URL nguồn, dấu kiểm nguồn và đầu vào, liên kết nội bộ EPUB, sự hiện diện của đoạn văn trong PDF, trang trắng và chữ vượt trang. Cảnh báo số liệu là danh sách để đọc đối chiếu: cách viết bằng chữ hoặc đổi đơn vị Trung Quốc sang triệu có thể tạo cảnh báo dù nghĩa không đổi. Đây không phải kiểm tra tự động toàn bộ ý nghĩa.

Trước khi phát hành, chạy EPUBCheck, xem trang PDF đã render và thử EPUB trên màn hình hẹp/cỡ chữ lớn. EPUB tự dàn lại theo thiết bị; vị trí ngắt trang không cố định. PDF giữ tiêu đề cùng đoạn tiếp theo và cho đoạn dài ngắt dòng có kiểm soát.

## Biên tập

Sửa Markdown trong `book/` hoặc `appendices/`, ghi lại đối chiếu trong `editorial/`, rồi build và validate lại. Tất cả chương trong phiên bản đầu đã được đăng ký. Khi thêm hoặc hoàn tất một chương chưa đăng ký, dùng ví dụ:

```sh
python3 tools/register.py 3 4 a1
```

`manifest.json` giữ commit nguồn, dấu kiểm từng file, số mục và trạng thái. `build-report.json` ghi dấu kiểm đầu vào và bản xuất để phát hiện việc sửa nội dung sau khi build. Các file xuất và ảnh QA không được đưa vào Git; bản phát hành chứa các file tải về.
