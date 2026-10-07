# Phân tích Block 1 — Tra cứu chính sách đúng phiên bản

## 1. Môi trường và bằng chứng

- Project: Block1_Refund_Policy.
- Stage thực hiện: stage-02-skills.
- Tools: read_file, write_file, list_files.
- Skill: refund-policy.
- Các file Conversation JSON nằm cùng thư mục với analysis.md.

Báo cáo sử dụng các lượt chạy cuối đã được kiểm tra đúng trên giao diện.

| File bằng chứng | Trường hợp |
|---|---|
| trace_THA.json | A |
| trace_THB.json | B |
| trace_doiten_THA.json | A sau đổi tên |
| trace_doiten_THB.json | B sau đổi tên |
| trace_thieuthongtin.json | Thiếu thông tin |

## 2. Kết quả kiểm tra tool

Tool list_files liệt kê tài liệu trong data/policies và trả về tên, đường dẫn, loại mục. Agent sử dụng đường dẫn trả về để gọi read_file.

Sau khi đổi tên tài liệu thành document-alpha.md và document-beta.md, agent tìm được các tên mới và đọc nội dung chính sách. Kết luận dựa trên phạm vi hiệu lực trong nội dung, không dựa trên tên file.

Bằng chứng:
- trace_doiten_THA.json và trace_doiten_THB.json.
- Trong messages, tìm lời gọi có tool_calls[].name là list_files.
- Kết quả tương ứng nằm ở message tool có name là list_files; trường content chứa entries.
- Các message tool có name là read_file chứa đường dẫn và nội dung tài liệu đã đọc.
- Ghép lời gọi và kết quả bằng tool_call_id.

Phần này xác nhận khả năng liệt kê và đọc tài liệu trong các tình huống thực tế. Các kiểm tra đường dẫn không hợp lệ cần bằng chứng kiểm thử riêng.

## 3. Kết quả từng trường hợp

| Trường hợp | Chính sách áp dụng | Số ngày | Kết quả | Đánh giá |
|---|---|---:|---|---|
| A: mua 28/09/2026, hoàn 06/10/2026, chưa kích hoạt | Chính sách trước 01/10/2026 | 8 | Không đủ điều kiện vì vượt giới hạn 7 ngày | PASS |
| B: mua 02/10/2026, hoàn 12/10/2026, chưa kích hoạt | Chính sách từ 01/10/2026 | 10 | Đủ điều kiện trong giới hạn 14 ngày; không thu phí | PASS |
| A sau đổi tên file | Chính sách trước 01/10/2026 | 8 | Không đủ điều kiện; dẫn đúng tên file mới | PASS |
| B sau đổi tên file | Chính sách từ 01/10/2026 | 10 | Đủ điều kiện, không phí; dẫn đúng tên file mới | PASS |
| Thiếu trạng thái kích hoạt | Chưa kết luận | — | Hỏi lại sản phẩm đã kích hoạt hay chưa | PASS |

Kết quả PASS được ghi theo các lượt chạy cuối đã được người thực hiện đối chiếu trên giao diện và lưu vào các file bằng chứng trên.

## 4. Vị trí bằng chứng trong trace

Các vị trí dưới đây là đường dẫn trong cấu trúc Conversation JSON. Chỉ số mảng bắt đầu từ 0.

### 4.1. Trường hợp A — trace_THA.json

- Câu hỏi: messages[0].content.
- Lời gọi tool: messages của assistant, trường tool_calls.
- Nội dung chính sách: messages của tool read_file, trường content.
- Kết luận: trường content của message assistant cuối cùng.

Đối chiếu: ngày mua 28/09/2026 trước 01/10/2026; áp dụng giới hạn 7 ngày. Ngày yêu cầu hoàn cách ngày mua 8 ngày nên không đủ điều kiện.

### 4.2. Trường hợp B — trace_THB.json

- Câu hỏi: messages[0].content.
- Nội dung chính sách: messages của tool read_file, trường content.
- Kết luận và phí: trường content của message assistant cuối cùng.

Đối chiếu: ngày mua 02/10/2026 thuộc chính sách từ 01/10/2026; 10 ngày không vượt giới hạn 14 ngày và sản phẩm chưa kích hoạt nên đủ điều kiện, không thu phí.

### 4.3. A sau đổi tên — trace_doiten_THA.json

- Tên file mới: trường content của message tool list_files.
- Đường dẫn và nội dung đã đọc: trường content của các message tool read_file.
- Kết luận và nguồn dẫn: trường content của message assistant cuối cùng.

Đối chiếu: tên file thay đổi nhưng nội dung giữ nguyên; kết luận vẫn là không đủ điều kiện.

### 4.4. B sau đổi tên — trace_doiten_THB.json

- Đọc skill: lời gọi read_file có path là skills/refund-policy/SKILL.md và kết quả tương ứng.
- Đọc reference: lời gọi read_file có path là skills/refund-policy/references/answer-template.md và kết quả tương ứng.
- Tìm tài liệu mới: lời gọi list_files và kết quả entries.
- Đọc chính sách: các kết quả read_file theo đường dẫn mới.
- Kết luận và nguồn dẫn: message assistant cuối cùng.

Đối chiếu: kết luận vẫn là đủ điều kiện, không thu phí; nguồn dẫn sử dụng tên file mới.

### 4.5. Thiếu thông tin — trace_thieuthongtin.json

- Câu hỏi thiếu trạng thái kích hoạt: messages[0].content.
- Hướng dẫn xử lý: kết quả read_file cho SKILL.md.
- Câu hỏi bổ sung: trường content của message assistant cuối cùng.

Agent hỏi trạng thái kích hoạt, không tự giả định và chưa kết luận đủ hay không đủ điều kiện.

Ngoài messages, snapshots lưu context gửi model; events lưu thứ tự sự kiện nếu có trong file xuất.

## 5. Vai trò của tool và skill

Tool cung cấp khả năng truy cập dữ liệu thực tế:
- list_files tìm tên và đường dẫn tài liệu hiện có.
- read_file đọc nội dung chính sách, skill và reference.

Skill cung cấp quy trình:
- Kiểm tra ngày mua, ngày yêu cầu hoàn và trạng thái kích hoạt.
- Chọn chính sách theo ngày mua.
- Tính số ngày đã qua.
- Đánh giá thời hạn và điều kiện kích hoạt.
- Trả lời theo mẫu và dẫn nguồn thực tế.

Tool và skill phối hợp giúp agent tìm đúng tài liệu và áp dụng đúng chính sách.

## 6. Sửa prompt có thay thế tool tìm file không?

Không. Prompt chỉ cung cấp hướng dẫn, không cho phép agent quan sát thư mục.

Khi tài liệu đổi tên, read_file không thể đọc đường dẫn cũ. list_files giúp agent tìm đường dẫn mới; sau đó skill hướng dẫn chọn chính sách dựa trên nội dung.

Ghi cứng tên file trong prompt không giải quyết được thay đổi tên và không phù hợp với mục tiêu bài tập.

## 7. Kết luận

Trong năm lượt chạy cuối đã kiểm tra, agent trả lời đúng A, B, A/B sau đổi tên và tình huống thiếu thông tin.

Việc đổi tên tài liệu không làm thay đổi kết luận khi nội dung chính sách giữ nguyên. Agent chọn phiên bản theo ngày mua và dẫn đường dẫn tài liệu thực tế.

Các kết quả này xác nhận những lượt được lưu làm bằng chứng; chưa đo độ ổn định qua nhiều lần chạy lặp lại.