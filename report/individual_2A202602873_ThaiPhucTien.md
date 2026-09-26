# Member Role Report — Day 10: Data Pipeline & Data Observability

## 1. Thông tin cá nhân

| Thông tin         | Nội dung                  |
| ------------------ | -------------------------- |
| Họ và tên       | Thái Phúc Tiến             |
| MSSV               | 2A202602873                |
| Khóa/Lớp         | K4                        |
| Tên nhóm         | chuadatten     |
| Vai trò chính    | Corruption & Pipeline Integration Owner |
| Repository         | https://github.com/tom-e666/K4-L3B-DAY10-chuadatten-DataPipelineDataObservability |
| Ngày hoàn thành | 2026-09-26               |

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

| Module/deliverable | File/hàm phụ trách | Input nhận vào | Output bàn giao | Trạng thái |
| ------------------ | --------------------- | ---------------- | ----------------- | :---: |
| Baseline Orchestration Pipeline (Phase 1) | `src/pipelines/phase1.py` (`run_phase1_pipeline`, `main`) | Cấu hình `settings`, raw records từ API/Snapshot | `papers_clean.csv`, `baseline_metrics.json`, `phase1_report.md` | Hoàn thành |
| Data Corruption Suite (Pha 2) | `src/ingestion/corruption.py` (`corrupt_clean_dataframe`) | Cleaned pandas DataFrame (`df`), đường dẫn log | Dữ liệu bị tiêm lỗi `papers_clean_corrupted.csv`, `corruption_log.json` ghi nhận 6 dạng lỗi | Hoàn thành |
| Idempotent Repair & 3-State Comparison Flow | `src/pipelines/corruption_flow.py` (`repair_from_raw_snapshot`, `run_corruption_flow_pipeline`) | Dữ liệu sạch, snapshot thô `crossref_records.json`, cấu hình `settings` | Dữ liệu phục hồi `papers_clean_repaired.csv`, `corrupted_metrics.json`, `repaired_metrics.json`, `corruption_report.md` | Hoàn thành |

### Việc hỗ trợ ngoài phạm vi chính

| Hoạt động | Thành viên/module được hỗ trợ | Kết quả |
| ------------------------------------ | ------------------------------------ | ---------------------------- |
| Debug mã hóa ký tự UTF-8 trên Windows | Cả nhóm | Giải quyết lỗi `UnicodeEncodeError` (cp1252) bằng cấu hình môi trường `$env:PYTHONUTF8=1` |
| Hỗ trợ tích hợp đầu ra báo cáo Markdown | Observability Owner | Đồng bộ cấu trúc dữ liệu truyền vào hàm `generate_corruption_report` và in bảng đối chiếu 3 trạng thái trực quan ra console |

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện | File/hàm/artifact liên quan | Kết quả bàn giao | Cách xác minh |
| --------------------------- | ----------------------------- | ------------------------- | ----------------------- |
| Xây dựng và thực thi Baseline Pipeline End-to-End | `src/pipelines/phase1.py`, `script/run_phase1.py` | 24 bài báo sạch được index vào ChromaDB `papers-baseline`, bộ 10 câu hỏi testset, baseline Hit Rate 1.0000 & Token F1 1.0000 | `python script/run_phase1.py` |
| Xây dựng bộ công cụ tiêm lỗi thực nghiệm (6 kịch bản) | `src/ingestion/corruption.py` | Tạo thành công 21 dòng dữ liệu lỗi, ghi log chi tiết từng bản ghi bị tác động | `python -c "from ingestion.corruption import corrupt_clean_dataframe..."` |
| Xây dựng cơ chế Idempotent Repair & Luồng đối chiếu 3 trạng thái | `src/pipelines/corruption_flow.py`, `script/run_corruption_flow.py` | Khôi phục 100% dữ liệu sạch từ snapshot thô, đo lường sự sụt giảm và phục hồi hoàn toàn chỉ số RAG | `python script/run_corruption_flow.py` |

Nêu một output cụ thể mà phần việc của bạn tạo ra hoặc giúp xác minh:
- Báo cáo so sánh đối chiếu 3 trạng thái tại `data/reports/corruption_report.md` và file log chi tiết `data/results/corruption_log.json`, chứng minh thực nghiệm: khi dữ liệu bị lỗi, Hit Rate của RAG sụt giảm mạnh từ 1.0000 xuống 0.5000 (hiện tượng Silent Failure) và sau khi kích hoạt cơ chế Idempotent Repair từ raw snapshot, toàn bộ hệ thống phục hồi về mức 1.0000.

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết
1. ** Giải quyết phần module:** Xây một pipeline orchestration tự động xâu chuỗi từ Ingestion ➔ Cleaning ➔ Indexing ➔ Test generation ➔ Evaluation ➔ Quality Gate.
2. **Silent Failure:** Khi dữ liệu bị bẩn như mất bản ghi, cắt ngắn tiêu đề, xóa tóm tắt, chèn nhiễu, hệ thống AI không gặp crash runtime mà trả về kết quả sai lệch hoặc không tìm thấy thông tin.
3. **Cơ chế tự phục hồi:** Xây phương pháp phục hồi dữ liệu tin cậy, có tính Idempotent thay vì chắp vá dữ liệu lỗi.

### Cách triển khai
- **Pipeline Orchestration:** Điều phối luồng dữ liệu tuần tự, đảm bảo mỗi bước tạo artifact trung gian trước khi bước tiếp theo đọc vào.
- **Data Corruption Suite:** Tiêm 6 kịch bản lỗi:
  1. *Drop latest records: Cắt bỏ 20% bài báo mới nhất để gây thiếu hụt tri thức retrieval.
  2. *Blank summary: Xóa rỗng trường tóm tắt ở 2 dòng, tạo vi phạm độ dài tối thiểu của Great Expectations.
  3. Inject noise: Chèn chuỗi ký tự rác vào tóm tắt làm sai lệch vector embedding cosine similarity.
  4. Truncate title: Cắt ngắn tiêu đề < 8 ký tự, phá hỏng khả năng exact lookup và semantic search.
  5. Stale date: Lùi ngày xuất bản 365 ngày trên 8 dòng, kích hoạt vi phạm ngưỡng cảnh báo Freshness SLA.
  6. Duplicate rows: Nhân đôi bản ghi để tạo trùng lặp `paper_id`, kích hoạt kiểm định tính duy nhất của Great Expectations.
- **Idempotent Repair:** Tái tạo sạch dữ liệu trực tiếp từ `crossref_records.json`, xây dựng lại chỉ mục vector store mới, đảm bảo khôi phục nguyên vẹn 100% mà không bị ảnh hưởng bởi trạng thái lỗi trước đó.

### Input, output và contract

| Thành phần | Mô tả |
| :--- | :--- |
| **Input** | Dữ liệu sạch `papers_clean.json` (24 dòng), raw snapshot `crossref_records.json`, cấu hình `Settings` |
| **Output** | `papers_clean_corrupted.csv`, `papers_clean_repaired.csv`, `corruption_log.json`, `baseline_metrics.json`, `corrupted_metrics.json`, `repaired_metrics.json`, `corruption_report.md` |
| **Module phụ thuộc** | `ingestion.cleaning`, `retrieval.index`, `evaluation.metrics`, `observability.quality`, `observability.reporting` |
| **Module sử dụng output** | Toàn bộ nhóm sử dụng để làm báo cáo nhóm `group_report.md`|
| **Điều kiện lỗi cần xử lý** | Thiếu file baseline metrics, lỗi mã hóa font tiếng Việt trên terminal Windows, lỗi collection đã tồn tại trong ChromaDB |

### Cách xác minh

```bash
# 1. Chạy toàn tuyến Baseline Phase 1
python script/run_phase1.py

# 2. Chạy toàn tuyến Corruption, Repair & Comparison Flow Phase 2
python script/run_corruption_flow.py
```

- **Kết quả mong đợi:** Cả 2 flow kết thúc với Exit Code 0, in ra bảng số liệu 3 cột rõ ràng, các file JSON metrics và báo cáo Markdown được sinh đầy đủ.
- **Kết quả thực tế:**
  - Phase 1 hoàn tất index 24 docs, Hit Rate = 1.0000, Token F1 = 1.0000, Quality Gate PASSED.
  - Phase 2 đo lường rõ rệt suy giảm ở Corrupted (Hit Rate giảm còn 0.5000, Token F1 giảm còn 0.8506, GX FAILED, Freshness STALE) và phục hồi hoàn toàn ở Repaired (Hit Rate = 1.0000, Token F1 = 1.0000, GX PASSED, Freshness FRESH).
- **Artifact/log:** `data/reports/phase1_report.md`, `data/reports/corruption_report.md`, `data/results/corruption_log.json`.

## 5. Một quyết định kỹ thuật quan trọng

- **Bối cảnh:** Khi thiết kế hàm `repair_from_raw_snapshot`, có hai hướng tiếp cận để xử lý dữ liệu bị hỏng:
  - Phương án A: Viết hàm vá lỗi, tìm dòng rỗng thì điền chuỗi mặc định, tìm dòng trùng thì drop duplicates, tìm ngày lỗi thì gán ngày hiện tại.
  - Phương án B: Áp dụng nguyên lý Idempotent Repair từ nguồn Single Source of Truth (SSOT) – đọc lại snapshot thô ban đầu `crossref_records.json', chạy lại toàn bộ quy trình `build_clean_dataframe()` chuẩn và nạp mới lại vector database.
- **Phương án đã chọn:** Phương án B.
- **Lý do:** Phương án A tiềm ẩn nguy cơ tích tụ lỗi cascading (ví dụ tóm tắt bị gán chuỗi mặc định sẽ làm embedding bị sai lệch ngữ nghĩa). Phương án B bảo đảm tính Idempotent tuyệt đối: dù chạy bao nhiêu lần, dữ liệu và vector index đều quay về trạng thái chuẩn hóa ban đầu, loại bỏ hoàn toàn dấu vết của dữ liệu bẩn.
- **Bằng chứng quyết định phù hợp:** Chỉ số `repaired_metrics.json` đạt Hit Rate 1.0000, Token F1 1.0000 và 100% kiểm định GX thành công, khôi phục tương đương 100% so với baseline ban đầu.

## 6. Một lỗi hoặc blocker đã xử lý

- **Triệu chứng/lỗi nguyên văn:**
  ```text
  UnicodeEncodeError: 'charmap' codec can't encode characters in position 6-7: character maps to <undefined>
  ```
- **Lệnh hoặc bước tái hiện:** Chạy script Python trên PowerShell Windows (`python script/run_phase1.py`) khi in ra chuỗi console chứa ký tự tiếng Việt có dấu.
- **Nguyên nhân gốc:** Môi trường Windows PowerShell mặc định sử dụng bảng mã `cp1252` thay vì `utf-8` cho stdout/stderr. Khi module in các thông báo tiếng Việt có dấu (ví dụ: `Môi trường sẵn sàng`), hàm `charmap_encode` bị lỗi do không biểu diễn được ký tự Unicode tiếng Việt.
- **Cách xử lý:**
  1. Cấu hình biến môi trường hệ thống trước khi thực thi: `$env:PYTHONUTF8="1"`.
  2. Bổ sung encoding `utf-8` rõ ràng trong tất cả các thao tác đọc/ghi file (`write_text`, `write_json`, `open(..., encoding="utf-8")`).
- **Cách xác minh sau khi sửa:** Chạy `$env:PYTHONUTF8="1"; python script/run_phase1.py` và `python script/run_corruption_flow.py` trên terminal, script chạy, không gặp lỗi encoding.
- **Điều học được:** Luôn chủ động xử lý encoding cross-platform ngay từ đầu khi xây dựng Data Pipeline trên hệ điều hành Windows.

## 7. Hiểu biết về luồng end-to-end

1. **Dữ liệu đi từ Crossref đến vector index:** API Crossref trả về JSON thô ➔ Lưu vào `crossref_response.json` & `crossref_records.json` ➔ Qua hàm cleaning để chuẩn hóa text, khử trùng lặp theo `paper_id`, tính `age_days` ➔ Ghép thành chuỗi chuẩn `text_for_embedding` ➔ Dùng `sentence-transformers/all-MiniLM-L6-v2` chuyển văn bản thành vector 384 chiều ➔ Lưu vào ChromaDB Collection với khoảng cách Cosine.
2. **Evaluation set và ground-truth document IDs:** Bộ test set gồm 10 câu hỏi chia đều 4 nhóm nghiệp vụ (`summary`, `authors`, `date`, `categories`). Khi kiểm thử, câu hỏi được nạp vào RAG, hệ thống truy vấn Top-K tài liệu gần nhất từ vector store. Nếu danh sách `retrieved_doc_ids` chứa `ground_truth_doc_ids`, ghi nhận `retrieval_hit = True` (đo lường Retrieval Hit Rate). Sau đó câu trả lời của AI được so sánh với `ground_truth` để tính Token F1 và LLM Judge.
3. **Quality checks khác Freshness monitoring:** Quality checks (Great Expectations) kiểm tra tính toàn vẹn và hợp lệ về mặt cấu trúc (schema, null, uniqueness, min length). Freshness monitoring kiểm tra chiều kích thời gian (tính thời sự) của dữ liệu dựa trên `age_days` và ngưỡng SLA 180 ngày. Một bản ghi có thể hoàn hảo về mặt cấu trúc (đầy đủ các trường) nhưng vẫn vi phạm Freshness nếu nó quá cũ.
4. **Vì sao phải dùng cùng test set cho cả 3 trạng thái:** Để đảm bảo tính khách quan và khoa học (Controlled Experiment). Khi giữ nguyên tập câu hỏi kiểm tra, mọi biến thiên về Hit Rate hay Token F1 giữa Baseline, Corrupted và Repaired đều chỉ phản ánh đúng chất lượng của dữ liệu và vector store, loại bỏ hoàn toàn nhiễu từ sự thay đổi câu hỏi.
5. **Tiêu chí đánh giá Repair thành công:** Dựa trên 2 khía cạnh: (1) *Data Observability:* Quality Gate chuyển từ FAILED ➔ PASSED (100% expectations thành công) và Freshness SLA chuyển từ STALE ➔ FRESH; (2) *AI Performance:* Retrieval Hit Rate hồi phục từ 0.5000 lên 1.0000 và Mean Token F1 hồi phục từ 0.8506 lên 1.0000.

## 8. Phân tích kết quả

### Metrics chính

| Metric/signal          | Baseline | Corrupted | Repaired | Nhận xét của cá nhân |
| ---------------------- | -------: | --------: | -------: | ------------------------- |
| `retrieval_hit_rate` |   1.0000 |    0.5000 |   1.0000 | Giảm mạnh 50% khi mất dữ liệu & nhiễu; phục hồi trọn vẹn sau repair |
| `mean_token_f1`      |   1.0000 |    0.8506 |   1.0000 | Suy giảm do tiêu đề bị cắt và tóm tắt bị nhiễu; lấy lại điểm tuyệt đối |
| `judge_accuracy`     |   1.0000 |    0.9000 |   1.0000 | Câu trả lời bị sai lệch nội dung ở trạng thái corrupted |
| `mean_judge_score`   |     5.00 |      4.20 |     5.00 | Điểm đánh giá chất lượng câu trả lời giảm 0.8 điểm |
| Quality checks         |   PASSED |    FAILED |   PASSED | Bị chặn bởi GX do vi phạm Uniqueness và Độ dài tóm tắt |
| Freshness status       |    FRESH |     STALE |    FRESH | Vi phạm ngưỡng 25% bài báo có tuổi > 180 ngày |

### Kết luận từ số liệu

Hoàn thành hai chuỗi nguyên nhân–bằng chứng sau:
1. *Data corruption (Drop 20% bài mới, truncate title, blank summary)* ➔ *Quality checks FAILED, Freshness STALE* ➔ *Retrieval Hit Rate giảm từ 1.0000 xuống 0.5000, Token F1 giảm còn 0.8506 (Silent Failure).*
2. *Idempotent Repair từ raw snapshot gốc* ➔ *Quality checks PASSED (6/6 checks), Freshness phục hồi FRESH (stale ratio 4.17%)* ➔ *Retrieval Hit Rate và Token F1 lấy lại 100% phong độ (1.0000).*

- **Corruption ảnh hưởng rõ nhất:** Kịch bản **Drop latest records** và **Truncate title**. Vì các câu hỏi test tập trung vào các bài báo quan trọng, việc mất bản ghi khiến vector store hoàn toàn không tìm thấy tài liệu liên quan, kéo tụt Hit Rate ngay lập tức 50%.
- **Kết quả khác kỳ vọng ban đầu:** Ban đầu dự đoán Judge Accuracy sẽ giảm sâu hơn 0.9000, nhưng do một số câu hỏi có thể fallback về nội dung tương đồng nên mô hình vẫn đạt 0.9000 dù Hit Rate chỉ còn 0.5000, chứng minh rõ hiện tượng AI "ảo giác" hoặc trả lời dựa trên tri thức sẵn có thay vì tài liệu retrieved nếu không có Data Observability kiểm soát.

## 9. Điều học được và hướng cải thiện

### Ba điều quan trọng nhất
1. **Tầm quan trọng của Data Contract:** Không có kiểm định tự động, dữ liệu bẩn sẽ đi xuyên suốt toàn bộ pipeline mà không báo lỗi runtime, gây ra lỗi nghiêm trọng ở tầng ứng dụng AI.
2. **Nguyên lý Idempotency:** Trong kỹ nghệ dữ liệu, một pipeline tự phục hồi đáng tin cậy phải được thiết kế mang tính Idempotent từ nguồn Raw bất biến.
3. **Data Observability song hành AI Observability:** Cần phải giám sát đồng thời cả hai lớp: lớp chất lượng dữ liệu và lớp hiệu năng mô hình.

### Nếu có thêm thời gian
- Xây dựng cơ chế **Automated Circuit Breaker**: Tự động chặn việc đánh chỉ mục vector (ngắt pipeline ngay lập tức) nếu Data Quality Gate phát hiện `success = False` hoặc Freshness SLA bị vi phạm, thay vì cho phép dữ liệu bẩn tiếp tục đi vào ChromaDB phục vụ người dùng. Đo lường hiệu quả qua việc giảm thiểu số lượng truy vấn AI bị ảnh hưởng khi có sự cố dữ liệu.

## 10. Cam kết của thành viên

Đánh dấu sau khi tự kiểm tra:

- [x] Nội dung báo cáo phản ánh đúng phần việc và mức hiểu của tôi.
- [x] Tôi có thể giải thích luồng end-to-end, không chỉ module mình phụ trách.
- [x] Mọi kết luận về kết quả đều có artifact hoặc metric để đối chiếu.
- [x] Tôi không ghi “đã chạy thành công” cho phần chưa được kiểm chứng.
- [x] Báo cáo không chứa `.env`, API key, token hoặc secret.
- [x] Báo cáo này không phải bản sao nguyên văn của báo cáo nhóm hoặc báo cáo thành viên khác.

**Họ và tên:** Thái Phúc Tiến  
**Ngày xác nhận:** 2026-09-26
