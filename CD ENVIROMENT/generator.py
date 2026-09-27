"""
generator.py — Sinh dữ liệu cho bài toán Countdown, theo dac ta (SPEC) da chot:

  1. Dung du 4 so, moi so dung dung 1 lan (multiset).
  2. So trung dung dung so lan xuat hien.
  3. Cho phep phan so trung gian, tinh bang Fraction (khong dung float).
  4. Cho phep gia tri trung gian am.
  5. Do dai bieu thuc <= 40 ky tu.
  6. Output khong co CoT — chi mot dong "FINAL: <bieu thuc>".
  (Khong ho tro unary minus trong ban sinh nay, de don gian hoa.)

Thiet ke: (a) sinh tu bieu thuc — dung cay nhi phan ngau nhien tren 4 la so,
gan toan tu ngau nhien, tinh gia tri bang Fraction, giu lai neu ket qua la
so nguyen duong. Cay sinh ra duoc luu lai lam `reference_expression`.

Chay:
    python3 generator.py
Sinh ra cac file trong ./data/: train.jsonl, val.jsonl, test_id.jsonl,
test_ood.jsonl, metadata.json
"""

import json
import random
import hashlib
import itertools
from fractions import Fraction
from collections import Counter

GENERATOR_VERSION = "v1"

OPS = ["+", "-", "*", "/"]
PRECEDENCE = {"+": 1, "-": 1, "*": 2, "/": 2}

# 5 cau truc cay nhi phan khac nhau tren 4 la (Catalan(3) = 5 hinh dang)
# Moi cay duoc bieu dien bang tuple long nhau: 0,1,2,3 la vi tri cua 4 la
TREE_SHAPES = [
    (((0, 1), 2), 3),   # ((a op b) op c) op d
    ((0, (1, 2)), 3),   # (a op (b op c)) op d
    (0, ((1, 2), 3)),   # a op ((b op c) op d)
    (0, (1, (2, 3))),   # a op (b op (c op d))
    ((0, 1), (2, 3)),   # (a op b) op (c op d)
]


def build_tree(shape, numbers, ops):
    """Gan gia tri la va toan tu vao cau truc cay, theo thu tu duyet post-order
    (khop voi thu tu cu the truoc day) de moi lan sinh deu tai lap duoc."""
    ops_iter = iter(ops)

    def assign(node):
        if isinstance(node, int):
            return ("leaf", numbers[node])
        left, right = node
        l = assign(left)
        r = assign(right)
        op = next(ops_iter)
        return ("op", op, l, r)

    return assign(shape)


def eval_node(node, frac_flag):
    """Tinh gia tri bang Fraction. Nem ZeroDivisionError neu chia cho 0 o node
    nao do (bat o noi goi). frac_flag la dict de danh dau neu co buoc chia nao
    sinh ra ket qua trung gian khong phai so nguyen (dung cho difficulty)."""
    if node[0] == "leaf":
        return Fraction(node[1])
    _, op, left, right = node
    lval = eval_node(left, frac_flag)
    rval = eval_node(right, frac_flag)
    if op == "+":
        return lval + rval
    if op == "-":
        return lval - rval
    if op == "*":
        return lval * rval
    # "/"
    if rval == 0:
        raise ZeroDivisionError
    result = lval / rval
    if result.denominator != 1:
        frac_flag["has_intermediate_fraction"] = True
    return result


def render_min_parens(node, min_prec=0):
    """In bieu thuc voi so ngoac toi thieu can thiet, dua tren do uu tien va
    tinh ket hop trai cua +,-,*,/ — dam bao khi parse lai bang quy tac uu tien
    chuan (vd. AST Python) se tai tao dung cay ban dau."""
    if node[0] == "leaf":
        return str(node[1])
    _, op, left, right = node
    prec = PRECEDENCE[op]
    left_str = render_min_parens(left, prec)
    # Voi phep tru/chia (khong doi cho duoc), nhanh phai can do uu tien
    # NGHIEM NGAT cao hon moi duoc bo ngoac; voi cong/nhan thi bang la du.
    right_min_prec = prec + 1 if op in ("-", "/") else prec
    right_str = render_min_parens(right, right_min_prec)
    expr = f"{left_str} {op} {right_str}"
    if prec < min_prec:
        expr = f"({expr})"
    return expr


def difficulty_of(expr, has_intermediate_fraction):
    n_parens = expr.count("(")
    if has_intermediate_fraction or n_parens >= 3:
        return "hard"
    if n_parens == 2:
        return "medium"
    return "easy"


def try_generate_one(rng, number_range):
    numbers = [rng.randint(*number_range) for _ in range(4)]
    rng.shuffle(numbers)
    shape = rng.choice(TREE_SHAPES)
    ops = [rng.choice(OPS) for _ in range(3)]
    tree = build_tree(shape, numbers, ops)

    frac_flag = {"has_intermediate_fraction": False}
    try:
        val = eval_node(tree, frac_flag)
    except ZeroDivisionError:
        return None

    if val.denominator != 1:
        return None
    target = val.numerator
    if target <= 0:
        return None

    expr = render_min_parens(tree)
    if len(expr) > 40:
        return None

    return {
        "numbers": sorted(numbers),
        "target": target,
        "reference_expression": expr,
        "difficulty": difficulty_of(expr, frac_flag["has_intermediate_fraction"]),
    }


def canonical_key(numbers, target):
    return (tuple(sorted(numbers)), target)


def generate_unique(n_needed, number_range, rng, seen_keys, max_tries=200000):
    out = []
    tries = 0
    while len(out) < n_needed and tries < max_tries:
        tries += 1
        item = try_generate_one(rng, number_range)
        if item is None:
            continue
        key = canonical_key(item["numbers"], item["target"])
        if key in seen_keys:
            continue
        seen_keys.add(key)
        out.append(item)
    return out


def assign_ids_and_split(items, split_name, start_index=1):
    result = []
    for i, item in enumerate(items, start=start_index):
        rec = {
            "id": f"{split_name}-{i:06d}",
            "numbers": item["numbers"],
            "target": item["target"],
            "reference_expression": item["reference_expression"],
            "difficulty": item["difficulty"],
            "generator_version": GENERATOR_VERSION,
            "split": split_name,
        }
        result.append(rec)
    return result


def write_jsonl(path, records):
    with open(path, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def sha256_of_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        h.update(f.read())
    return h.hexdigest()


def main():
    SEED = 20260927
    rng = random.Random(SEED)

    # ---- Kich thuoc bo DAY DU theo dung ti le goc trong SPEC ----
    N_TRAIN, N_VAL, N_TEST_ID, N_TEST_OOD = 630, 135, 135, 100

    seen_keys = set()

    id_pool = generate_unique(N_TRAIN + N_VAL + N_TEST_ID, (1, 10), rng, seen_keys)
    rng.shuffle(id_pool)  # BUOC KHONG DUOC BO: xao tron truoc khi cat split

    train_items = id_pool[:N_TRAIN]
    val_items = id_pool[N_TRAIN:N_TRAIN + N_VAL]
    test_id_items = id_pool[N_TRAIN + N_VAL:N_TRAIN + N_VAL + N_TEST_ID]

    ood_items = generate_unique(N_TEST_OOD, (11, 20), rng, seen_keys)

    train = assign_ids_and_split(train_items, "train")
    val = assign_ids_and_split(val_items, "val")
    test_id = assign_ids_and_split(test_id_items, "test_id")
    test_ood = assign_ids_and_split(ood_items, "test_ood")

    import os
    os.makedirs("data", exist_ok=True)
    write_jsonl("data/train.jsonl", train)
    write_jsonl("data/val.jsonl", val)
    write_jsonl("data/test_id.jsonl", test_id)
    write_jsonl("data/test_ood.jsonl", test_ood)

    metadata = {
        "generator_version": GENERATOR_VERSION,
        "seed": SEED,
        "counts": {
            "train": len(train),
            "val": len(val),
            "test_id": len(test_id),
            "test_ood": len(test_ood),
        },
        "sha256": {
            "train.jsonl": sha256_of_file("data/train.jsonl"),
            "val.jsonl": sha256_of_file("data/val.jsonl"),
            "test_id.jsonl": sha256_of_file("data/test_id.jsonl"),
            "test_ood.jsonl": sha256_of_file("data/test_ood.jsonl"),
        },
        "spec": {
            "n_numbers": 4,
            "id_range": [1, 10],
            "ood_range": [11, 20],
            "allow_intermediate_fraction": True,
            "allow_intermediate_negative": True,
            "max_expression_length": 40,
            "unary_minus_allowed": False,
            "output_format": "FINAL: <expression>  (khong CoT)",
        },
    }
    with open("data/metadata.json", "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)

    print("Da sinh xong du lieu mau:")
    for k, v in metadata["counts"].items():
        print(f"  {k:10s}: {v} bai")
    print("Ghi vao thu muc ./data/")


if __name__ == "__main__":
    main()
