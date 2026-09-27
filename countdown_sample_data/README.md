# Bộ dữ liệu mẫu — Bài toán Countdown (bản ứng dụng, chạy được ngay)

Đây không phải chỉ là dữ liệu tĩnh — đây là **một pipeline nhỏ hoàn chỉnh** (sinh dữ liệu →
kiểm chứng → chấm điểm) bạn có thể chạy thẳng và cắm vào dự án của mình.

## Cấu trúc

```
generator.py            sinh dữ liệu Countdown (thiết kế a: sinh từ biểu thức, dùng Fraction)
verifier.py              chấm một lời giải theo đúng pipeline 8 bước + mã lỗi (P0/P1/R1/R2/R3/R4/A1)
reward.py                 2 hàm reward: binary_reward(), shaped_reward()
qc_check.py               chạy QC toàn bộ dữ liệu đã sinh (verify 100%, check trùng khoá)
demo_score_outputs.py     ví dụ áp dụng: giả lập 4 kiểu output của "mô hình" rồi chấm điểm
data/
  train.jsonl        (630 bài, miền số 1–10)
  val.jsonl          (135 bài, miền số 1–10)
  test_id.jsonl      (135 bài, miền số 1–10)
  test_ood.jsonl     (100 bài, miền số 11–20 — tập ngoài phân phối)
  metadata.json      seed, sha256 từng split, các quyết định thiết kế đã chốt
```

Đây là **bộ dữ liệu đầy đủ** theo đúng tỉ lệ 630/135/135/100 trong SPEC gốc — không phải bản thu nhỏ nữa.
Toàn bộ 1000 bài đã được QC bằng chính `verifier.py`: **1000/1000 hợp lệ, 0 trùng canonical key** giữa các split.

> **Lưu ý về phân bố độ khó:** vì sinh ngẫu nhiên thuần trên miền số nhỏ (1–10), phần lớn bài
> rơi vào mức `easy` (~85–90%), còn `medium`/`hard` chiếm thiểu số. Đây là đặc điểm tự nhiên
> của cách sinh (a) — không phải lỗi. Nếu bạn cần phân bố đều hơn (ví dụ 1/3 mỗi mức), nói tôi
> biết — cần thêm bước lấy mẫu có định mức (quota sampling) theo độ khó.

## Chạy thử ngay

```bash
python3 generator.py          # sinh lại data/ (idempotent nếu giữ nguyên SEED)
python3 verifier.py           # verifier tự kiểm bằng 13 test case chuẩn từ SPEC
python3 qc_check.py           # QC toàn bộ 100 bài đã sinh — phải ra 100/100 valid
python3 demo_score_outputs.py # minh hoạ chấm điểm 4 kiểu output khác nhau
```

## Cách cắm vào dự án của bạn

```python
from verifier import verify
from reward import binary_reward, shaped_reward

raw_model_output = "Tôi nghĩ là... FINAL: (10 - 3) * 7 - 2"
result = verify(raw_model_output, numbers=[2, 3, 7, 10], target=47)
# result = {"parse_ok": True, ..., "valid": True, "error_code": None, ...}

r_binary = binary_reward(result)   # 1.0
r_shaped = shaped_reward(result)   # 1.0
```

Đọc dữ liệu:

```python
import json
with open("data/train.jsonl", encoding="utf-8") as f:
    train = [json.loads(line) for line in f]
```

## Các quyết định thiết kế đã cố định trong bộ mẫu này (ghi trong `data/metadata.json`)

| Quyết định | Giá trị đã chọn |
|---|---|
| Số lượng số | n = 4, miền ID 1–10, miền OOD 11–20 |
| Số trùng | multiset — dùng đúng số lần xuất hiện |
| Phân số trung gian | Cho phép, tính bằng `Fraction` |
| Trung gian âm | Cho phép |
| Độ dài biểu thức | ≤ 40 ký tự |
| Output | Không CoT, chỉ `FINAL: <biểu thức>` |
| Unary minus | **Không** hỗ trợ trong bộ sinh này (để verifier gọn hơn) |

Nếu bạn muốn đổi bất kỳ quyết định nào ở trên (ví dụ: cấm phân số trung gian, hoặc thêm
unary minus), nói cho tôi biết — tôi sẽ sửa lại `generator.py`/`verifier.py` và sinh lại
bộ dữ liệu tương ứng.
