# Member Role Report — Day 10: Data Pipeline & Data Observability

> Mỗi thành viên trong nhóm tự hoàn thành mẫu này để báo cáo đúng vai trò, phần việc và mức hiểu của mình. Không sao chép nguyên báo cáo chung hoặc báo cáo của thành viên khác. Thay nội dung trong dấu `[ ]` và xóa các dòng hướng dẫn không cần thiết trước khi nộp.

## 1. Thông tin cá nhân

| Thông tin         | Nội dung                  |
| ------------------ | -------------------------- |
| Họ và tên       | Nguyễn Đức Long             |
| MSSV               | 2A202602917                |
| Khóa/Lớp         | 3b                        |
| Tên nhóm         | chuadatten     |
| Vai trò chính    | Thực hiện giám sát chuất lượng dữ liệu          |
| Repository         | https://github.com/tom-e666/K4-L3B-DAY10-chuadatten-DataPipelineDataObservability |
| Ngày hoàn thành | 2026-09-26                  |

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

| Module/deliverable | File/hàm phụ trách | Input nhận vào | Output bàn giao  | Trạng thái |
| ------------------ | --------------------- | ---------------- | ----------------- | -------------------------------------------- |
| Observability Gate (GX 1.x)| `src/observability/quality.py` (`run_data_quality_checks`, `build_freshness_report`) | Cleaned pandas DataFrame (`df` từ `cleaning.py` gồm `paper_id`, `title`, `summary`, `text_for_embedding`, `age_days`) | `baseline_quality_report.json`, `corrupted_quality_report.json`, `freshness_report.json` | Hoàn thành |
| Markdown Observability Reporting | `src/observability/reporting.py` (`generate_phase1_report`, `generate_corruption_report`) | Source summary, Evaluation metrics dicts (baseline, corrupted, repaired), Quality & Freshness results | `data/reports/phase1_report.md`, `data/reports/corruption_report.md` (Báo cáo đối chiếu 3 trạng thái) | Hoàn thành |

Chỉ nhận ownership cho phần bạn trực tiếp thực hiện. Liên hệ rõ phần việc của bạn với đầu vào, đầu ra và các thành viên phụ thuộc vào phần đó.

### Việc hỗ trợ ngoài phạm vi chính

| Hoạt động | Thành viên/module được hỗ trợ | Kết quả |
| ------------------------------------ | ------------------------------------ | ---------------------------- |



## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện | File/hàm/artifact liên quan | Kết quả bàn giao       | Cách xác minh         |
| --------------------------- | ----------------------------- | ------------------------- | ----------------------- |
| Xây dựng Data Quality Gate (GX 1.x) & Freshness SLA | `src/observability/quality.py`, `data/quality/baseline_quality_report.json`, `data/quality/freshness_report.json` | Bộ 4 Expectations chuẩn GX 1.x Ephemeral Context & cơ chế cảnh báo Freshness SLA (`age_days > 180`) | Lệnh inline check status trả về `Quality check status = True` và file `baseline_quality_report.json` xuất hiện |
| Tự động xuất Báo cáo Observability Markdown | `src/observability/reporting.py`, `data/reports/phase1_report.md`, `data/reports/corruption_report.md` | Các hàm `generate_phase1_report` & `generate_corruption_report` tổng hợp số liệu và sinh file báo cáo Markdown | File `phase1_report.md` và bảng đối chiếu 3 trạng thái trong `corruption_report.md` được tạo thành công |

Nêu một output cụ thể mà phần việc của bạn tạo ra hoặc giúp xác minh:

Báo cáo kiểm định chất lượng `data/quality/baseline_quality_report.json` xác nhận 100% (6/6) tiêu chí chất lượng dữ liệu đạt trạng thái PASSED trên tập 24 bài báo sạch. Đồng thời, báo cáo `data/reports/corruption_report.md` tạo ra bảng đối chiếu 3 trạng thái (Baseline vs Corrupted vs Repaired), minh chứng rõ rệt hiện tượng Silent Failure khi RAG bị tiêm dữ liệu bẩn và sự khôi phục hoàn toàn chỉ số hiệu năng sau khi Idempotent Repair.

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết

Trong các hệ thống RAG Agent thực tế, dữ liệu bẩn hoặc rác (thiếu summary, trùng lặp DOI, tiêu đề bị rác, hoặc bài báo quá cũ) khi đi vào pipeline sẽ không làm bị crash, nhưng sẽ gây ra hiện tượng Silent Failure — làm suy giảm nghiêm trọng độ chính xác của tìm kiếm và làm cho LLM sinh câu trả lời sai lệch.

Phần việc Observability & Reporting của tôi giải quyết 3 vấn đề cốt lõi:
1. Thiết lập Quality Gate tự động: Chặn đứng dữ liệu bẩn/lỗi ngay tại chốt kiểm dịch trước khi nạp vào Vector Database.
2. Giám sát độ tươi mới (Freshness SLA): Cảnh báo sớm khi tỷ lệ dữ liệu quá hạn vượt ngưỡng an toàn, tránh phục vụ thông tin lỗi thời.
3. Tự động hóa đối chiếu & báo cáo: Xuất các báo cáo Markdown chuẩn hóa với bảng đối chiếu định lượng 3 trạng thái (Baseline vs Corrupted vs Repaired), giúp nhóm và giám khảo đánh giá chính xác tác động của dữ liệu tới hiệu năng RAG.

### Cách triển khai

1. **Kiểm tra chất lượng dữ liệu (Great Expectations 1.x)**
   - Đảm bảo tổng số bài báo nằm trong khoảng từ 5 đến 5.000 bài.
   - Đảm bảo các trường bắt buộc (paper_id, title, text_for_embedding) không được trống.
   - Đảm bảo mỗi bài báo có một paper_id duy nhất, không bị trùng.
   - Đảm bảo đoạn tóm tắt (summary) có độ dài tối thiểu 30 ký tự, tránh trường hợp bị cắt xén hỏng.
   - Lưu kết quả: Xuất báo cáo đạt/không đạt dưới dạng file JSON vào thư mục data/quality/.

2. **Kiểm tra độ tươi mới dữ liệu (Freshness SLA):**
    Đánh giá xem dữ liệu có bị "lỗi thời" hay không dựa trên số ngày tuổi (age_days):
   - Đếm số lượng bài báo có `age_days > 180` (quá 6 tháng) và tính tỷ lệ dữ liệu cũ (`stale_ratio = stale_rows / total_rows`).
   - Nếu `stale_ratio <= 0.25` (tỷ lệ cũ <= 25%), hệ thống ghi nhận `is_fresh = True`. Nếu vượt ngưỡng 25%, gắn cờ cảnh báo `is_fresh = False`.

3. **Tự động hóa xuất Báo cáo Markdown (Reporting Engine):**
   - Xây dựng hàm `generate_phase1_report` tổng hợp số liệu dữ liệu đầu vào, các metric retrieval/eval và kết quả quality/freshness thành file `data/reports/phase1_report.md`.
   - Xây dựng hàm `generate_corruption_report` lập bảng so sánh định lượng 3 trạng thái (Baseline vs Corrupted vs Repaired), tự động tính toán chênh lệch delta (`+`/`-`) cho từng metric để làm nổi bật tác động của dữ liệu bẩn và mức độ khôi phục của pipeline.

### Input, output và contract

| Thành phần                   | Mô tả                                     |
| ------------------------------ | ------------------------------------------- |
| Input                          | Cleaned `pandas.DataFrame` và các dict đo lường chỉ số RAG |
| Output                         | Các dict kết quả chất lượng/độ tươi mới và các file artifact JSON (`data/quality/*.json`) cùng 2 file báo cáo Markdown (`data/reports/phase1_report.md`, `data/reports/corruption_report.md`) |
| Module phụ thuộc             | `src/ingestion/cleaning.py` (cung cấp cleaned DataFrame), `src/evaluation/metrics.py` (cung cấp chỉ số RAG), `src/core/config.py` & `src/core/utils.py` (cung cấp đường dẫn paths và helper IO) |
| Module sử dụng output        | `src/pipelines/phase1.py` và `src/pipelines/corruption_flow.py` (sử dụng tín hiệu `success` & `is_fresh` để quyết định luồng)|
| Điều kiện lỗi cần xử lý | DataFrame rỗng hoặc thiếu cột `age_days`/`paper_id`: Tự động ghi nhận `is_fresh = False` hoặc `success = False` an toàn; Thư mục đầu ra chưa tồn tại: Tự động khởi tạo đường dẫn cha trước khi ghi file |

### Cách xác minh

```bash
# Chạy câu lệnh kiểm tra chính thức Data Quality Gate trên tập dữ liệu sạch:
python -c "from core.config import load_settings; from observability.quality import run_data_quality_checks; import pandas as pd; s=load_settings(); df=pd.read_json(s.paths.clean_json); res=run_data_quality_checks(df, s, 'test'); print('Tín hiệu hoàn thành: Quality check status =', res['success'])"
```

- **Kết quả mong đợi:**
  - Lệnh inline check status trả về `Tín hiệu hoàn thành: Quality check status = True` (100% tiêu chuẩn đạt PASSED).
  - Tự động xuất tệp kết quả kiểm định chất lượng dữ liệu dưới dạng JSON artifact.
- **Kết quả thực tế:**
  - Console in đúng chuỗi: `Tín hiệu hoàn thành: Quality check status = True`.
  - Tệp kết quả `baseline_quality_report.json` và `freshness_report.json` được khởi tạo thành công tại `data/quality/`.
- **Artifact/log:**
  - `data/quality/baseline_quality_report.json`
  - `data/quality/freshness_report.json`
  - `data/reports/phase1_report.md`
  - `data/reports/corruption_report.md`

## 5. Một quyết định kỹ thuật quan trọng

- **Bối cảnh:** Thiết lập quy tắc kiểm tra và ngưỡng phát tín hiệu cảnh báo dữ liệu lỗi thời (Freshness SLA) trong module Data Observability (`src/observability/quality.py`).
- **Các phương án đã cân nhắc:**
  1. Phương án 1 (Per-item Hard Failure): Phát tín hiệu cảnh báo `is_fresh = False` ngay lập tức nếu hệ thống phát hiện dù chỉ 1 bài báo duy nhất có độ tuổi `age_days > 180` ngày.
  2. Phương án 2 (Stale Ratio Threshold <= 25%): Tính toán tỷ lệ phần trăm các bài báo bị cũ trên tổng số bài (`stale_ratio = stale_rows / total_rows`). Chỉ khi tỷ lệ dữ liệu cũ này vượt quá ngưỡng an toàn **25%** (`0.25`), hệ thống mới gắn cờ cảnh báo `is_fresh = False`.
- **Phương án đã chọn:** Phương án 2 — Kiểm soát độ tươi mới theo Tỷ lệ diện rộng (Stale Ratio Threshold <= 25%).
- **Lý do:** 
  - Tránh báo động giả (Avoid False Positives): Bộ dữ liệu Crossref chứa các bài báo nghiên cứu khoa học có phân bố độ tuổi tự nhiên, việc tồn tại một vài bài báo kinh điển có giá trị nhưng xuất bản lâu năm là hoàn toàn bình thường. Nếu áp dụng Phương án 1 sẽ liên tục gây ra báo động giả (False Positive) làm gián đoạn luồng dữ liệu sạch.
  - Bắt chính xác sự cố dữ liệu bẩn (Data Quality Sensitivity): Phương án 2 phản ánh đúng "sức khỏe" tổng thể của dữ liệu (Data Health). Hệ thống chỉ thực sự phát cảnh báo khi xuất hiện sự cố tiêm lỗi dữ liệu bẩn làm lùi ngày xuất bản diện rộng ở CP4.
- **Bằng chứng quyết định phù hợp:** 
  - Tại trạng thái Baseline dữ liệu sạch: `stale_ratio = 0.00%` <= 25% ➔ `is_fresh = True` (Giữ pipeline hoạt động mượt mà, không báo động giả).
  - Tại trạng thái Corrupted khi bị tiêm lỗi lùi ngày xuất bản: `stale_ratio` vọt lên cao vượt 25% ➔ `is_fresh = False` (Phát hiện chính xác và kịp thời sự cố dữ liệu bẩn).

## 6. Một lỗi hoặc blocker đã xử lý

- **Triệu chứng/lỗi nguyên văn:** `ModuleNotFoundError: No module named 'core'` xuất hiện khi thực thi câu lệnh kiểm tra chất lượng dữ liệu.
- **Lệnh hoặc bước tái hiện:** 
  Chạy lệnh inline check trực tiếp từ terminal:
  `python -c "from core.config import load_settings; from observability.quality import run_data_quality_checks; import pandas as pd; s=load_settings(); df=pd.read_json(s.paths.clean_json); res=run_data_quality_checks(df, s, 'test'); print('Quality check status =', res['success'])"`
- **Nguyên nhân gốc:** Chưa kích hoạt môi trường ảo (`.venv`), khiến Python sử dụng môi trường hệ thống mặc định chưa được cài đặt dependencies và chưa đăng ký module dự án.
- **Cách xử lý:** Kích hoạt môi trường ảo `.venv` (`.venv\Scripts\activate` trên Windows) trước khi chạy lệnh.
- **Cách xác minh sau khi sửa:** 
  Chạy lại lệnh inline check sau khi đã vào môi trường ảo `.venv`:
  `python -c "from core.config import load_settings; from observability.quality import run_data_quality_checks; import pandas as pd; s=load_settings(); df=pd.read_json(s.paths.clean_json); res=run_data_quality_checks(df, s, 'test'); print('Tín hiệu hoàn thành: Quality check status =', res['success'])"`
  Output in ra đúng kết quả: `Tín hiệu hoàn thành: Quality check status = True`.
- **Điều học được:** Luôn đảm bảo kích hoạt virtual environment (`.venv`) trước khi thực thi bất kỳ câu lệnh hay script Python nào trong dự án.

## 7. Hiểu biết về luồng end-to-end

Giải thích ngắn gọn bằng lời của bạn:

1. Dữ liệu đi từ Crossref đến vector index như thế nào?
2. Evaluation set và ground-truth document IDs dùng để đo retrieval/answer quality ra sao?
3. Quality checks khác freshness monitoring ở điểm nào trong bài lab?
4. Vì sao phải dùng cùng test set cho baseline, corrupted và repaired?
5. Repair được xem là thành công dựa trên artifact và metric nào?

**Câu trả lời:**

1. Dữ liệu từ Crossref API được tải về dạng JSON. Pipeline làm sạch dữ liệu (lọc thẻ HTML, chuẩn hóa khoảng trắng, xóa trùng ID, tính tuổi bài báo). Văn bản sau xử lý được đưa qua mô hình all-MiniLM-L6-v2 để tạo vector embedding và lưu vào ChromaDB.

2. Evaluation set chứa 10 câu hỏi test kèm mã tài liệu đúng (ground-truth IDs) và đáp án mẫu. Retrieval Hit Rate kiểm tra xem kết quả ChromaDB trả về có chứa ground-truth ID hay không. Chất lượng câu trả lời được đo qua so sánh từ vựng (Token F1) và điểm đánh giá từ LLM Judge.

3. Quality checks kiểm tra tính toàn vẹn cấu trúc dữ liệu (số dòng, trùng ID, null, độ dài summary). Freshness monitoring kiểm tra độ mới của dữ liệu theo thời gian (tỷ lệ bài báo cũ quá 180 ngày không vượt ngưỡng 25%).

4. Dùng chung một test set giúp đảm bảo tính đối chứng. Mọi sự thay đổi về chỉ số giữa 3 trạng thái Baseline, Corrupted và Repaired sẽ phản ánh đúng ảnh hưởng từ chất lượng dữ liệu, tránh bị nhiễu do độ khó khác nhau giữa các câu hỏi.

5. Repair thành công khi tạo lại được dữ liệu sạch (papers_clean_repaired.json), kiểm tra chất lượng đạt success = True, độ mới is_fresh = True, đồng thời các chỉ số của RAG agent (Retrieval Hit Rate, Token F1, LLM Judge) được phục hồi trở lại mức tương đương với Baseline.

## 8. Phân tích kết quả

### Metrics chính

| Metric/signal          | Baseline | Corrupted | Repaired | Nhận xét của cá nhân |
| ---------------------- | -------: | --------: | -------: | ------------------------- |
| `retrieval_hit_rate` |     1.00 |      0.50 |     1.00 | Giảm mạnh 50% khi dữ liệu hỏng, phục hồi hoàn toàn 100% sau repair |
| `mean_token_f1`      |     1.00 |      0.85 |     1.00 | Giảm xuống 0.85 do mất ngữ cảnh, phục hồi lại 1.00 sau khi sửa |
| `judge_accuracy`     |     1.00 |      0.90 |     1.00 | Giảm xuống 0.90 do thiếu thông tin chính xác, đạt lại 1.00 |
| `mean_judge_score`   |     5.00 |      4.20 |     5.00 | Giảm từ 5.0 xuống 4.2 khi dữ liệu nhiễu, quay lại mức tối đa 5.0 |
| Quality checks         |   PASSED |    FAILED |   PASSED | Phát hiện lỗi vi phạm schema/integrity khi corrupted và khôi phục khi repaired |
| Freshness status       |    FRESH |     STALE |    FRESH | Cảnh báo STALE khi dữ liệu cũ/lỗi tuổi, trở lại FRESH sau repair |

### Kết luận từ số liệu

1. Hai chuỗi nguyên nhân - bằng chứng:
- Chuỗi suy giảm: Dữ liệu bị làm hỏng (chèn lỗi HTML, xáo trộn summary, sai năm) khiến Quality checks thất bại (FAILED) và Freshness bị cảnh báo cũ (STALE). Điều này làm cho Retrieval Hit Rate giảm từ 1.00 xuống 0.50, Token F1 giảm từ 1.00 xuống 0.85 và điểm LLM Judge giảm từ 5.0 xuống 4.2.
- Chuỗi phục hồi: Thực hiện repair (chạy lại pipeline làm sạch từ nguồn thô) giúp Quality khôi phục PASSED và Freshness khôi phục FRESH. Nhờ đó, tất cả chỉ số của RAG agent khôi phục 100% về mức Baseline ban đầu.

2. Corruption ảnh hưởng rõ nhất và lý do:
Hành vi làm mờ văn bản tóm tắt (summary) và xóa từ khóa nội dung gây ảnh hưởng nặng nhất. Nguyên nhân do vector embedding phụ thuộc trực tiếp vào ngữ nghĩa của summary. Khi summary bị mất hoặc nhiễu, ChromaDB không thể tìm đúng tài liệu chứa ground-truth (Retrieval Hit Rate giảm 50%), khiến LLM thiếu ngữ cảnh đúng để trả lời.

3. Kết quả khác với kỳ vọng ban đầu:
Dù Retrieval Hit Rate bị giảm sâu xuống 0.50, chỉ số Judge Accuracy vẫn đạt mốc 0.90 (thay vì giảm quá thấp). Giả thuyết là LLM vẫn tận dụng được ngữ cảnh từ các tài liệu đúng còn lại hoặc tự suy luận cho các câu hỏi đơn giản. Đã kiểm tra lại log chi tiết và xác nhận các câu hỏi bị trừ điểm rơi đúng vào những câu có tài liệu ground-truth bị tìm thiếu.

## 9. Điều học được và hướng cải thiện

### Ba điều quan trọng nhất

1. Về data pipeline: Thiết kế pipeline theo nguyên tắc Idempotency (khả năng chạy lại nhiều lần cho cùng một kết quả) và duy trì dữ liệu thô (raw snapshot) là chìa khóa để hỗ trợ cơ chế Self-healing (tự phục hồi) khi xảy ra sự cố dữ liệu.
2. Về data quality và observability: Cần kết hợp cả kiểm tra cấu trúc (Quality checks với Great Expectations) và kiểm tra độ mới theo mốc thời gian (Freshness SLA monitoring). Việc phát hiện sớm dữ liệu xấu ngay trên pipeline giúp chặn rủi ro trước khi dữ liệu được nạp vào Vector DB.
3. Về ảnh hưởng của data tới RAG agent: Chất lượng câu trả lời của RAG agent phụ thuộc hoàn toàn vào chất lượng dữ liệu đầu vào. Dữ liệu bị nhiễu hoặc mất ngữ cảnh làm sụt giảm trực tiếp hiệu năng truy xuất (Retrieval Hit Rate) và độ chính xác của LLM.

### Nếu có thêm thời gian

Tự động hóa luồng cảnh báo và tự động Trigger Repair Pipeline ngay khi phát hiện kiểm tra chất lượng bị FAILED hoặc Freshness bị STALE (chuyển từ cảnh báo thủ công sang tự động khôi phục dữ liệu). Cách đo cải thiện: Đo thời gian phục hồi hệ thống (MTTR - Mean Time To Recovery) giảm từ vài phút thao tác tay xuống dưới 10 giây xử lý tự động.

## 10. Cam kết của thành viên

Đánh dấu sau khi tự kiểm tra:

- [x] Nội dung báo cáo phản ánh đúng phần việc và mức hiểu của tôi.
- [x] Tôi có thể giải thích luồng end-to-end, không chỉ module mình phụ trách.
- [x] Mọi kết luận về kết quả đều có artifact hoặc metric để đối chiếu.
- [x] Tôi không ghi “đã chạy thành công” cho phần chưa được kiểm chứng.
- [x] Báo cáo không chứa `.env`, API key, token hoặc secret.
- [x] Báo cáo này không phải bản sao nguyên văn của báo cáo nhóm hoặc báo cáo thành viên khác.

**Họ và tên:** Nguyễn Đức Long
**Ngày xác nhận:** 2026-09-26
