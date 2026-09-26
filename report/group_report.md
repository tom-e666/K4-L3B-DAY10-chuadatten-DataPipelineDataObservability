# Group Report — Day 10: Data Pipeline & Data Observability

## 1. Thông tin bài nộp

| Thông tin         | Nội dung                  |
| ------------------ | -------------------------- |
| Khóa/Lớp         | K4                        |
| Tên nhóm         | chuadatten                |
| Repository         | https://github.com/tom-e666/K4-L3B-DAY10-chuadatten-DataPipelineDataObservability |
| Ngày hoàn thành | 2026-09-26               |

### Thành viên và phân công

| STT | Họ và tên | MSSV | Vai trò chính | Module/deliverable sở hữu | Báo cáo cá nhân |
| --: | --- | --- | --- | --- | --- |
| 1 | Nguyễn Thành Luân | 2A202602769 | Source & Ingestion Owner | `src/ingestion/crossref.py`, tải 24 records thô, lưu `data/raw/crossref_response.json` & `crossref_records.json` | [individual_2A202602769_report_NguyenThanhLuan.md](individual_2A202602769_report_NguyenThanhLuan.md) |
| 2 | Trần Đình Duy | 2A202602631 | Data Cleaning Owner | `src/ingestion/cleaning.py`, làm sạch text, tính `age_days`, tạo `text_for_embedding`, xuất `data/clean/papers_clean.csv` | [individual_2A202602631_TranDinhDuy.md](individual_2A202602631_TranDinhDuy.md) |
| 3 | Nguyễn Đức Long | 2A202602917 | Observability & Reporting Owner | `src/observability/quality.py`, `src/observability/reporting.py`, Great Expectations 1.x, Freshness SLA, `phase1_report.md`, `corruption_report.md` | [individual_2A202502917_NguyenDucLong.md](individual_2A202502917_NguyenDucLong.md) |
| 4 | Thái Phúc Tiến | 2A202602873 | Corruption & Pipeline Integration Owner | `src/pipelines/phase1.py`, `src/ingestion/corruption.py`, `src/pipelines/corruption_flow.py`, ChromaDB indexing, 3-state evaluation & Idempotent Repair | [individual_2A202602873_ThaiPhucTien.md](individual_2A202602873_ThaiPhucTien.md) |

## 2. Tóm tắt kết quả

Nhóm đã xây dựng hoàn chỉnh và kiểm thử thành công hệ thống Data Pipeline tích hợp Data Observability cho ứng dụng RAG Agent:
1. **Pha Baseline:** Ingest thành công 24 bài báo học thuật từ Crossref API, làm sạch dữ liệu, tạo vector store ChromaDB với `all-MiniLM-L6-v2`, tự động sinh 10 câu hỏi benchmark và đánh giá Baseline RAG đạt hiệu năng hoàn hảo: **Retrieval Hit Rate = 1.0000**, **Mean Token F1 = 1.0000**, vượt qua 6/6 bài kiểm tra của Great Expectations 1.x và đạt chuẩn Freshness SLA (chỉ 4.17% bài cũ quá 180 ngày).
2. **Pha Data Corruption (Silent Failure):** Giả lập 6 lỗi dữ liệu thực tế (bỏ rơi 20% bài mới, xóa tóm tắt, chèn chuỗi rác, cắt ngắn tiêu đề < 8 ký tự, lùi ngày xuất bản 365 ngày, nhân bản dòng). Kết quả chứng minh hiện tượng **Silent Failure**: AI không crash code nhưng **Hit Rate sụt giảm nghiêm trọng 50%** (từ 1.0000 xuống 0.5000), Token F1 giảm còn 0.8506, đồng thời kích hoạt cảnh báo Quality Gate FAILED và Freshness STALE.
3. **Pha Idempotent Self-Healing:** Kích hoạt cơ chế tự phục hồi an toàn từ snapshot thô ban đầu `crossref_records.json`, tái tạo hoàn toàn dữ liệu sạch và vector store mới, giúp toàn bộ chỉ số RAG **khôi phục 100% phong độ** (Hit Rate trở lại 1.0000, Token F1 đạt 1.0000, Quality Gate PASSED).

## 3. Kiến trúc và luồng dữ liệu

### Luồng end-to-end

```text
[Crossref REST API]
       │
       ▼
[Raw Response & Snapshot] ─── (data/raw/crossref_records.json - SSOT)
       │
       ▼
[Data Cleaning & Feature Eng] ─── (Lọc HTML, tính age_days, text_for_embedding)
       │
       ▼
[ChromaDB Vector Store] ─── (Collection: papers-baseline, all-MiniLM-L6-v2)
       │
       ▼
[Benchmark Evaluation & GX Gate] ─── (Hit Rate: 1.0, Token F1: 1.0, GX 6/6 PASSED, Freshness FRESH)
       │
       ▼
[Data Corruption Suite] ─── (Tiêm 6 lỗi, 21 dòng bẩn, corruption_log.json)
       │
       ▼
[Degraded Evaluation (Silent Failure)] ─── (Hit Rate sụt còn 0.5000, GX FAILED, Freshness STALE)
       │
       ▼
[Idempotent Repair từ Raw Snapshot] ─── (Khôi phục từ SSOT gốc, nạp lại papers-repaired)
       │
       ▼
[Phục Hồi 100% & Báo Cáo Đối Chiếu] ─── (Hit Rate: 1.0000, Token F1: 1.0000, corruption_report.md)
```

### Trách nhiệm của từng khối

| Khối | Input | Xử lý chính | Output/artifact | Owner |
| :--- | :--- | :--- | :--- | :--- |
| **Ingestion** | Crossref REST API / Snapshot | Fetch HTTP, retry/fallback, parse payload JSON | `data/raw/crossref_response.json`, `crossref_records.json` | Nguyễn Thành Luân |
| **Cleaning** | Raw `PaperRecord` objects | Xóa tag HTML, chuẩn hóa ngày, tính `age_days`, tạo `text_for_embedding` | `data/clean/papers_clean.csv`, `papers_clean.json` | Trần Đình Duy |
| **Embedding & Index** | `text_for_embedding` | Mã hóa vector 384 chiều (`all-MiniLM-L6-v2`), index cosine similarity | `data/chroma/`, `data/embeddings/papers_embeddings.json` | Thái Phúc Tiến |
| **Evaluation** | Clean DataFrame | Sinh 10 câu hỏi test (4 nhóm), đo Hit Rate, Token F1, LLM Judge | `data/eval/test_set.json`, `data/results/baseline_metrics.json` | Thái Phúc Tiến |
| **Observability** | Clean & Corrupted DF | 6 Expectations GX 1.x ephemeral, tính tỷ lệ Stale quá 180 ngày | `data/quality/*.json`, `data/reports/phase1_report.md` | Nguyễn Đức Long |
| **Corruption & Repair**| Clean DF & Raw SSOT | Tiêm 6 lỗi dữ liệu; Idempotent repair từ snapshot thô gốc | `corruption_log.json`, `papers_clean_corrupted.csv`, `repaired.csv` | Thái Phúc Tiến |
| **Orchestration** | Toàn bộ pipeline | Điều phối chạy end-to-end 2 flow, in ma trận 3 trạng thái | `script/run_phase1.py`, `script/run_corruption_flow.py` | Thái Phúc Tiến |

## 4. Cách tái hiện kết quả

### Cấu hình không chứa secret

| Biến/cấu hình | Giá trị sử dụng |
| :--- | :--- |
| `LLM_PROVIDER` | `gemini` |
| `LLM_MODEL` | `gemini-2.5-flash` |
| Embedding model | `sentence-transformers/all-MiniLM-L6-v2` |
| Số lượng Crossref records | 24 |
| Retrieval `top_k` | 4 |
| Freshness threshold | 180 ngày (ngưỡng vi phạm > 25%) |
| Vector similarity metric | Cosine Distance |

### Lệnh cài đặt

```bash
# Cài đặt qua uv (khuyến nghị)
uv sync

# Hoặc qua pip truyền thống
pip install -e .
```

### Lệnh chạy toàn tuyến

1. **Chạy Baseline Pipeline (Pha 1):**
```bash
$env:PYTHONUTF8="1"; python script/run_phase1.py
```

2. **Chạy Corruption, Repair & Comparison Flow (Pha 2):**
```bash
$env:PYTHONUTF8="1"; python script/run_corruption_flow.py
```

### Lệnh kiểm thử từng module theo vai trò cá nhân

| Module | Phụ trách | Lệnh kiểm thử nhanh (One-liner) | Tín hiệu hoàn thành kỳ vọng |
| :--- | :--- | :--- | :--- |
| **Ingestion** | Nguyễn Thành Luân | `python -c "from core.config import load_settings; from ingestion.crossref import fetch_source_records, load_raw_records; s=load_settings(); r1=fetch_source_records(s); r2=load_raw_records(s.paths.raw_records_json); print(f'Fetch: {len(r1)} | Snapshot: {len(r2)}')"` | In ra `Fetch: 24 | Snapshot: 24` |
| **Cleaning** | Trần Đình Duy | `python -c "from core.config import load_settings; from ingestion.cleaning import build_clean_dataframe; from ingestion.crossref import load_raw_records; s=load_settings(); df=build_clean_dataframe(load_raw_records(s.paths.raw_records_json), s.run_date); print(f'Clean: {len(df)} dòng')"` | In ra `Clean: 24 dòng` |
| **Observability** | Nguyễn Đức Long | `python -c "from core.config import load_settings; from observability.quality import run_data_quality_checks; import pandas as pd; s=load_settings(); df=pd.read_json(s.paths.clean_json); res=run_data_quality_checks(df, s, 'test'); print('Quality check status =', res['success'])"` | In ra `Quality check status = True` |
| **Corruption & Repair** | Thái Phúc Tiến | `$env:PYTHONUTF8="1"; python script/run_corruption_flow.py` | Bảng so sánh 3 trạng thái in ra console, Exit code 0 |

### Kết quả tái hiện

| Lệnh | Trạng thái | Thời điểm chạy gần nhất | Bằng chứng |
| :--- | :--- | :--- | :--- |
| **Baseline pipeline** | Thành công (Exit 0) | 2026-09-26 | `papers_clean.csv` (24 dòng), `baseline_metrics.json` (Hit Rate = 1.0, Token F1 = 1.0), `phase1_report.md` |
| **Corruption flow** | Thành công (Exit 0) | 2026-09-26 | `corruption_log.json` (6 lỗi), `corrupted_metrics.json` (Hit Rate = 0.5), `repaired_metrics.json` (Hit Rate = 1.0), `corruption_report.md` |

## 5. Ingestion, cleaning và data contract

### Nguồn dữ liệu

| Thuộc tính | Giá trị |
| :--- | :--- |
| Source | Crossref REST API (`https://api.crossref.org/works`) |
| Query/filter | `query=agentic retrieval augmented generation large language model&filter=has-abstract:true,from-pub-date:2026-03-30&rows=24` |
| Thời điểm lấy dữ liệu | 2026-09-26 |
| Số record nhận được | 24 records |
| Cơ chế retry/backoff | Fallback tự động đọc snapshot local `crossref_response.json` khi API lỗi hoặc dính 429 Too Many Requests |

### Raw và clean schema

| Trường | Kiểu dữ liệu | Bắt buộc? | Ý nghĩa | Xử lý khi thiếu/sai |
| :--- | :--- | :---: | :--- | :--- |
| `paper_id` | String | Có | DOI định danh duy nhất của bài báo | Bỏ bản ghi nếu rỗng; khử trùng lặp giữ bản ghi đầu tiên |
| `title` | String | Có | Tiêu đề bài báo | Bỏ bản ghi nếu rỗng; chuẩn hóa khoảng trắng |
| `summary` | String | Có | Tóm tắt (Abstract) bài báo | Xóa tag HTML/JATS; nếu rỗng gắn chuỗi rỗng |
| `authors` / `authors_joined` | List[str] / String | Không | Danh sách tác giả | Chuẩn hóa `Given Family`, nối bằng dấu phẩy |
| `categories_joined` | String | Không | Chủ đề / Lĩnh vực nghiên cứu | Nếu thiếu gán giá trị mặc định `"General"` |
| `published` | String (YYYY-MM-DD) | Có | Ngày xuất bản chính thức | Parse `date-parts`; nếu thiếu fallback về ngày run_date |
| `age_days` | Integer | Có | Số ngày tuổi tính đến ngày chạy pipeline | `(run_date - published).days`, dùng cho Freshness SLA |
| `text_for_embedding` | String | Có | Chuỗi text tổng hợp để nạp vector store | Ghép 5 phần: Title, Authors, Published, Categories, Summary |

### Quy tắc cleaning

| Quy tắc | Quality dimension | Số record bị tác động | Cách xác minh |
| :--- | :--- | :---: | :--- |
| Khử trùng lặp theo `paper_id` | Uniqueness | 0 (tập thô không trùng) | Kiểm định `ExpectColumnValuesToBeUnique` |
| Loại bỏ thẻ HTML/JATS trong summary | Validity | 24 | Regex `re.sub(r"<[^>]+>", "", summary)` |
| Chuẩn hóa ngày về `YYYY-MM-DD` | Conformance | 24 | Parse `date-parts` an toàn |
| Tính toán `age_days` | Timeliness | 24 | Cột `age_days` trong DataFrame |
| Tạo `text_for_embedding` không chứa null | Completeness | 24 | Kiểm định `ExpectColumnValuesToNotBeNull` |

**Cơ chế tạo `text_for_embedding`, document ID và `age_days`:**
- `age_days`: Được tính bằng `(run_date.date() - pub_date).days`.
- `document ID`: Tạo dưới dạng `{paper_id}::{index}` để đảm bảo tính duy nhất và khả năng truy vết ngược lại dòng trong bảng dữ liệu sạch.
- `text_for_embedding`: Ghép 5 trường thông tin có cấu trúc:
  ```text
  Title: {title}
  Authors: {authors_joined}
  Published: {published}
  Categories: {categories_joined}
  Summary: {summary}
  ```

## 6. Evaluation setup

| Thành phần | Cấu hình thực tế |
| :--- | :--- |
| Số câu hỏi | 10 câu |
| Các `question_type` | 3 `summary`, 3 `authors`, 2 `date`, 2 `categories` |
| Ground-truth document ID | Trích xuất trực tiếp `paper_id` từ dòng được lấy mẫu trong `papers_clean.csv` |
| Embedding model | `sentence-transformers/all-MiniLM-L6-v2` (384 dimensions) |
| Vector store/collection | ChromaDB (`papers-baseline`, `papers-corrupted`, `papers-repaired`) |
| Retrieval `top_k` | 4 |
| LLM provider/model | Gemini (`gemini-2.5-flash`), temperature = 0.0 |
| Test set dùng chung cho 3 trạng thái | `data/eval/test_set.json` (10 câu hỏi cố định) |

**Giải thích vì sao test set được giữ nguyên cho cả 3 trạng thái:**
Việc giữ nguyên bộ câu hỏi đánh giá là nguyên tắc khoa học cốt lõi (Controlled Experiment). Khi câu hỏi và đáp án chuẩn không thay đổi, mọi biến thiên về **Hit Rate**, **Token F1** hay **Judge Accuracy** giữa Baseline, Corrupted và Repaired đều phản ánh đúng 100% chất lượng của dữ liệu và vector index, loại bỏ hoàn toàn các yếu tố nhiễu do câu hỏi thay đổi.

## 7. Kết quả baseline

### Artifact checklist

| Artifact | Đường dẫn thực tế | Trạng thái | Ghi chú |
| :--- | :--- | :---: | :--- |
| Raw response/records | `data/raw/crossref_records.json` | Có | 24 bản ghi thô, 18.4 KB |
| Cleaned dataset | `data/clean/papers_clean.csv` | Có | 24 dòng sạch đầy đủ cột |
| Embedding manifest/index | `data/embeddings/papers_embeddings.json` | Có | Collection `papers-baseline` |
| Evaluation set | `data/eval/test_set.json` | Có | 10 câu hỏi benchmark chuẩn |
| Baseline metrics | `data/results/baseline_metrics.json` | Có | Hit Rate 1.0000, F1 1.0000 |
| Quality/freshness | `data/quality/baseline_quality_report.json` | Có | 6/6 checks PASSED, Freshness FRESH |
| Baseline report | `data/reports/phase1_report.md` | Có | Markdown report tổng hợp |

### Baseline metrics

| Metric | Giá trị | Diễn giải |
| :--- | :---: | :--- |
| `retrieval_hit_rate` | **1.0000** | 10/10 câu hỏi truy vấn trúng tài liệu gốc trong Top-4 |
| `mean_token_f1` | **1.0000** | Trùng khớp từ vựng hoàn hảo với ground-truth |
| `judge_accuracy` | **1.0000** | 100% câu trả lời được LLM Judge đánh giá đúng ngữ nghĩa |
| `mean_judge_score` | **5.00 / 5.0** | Điểm chất lượng tối đa |
| Ragas, nếu có | Skipped | Bỏ qua để tối ưu tốc độ thực thi lab (`RUN_RAGAS=0`) |

## 8. Data quality và freshness

### Quality checks (Great Expectations 1.x)

| Check | Quality dimension | Ngưỡng/kỳ vọng | Kết quả baseline | Bằng chứng |
| :--- | :--- | :--- | :--- | :--- |
| `ExpectTableRowCountToBeBetween` | Completeness | 5 đến 5,000 dòng | PASSED (24 dòng) | `baseline_quality_report.json` |
| `ExpectColumnValuesToNotBeNull` (`paper_id`) | Completeness | Không được null | PASSED (0 null) | `baseline_quality_report.json` |
| `ExpectColumnValuesToNotBeNull` (`title`) | Completeness | Không được null | PASSED (0 null) | `baseline_quality_report.json` |
| `ExpectColumnValuesToNotBeNull` (`text_for_embedding`) | Completeness | Không được null | PASSED (0 null) | `baseline_quality_report.json` |
| `ExpectColumnValuesToBeUnique` (`paper_id`) | Uniqueness | Duy nhất 100% | PASSED (0 trùng lặp) | `baseline_quality_report.json` |
| `ExpectColumnValueLengthsToBeBetween` (`summary`) | Validity | Tối thiểu 30 ký tự | PASSED (min 193 ký tự) | `baseline_quality_report.json` |

### Freshness SLA

| Thuộc tính | Giá trị |
| :--- | :--- |
| Freshness được đo tại | `data/quality/freshness_report.json` trên tập `papers_clean.csv` |
| Timestamp mới nhất / Cũ nhất | `2026-07-22` / `2026-03-28` |
| Ngưỡng freshness SLA | Tỷ lệ bài báo có `age_days > 180` ngày phải &le; 25% |
| Trạng thái baseline | **FRESH** |
| Lý do | Chỉ có 1 / 24 bài cũ quá 180 ngày (tỷ lệ **4.17%** &le; 25%), kho dữ liệu đạt độ tươi mới cao |

## 9. Corruption scenarios và repair

| Corruption | Cách tạo | Record bị tác động | Quality signal kỳ vọng | Tác động thực tế | Cách repair |
| :--- | :--- | :---: | :--- | :--- | :--- |
| **Drop latest records** | Cắt bỏ 20% bài mới nhất | 5 bài | Mất tri thức mới | Hit Rate sụt giảm nghiêm trọng | Phục hồi toàn bộ từ raw snapshot |
| **Blank summary** | Xóa rỗng summary | 2 bài | Vi phạm GX min length | AI trả lời rỗng (`token_f1 = 0`) | Đọc lại abstract gốc từ snapshot |
| **Inject noise** | Chèn chuỗi rác `### NOISE ###` | 2 bài | Sai lệch vector embedding | Giảm độ tương đồng ngữ nghĩa | Lấy lại summary sạch từ raw |
| **Truncate title** | Cắt ngắn tiêu đề < 8 ký tự | 2 bài | Phá vỡ exact lookup | Không tìm thấy bài qua title | Khôi phục title gốc từ raw |
| **Stale date** | Lùi ngày xuất bản 365 ngày | 8 bài | Vi phạm Freshness SLA | Tỷ lệ cũ vọt lên 38.10% (STALE) | Khôi phục ngày xuất bản chuẩn |
| **Duplicate rows** | Nhân bản dòng tạo trùng `paper_id` | 2 bài | Vi phạm GX Uniqueness | Tăng kích thước bẩn, GX FAILED | Khử trùng lặp qua quy tắc cleaning |

**Corruption log:**
- Đường dẫn: `data/results/corruption_log.json`
- Trạng thái: Có đầy đủ
- Nhận xét: Ghi nhận chi tiết 6 kịch bản, số lượng bản ghi bị tác động, danh sách `paper_id`, `title` trước và sau khi tiêm lỗi.

**Giải thích cơ chế Idempotent Repair từ nguồn tin cậy:**
Nhóm không áp dụng giải pháp "vá chắp vá" (in-place patching) trên tập dữ liệu bẩn vì việc điền giá trị mặc định cho summary hay sửa ngày giả lập sẽ để lại tác dụng phụ và gây trôi dạt ngữ nghĩa (semantic drift) trong vector store. Thay vào đó, nhóm áp dụng **nguyên lý Idempotency**: đọc lại snapshot thô bất biến `crossref_records.json` (Single Source of Truth), chạy lại toàn bộ hàm `build_clean_dataframe()` chuẩn hóa, và tái tạo hoàn toàn collection `papers-repaired`. Cơ chế này đảm bảo dù pipeline có bị lỗi bao nhiêu lần, kết quả sau repair luôn là một trạng thái sạch duy nhất và hoàn hảo 100%.

## 10. So sánh baseline, corrupted và repaired

| Metric / Signal | Baseline | Corrupted | Repaired | Thay đổi do corruption | Mức phục hồi (Recovery) | Nhận xét |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| `retrieval_hit_rate` | **1.0000** | **0.5000** | **1.0000** | **-0.5000 (-50%)** | **+0.5000 (+100%)** | Mất 5 bài mới kéo tụt 50% khả năng tìm kiếm; phục hồi nguyên vẹn sau repair |
| `mean_token_f1` | **1.0000** | **0.8506** | **1.0000** | **-0.1494** | **+0.1494** | Giảm do tóm tắt rỗng và tiêu đề bị cắt; lấy lại điểm tuyệt đối |
| `judge_accuracy` | **1.0000** | **0.9000** | **1.0000** | **-0.1000** | **+0.1000** | Câu trả lời bị sai lệch nội dung ở trạng thái bẩn |
| `mean_judge_score` | **5.00** | **4.20** | **5.00** | **-0.80** | **+0.80** | Điểm đánh giá chất lượng câu trả lời giảm rõ rệt |
| Quality checks (GX) | **PASSED** | **FAILED** | **PASSED** | Bị chặn | Khôi phục | Vi phạm Uniqueness & độ dài tóm tắt; phục hồi 6/6 checks |
| Freshness status | **FRESH** | **STALE** | **FRESH** | Vi phạm SLA | Khôi phục | Tỷ lệ bài cũ tăng từ 4.17% lên 38.10%; phục hồi về 4.17% |

**Hai kết luận có quan hệ nhân quả được hỗ trợ bởi artifacts:**
1. *Dữ liệu bị drop 20% bài mới & cắt ngắn title* ➔ *Great Expectations báo FAILED và Freshness SLA báo STALE* ➔ *Retrieval Hit Rate sụt giảm nghiêm trọng từ 1.0000 xuống 0.5000, Token F1 giảm còn 0.8506 (Minh chứng hiện tượng Silent Failure).*
2. *Hành động Idempotent Repair từ raw snapshot thô bất biến* ➔ *Quality Gate phục hồi PASSED và Freshness phục hồi FRESH* ➔ *Retrieval Hit Rate và Token F1 hồi sinh 100% phong độ (1.0000).*

## 11. Vấn đề tích hợp quan trọng

Hệ thống ghi nhận và đã xử lý dứt điểm 4 vấn đề kỹ thuật phát sinh trong quá trình tích hợp giữa các thành viên:

### 1. Mã hóa ký tự UTF-8 trên môi trường Windows PowerShell (Thái Phúc Tiến)
- **Triệu chứng:** Khi chạy script trên PowerShell Windows (`python script/run_phase1.py`), script bị dừng đột ngột do lỗi `UnicodeEncodeError`:
  ```text
  UnicodeEncodeError: 'charmap' codec can't encode characters in position 6-7: character maps to <undefined>
  ```
- **Nguyên nhân:** Windows PowerShell mặc định sử dụng codepage `cp1252` thay vì `utf-8`. Khi pipeline in các log tiến trình chứa tiếng Việt có dấu ra terminal, bộ giải mã console bị lỗi.
- **Cách xử lý:** 
  1. Cấu hình biến môi trường trước khi thực thi lệnh: `$env:PYTHONUTF8="1"`.
  2. Khai báo tường minh encoding `utf-8` trong toàn bộ các thao tác I/O đọc và ghi file (`open(..., encoding="utf-8")`, `to_json(..., force_ascii=False)`).
- **Cách xác minh:** Chạy lại toàn tuyến `$env:PYTHONUTF8="1"; python script/run_phase1.py` và `script/run_corruption_flow.py`, toàn bộ pipeline chạy mượt mà đến Exit Code 0, in đầy đủ bảng so sánh ra console.

### 2. Module Resolution & Rate Limit khi Ingestion Crossref (Nguyễn Thành Luân)
- **Triệu chứng:** Xuất hiện lỗi `ModuleNotFoundError: No module named 'core'` hoặc `ingestion` khi chạy kiểm thử độc lập hàm ingestion từ dòng lệnh; đồng thời gặp nguy cơ dính mã lỗi HTTP `429 Too Many Requests` khi gọi API Crossref liên tục trong cùng một IP.
- **Nguyên nhân:** Thư mục `src/` chưa được đưa vào `PYTHONPATH` của môi trường ảo; Crossref API áp dụng chính sách giới hạn lưu lượng nghiêm ngặt đối với client chưa cấu hình header Polite Pool.
- **Cách xử lý:**
  1. Chạy `pip install -e .` để cài đặt project ở chế độ editable package.
  2. Thiết kế cơ chế fallback hai lớp: ưu tiên nạp từ local snapshot `data/raw/crossref_response.json` khi `REFRESH_SOURCE=false` hoặc khi API trả về mã lỗi 429/503.
- **Cách xác minh:** Khi ngắt toàn bộ kết nối Internet, hệ thống vẫn load thành công 24 bản ghi chuẩn hóa `PaperRecord` trong 0.02 giây từ local snapshot thô.

### 3. Thiếu trường Subject/Category trong Raw Schema & Nguy cơ Duplicate Index (Trần Đình Duy)
- **Triệu chứng:** Trường `subject` từ raw JSON của Crossref thường xuyên bị rỗng (`[]`), dẫn đến cột `categories_joined` bị null, làm hỏng câu hỏi kiểm thử loại `category` và phá vỡ cấu trúc chuỗi 5 phần của `text_for_embedding`. Ngoài ra, nếu có DOI trùng lặp trong dữ liệu thô, vector store sẽ bị phân mảnh.
- **Nguyên nhân:** Dữ liệu thô từ nhiều nhà xuất bản học thuật không khai báo trường phân loại môn học.
- **Cách xử lý:**
  1. Bổ sung giá trị mặc định `"General"` khi `categories` rỗng, đảm bảo `text_for_embedding` không bao giờ bị null.
  2. Thiết lập quy tắc deduplication nghiêm ngặt theo `paper_id`: tự động giữ lại bản ghi đầu tiên và loại bỏ toàn bộ bản ghi trùng lặp.
- **Cách xác minh:** 100% (24/24) dòng dữ liệu sạch đều có chuỗi `text_for_embedding` hợp lệ, vượt qua bài kiểm tra `ExpectColumnValuesToNotBeNull` và `ExpectColumnValuesToBeUnique`.

### 4. Tương thích Great Expectations 1.x & Mô hình Ephemeral Data Context (Nguyễn Đức Long)
- **Triệu chứng:** Cú pháp cũ của Great Expectations 0.18 (`ge.from_pandas()`) đã bị loại bỏ hoàn toàn trong phiên bản GX 1.x, gây lỗi `AttributeError` khi tích hợp vào pipeline CI/CD.
- **Nguyên nhân:** GX 1.x tái thiết kế toàn bộ kiến trúc sang mô hình Data Context phân cấp (`DataContext` ➔ `BatchDefinition` ➔ `ExpectationSuite` ➔ `ValidationDefinition`).
- **Cách xử lý:** Khởi tạo Ephemeral Context in-memory thông qua `gx.get_context(mode="ephemeral")`, đăng ký DataFrame Pandas qua InMemory Data Source và định nghĩa 6 Expectation definitions độc lập không phụ thuộc file cấu hình tĩnh.
- **Cách xác minh:** Chạy lệnh kiểm thử inline, hàm trả về kết quả tức thì với `Quality check status = True` và xuất file `baseline_quality_report.json` đầy đủ kết quả kiểm tra 6 tiêu chí.

## 12. Giới hạn và hướng cải thiện

| Giới hạn hiện tại | Ảnh hưởng | Hướng cải thiện có thể kiểm chứng |
| :--- | :--- | :--- |
| **Chưa có Automated Circuit Breaker** | Dữ liệu lỗi vẫn đi vào vector database nếu người điều hành không chủ động dừng pipeline | Tích hợp ngắt mạch tự động: nếu GX báo `success=False`, tự động rollback và abort quá trình nạp vector store |
| **Quy mô tập dữ liệu còn nhỏ (24 records)** | Chưa kiểm thử được tải lớn và độ trễ khi kho tri thức có hàng triệu bài báo | Mở rộng ingestion đa luồng (Asyncio/Ray), phân mảnh partition vector theo năm xuất bản |
| **Khắc phục stale date phụ thuộc snapshot cũ** | Bài báo cũ chỉ được hồi phục về ngày lưu snapshot chứ chưa cập nhật phiên bản mới nhất trên mạng | Tích hợp cron job định kỳ quét Crossref API để tự động re-fetch bài báo có bản cập nhật mới |

## 13. Checklist trước khi nộp

- [x] Thông tin nhóm và repository chính xác (`https://github.com/tom-e666/K4-L3B-DAY10-chuadatten-DataPipelineDataObservability`).
- [x] Phân công khớp với module, artifact và kết quả thực tế của 4 thành viên.
- [x] Lệnh tái hiện đã được chạy lại trên phiên bản dùng để nộp (`$env:PYTHONUTF8="1"; python script/run_phase1.py` & `script/run_corruption_flow.py`).
- [x] Baseline, corrupted và repaired dùng cùng evaluation set (`data/eval/test_set.json`).
- [x] Bảng metrics khớp với các file trong `data/results/` (`baseline_metrics.json`, `corrupted_metrics.json`, `repaired_metrics.json`).
- [x] Quality/freshness conclusions khớp với `data/quality/` (6/6 checks PASSED ở baseline, FAILED ở corrupted, PASSED ở repaired).
- [x] Các đường dẫn báo cáo và artifact truy cập được.
- [x] Mỗi thành viên đã hoàn thành báo cáo vai trò riêng:
  - [Nguyễn Thành Luân (MSSV: 2A202602769)](individual_2A202602769_report_NguyenThanhLuan.md)
  - [Trần Đình Duy (MSSV: 2A202602631)](individual_2A202602631_TranDinhDuy.md)
  - [Nguyễn Đức Long (MSSV: 2A202602917)](individual_2A202502917_NguyenDucLong.md)
  - [Thái Phúc Tiến (MSSV: 2A202602873)](individual_2A202602873_ThaiPhucTien.md)
- [x] Không có `.env`, API key, token hoặc secret trong source, report, log hay ảnh.
- [x] Binary tạm của vector database (`data/chroma/chroma.sqlite3`, `*.bin`) đã được loại khỏi Git tracking qua `.gitignore`.
