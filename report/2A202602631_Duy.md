# Báo cáo cá nhân — Day 10: Data Pipeline & Data Observability

## 1. Thông tin cá nhân

| Thông tin | Nội dung |
| --- | --- |
| Họ và tên | Trần Đình Duy |
| MSSV | 2A202602631 |
| Khóa/Lớp | 3B |
| Tên nhóm | chuadattten |
| Vai trò | Data cleaner |
| Repository | https://github.com/tom-e666/K4-L3B-DAY10-chuadatten-DataPipelineDataObservability |
| Ngày chạy baseline | 2026-09-26 |

## 2. Phần việc phụ trách

Tôi phụ trách làm sạch dữ liệu trong src/ingestion/cleaning.py, hàm build_clean_dataframe.

| Input | Xử lý | Output |
| --- | --- | --- |
| Danh sách PaperRecord từ Crossref và run_date | Làm sạch text, chuẩn hóa ngày, tính age_days, bỏ bản ghi lỗi/trùng | DataFrame sạch dùng cho embedding, evaluation và quality check |

Các cột quan trọng tôi bàn giao là paper_id, title, summary, authors_joined, categories_joined, published, age_days và text_for_embedding.

## 3. Phần đã thực hiện

- Xóa khoảng trắng thừa trong title, summary, author và category.
- Loại tag HTML/JATS còn sót trong summary.
- Chuẩn hóa published/updated về YYYY-MM-DD. Khi ngày không hợp lệ, hàm dùng ngày fallback để pipeline không bị dừng.
- Tính age_days bằng chênh lệch giữa run_date và published.
- Bỏ dòng không có paper_id hoặc title; giữ dòng đầu tiên khi paper_id bị lặp.
- Tạo text_for_embedding theo 5 phần: Title, Authors, Published, Categories, Summary.
- Với raw snapshot hiện tại không có subject/category, bổ sung giá trị General để text embedding và câu hỏi category không bị rỗng.

Ví dụ format text:

    Title: <title>
    Authors: <authors>
    Published: <published>
    Categories: <categories>
    Summary: <summary>

## 4. Kết quả sau khi chạy baseline

Tôi chạy lại bằng lệnh dưới đây:

    uv run python script/run_phase1.py

| Hạng mục | Kết quả |
| --- | --- |
| Raw records từ Crossref snapshot | 24 |
| Clean records | 24 |
| ID raw có mặt trong clean data | 24/24 |
| paper_id trùng/rỗng sau cleaning | 0/0 |
| Title rỗng | 0 |
| text_for_embedding rỗng | 0 |
| Documents trong Chroma collection papers-baseline | 24 |
| Câu hỏi evaluation | 10 |
| Loại câu hỏi | 3 summary, 3 authors, 2 date, 2 categories |
| Quality gate | 6/6 checks pass |
| Freshness | Fresh; 0/24 bài quá 180 ngày |
| Khoảng ngày xuất bản | 2026-04-01 đến 2026-09-15 |

Artifact đã sinh sau khi chạy:

- data/clean/papers_clean.csv và data/clean/papers_clean.json
- data/embeddings/papers_embeddings.json và data/chroma/
- data/eval/test_set.json
- data/results/baseline_metrics.json và baseline_answers.json
- data/quality/baseline_quality_report.json và freshness_report.json
- data/reports/phase1_report.md

## 5. Metrics baseline

| Metric | Giá trị |
| --- | ---: |
| retrieval_hit_rate | 1.0000 |
| mean_token_f1 | 0.7754 |
| judge_accuracy | 0.8000 |
| mean_judge_score | 4.30 |
| Ragas | Chưa chạy; biến RUN_RAGAS chưa bật |

Kết quả retrieval đạt 10/10 vì mỗi câu hỏi có title của bài báo và retriever tìm đúng document. Token F1 chưa đạt 1.0 chủ yếu ở 3 câu summary: hàm QA hiện chỉ trả câu đầu của summary, trong khi ground truth lưu toàn bộ summary. Hai câu summary có judge đánh giá chưa đúng, nên judge accuracy là 0.8. Đây là giới hạn của cách trả lời hiện tại, không phải lỗi của cleaning hay index.

## 6. Kiểm tra quality và freshness

Quality gate trong data/quality/baseline_quality_report.json đạt 6/6:

1. Số dòng nằm trong khoảng 5–5000.
2. paper_id không null.
3. paper_id duy nhất.
4. title không null.
5. text_for_embedding không null.
6. summary có ít nhất 30 ký tự.

Freshness threshold là 180 ngày. Baseline có stale_rows=0, stale_ratio=0.0 và is_fresh=true. Cột age_days do cleaning tạo là đầu vào trực tiếp cho phép kiểm tra này.

## 7. Quyết định kỹ thuật

- **Vấn đề:** Nếu cùng một paper_id xuất hiện nhiều lần, vector store có thể index lặp và kết quả evaluation khó tin cậy.
- **Lựa chọn:** Lọc paper_id/title rỗng, sau đó deduplicate theo paper_id và giữ bản ghi đầu tiên.
- **Lý do:** paper_id được dùng làm document ID ở index và ground truth của evaluation. Làm sạch sớm giúp các bước sau dùng cùng một identity.
- **Kiểm tra:** Baseline mới có 24 ID duy nhất, Chroma cũng có đúng 24 documents.

## 8. Hiểu biết về luồng end-to-end

Crossref được parse thành PaperRecord, rồi cleaning tạo DataFrame và text_for_embedding. Embedding model all-MiniLM-L6-v2 biến text thành vector và lưu trong ChromaDB. Test set lưu câu hỏi, đáp án và ground-truth paper_id. Evaluation so document ID retrieved với ground truth để tính hit rate, sau đó so câu trả lời với đáp án để tính Token F1 và judge score.

Quality check kiểm tra schema và độ đầy đủ của data. Freshness check dùng age_days để đo số bài quá hạn. Khi chạy corruption và repair, cần giữ nguyên test set để sự khác biệt metric phản ánh do dữ liệu thay đổi, không phải do câu hỏi thay đổi.

## 9. Lỗi đã gặp và cách xử lý

- **Lỗi:** Lúc đầu script baseline dừng ở NotImplementedError vì phase1.py và testset.py mới chỉ có khung TODO.
- **Cách xử lý:** Nối lại pipeline theo thứ tự: load raw → clean → lưu clean artifact → build index → tạo test set → evaluate → quality/freshness → report.
- **Kết quả:** Lệnh baseline chạy xong và tạo đủ artifact nêu ở phần 4.

Lưu ý: raw snapshot không có category. Tôi dùng General làm fallback trong cleaning để trường Categories trong embedding và evaluation không rỗng.

## 10. Điều học được và hướng cải thiện

1. Cleaning là bước tạo data contract cho embedding, evaluation và observability; sai ID hoặc ngày sẽ ảnh hưởng toàn bộ pipeline.
2. age_days cần được tính ngay khi chuẩn hóa ngày để freshness có dữ liệu chính xác.
3. Baseline nên chạy lại từ raw đến report trong một lượt để các artifact luôn khớp nhau.

Nếu có thêm thời gian, tôi sẽ cải thiện phần trả lời summary để trả về nội dung đầy đủ hơn hoặc dùng LLM để tóm tắt. Mục tiêu là tăng Token F1 và judge accuracy ở các câu hỏi summary.

## 11. Cam kết

- [x] Báo cáo phản ánh đúng phần cleaning tôi phụ trách.
- [x] Các số liệu baseline được lấy từ artifact vừa chạy.
- [x] Báo cáo không chứa API key, token hay nội dung .env.

**Họ và tên:** Trần Đình Duy

**Ngày xác nhận:** 2026-09-26
