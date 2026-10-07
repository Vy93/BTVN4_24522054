# Bài luyện tập Block 1 — Tra cứu chính sách đúng phiên bản

Bài làm gồm stage 00–02, tool `list_files`, skill `refund-policy`, tài liệu chính sách hoàn tiền, bộ kiểm thử và báo cáo `analysis.md`.

Agent tìm tài liệu trong workspace, chọn chính sách theo **ngày mua**, kiểm tra thời hạn và trạng thái kích hoạt, sau đó trả lời kèm căn cứ.

## 1. Trạng thái thực hiện

- Đã bổ sung và đăng ký tool `list_files` ở stage 01 và 02.
- Đã tạo skill `refund-policy` và mẫu trả lời.
- Đã chạy model qua giao diện Streamlit.
- Đã kiểm tra đúng các lượt chạy cuối: A, B, A/B sau đổi tên và thiếu thông tin.
- Đã tải Conversation JSON và lưu cùng thư mục với README.
- Kết quả và vị trí bằng chứng được trình bày trong `analysis.md`.

Kết quả kiểm thử đã ghi nhận trước đó: stage 01 có 42 tests đạt, stage 02 có 49 tests đạt. Kết quả kiểm thử mã nguồn không thay thế việc đánh giá câu trả lời của model.

## 2. Cài môi trường

Yêu cầu Python 3.11 trở lên.

Nếu chưa có môi trường, mở PowerShell tại thư mục `BTVN4`:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
cd .\Block1_Refund_Policy
python -m pip install -r requirements-verified.txt
```

Nếu terminal đã có dấu `(.venv)`, dùng môi trường đang kích hoạt, không chạy lại lệnh tạo `.venv`.

Các lệnh ở những phần tiếp theo được chạy tại thư mục `Block1_Refund_Policy`, với môi trường đã kích hoạt.

## 3. Cấu hình model

Mỗi stage sử dụng file `.env` riêng. Nếu chưa có file này, sao chép từ `.env.example`:

```powershell
foreach ($stage in @("stage-00-chat", "stage-01-files", "stage-02-skills")) {
    if (-not (Test-Path "$stage/.env")) {
        Copy-Item "$stage/.env.example" "$stage/.env"
    }
}
```

Điền các biến theo mẫu:

```dotenv
OPENAI_API_KEY=YOUR_API_KEY
MODEL_NAME=YOUR_MODEL_NAME
OPENAI_BASE_URL=YOUR_BASE_URL
```

`OPENAI_BASE_URL` chỉ cần thiết khi dùng endpoint tùy chỉnh. Model và endpoint phải hỗ trợ tool calling.

Dùng cùng cấu hình model khi so sánh giữa các stage. Sau khi thay đổi `.env`, dừng và khởi động lại ứng dụng.

Không đưa API key vào mã nguồn hoặc bài nộp.

## 4. Chạy giao diện

```powershell
python -m streamlit run stage-02-skills/app.py
```

Mở địa chỉ hiển thị trong terminal, thường là:

```text
http://localhost:8501
```

Trong phần `State & Context`, kiểm tra:

- Tool schema có `read_file`, `write_file`, `list_files`.
- Skill catalog có `refund-policy`.

Dòng mô tả tĩnh ở đầu trang có thể chỉ ghi hai tool; danh sách tool schema thể hiện các tool thực sự được cấp cho model.

Mỗi trường hợp cần bắt đầu bằng nút **Cuộc trò chuyện mới**.

### Trường hợp A

```text
Tôi mua ngày 28/09/2026, yêu cầu hoàn ngày 06/10/2026, chưa kích hoạt. Tôi có được hoàn không?
```

Kỳ vọng: chính sách trước 01/10/2026; 8 ngày vượt giới hạn 7 ngày; không đủ điều kiện hoàn tiền.

### Trường hợp B

```text
Tôi mua ngày 02/10/2026, yêu cầu hoàn ngày 12/10/2026, chưa kích hoạt. Tôi có được hoàn không?
```

Kỳ vọng: chính sách từ 01/10/2026; 10 ngày trong giới hạn 14 ngày; đủ điều kiện và không thu phí.

### Sau đổi tên file

Đổi tên hai tài liệu trong:

```text
stage-02-skills/workspace/data/policies/
```

Giữ nguyên nội dung, tạo hội thoại mới rồi chạy lại A và B.

Kỳ vọng: kết luận không thay đổi; agent dùng `list_files` tìm tên mới, đọc tài liệu và dẫn đúng đường dẫn hiện tại.

### Thiếu thông tin

```text
Tôi mua ngày 02/10/2026, muốn hoàn ngày 12/10/2026.
```

Kỳ vọng: hỏi trạng thái kích hoạt; không tự giả định và chưa kết luận.

## 5. Lưu bằng chứng

Sau mỗi lượt chạy, tải **Conversation JSON** từ giao diện. Các file bằng chứng hiện được lưu cùng thư mục với README:

| File | Nội dung |
|---|---|
| `trace_THA.json` | Trường hợp A |
| `trace_THB.json` | Trường hợp B |
| `trace_doiten_THA.json` | A sau đổi tên |
| `trace_doiten_THB.json` | B sau đổi tên |
| `trace_thieuthongtin.json` | Thiếu trạng thái kích hoạt |

Conversation JSON chứa câu hỏi, lời gọi tool, kết quả tool, context và câu trả lời cuối.

Ứng dụng cũng tự ghi nhật ký sự kiện `.jsonl` tại:

```text
stage-02-skills/traces/
```

Giữ các trace `.jsonl` tương ứng để nộp kèm Conversation JSON. Không chỉnh sửa nội dung bằng chứng.

Trong `analysis.md`, ghi kết quả từng trường hợp và vị trí bằng chứng bằng số dòng hoặc đường dẫn trường JSON.

## 6. Chạy bằng công cụ thu trace

Ngoài giao diện, có thể chạy:

```powershell
python run_cases.py --stage 00 --case A
python run_cases.py --stage 01 --case all
python run_cases.py --stage 02 --case all
```

Các ca hỗ trợ:

- `A`, `B`, `missing`.
- `boundary_old`, `boundary_new`, `activated`.
- `A_renamed`, `B_renamed`.

Ví dụ chạy riêng B sau đổi tên:

```powershell
python run_cases.py --stage 02 --case B_renamed
```

Mỗi ca sử dụng agent và workspace tạm mới. Việc đổi tên chỉ diễn ra trong workspace tạm.

Kết quả lưu tại `evidence/live/`, gồm trace `.jsonl` và chỉ mục `.index.md`.

Chạy hoàn tất không đồng nghĩa câu trả lời đúng; cần đối chiếu chính sách và kết luận.

## 7. Kiểm thử không cần API

```powershell
python -m pytest stage-01-files/tests -q
python -m pytest stage-02-skills/tests -q
python check_tools.py --stage 01
python check_tools.py --stage 02
```

Chạy hai stage bằng các lệnh riêng vì tên module nội bộ trùng nhau.

Trên Windows, các test tạo symlink có thể cần Developer Mode hoặc quyền phù hợp. Phân biệt lỗi quyền tạo symlink với lỗi xử lý của tool.

Kiểm thử trực tiếp tool không thay thế trace hội thoại với model.

## 8. Nội dung nộp

- Mã nguồn stage 01 và 02 đã sửa.
- Skill `refund-policy`, reference và tài liệu chính sách.
- `analysis.md`: kết quả kiểm tra tool, kết quả từng trường hợp và vị trí bằng chứng.
- Các trace `.jsonl` cần thiết và Conversation JSON tương ứng, đặc biệt A, B sau đổi tên và thiếu thông tin.

Không nộp `.env`, `.venv`, API key hoặc cache như `__pycache__`.

Block 1 sử dụng stage 00–02; không cần stage 03/04.
