# ĐẶC TẢ BÀI TOÁN COUNTDOWN — bản chi tiết (tài liệu tham chiếu Buổi 1)

> **File này là gì:** bản *đầy đủ* của những gì cẩm nang quy định về bài toán, gom từ 4 file gốc về một chỗ để bạn đọc đối chiếu.
>
> **File này KHÔNG là gì:** nó **không phải** `SPEC.md` của bạn. `SPEC.md` (thư mục gốc project) là **bài tập phần B Buổi 1** — bạn tự chốt 6 quyết định, tự ghi tên mình vào, và đó là phần được chấm. Ở đây các mục "Đề xuất" chỉ là lập luận để bạn chọn, không phải lệnh.
>
> **Nguồn:** `03-bai-toan-countdown/01-phat-bieu-bai-toan.md`, `02-du-lieu-va-cach-chia-tap.md`, `03-parser-verifier-va-reward.md`, `04-rui-ro-reward-hacking-va-data-leakage.md`, `04-thiet-ke-thuc-nghiem/06-phan-tich-loi.md`.

---

## 1. Phát biểu hình thức

```text
Input :  một multiset  A = {a1, ..., an}  các số nguyên dương   (n = 4)
         một số nguyên dương  T  (target)
Output:  một dòng chứa  "FINAL: <biểu thức>"
Yêu cầu: giá trị của biểu thức == T, và biểu thức tuân thủ mọi luật ở mục 2
```

Chú ý từ **multiset** (danh sách có lặp, không quan tâm thứ tự), không phải **set**. Đây là chi tiết pháp lý của cả bài toán: đề `[3, 3, 7, 10]` cho phép bạn dùng số 3 **hai lần**. Viết verifier bằng `set()` là sai ngay từ gốc.

Ví dụ chuẩn (`01:9-15`):

```text
A = {2, 3, 7, 10},  T = 47
FINAL: (10 - 3) * 7 - 2
```

Cặp không ví dụ (`01:53-60`) — mỗi cái một kiểu vi phạm khác nhau:

| Biểu thức | Vi phạm | Mã lỗi |
|---|---|---|
| `(10 - 3) * 7 - 2 + 1` | số 1 không có trong đề | **R1** |
| `10 * 3 + 10 + 7` | dùng 10 hai lần, **và = 47 đúng đích** | **R2** |
| `sum([2,3,7,10])` | gọi hàm | **R3** |
| `3 / (10 - 5 * 2)` với đề [2,3,5,10] | chia cho 0 ở node giữa, bài **đúng luật hoàn toàn** tới tận bước chia | **R4** |
| `(10 + 3) * 7 - 2` | = 89 ≠ 47, đúng luật nhưng sai đích | **A1** |
| `FINAL: 7*7-2` | = 47 **đúng đích**, nhưng literal 7 lặp, bỏ 10 và 3 | **R2** |

Hai dòng đầu từ dưới đếm lên cho bạn thấy: **cố tình chọn số sao cho biểu thức sai luật vẫn ra đúng đích** thì dễ hơn bạn tưởng (`10*3+10+7 = 47`). Vì vậy "verifier tính ra đúng target" **không phải** bằng chứng gì cả.

Dòng cuối là dòng quan trọng nhất của cả tài liệu này. Xem mục 2.7.

---

## 2. Luật chơi — từng điều một, kèm "verifier kiểm bằng cách nào"

### 2.1 Số lượng số và miền giá trị
- **n = 4** số cho split train/val/test-ID.
- **ID:** mỗi số nguyên dương, miền **1–10** (đây là cái tạo ra OOD ở 2.13).
- Verifier so multiset literal với multiset được cấp — không có "gần đúng".

### 2.2 Mỗi số dùng đúng một lần
Đếm bằng `collections.Counter`: `Counter(literals) == Counter(numbers)`.
Không phải `in`, không phải `set(...) == set(...)`.

### 2.3 Số trùng
Số trùng xuất hiện k lần trong đề ⇒ được dùng đúng k lần. `[3,3,7,10]` ⇒ `3*3+7*10` hợp lệ, `3+7+10` **thiếu** một con 3 ⇒ R2.

### 2.4 Phép toán
**Chỉ** `+`, `-`, `*`, `/` (nhị phân) — cộng, trừ, nhân, chia. **Không** `**`, `//`, `%`, không `sqrt`, không `!`, không hàm nào.

### 2.5 Unary minus
`-5` **không phải** một số literal, nó là `UnaryOp(Minus, Constant(5))`. Cho phép hay không là **quyết định của bạn** (mục 3.4). Hệ quả nếu cho phép: `Counter` literal của `-5` vẫn là `{5}`, nên không phá vỡ check số.

### 2.6 Ngoặc
Được dùng, không giới hạn độ sâu, và **AST tự biểu diễn ngoặc** — bạn không cần xử lý ngoặc thủ công. Cái cây *là* thứ tự tính.

### 2.7 ⚠️ Literal ≠ giá trị trung gian

> **Luật nằm ở các con số XUẤT HIỆN TRONG VĂN BẢN biểu thức, không nằm ở các giá trị trung gian.**

```text
(10 - 3) * 7 - 2      literals = {10, 3, 7, 2}  = đề  ✓
       ↑ trong quá trình tính có hai con 7 (một từ phép trừ), hoàn toàn hợp lệ
```

```text
7 * 7 - 2             literals = {7, 7, 2}      ≠ đề  ✗ R2
```

`7*7-2` tính ra **đúng 47**. Một verifier chỉ so kết quả cuối (`eval(expr) == target`) sẽ cho nó **điểm tuyệt đối**. Đó chính là **reward hacking** định nghĩa ở `04:9`, và đó là lý do mục 2.2 (check multiset) tồn tại thành một lớp riêng chứ không phải chi tiết phụ.

### 2.8 Chia cho 0
Không bao giờ được xảy ra, **kể cả ở một node giữa của cây**. `10 / (7 - 3 - 4)` có mẫu số = 0 ở tầng dưới ⇒ R4. Khi fold cây bằng `Fraction`, `ZeroDivisionError` **không được phép lọt ra ngoài** — phải bắt và biến thành `{"valid": false, "error_code": "R4"}` (fail-closed, `04:21`).

### 2.9 Phân số trung gian
Đề bài gốc cho "có thể cho phép, nhưng nhóm **phải khóa quy tắc này**" (`01:19`). Nếu cho phép, bắt buộc tính bằng **số hữu tỉ `Fraction`**, không dùng float. Lý do định lượng ở mục 6.3.

### 2.10 Kết quả trung gian âm
Một quyết định riêng (`01:47`). Cho phép ⇒ đơn giản hơn và không mất học thuật; cấm ⇒ verifier phải theo dõi mọi node trung gian, thêm một lớp trạng thái.

### 2.11 Kết quả cuối
**Phải là số nguyên và đúng bằng target.** Nếu cho phân số trung gian mà kết quả ra `47/2`, đó là **A1**, không phải đúng.

### 2.12 Độ dài
Giới hạn độ dài biểu thức **và** `max_tokens` của model — hai thứ khác nhau, phải có cả hai:
- `len(expression) ≤ ~40 ký tự` → vi phạm là một mã lỗi rõ.
- `max_tokens` đủ lớn để **không** cắt giữa câu → nếu bị cắt, đó là **F1** (`06:18`), và F1 phải phân biệt được với P0/P1. Không đặt trần thì bạn **không đếm được** loại lỗi này.

### 2.13 Format output và OOD
- **Chỉ** một dòng `FINAL: <biểu thức>`. Mọi phần giải thích nằm **trước** marker.
- **OOD đổi đúng một yếu tố** (`02:52`). Kế hoạch: train số 1–10, **OOD số 11–20**. Cấm "OOD = bài khó hơn" (`04:49`: "OOD không có nghĩa 'khó hơn' chung chung").

---

## 3. Sáu câu PHẢI chốt trước khi sinh dữ liệu (`01:42-49`)

Quy tắc của cẩm nang: *"Mọi split và phương pháp phải dùng cùng một đặc tả"* (`01:51`). Đổi một ô trong bảng này = sinh lại toàn bộ dataset = đổi experiment ID.

| # | Câu hỏi | Phương án A | Phương án B | Hệ quả nếu chọn B | **Đề xuất** |
|---|---|---|---|---|---|
| 1 | Dùng đủ mọi số hay được bỏ? | **đủ, mỗi số đúng 1 lần** | được bỏ số | B mở toang cửa nghiệm tầm thường (`0*big`), bài mất ý nghĩa; verifier mất lớp numbers_ok | **A** |
| 2 | Số trùng dùng mấy lần? | đúng số lần nó xuất hiện (**multiset**) | tối đa 1 lần (set) | chọn set = **bug**, không phải lựa chọn | **multiset / `Counter`** |
| 3 | Cho phân số trung gian? | có, tính bằng `Fraction` | cấm, mọi node trung gian phải nguyên | cấm làm generator khó sinh hơn và checker phức tạp hơn, không thêm gì | **có + `Fraction`** |
| 4 | Cho kết quả trung gian âm? | có | cấm | phải thêm vết-luân-trung-gian vào verifier | **có** |
| 5 | Độ dài tối đa? | **~40 ký tự**, `max_tokens` generous | không giới hạn | không giới hạn ⇒ không đo được F1 | **40 ký tự + max_tokens** |
| 6 | Output có lời giải thích? | chỉ một dòng `FINAL:` | cho CoT trước marker | CoT làm thay đổi biến số so với baseline khác ⇒ phải là experiment ID riêng | **v1: không CoT** |

**Ghi vào `SPEC.md` của bạn:** lựa chọn + *một câu vì sao*. Không có vì sao thì người đọc không biết bạn chọn hay đoán.

---

## 4. Pipeline kiểm chứng — 8 bước (`03:15-25`)

```text
[0] output text  (raw, từ model — DỮ LIỆU KHÔNG TIN CẬY)
      │
[1] lấy nội dung sau FINAL:            →  P0 nếu không có marker
      │                                  →  lấy marker CUỐI, không lấy đầu (`04:11`)
[2] parse bằng AST                     →  P1 nếu cú pháp sai
[3] allowlist node / toán tử           →  R3 nếu có node ngoài danh mục
[4] thu multiset literal numbers
[5] kiểm tra đúng numbers được cấp     →  R1 (số lạ) / R2 (thừa-thiếu-lặp)
[6] tính bằng số hữu tỉ                →  R4 nếu chia 0
[7] so sánh target                     →  A1 nếu đúng luật mà ≠ target
[8] trả structured result
```

**Ba trách nhiệm tách biệt, cấm gộp** (`03:5-11`):

| Thành phần | Việc | Không được làm |
|---|---|---|
| **Parser** | tách chuỗi, dựng cây cú pháp | quyết định đúng/sai |
| **Verifier** | kiểm cây theo đề bài | trả về mỗi `bool` (mất error analysis) |
| **Reward function** | `verifier_result → con số` | tự ý nới luật |

> "Không gộp ba phần thành một regex khó kiểm thử." (`03:11`)

**Mọi bước ở giữa phải trả về lỗi, không được phép throw.** Mặc định fail-closed (`04:21`).

---

## 5. Cái được phép / không được phép trong AST

### 5.1 Node được phép (allowlist)

| Node | Ý nghĩa | Ràng buộc thêm |
|---|---|---|
| `Expression` | bọc toàn bộ | `mode="eval"` |
| `BinOp` | `a op b` | op ∈ {`Add`, `Sub`, `Mult`, `Div`} |
| `UnaryOp` | `-a` | chỉ `USub`, **nếu** spec 3.4 cho phép |
| `Constant` | số | chỉ **`int`, ≥ 1** |

### 5.2 Node bị từ chối — và vì sao từng cái đáng sợ

| Node | Ví dụ tấn công | chuyện gì xảy ra nếu bạn quên chặn |
|---|---|---|
| `Name` | `x`, `__import__` | tra biến toàn cục, đường vào `eval` |
| `Call` | `sum([2,3,7,10])`, `int(...)` | **thực thi hàm** |
| `Attribute` | `().__class__` | chuỗi thoát tới class object |
| `Subscript` | `[1,2][0]` | chọn giá trị từ danh sách nhồi vào |
| `Import` | `import os` | mã lệnh thật |
| `Pow` | `2**10` | tạo số khổng lồ ngoài ý đồ luật |
| `List`/`Tuple`/`Dict`/`Set` | `[7]` | vỏ bọc cho Subscript |
| `Slice`, `Lambda`, `Compare`, `BoolOp`, `IfExp`, `JoinedStr` (f-string) | — | mọi thứ khác: **mặc định từ chối** |

### 5.3 Bẫy `Constant` — chỗ template nào cũng dễ nới

`ast.parse("1e1 * 3 + 7 + 2", mode="eval")` cho một `Constant(value=10.0)`. Nó là *literal số*, nên một allowlist viết kiểu "**cứ `Constant` là cho qua**" sẽ **accept**. Biểu thức đó = 39 *(đã sửa: bản gốc ghi nhầm 19; khớp lại với bảng mục 15, hàng 5)*, và với đề `[2,3,7,10]` + target 47 thì sai; nhưng điểm chết người là: **số 10 chui vào bằng ký hiệu khoa học**, lách qua check multiset nếu bạn so `int(...)` một cách hời hợt. Đây chính xác là khai thác thứ hai trong danh sách `04:12`.

⇒ **Chặn ở ba tầng, không phải một:** `type(c.value) is int` (chặn float *và* `1e1`) + `c.value >= 1` (chặn 0/âm-as-literal) + **độ dài chuỗi literal** (chặn `1_000_000` và ký tự lạ). Và `ast.literal_eval` cũng **không** được dùng thay cho việc đọc `node.value`.

### 5.4 Ký tự trắng và chữ lạ
Chấp nhận khoảng trắng linh hoạt; **từ chối** `×`, `÷`, `–` (en-dash), dấu phẩy thập phân, unicode digits. Lý do: model hay sinh chúng, và nếu bạn "độ lượng" chuyển đổi chúng ở parser thì bạn đang **viết lại bài toán**.

---

## 6. Kết quả có cấu trúc (`03:40-49`)

### 6.1 Schema — thêm `error_code`, `expression`, `elapsed_ms`

```json
{
  "parse_ok": true,
  "operators_ok": true,
  "numbers_ok": true,
  "value": "47",
  "target_ok": true,
  "valid": true,
  "error_code": null,
  "expression": "(10 - 3) * 7 - 2",
  "elapsed_ms": 0.4
}
```

### 6.2 Vì sao 5 cờ chứ không phải 1 `bool`
Vì sau khi chạy xong bạn **phải** trả lời được "30 bài sai của tôi sai kiểu gì" (`06:5`: "Accuracy cho biết bao nhiêu, error analysis giải thích sai như thế nào"). Và vì **reward shaping** (`03:52`) cần biết "parse được nhưng sai target" khác "parse lỗi".

### 6.3 Vì sao `value` là **chuỗi**, và vì sao cấm float — hai chuyện khác nhau

**(a) Kiểu của `value` trong kết quả.** `Fraction` là duy nhất trong Python giữ chính xác tuyệt đối mọi phép `+ - * /` trên số nguyên. Nhưng **JSON không có kiểu hữu tỉ** — mọi con số trong JSON đều là double. Nên hoặc bạn ghi `"value": "47"` (chuỗi), hoặc bạn đã âm thầm ép kết quả đi qua float ngay lúc serialize. Dùng chuỗi, và dùng chuỗi cả khi kết quả là `"22/3"`.

**(b) Cấm float trong tính toán.** Không phải vì "float không chính xác nói chung" — mà vì nó **phá đúng những bài có nghiệm**. Ba biểu thức Countdown hợp lệ, đã chạy và kiểm chứng:

```python
1 / ((1 / 7) / 7)        == 49    # False  float = 49.00000000000001
(3 / 11) * (11 / 3)      == 1     # False  float = 0.9999999999999999
(11 * 11) / (11 / 18)    == 198   # False  float = 197.99999999999997

Fraction(1) / ((Fraction(1) / Fraction(7)) / Fraction(7)) == 49   # True
```

Và để bạn không chủ quan theo chiều ngược lại — float **ăn may** ở nhiều cái:

```python
(5 + 1/2) * 4   == 22   # True   (1/2 biểu diễn chính xác trong hệ nhị phân)
0.1 + 0.2              # 0.30000000000000004   <- cái này nổi tiếng, nhưng 0.1 và 0.2
                        #   là literal float, biểu thức Countdown hợp lệ KHÔNG có nó
```

**Số đo thật, để bạn biết quy mô vấn đề** (tôi liệt kê 60.000 biểu thức 4 số, chỉ tính các dạng có dây chia `a/((b/c)/d)`, `(a*b)/(c/d)`, `(a*(b/c))*d`, `a/(b/(c*d))`, `(a/b)*(c/d)`, `(a/(b/c))/d`):

| Range | Số biểu thức mà kết quả hữu tỉ là **số nguyên** nhưng float trả về **khác số nguyên đó** |
|---|---|
| **1–10** (split ID của ta) | **484 / 60.000 = 0,807%** |
| **11–20** (split OOD của ta) | **897 / 60.000 = 1,495%** |

Quy luật: hỏng ở **chuỗi chia lặp**, không hỏng ở một phép chia đơn.

> ⚠️ **Ghi chú thêm (chưa tự kiểm chứng):** hai con số 0,807% và 1,495% ở trên là số liệu làm căn cứ cho quyết định "bắt buộc dùng `Fraction`" (mục 3, câu 3) — nên tự chạy lại phép đếm 60.000 biểu thức này trước khi trích nguyên văn vào báo cáo tuần, thay vì coi nó là fact đã kiểm chứng.

**Hậu quả lan truyền:** bài `[1,1,7,7] → 49` có nghiệm đúng → verifier gắn **A1** → reward `0.0` → model **không học được gì từ chính lời giải đúng của nó** (`03:63-67`). Sang OOD tỷ lệ gần gấp đôi, nên điểm OOD tụt mà không có traceback nào cả. Bug trông như *kết quả*, không như *lỗi code* — đó là loại khó phát hiện nhất, và cẩm nang gọi đích danh nó là "sai số float làm biểu thức gần target được chấp nhận" (`04:14`).

**Kéo theo một cấm:** `abs(value - target) < 1e-9` **không phải** giải pháp sửa float. Nó là cách biến lỗ hổng thành chính sách. Sửa duy nhất: `Fraction`.

### 6.4 Ba bất biến của verifier (test ba cái này trước tiên)
1. **Không crash.** Mọi chuỗi đầu vào, kể cả rỗng / 10k ký tự / fuzz random, đều trả về một dict hợp lệ.
2. **Không bao giờ trả `valid: true` khi chưa đi hết 8 bước.**
3. **Xác định.** Cùng `(raw_output, numbers, target)` ⇒ cùng result (verifier **không có trạng thái, không có random, không có network**).

---

## 7. Bảng mã lỗi — 9 mã (`06:11-19`)

| Mã | Loại lỗi | Bật ra ở bước | Cờ |
|---|---|---|---|
| **P0** | Không tìm thấy marker / không parse được | 1 | `parse_ok=false` |
| **P1** | Cú pháp không hợp lệ | 2 | `parse_ok=false` |
| **R1** | Dùng số ngoài đề | 5 | `numbers_ok=false` |
| **R2** | Dùng thiếu / thừa / lặp số | 5 | `numbers_ok=false` |
| **R3** | Toán tử không cho phép | 3 | `operators_ok=false` |
| **R4** | Chia cho 0 hoặc vi phạm luật trung gian | 6 | `valid=false` |
| **A1** | Hợp lệ nhưng sai target | 7 | `target_ok=false` |
| **F1** | Bị cắt do giới hạn output | 0 | `parse_ok=false` |
| **H1** | Nghi ngờ reward hacking | review tay | — |

### 7.1 Thứ tự ưu tiên khi nhiều lỗi cùng xảy ra — PHẢI CHỐT TRƯỚC

Ví dụ thật: `sqrt(9) + 2` với đề `[2,3,7,10]`. Vừa R3 (hàm), vừa R1 (số 9), vừa A2... bạn báo mã nào? Nếu không chốt, hai lần chạy cùng code cho hai nhãn khác nhau và bảng phân tích lỗi của bạn vô nghĩa.

**Thứ tự đề xuất** (từ "dừng sớm nhất" tới "sai muộn nhất"):

```text
F1 → P0 → P1 → R3 → R1 → R2 → R4 → A1
```

Logic: lỗi ở bước pipeline sớm hơn thắng, vì nó là **nguyên nhân trực tiếp** của việc không kiểm được các bước sau. **H1 đứng ngoài dãy này** — H1 không do verifier sinh ra, mà do **bạn mắt nhìn** những output có reward cao bất thường (`04:25`).

### 7.2 F1 vs P0 vs P1 — đừng gộp làm một
- **F1**: output **kết thúc giữa câu** và độ dài đúng bằng `max_tokens` → model không được sinh đủ, đây là lỗi *cấu hình*, không phải lỗi *model*.
- **P0**: model sinh hết, nhưng không có `FINAL:` → lỗi *format/instruction following*.
- **P1**: có `FINAL:`, nhưng sau đó là `((10-3` → lỗi *cú pháp*.

Gộp ba cái = bạn không biết mình phải tăng `max_tokens` hay sửa prompt.

---

## 8. Bài toán phụ: dữ liệu ở đâu ra (`03.../02:7-22`)

**Không có file nào để tải.** Bạn phải sinh ra, và có đúng hai thiết kế:

| | **(a) sinh từ biểu thức** | **(b) sinh số + target rồi tìm nghiệm** |
|---|---|---|
| Làm | dựng cây phép toán ngẫu nhiên → tính ra target → **giữ cây làm `reference_expression`** | lấy 4 số + 1 target ngẫu nhiên → solver vét cạn xem có nghiệm không |
| Ưu | **chắc chắn có lời giải**; có sẵn reference để QC | kiểm soát được phân phối target; sinh được bài "khó" thật |
| Nhược | phân phối biểu thức **thiên lệch theo cây của bạn** | tốn kém; phải viết solver; vẫn phải lưu nghiệm tìm được |
| Độ khó code | ~120 dòng | thêm ~80 dòng `itertools` |

**Kế hoạch: (a) làm chính + (b) một phần.** Lý do bắt buộc phải có reference: checklist QC (`02:60`) nói *"Reference qua chính verifier dùng lúc đánh giá"*. Không lưu cây ⇒ không có reference ⇒ không chạy được QC ⇒ **không chứng minh được** bài nào có lời giải (`02:59`).

### 8.1 ba việc bắt buộc khi generator tính ra giá trị
1. **`Fraction`, không float** (mục 6.3).
2. **`ZeroDivisionError` ở node giữa → bỏ bài đó**, không crash cả vòng lặp.
3. **`value.denominator == 1` và `value.numerator == target`**, nếu không thì bài sinh ra **không có lời giải đúng theo đặc tả của chính bạn**.

### 8.2 `difficulty` — không được gán cảm tính
Checklist (`02:63`) nói rõ *"Difficulty có định nghĩa, không gán cảm tính"*. **Định nghĩa để bạn dùng ngay:**

```text
easy   : biểu thức nghiệm cần ≤ 1 cặp ngoặc
medium : cần đúng 2 cặp ngoặc
hard   : cần ≥ 3 cặp, hoặc có phép chia sinh phân số trung gian
```

Đếm **cặp ngoặc trong `reference_expression`** — khách quan, tái lập được, và không cần model nào cả.

---

## 9. Dedup + canonical key (`02:54-56`)

```text
canonical_key = (tuple(sorted(numbers)), target)
```

- `(10,3,7,2)` và `(2,3,7,10)` và `(3,10,2,7)` ⇒ **MỘT bài**.
- **Nhiều lời giải cho một bài ⇒ vẫn cùng problem ID** — không được nhân bản thành 3 dòng để pass@1 trông cao.
- Vì sao phải nghiêm: `[2,3,7,10]→47` nằm ở train và `(10,7,3,2)→47` nằm ở test **là leakage**, dù trông như hai dòng khác nhau (`04:33`).
- **Chống va chạm key giữa các lần chạy:** thêm `generator_version` vào key hoặc metadata, để dataset v1 và v2 không vô tình "trùng".

---

## 10. Đặc tả dữ liệu

### 10.1 Schema một dòng JSONL (`02:26-35`)

```json
{
  "id": "train-000001",
  "numbers": [2, 3, 7, 10],
  "target": 47,
  "reference_expression": "(10 - 3) * 7 - 2",
  "difficulty": "easy",
  "generator_version": "v1",
  "split": "train"
}
```

Thiếu bất kỳ trường nào trong 7 trường trên ⇒ **không hợp lệ**. `id` phải ổn định theo seed. `reference_expression` **bắt buộc** (QC + SFT data sau này).

### 10.2 Bốn split

| Split | Size | Dùng để | **Được nhìn mấy lần** |
|---|---|---|---|
| `train` | 630 | SFT / RL | tùy ý |
| `val` | 135 | chọn checkpoint, chọn prompt, chọn siêu tham số | **nhiều lần** |
| `test_id` | 135 | báo cáo cuối kỳ | **ĐÚNG MỘT LẦN** |
| `test_ood` | 100 | đo tổng quát hóa | **ĐÚNG MỘT LẦN** |

(900 bài → 630/135/135 theo `02:41`, cộng 100 OOD sinh riêng. Template `countdown-starter` chỉ có 30 bài test_id → sai số chuẩn `sqrt(0.5*0.5/30) ≈ 9%`, tức ±18% ở mức 95% CI — không kết luận được gì.)

### 10.3 Chia split — trình tự bắt buộc

```text
1. sinh toàn bộ candidate với seed cố định
2. canonicalize + dedup
3. random.shuffle(danh sách, seed)          ← KHÔNG được bỏ
4. cắt 630 / 135 / 135
5. sinh 100 OOD (đổi duy nhất: range số 11–20), dedup chéo với train
6. hash từng split (sha256 của file nội dung chuẩn hóa) → ghi vào metadata.json
7. đóng băng test_id + test_ood (commit, không regenerate)
```

Vì sao bước 3 sống còn: generator của bạn có **trật tự xác định**, nên `problems[:int(0.7*n)]` mà không shuffle sẽ cắt theo *kiểu biểu thức*, không theo *bài* — train và test sẽ khác phân phối ngay từ đầu, và mọi so sánh sau này vô nghĩa.

Vì sao bước 6: không có hash thì sau 3 tuần bạn **không chứng minh được** test hôm nay là test hôm qua.

### 10.4 Test-OOD phải đổi ĐÚNG MỘT yếu tố

| | Hợp lệ ✓ | Không hợp lệ ✗ |
|---|---|---|
| 1 | số **11–20**, vẫn 4 số | số 11–20 **và** 5 số |
| 2 | 5 toán hạng, vẫn range 1–10 | target âm |
| 3 | toàn bài cần phân số trung gian, range giữ nguyên | "bài khó hơn" (không định nghĩa) |

Kết luận từ OOD hợp lệ: "model kém hơn khi gặp **số ngoài range**". Từ OOD không hợp lệ: **không kết luận được gì**, vì hai biến cùng đổi.

### 10.5 Checklist QC 6 mục (`02:58-65`) — chạy trước khi tin bất kỳ số nào

- [ ] Mọi mẫu có ít nhất một nghiệm.
- [ ] `verify(reference_expression, numbers, target).valid == True` với **100%** bài train/val/test, dùng **chính verifier ở Buổi 7**.
- [ ] Không trùng canonical key giữa các split.
- [ ] `difficulty` có định nghĩa (mục 8.2), không gán cảm tính.
- [ ] `generator_version` + seed được lưu.
- [ ] Test được đóng băng **trước khi** huấn luyện.

Chạy 2 lần với cùng seed ⇒ 2 file **byte-identical**. Không đạt ⇒ seed của bạn chưa thực sự khóa (`random.seed` không che được phân phối phụ thuộc *thời gian* hoặc iteration qua `dict` không đảm bảo thứ tự ở một số chỗ).

---

## 11. Reward (`03:54-69`)

### 11.1 Binary — dùng cho run đầu tiên

```text
1.0  nếu valid và target_ok
0.0  nếu còn lại
```

### 11.2 Shaped — **chỉ khi binary quá thưa**, và chỉ 3 mức

```text
1.0 : hợp lệ và đúng target
0.1 : parse được, đúng numbers/operators nhưng sai target
0.0 : parse lỗi hoặc vi phạm luật
```

> ⚠️ **Đúng 3 mức.** Cẩm nang không có `0.3` hay `0.5`. Bằng chứng ngược: `countdown-starter/README.md` mục M4 mô tả thang **5 mức** `0.0/0.1/0.3/0.5/1.0` — template đó đã tự ý thêm hai mức so với `03:63-67`. **Không theo.** (Chi tiết này tôi lấy từ README của template, chưa kiểm chứng trên code của nó — xem `LO-TRINH-17-BUOI.md` mục S1.)

### 11.3 Hai quy tắc kỷ luật
1. **Báo cáo riêng binary và shaped** (`03:69`). Không gộp vào một cột "reward".
2. **Đổi thang reward = đổi experiment ID** (`03:69`). Vì reward *là* hàm mục tiêu; đổi nó là đổi thí nghiệm, không phải đổi tham số.

---

## 12. Mười khai thác verifier mà bạn phải chặn (tổng hợp)

5 cái đầu từ `04-rui-ro...md:11-15`, 5 cái sau bổ sung. Đây là danh sách **attack test** ở Buổi 8.

| # | Khai thác | nguồn | Verifier phải từ chối bằng |
|---|---|---|---|
| 1 | Nhiều marker `FINAL:`, parser lấy nhầm cái đầu | `04:11` | `rsplit("FINAL:", 1)[-1]` — lấy **cuối** |
| 2 | Ký hiệu khoa học `1e1`, `5e2` smuggle số ngoài đề | `04:12` | `type(value) is int` (chặn float) + so **literal**, không so giá trị đã convert |
| 3 | Không kiểm multiset ⇒ dùng một số nhiều lần | `04:13` | `Counter(literals) == Counter(numbers)` |
| 4 | Sai số float chấp "gần đúng target" | `04:14` | `Fraction`, so bằng `==`, **không** `abs(v-t) < eps` |
| 5 | Chuỗi đặc biệt làm parser fallback thành "đúng" | `04:15` | mọi exception ⇒ `valid:false`; **không có nhánh default trả True** |
| 6 | `eval()` / `exec()` trên output model | `03:27`, `CAC-SAI-LAM` #1 | grep `eval(`/`exec(`/`compile(`/`os.popen` trong `src/` ⇒ **0 kết quả** |
| 7 | `Call`/`Attribute`/`Subscript`/`Import`: `__import__('os').system(...)` | `03:36` | allowlist node, từ chối mọi node ngoài 4 mục 5.1 |
| 8 | Chuỗi 10k ký tự làm treo verifier | test #9 `03:81` | `len(raw) <= MAX_INPUT`; `sys.setrecursionlimit` **không** phải cách sửa, chặn độ dài mới là cách sửa |
| 9 | `pow` làm bùng nổ số: `9**9**9` | `03:77`, `01:53-60` | `Pow` không thuộc 4 toán tử ⇒ R3 |
| 10 | Unicode: `１０` (fullwidth), `×`, `–` | `01:58` | từ chối: `Constant` chỉ đọc ASCII digits; ký tự lạ ⇒ P1 |

**Quy trình phòng tránh nguyên văn** (`04:19-25`): AST allowlist · số hữu tỉ · mặc định không hợp lệ · unit test đối kháng · fuzz nếu đủ thời gian · **lưu raw output + structured result** · **review tay output reward cao bất thường**.

---

## 13. Danh sách "điều phải quyết" — chính là mục 6 của `01:42-49`

Copy nguyên văn để không sót câu nào (`01:44-49`):

1. Dùng đúng mọi số hay được bỏ số?
2. Một số trùng nhau được dùng bao nhiêu lần?
3. Có cho phép phép chia tạo phân số trung gian?
4. Có cho phép kết quả trung gian âm?
5. Độ dài biểu thức tối đa?
6. Output có lời giải thích hay chỉ biểu thức?

**Và 6 điều phát sinh từ tài liệu này mà bạn phải chốt thêm** (cẩm nang không trả lời hộ):

7. Thứ tự ưu tiên error code (mục 7.1)?
8. Unary minus có phải literal không, đếm vào multiset thế nào (mục 2.5)?
9. Ngưỡng độ dài: tính trên raw output hay trên biểu thức đã parse (mục 2.12)?
10. Định nghĩa `difficulty` bằng gì (mục 8.2)?
11. Yếu tố đổi ở OOD là gì, và chỉ một (mục 10.4)?
12. `value` trả về kiểu gì để không qua float (mục 6.3)?

---

## 14. Mẫu khung `SPEC.md` để bạn điền

Đừng viết xuôi. Điền theo khung này, mỗi mục **một câu vì sao**:

```markdown
# SPEC — đặc tả khóa, phiên bản v1
Ngày chốt: ....            Người chốt: <tên bạn>

## A. Bài toán
- n = 4, miền ID: ..., target: ...
- Marker: `FINAL:`, lấy marker ..., độ dài raw tối đa ...

## B. Sáu quyết định bắt buộc
| Câu | Quyết định | Vì sao (1 câu) |
|---|---|---|
| 1 đủ/thừa số | ... | ... |
| 2 số trùng | ... | ... |
| 3 phân số trung gian | ... | ... |
| 4 trung gian âm | ... | ... |
| 5 độ dài | ... | ... |
| 6 lời giải thích | ... | ... |

## C. Sáu quyết định phát sinh (mục 13 câu 7-12)
...

## D. Pipeline & mã lỗi
(thứ tự ưu tiên đã chốt ở câu C7)

## E. Ví dụ
3 hợp lệ  |  3 không hợp lệ (kèm mã lỗi + lý do)  |  6 attack (chọn từ mục 12)

## F. Chữ "tùy" còn sót ở đâu?  → phải bằng 0
```

**Gate tự kiểm:** `grep -in "tùy\|tuy chon\|TODO\|..." SPEC.md` phải trả về **0 kết quả**. Còn chữ "tùy" nghĩa là đặc tả chưa khóa, và mọi dữ liệu sinh sau đó là rủi ro.

---

## 15. Bảng ví dụ — **đã chạy và kiểm chứng bằng Python**, dùng làm test case

Mỗi hàng dưới đây tôi đã tính thật, không đoán. Cột cuối là **dấu hiệu bạn sẽ gặp nếu verifier viết sai**.

| # | `numbers` | `target` | biểu thức | verdict đúng | mã | nếu verifier sai thì ra gì |
|---|---|---|---|---|---|---|
| 1 | [2,3,7,10] | 47 | `(10 - 3) * 7 - 2` | ✓ valid (=47) | — | — |
| 2 | [2,3,7,10] | 47 | `7 * 7 - 2` | ✗ (=47 **đúng đích**) | **R2** | **`valid:true`** ← verifier chỉ so kết quả |
| 3 | [2,3,7,10] | 47 | `(10 - 3) * 7 - 3` | ✗ (=46) | **R2** (lặp 3, thiếu 2) | ra A1, vì numbers_ok bị bỏ |
| 4 | [2,3,7,10] | 47 | `(10 - 3) * 7 - 2 + 1` | ✗ (=48) | **R1** (số 1 ngoài đề) | ra A1 |
| 5 | [2,3,7,10] | 47 | `1e1 * 3 + 7 + 2` | ✗ (=39.0) | **R3** (Constant là float, ngoài allowlist) | ra A1, và **số 10 chui lọt** qua check `int(1e1)==10` |
| 6a | [2,3,7,10] | 47 | raw: `FINAL: 7*7-2 FINAL: (10-3)*7-2` | lấy marker **cuối** ⇒ ✓ valid | — | lấy marker đầu ⇒ R2, **điểm thấp giả** |
| 6b | [2,3,7,10] | 47 | raw: `FINAL: (10-3)*7-2 FINAL: 7*7-2` | lấy marker **cuối** ⇒ ✗ | **R2** | lấy marker đầu ⇒ **`valid:true`, điểm CAO GIẢ** |
| 7 | [2,3,7,10] | 47 | `sqrt(10)*3+7+2` | ✗ | **R3** (Call) | crash `NameError`, hoặc R1 (9 không có) |
| 8 | [2,3,5,10] | 7 | `3 / (10 - 5 * 2)` | ✗ | **R4** (mẫu số = 0 ở node giữa) | **verifier throw ZeroDivisionError** → cả batch chết |
| 9 | [1,2,4,5] | 22 | `(5 + 1/2) * 4` | ✓ chỉ khi **cho** phân số trung gian | — | nếu spec 3.3 chọn "cấm": phải là **R4**. Float *ăn may* đúng đây — xem 6.3 |
| 10 | [2,3,7,10] | 47 | `((10 - 3) * 7 - 2` | ✗ | **P1** ngoặc không cân | P0, nếu bạn gộp P0/P1 |
| 11 | [2,3,7,10] | 47 | `Tôi nghĩ mãi mà không ra.` | ✗ | **P0** không marker | P1, nếu gộp P0/P1 |
| 12 | [3,3,7,10] | 51 | `3 * 3 + 7 * 6` | ✗ (=51 **đúng đích**) | **R1** (số 6 ngoài đề) | **`valid:true`** ← cùng họ với hàng 2 |
| 13a | [3,3,7,10] | 50 | `10 * 3 + 3 * 7` | ✗ (=51) | **A1** | hợp lệ, đây là A1 sạch |
| 13b | [3,3,7,10] | 51 | `10 * 3 + 3 * 7` | ✓ valid | — | nếu verifier dùng `set`: chỉ thấy {3,7,10} → **R2 sai** cho bài đúng |

### 15.1 Ba hàng đáng học nhất

- **Hàng 2 và 12** là **cùng một họ tấn công**: `đúng target + sai luật`. Hai cái này fail mọi verifier "thông minh vừa đủ" (chỉ `eval` rồi so). Nếu verifier của bạn trả `valid:true` cho một trong hai, **toàn bộ kết quả RL về sau vô nghĩa**.
- **Hàng 6a/6b là một cặp**, và cặp này mới là test đúng nghĩa: chỉ cần một hàng, bạn không phân biệt được parser lấy marker nào. 6b là hàng **nguy hiểm** — lấy nhầm marker đầu cho bạn số **đẹp giả**, còn 6a cho bạn số **xấu giả**. Cẩm nang nêu đúng 6b ở `04:11`.
- **Hàng 13b** là test duy nhất cho **multiset có số trùng** (`[3,3,7,10]` phải dùng 3 **hai lần**). `set()` qua được hàng 13a nhưng **fail** hàng 13b.

### 15.2 Hàng 8 — tại sao `[2,3,5,10]`, không phải `[2,3,7,10]`

Vì với `[2,3,7,10]` mọi cách tạo mẫu số 0 đều phải dùng số ngoài đề hoặc lặp số ⇒ verifier trả về **R1/R2 trước** (theo thứ tự 7.1) và bạn **không bao giờ** kích được nhánh R4. Muốn test R4 sạch, bài phải **đúng luật hoàn toàn** cho tới tận bước chia. Đây là kỹ thuật viết test mà bạn sẽ dùng lại cả kỳ: *muốn đo lớp nào, hãy vô hiệu hóa mọi lớp trước nó.*

---

## 16. Đọc thêm trong cẩm nang (nếu muốn đối chiếu gốc)

| Nội dung trên | File gốc, dòng |
|---|---|
| Phát biểu, luật, output chuẩn, 6 câu | `03-bai-toan-countdown/01:5-60` |
| Generator 2 thiết kế, schema, split, dedup, QC | `03.../02:7-65` |
| Pipeline 8 bước, allowlist, structured result, reward, 12 nhóm test | `03.../03:13-86` |
| 5 khai thác + phòng tránh + leakage + dấu hiệu dừng | `03.../04:9-57` |
| 9 mã lỗi + mẫu phân tích 30–50 lỗi | `04-thiet-ke-thuc-nghiem/06:11-46` |
| "Không dùng test để chọn prompt", "so sánh cùng k" | `04.../05:24-44` |

---

*Quay lại: [`buoi-01-bai-toan-countdown.md`](buoi-01-bai-toan-countdown.md) · Kế hoạch tổng thể: [`../LO-TRINH-17-BUOI.md`](../LO-TRINH-17-BUOI.md)*
