# Member Role Report — Day 10: Data Pipeline & Data Observability

> Mỗi thành viên trong nhóm tự hoàn thành mẫu này để báo cáo đúng vai trò, phần việc và mức hiểu của mình. Không sao chép nguyên báo cáo chung hoặc báo cáo của thành viên khác. Thay nội dung trong dấu `[ ]` và xóa các dòng hướng dẫn không cần thiết trước khi nộp.

## 1. Thông tin cá nhân

| Thông tin         | Nội dung                  |
| ------------------ | -------------------------- |
| Họ và tên       | [Nguyễn Thành Luân]             |
| MSSV               | [2A202602769]                     |
| Khóa/Lớp         | [K4]              |
| Tên nhóm         | [chuadatten]     |
| Vai trò chính    | [Data_Collect]                 |
| Repository         | [https://github.com/tom-e666/K4-L3B-DAY10-chuadatten-DataPipelineDataObservability.git] |
| Ngày hoàn thành | [2026-09-26]               |

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

| Module/deliverable | File/hàm phụ trách | Input nhận vào | Output bàn giao | Trạng thái |
|---|---|---|---|---|
| [Thu thập dữ liệu bài báo] | [`src/ingestion/crossref.py` · `fetch_source_records()`] | [Cấu hình truy vấn Crossref] | [Dữ liệu thô trong `data/raw/crossref_response.json`] | [Hoàn thành] |
| [Chuẩn hóa dữ liệu Crossref] | [`src/ingestion/crossref.py` · `parse_crossref_payload()`] | [JSON phản hồi từ Crossref] | [Danh sách bản ghi bài báo đã chuẩn hóa] | [Hoàn thành] |
| [Lưu snapshot dữ liệu] | [`src/ingestion/crossref.py` · `load_raw_records()`] | [Đường dẫn file dữ liệu] | [`data/raw/crossref_records.json`] | [Hoàn thành] |

Chỉ nhận ownership cho phần bạn trực tiếp thực hiện. Liên hệ rõ phần việc của bạn với đầu vào, đầu ra và các thành viên phụ thuộc vào phần đó.

### Việc hỗ trợ ngoài phạm vi chính

| Hoạt động                         | Thành viên/module được hỗ trợ | Kết quả                    |
| ------------------------------------ | ------------------------------------ | ---------------------------- |
| [Debug] | [Trần Đình Duy/Clean data] | [Chạy được cho ra output: "Tín hiệu hoàn thành: Clean thành công 24 dòng"] |

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện | File/hàm/artifact liên quan | Kết quả bàn giao       | Cách xác minh         |
| --------------------------- | ----------------------------- | ------------------------- | ----------------------- |
| [Thu thập và xử lý 24 bài báo] | [src/ingestion/crossref.py (fetch_source_records, parse_crossref_payload)] | [data/raw/crossref_response.json] | [Lệnh] |
| [Lưu dữ liệu thô và theo dõi nguồn] | [src/ingestion/crossref.py (load_raw_records)] | [data/raw/crossref_records.json] | [Lệnh] |


Nêu một output cụ thể mà phần việc của bạn tạo ra hoặc giúp xác minh:

[File artifact `data/raw/crossref_records.json` chứa 24 cái metadata bài báo khoa học đã được chuẩn hóa từ Crossref API. Đây là Single Source of Truth cho toàn bộ hệ thống RAG, đảm bảo tính Data Lineage và làm căn cứ gốc để cơ chế Idempotent Repair tự động khôi phục 100% dữ liệu sạch khi pipeline gặp sự cố tiêm lỗi dữ liệu rác (Data Corruption).]

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết

[Thu thập data để bắt đầu tiến hành dự án, hỗ trợ cho bước data clean, Single Source of Truth cho toàn bộ hệ thống RAG, đảm bảo tính Data Lineage và làm căn cứ gốc để cơ chế Idempotent Repair tự động]

### Cách triển khai

[1. **Thu thập dữ liệu:** Hỗ trợ gọi Crossref API hoặc dùng snapshot offline khi lỗi mạng, Rate Limit (429) hoặc API lỗi (503).
2. **Chuẩn hóa metadata:** Làm sạch abstract, chuẩn hóa ngày, tên tác giả và chủ đề.
3. **Bảo toàn dữ liệu:** Dùng `PaperRecord` bất biến và lưu dữ liệu gốc cùng bản ghi chuẩn hóa trong `data/raw/`.]

### Input, output và contract

| Thành phần                   | Mô tả                                     |
| ------------------------------ | ------------------------------------------- |
| Input                          | [Cấu hình Crossref hoặc snapshot `data/raw/crossref_response.json`]           |
| Output                         | [Danh sách `PaperRecord` và hai file JSON: dữ liệu gốc, dữ liệu đã chuẩn hóa] |
| Module phụ thuộc             | [`core/config.py`, `core/utils.py`]                    |
| Module sử dụng output        | [Module cleaning và các pipeline Phase 1, Repair]                    |
| Điều kiện lỗi cần xử lý | [Mất mạng, lỗi API, metadata thiếu hoặc snapshot không tồn tại]                   |

### Cách xác minh

```bash
[python -c "from core.config import load_settings; from ingestion.crossref import fetch_source_records, load_raw_records; s=load_settings(); r1=fetch_source_records(s); r2=load_raw_records(s.paths.raw_records_json); print(f'Fetch thành công: {len(r1)} bài báo | Load snapshot: {len(r2)} bài báo')"]
```

- **Kết quả mong đợi:** [`Tín hiệu hoàn thành: Đã tải 24 bài báo` và sinh đủ 2 file artifact tại `data/raw/`]
- **Kết quả thực tế:** [`Tín hiệu hoàn thành: Đã tải 24 bài báo` Load snapshot: `24 bài báo`]
- **Artifact/log:** [`data/raw/crossref_response.json` và `data/raw/crossref_records.json`]

## 5. Một quyết định kỹ thuật quan trọng

- **Bối cảnh:** [Crossref API có thể chậm, mất kết nối hoặc giới hạn truy cập]
- **Các phương án đã cân nhắc:** [Chỉ dùng Live API hoặc kết hợp Live API với snapshot offline.]
- **Phương án đã chọn:** [Dùng snapshot mặc định; gọi API khi bật `REFRESH_SOURCE=true` và dự phòng snapshot nếu API lỗi]
- **Lý do:** [Pipeline chạy ổn định, dễ tái lập và giữ dữ liệu gốc cho Repair]
- **Bằng chứng quyết định phù hợp:** [Khi ngắt mạng, hệ thống vẫn tải đủ 24 bài từ snapshot trong 0,02 giây.]

## 6. Một lỗi hoặc blocker đã xử lý

- **Triệu chứng/lỗi nguyên văn:** [ModuleNotFoundError: No module named 'core'` hoặc `NotImplementedError` tại `load_raw_records()]
- **Lệnh hoặc bước tái hiện:** [Chạy lệnh kiểm thử `load_raw_records()` và `build_clean_dataframe()`]
- **Nguyên nhân gốc:** [Chưa cài project ở chế độ editable; hàm `load_raw_records()` chưa được triển khai đầy đủ]
- **Cách xử lý:** [Chạy `pip install -e .` và hoàn thiện hàm đọc JSON, tạo danh sách `PaperRecord`]
- **Cách xác minh sau khi sửa:** [Chạy lại lệnh kiểm thử; kết quả: `Clean thành công 24 dòng`]
- **Điều học được:** [Với dự án Python dùng cấu trúc `src/`, cài project bằng `pip install -e .` để import module nhất quán]

Nếu chưa xử lý xong:

- **Phạm vi bị ảnh hưởng:** [Module/artifact.]
- **Những gì đã loại trừ:** [Các giả thuyết đã kiểm tra.]
- **Bước tiếp theo:** [Hành động có thể kiểm chứng.]

## 7. Hiểu biết về luồng end-to-end

Giải thích ngắn gọn bằng lời của bạn:

1. Dữ liệu đi từ Crossref đến vector index như thế nào?
2. Evaluation set và ground-truth document IDs dùng để đo retrieval/answer quality ra sao?
3. Quality checks khác freshness monitoring ở điểm nào trong bài lab?
4. Vì sao phải dùng cùng test set cho baseline, corrupted và repaired?
5. Repair được xem là thành công dựa trên artifact và metric nào?

**Câu trả lời:**

[1. Dữ liệu được lấy từ Crossref hoặc snapshot, chuẩn hóa thành `PaperRecord`, làm sạch, chia thành các đoạn, tạo embedding rồi lưu vào vector index.
2. Evaluation set chứa câu hỏi và các document ID liên quan. Dùng chúng để so sánh kết quả truy xuất và đánh giá câu trả lời của mô hình.
3. Quality checks kiểm tra chất lượng dữ liệu/index tại một thời điểm; freshness monitoring theo dõi dữ liệu mới hoặc thay đổi theo thời gian.
4. Dùng cùng test set giúp so sánh công bằng giữa baseline, dữ liệu bị lỗi và dữ liệu đã sửa.
5. Repair thành công khi artifact sau sửa hợp lệ và metric retrieval/answer được cải thiện hoặc trở lại gần baseline.
]

## 8. Phân tích kết quả

### Metrics chính

| Metric/signal          | Baseline | Corrupted | Repaired | Nhận xét của cá nhân |
| ---------------------- | -------: | --------: | -------: | ------------------------- |
| `retrieval_hit_rate` |   `1.0000` |    `0.6000` |   `1.0000` | Sụt giảm 40% ở trạng thái Corrupted do 20% bản ghi mới nhất bị xóa và tiêu đề bị ngắn. Idempotent Repair khôi phục 100% khả năng truy vết Top-K. |
| `mean_token_f1`      |   `0.9377` |    `0.7271` |   `0.9377` | Mức độ trùng khớp từ vựng sụt giảm đáng kể khi summary bị xóa rỗng/chèn rác. Khôi phục hoàn toàn về 93.77% sau khi Repair. |
| `judge_accuracy`     |   `1.0000` |    `0.8000` |   `1.0000` | Thể hiện hiện tượng **Silent Failure**: Tỷ lệ trả lời chính xác của Agent sụt giảm 20% mặc dù mã nguồn không quăng bất kỳ exception nào. |
| `mean_judge_score`   |   `4.60` |    `3.80` |   `4.60` | Điểm đánh giá chất lượng ngữ nghĩa định lượng sụt giảm 0.8 điểm ở Corrupted và phục hồi lại mốc 4.6/5.0 ban đầu. |
| Quality checks         | `PASS (True)` | `FAIL (False)` | `PASS (True)` | Great Expectations 1.x lập tức báo động FAIL ở Corrupted do bắt được các vi phạm (Title length < 8 chars, Un-unique paper_id). |
| Freshness status       | `FRESH (True)` | `FRESH (True)` | `FRESH (True)` | Trạng thái Freshness SLA được giám sát liên tục để đảm bảo độ tươi của dữ liệu bài báo khoa học. |

### Kết luận từ số liệu

Hoàn thành hai chuỗi nguyên nhân–bằng chứng sau:

1. [Data corruption] → [Xóa bản ghi mới và làm hỏng metadata → Quality checks chuyển từ `PASS` sang `FAIL`, freshness vẫn `FRESH`] → [Hit rate giảm `1.0000` xuống `0.6000`, Token F1 giảm `0.9377` xuống `0.7271`, Judge accuracy giảm `1.0000` xuống `0.8000`].
2. [Repair action] → [Nạp lại dữ liệu sạch từ snapshot → Quality checks trở lại `PASS`, freshness vẫn `FRESH`] → [Các agent metric phục hồi về mức Baseline.].

Corruption nào ảnh hưởng rõ nhất và vì sao?

[Xóa 20% bản ghi mới làm mất tài liệu ground truth, khiến hit rate giảm 40%. Tiêu đề bị cắt cũng làm giảm thông tin dùng để tìm kiếm.]

Kết quả nào khác với kỳ vọng ban đầu?

[Agent vẫn chạy không lỗi dù chất lượng câu trả lời giảm (*Silent Failure*). Có thể Agent đã trả lời dựa trên tài liệu kém liên quan. Đã kiểm tra bằng cách đối chiếu kết quả chạy với báo cáo Great Expectations: script không báo lỗi, nhưng Quality checks chuyển sang `FAIL`.]

## 9. Điều học được và hướng cải thiện

### Ba điều quan trọng nhất

1. [Lưu dữ liệu gốc giúp pipeline có thể khôi phục về trạng thái sạch.]
2. [Quality Gate và Freshness SLA giúp phát hiện dữ liệu lỗi trước khi đưa vào Vector Store.]
3. [Dữ liệu bẩn làm giảm chất lượng RAG dù ứng dụng không báo lỗi: Hit Rate giảm 40%, Token F1 từ 0.9377 xuống 0.7271.]

### Nếu có thêm thời gian

[Tự động phát hiện lỗi, chạy Repair từ snapshot và gửi cảnh báo. Đánh giá bằng MTTR dưới 5 giây và Hit Rate phục hồi về 1.0000.]

## 10. Cam kết của thành viên

Đánh dấu sau khi tự kiểm tra:

- [X] Nội dung báo cáo phản ánh đúng phần việc và mức hiểu của tôi.
- [X] Tôi có thể giải thích luồng end-to-end, không chỉ module mình phụ trách.
- [X] Mọi kết luận về kết quả đều có artifact hoặc metric để đối chiếu.
- [X] Tôi không ghi “đã chạy thành công” cho phần chưa được kiểm chứng.
- [X] Báo cáo không chứa `.env`, API key, token hoặc secret.
- [X] Báo cáo này không phải bản sao nguyên văn của báo cáo nhóm hoặc báo cáo thành viên khác.

**Họ và tên:** [Nguyễn Thành Luân]
**Ngày xác nhận:** [2026-09-26]
