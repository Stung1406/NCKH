"""
demo_score_outputs.py — Vi du ung dung thuc te: gia lap output cua mot mo hinh
cho vai bai trong data/test_id.jsonl (mot cau tra dung, mot cau "tan cong" /
sai), roi cham diem bang verifier.py + reward.py. Day la khung ban co the
cam thang vao vong lap danh gia / RL that cua du an.
"""
import json
from verifier import verify
from reward import binary_reward, shaped_reward


def load(split):
    with open(f"data/{split}.jsonl", encoding="utf-8") as f:
        return [json.loads(line) for line in f]


def fake_model_output(rec, mode):
    """Gia lap cac kieu output khac nhau cua 'mo hinh' de minh hoa cham diem."""
    expr = rec["reference_expression"]
    if mode == "dung":
        return f"FINAL: {expr}"
    if mode == "sai_dich":
        # Doi mot toan tu (khong them so moi) de bieu thuc van dung luat
        # nhung ra sai target — minh hoa dung nghia loi A1.
        swap = {"+": "-", "-": "+", "*": "/", "/": "*"}
        for ch, other in swap.items():
            if ch in expr:
                return f"FINAL: {expr.replace(ch, other, 1)}"
        return f"FINAL: {expr}"
    if mode == "thieu_marker":
        return f"Toi nghi la {expr} nhung khong chac."
    if mode == "goi_ham":
        return f"FINAL: sum({rec['numbers']})"
    return f"FINAL: {expr}"


def main():
    test_id = load("test_id")
    modes = ["dung", "sai_dich", "thieu_marker", "goi_ham"]

    print(f"{'id':12s} {'mode':14s} {'valid':6s} {'code':6s} {'binary':7s} {'shaped':7s}")
    print("-" * 60)
    for rec in test_id[:5]:
        for mode in modes:
            raw = fake_model_output(rec, mode)
            result = verify(raw, rec["numbers"], rec["target"])
            b = binary_reward(result)
            s = shaped_reward(result)
            print(f"{rec['id']:12s} {mode:14s} {str(result['valid']):6s} "
                  f"{str(result['error_code']):6s} {b:<7} {s:<7}")


if __name__ == "__main__":
    main()
