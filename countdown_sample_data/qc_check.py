"""
qc_check.py — Checklist QC (rut gon) chay tren du lieu da sinh:
  1. Moi mau: verify(reference_expression, numbers, target).valid == True
  2. Khong trung canonical_key giua cac split
  3. difficulty co mat va hop le
"""
import json
from verifier import verify

SPLITS = ["train", "val", "test_id", "test_ood"]


def load(split):
    with open(f"data/{split}.jsonl", encoding="utf-8") as f:
        return [json.loads(line) for line in f]


def canonical_key(numbers, target):
    return (tuple(sorted(numbers)), target)


def main():
    all_keys = {}
    total = 0
    total_valid = 0
    dup_found = False

    for split in SPLITS:
        records = load(split)
        n_valid = 0
        for rec in records:
            total += 1
            raw = f"FINAL: {rec['reference_expression']}"
            result = verify(raw, rec["numbers"], rec["target"])
            if result["valid"]:
                n_valid += 1
                total_valid += 1
            else:
                print(f"  [LOI] {split}/{rec['id']}: verifier tra "
                      f"error_code={result['error_code']} cho reference_expression "
                      f"da duoc chinh generator sinh ra -> co bug!")

            key = canonical_key(rec["numbers"], rec["target"])
            if key in all_keys:
                dup_found = True
                print(f"  [TRUNG KHOA] {split}/{rec['id']} trung voi {all_keys[key]} "
                      f"(canonical_key={key})")
            else:
                all_keys[key] = f"{split}/{rec['id']}"

            if rec.get("difficulty") not in ("easy", "medium", "hard"):
                print(f"  [LOI] {split}/{rec['id']}: difficulty khong hop le")

        print(f"{split:10s}: {n_valid}/{len(records)} valid qua verifier")

    print(f"\nTONG: {total_valid}/{total} bai hop le "
          f"({100*total_valid/total:.1f}%)")
    print("Trung khoa giua cac split:", "CO — CAN SUA" if dup_found else "KHONG (dat)")


if __name__ == "__main__":
    main()
