# Block 1 — Tra cứu chính sách đúng phiên bản

## 1. Phạm vi và trạng thái

Đề: https://pub.nndkhoa9.win/agentic-ai-engineering/d05-tool-use-skill-use/exercise-block-1.html

Bài làm dựa trên bản sao stage 00–02 của ZIP đã cung cấp. Stage 00 giữ nguyên mã nguồn. Stage 01 và 02 thêm tool `list_files` và đăng ký tool; không sửa system prompt, không đưa tên file, nội dung chính sách hoặc đáp án vào mã tool. Thêm dữ liệu chính sách, skill và bộ kiểm thử. Các trace cũ của bài weekly-report đã được loại khỏi bản nộp để tránh nhầm với bằng chứng của Block 1. Bản ZIP nguồn vẫn nguyên vẹn.

**Đã thực thi:** kiểm thử Python, kiểm thử tích hợp agent bằng mock model của project gốc, kiểm thử giao diện Streamlit và gọi tool trực tiếp. Stage 01: **42 passed**; stage 02: **49 passed**. Nhật ký tại `evidence/tests_stage01.txt` và `evidence/tests_stage02.txt`.

**Chưa thực thi:** hội thoại với model thật cho stage 00, A, B, A/B đổi tên, thiếu thông tin và các ca biên. Môi trường thực hiện không có OPENAI_API_KEY. Không tạo trace giả hoặc dùng mock để khẳng định model đã tự chọn skill. Vì vậy bộ bài còn cần chạy `run_cases.py` bằng cấu hình model của người học để đủ minh chứng nộp theo đề. Các kết quả chính sách ở mục 5 là đối chiếu bằng tay, không phải kết quả thực nghiệm model.

## 2. Giới hạn stage 00

Kiểm tra mã nguồn `stage-00-chat/agent.py` cho thấy agent không được cấp tool đọc/liệt kê tài liệu. Khi hỏi A mà không dán chính sách, agent chưa có căn cứ xác định phạm vi hiệu lực, thời hạn hoàn, mức phí và điều kiện kích hoạt. Nó có thể tính chênh lệch ngày từ câu hỏi nhưng không thể xác minh chính sách nội bộ. Cần kiểm tra trace thật: không có kết quả đọc tài liệu; một câu trả lời đúng ngẫu nhiên không chứng minh đã truy cập nguồn.

Lệnh tái hiện: `python run_cases.py --stage 00 --case A`. Trạng thái hiện tại: chưa có kết quả model thật.

## 3. Tool list_files

- Mã nguồn: `stage-01-files/tools/files.py`, `stage-02-skills/tools/files.py`; hàm `_list` và `list_files`.
- Đăng ký: import/export trong `tools/__init__.py`, thêm vào `TOOLS` trong `agent.py` của cả hai stage.
- Input: `path: str`, tương đối workspace; `.` là thư mục gốc.
- Output thành công: `{"ok": true, "path": "...", "entries": [{"name": "...", "path": "...", "type": "file|directory"}]}`.
- Không đệ quy; sắp xếp theo tên; đường dẫn mỗi mục tương đối workspace. Một thư mục hợp lệ rỗng trả `entries: []`.
- Tái sử dụng `_resolve` và `_error` của file tools gốc. Chặn đường dẫn tuyệt đối, `..` thoát gốc và symlink ra ngoài. Nếu một thư mục chứa symlink ra ngoài, tool trả lỗi cho cả lần liệt kê, không theo link và không trả kết quả một phần.
- Symlink trong workspace được chấp nhận. Link hỏng, loại mục không hỗ trợ hoặc lỗi truy cập trả lỗi rõ ràng.
- Đây là kiểm soát đường dẫn của lab cục bộ; không phải sandbox hệ điều hành chống tiến trình đối nghịch đồng thời thay đổi symlink giữa các thao tác.

### Bằng chứng gọi tool trực tiếp

Hai file `evidence/direct_tools_stage01.jsonl` và `evidence/direct_tools_stage02.jsonl` có cùng bố cục. Tất cả dữ liệu thử là dữ liệu giả. Mỗi dòng chứa arguments, kết quả thật và assertion thành công; trường `execution=direct_tool_not_model` phân biệt với trace model.

| Dòng | Trường hợp | Kết quả thực tế |
|---|---|---|
| 1 | Thư mục data hợp lệ | Thành công; demo.md và subdir, không có nested.md ở cấp này |
| 2 | Đường dẫn file | NOT_A_DIRECTORY |
| 3 | Đường dẫn không tồn tại | DIRECTORY_NOT_FOUND |
| 4 | ../fake-outside | PATH_OUTSIDE_WORKSPACE |
| 5 | Đường dẫn tuyệt đối | PATH_OUTSIDE_WORKSPACE |
| 6 | Symlink dẫn ra ngoài | PATH_OUTSIDE_WORKSPACE |
| 7 | Liệt kê thư mục chứa link ra ngoài | PATH_OUTSIDE_WORKSPACE |
| 8 | Đổi demo.md thành renamed.md | Thành công, trả tên mới |

`tests/test_list_files.py` kiểm tra thêm thư mục rỗng, đường dẫn rỗng, thứ tự tên, symlink nội bộ. Các test agent gốc đã cập nhật danh sách tools kỳ vọng, kiểm tra schema xuất hiện trong model_request. Các assertion giao diện/catalog chỉ được điều chỉnh từ 2 thành 3 tools và từ 1 thành 2 skills; không bỏ kiểm tra hành vi cũ.

## 4. Skill refund-policy

Nằm tại `stage-02-skills/workspace/skills/refund-policy/`, có bản sao trong `fixtures` để không mất sau reset workspace. Hai chính sách cũng có trong workspace và fixtures của stage 01/02.

Frontmatter có name và description nêu nhiệm vụ/điều kiện sử dụng. Skill yêu cầu đọc reference, kiểm tra đủ ba dữ kiện, tìm file bằng list_files, đọc nội dung và chọn phạm vi chứa ngày mua. Không chọn theo ngày yêu cầu hoặc ngày máy, không suy từ tên file. Nếu thiếu dữ kiện phải hỏi rồi dừng, không tự giả định chưa kích hoạt. Ngày ngược, tài liệu thiếu hoặc hiệu lực mâu thuẫn đều không cho phép kết luận tùy tiện.

Reference quy định đầy đủ: chính sách áp dụng; số ngày lịch; kết luận; phí khi đủ điều kiện; đường dẫn nguồn thực tế đã đọc. Skill không chứa tên hai file chính sách, đáp án A/B hay yêu cầu Bash/script.

## 5. Đối chiếu từng trường hợp

| Ca | Chính sách theo nội dung | Ngày lịch | Kết luận kỳ vọng | Trạng thái model thật |
|---|---|---:|---|---|
| A: 28/09 → 06/10, chưa kích hoạt | Trước 01/10 | 8 | Không đủ: 8 > 7; không áp dụng phí cho yêu cầu bị từ chối | Chưa chạy |
| B: 02/10 → 12/10, chưa kích hoạt | Từ 01/10 | 10 | Đủ: 10 ≤ 14; không thu phí | Chưa chạy |
| A sau đổi tên | Trước 01/10 | 8 | Không đổi kết luận; dẫn tên mới | Chưa chạy |
| B sau đổi tên | Từ 01/10 | 10 | Không đổi kết luận; dẫn tên mới | Chưa chạy |
| Thiếu trạng thái kích hoạt | Chưa kết luận | — | Hỏi sản phẩm đã kích hoạt chưa | Chưa chạy |
| Biên cũ: 24/09 → 01/10 | Trước 01/10 | 7 | Đủ nếu chưa kích hoạt; phí 10% giá trị đơn | Chưa chạy |
| Biên mới: 01/10 → 15/10 | Từ 01/10, gồm ngày này | 14 | Đủ nếu chưa kích hoạt; không phí | Chưa chạy |
| 02/10 → 12/10, đã kích hoạt | Từ 01/10 | 10 | Không đủ vì đã kích hoạt | Chưa chạy |

## 6. Cách thu và đối chiếu trace thật

Chạy các lệnh trong README. `run_cases.py` sử dụng chính `build_model`, `build_agent`, `ObserverMiddleware` của lab. Không có câu trả lời định sẵn hoặc model mock. Mỗi ca tạo agent và workspace tạm mới, chỉ có một HumanMessage; không dùng lịch sử cũ. Khi đổi tên, hai file nhận tên ngẫu nhiên và giữ nguyên nội dung. Câu hỏi chỉ là câu hỏi của đề, không nhắc skill, file hay thứ tự tool.

Trace xuất tại `evidence/live/stageXX_CASE.jsonl`; file `.index.md` bên cạnh ghi số dòng thực tế cho model_request, tool_finished và run_completed. Chương trình chỉ xác nhận chạy xong, **không tự đánh dấu chất lượng câu trả lời là PASS**.

Đối chiếu bắt buộc sau khi chạy:
1. A: tìm tool_finished/list_files và read_file trả ok=true, nội dung chính sách cũ; run_completed phải nêu 8 ngày, không đủ, dẫn đúng nguồn.
2. B ở stage 02: có read_file thành công cho SKILL.md và answer-template.md; model_request tiếp theo phải chứa các tool results này. Câu trả lời phải chọn chính sách mới, 10 ngày, đủ và không phí.
3. A_renamed/B_renamed: list_files trả tên mới; read_file và citation cuối cùng dùng tên mới; model_request đầu chỉ có câu hỏi mới và catalog, không có lịch sử ca trước.
4. missing: kết quả hỏi trạng thái kích hoạt, không chốt đủ điều kiện. Việc chưa đọc chính sách ở ca này là hợp lệ vì skill yêu cầu hỏi trước khi kết luận.
5. Stage 00: xác nhận không có tool đọc chính sách. Nếu model vẫn chốt câu trả lời, ghi nhận đó là suy đoán không có căn cứ.
6. Nếu xảy ra run_failed hoặc hết giới hạn model/tool, không xem ca đó là đạt. Kiểm tra endpoint/tool-calling, chạy lại và cập nhật báo cáo bằng kết quả thực tế.

Sau khi có trace, bổ sung kết quả quan sát và số dòng từ `.index.md` vào bảng trên. Hiện không có vị trí trace model để viện dẫn; các số dòng ở mục 3 chỉ thuộc bằng chứng tool trực tiếp.

## 7. Trả lời câu hỏi cuối bài

**Vì sao cần tool để tìm file và skill để chọn chính sách?** Tool bổ sung khả năng tác động vào môi trường: nó liệt kê dữ liệu thật đang có, trả tên/đường dẫn để agent có thể đọc. Skill bổ sung quy trình suy luận: kiểm tra dữ kiện, đọc hiệu lực, chọn theo ngày mua, tính ngày đúng quy ước, đánh giá kích hoạt và trình bày căn cứ. Tool không tự quyết định nghiệp vụ; skill không tự có quyền truy cập hệ thống file. Hai thành phần giải quyết hai lớp khác nhau của nhiệm vụ.

**Nếu chưa có tool tìm file, sửa prompt có giải quyết đổi tên file không?** Không giải quyết đáng tin cậy trong cấu hình stage 01/02 này. read_file chỉ đọc đường dẫn đã biết; write_file chỉ ghi. Prompt không tạo ra phép liệt kê thư mục và không biết tên mới trong môi trường. Ghi cứng tên chỉ hoạt động trước khi đổi tên; đoán hàng loạt tên không bảo đảm đầy đủ hoặc chính xác. Cần thêm list_files hoặc một công cụ khám phá tài liệu tương đương. Khi đã có capability, prompt/skill mới hướng dẫn sử dụng capability đó đúng cách.
