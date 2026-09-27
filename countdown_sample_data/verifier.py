"""
verifier.py — Kiem chung mot loi giai Countdown theo dung pipeline 8 buoc
va bang ma loi trong SPEC (P0, P1, R1, R2, R3, R4, A1).

Su dung:
    from verifier import verify
    result = verify(raw_output, numbers=[2,3,7,10], target=47)
    # result la mot dict co cau truc, xem RESULT SCHEMA ben duoi.

RESULT SCHEMA:
{
  "parse_ok": bool,
  "operators_ok": bool,
  "numbers_ok": bool,
  "value": str | None,      # vi du "47" hoac "22/3"
  "target_ok": bool,
  "valid": bool,
  "error_code": str | None, # None neu valid=True
  "expression": str | None, # bieu thuc da trich xuat (sau FINAL:)
}

Ba bat bien bat buoc:
  1. Khong crash voi bat ky input nao.
  2. Khong bao gio tra valid=True khi chua di het 8 buoc.
  3. Xac dinh: cung input -> cung output (khong random, khong trang thai).
"""

import ast
import re
from fractions import Fraction
from collections import Counter

MAX_INPUT_LEN = 2000          # chan tan cong chuoi qua dai (khai thac #8)
MAX_EXPR_LEN = 40             # gioi han do dai bieu thuc theo SPEC muc 3.12

ALLOWED_BINOPS = (ast.Add, ast.Sub, ast.Mult, ast.Div)


def _empty_result():
    return {
        "parse_ok": False,
        "operators_ok": False,
        "numbers_ok": False,
        "value": None,
        "target_ok": False,
        "valid": False,
        "error_code": None,
        "expression": None,
    }


def _fail(result, code):
    result["error_code"] = code
    result["valid"] = False
    return result


def extract_expression(raw: str):
    """Buoc 1: lay noi dung sau marker FINAL: CUOI CUNG (khai thac #1)."""
    if "FINAL:" not in raw:
        return None
    # rsplit lay marker cuoi cung, khong lay dau
    tail = raw.rsplit("FINAL:", 1)[-1]
    # chi lay dong dau tien sau marker (output phai la 1 dong)
    line = tail.strip().splitlines()[0].strip() if tail.strip() else ""
    return line if line else None


def _check_charset(expr: str):
    """Buoc phong ve ky tu la: chan moi ky tu ngoai ASCII (unicode digit, x, ÷,
    en-dash, dau phay thap phan, fullwidth...). Cac ky tu ASCII con lai (kem
    chu cai, ngoac vuong, dau phay ...) van duoc di qua de ast.parse tu nhien
    phat hien va tu choi bang allowlist node (vi du sum([...]) -> R3), thay vi
    bi chan som va gan nham thanh loi cu phap P1."""
    return all(ord(ch) < 128 for ch in expr)


def _validate_constant(node):
    """Chan bay Constant: chi int, >=1, khong phai bool, khong phai 1e1 (float)."""
    if not isinstance(node, ast.Constant):
        return False
    val = node.value
    if isinstance(val, bool):  # bool la subclass cua int trong Python — phai chan rieng
        return False
    if type(val) is not int:
        return False
    if val < 1:
        return False
    return True


def _collect_and_check(node, literals):
    """Buoc 3 + 4: di qua AST, chi cho phep node trong allowlist, thu thap literal."""
    if isinstance(node, ast.Expression):
        return _collect_and_check(node.body, literals)
    if isinstance(node, ast.Constant):
        if not _validate_constant(node):
            return False
        literals.append(node.value)
        return True
    if isinstance(node, ast.BinOp):
        if not isinstance(node.op, ALLOWED_BINOPS):
            return False
        return _collect_and_check(node.left, literals) and _collect_and_check(node.right, literals)
    # UnaryOp, Call, Name, Attribute, Subscript, Pow, List, Tuple, ... deu bi tu choi
    return False


def _eval_fraction(node):
    """Buoc 6: tinh gia tri bang Fraction; None neu chia cho 0 o node nao do."""
    if isinstance(node, ast.Expression):
        return _eval_fraction(node.body)
    if isinstance(node, ast.Constant):
        return Fraction(node.value)
    if isinstance(node, ast.BinOp):
        lval = _eval_fraction(node.left)
        if lval is None:
            return None
        rval = _eval_fraction(node.right)
        if rval is None:
            return None
        if isinstance(node.op, ast.Add):
            return lval + rval
        if isinstance(node.op, ast.Sub):
            return lval - rval
        if isinstance(node.op, ast.Mult):
            return lval * rval
        if isinstance(node.op, ast.Div):
            if rval == 0:
                return None
            return lval / rval
    return None


def verify(raw_output: str, numbers, target: int) -> dict:
    result = _empty_result()

    # --- fail-closed ngay tu dau: input qua dai / khong phai string ---
    if not isinstance(raw_output, str) or len(raw_output) > MAX_INPUT_LEN:
        return _fail(result, "P0")

    # --- Buoc 1: trich xuat bieu thuc sau marker FINAL: cuoi cung ---
    expr = extract_expression(raw_output)
    if expr is None:
        return _fail(result, "P0")
    result["expression"] = expr

    if len(expr) > MAX_EXPR_LEN:
        return _fail(result, "P1")

    if not _check_charset(expr):
        return _fail(result, "P1")

    # --- Buoc 2: parse bang AST ---
    try:
        tree = ast.parse(expr, mode="eval")
    except (SyntaxError, ValueError):
        return _fail(result, "P1")
    result["parse_ok"] = True

    # --- Buoc 3+4: allowlist node/toan tu + thu thap literal ---
    literals = []
    try:
        ops_ok = _collect_and_check(tree, literals)
    except Exception:
        return _fail(result, "R3")
    if not ops_ok:
        return _fail(result, "R3")
    result["operators_ok"] = True

    # --- Buoc 5: kiem tra multiset dung voi numbers duoc cap ---
    lit_counter = Counter(literals)
    num_counter = Counter(numbers)
    # R1: co literal khong nam trong de bai (so la) — uu tien kiem truoc
    for value, cnt in lit_counter.items():
        if num_counter.get(value, 0) == 0:
            return _fail(result, "R1")
    # R2: moi literal deu ton tai trong de, nhung so lan dung sai (thieu/thua/lap)
    if lit_counter != num_counter:
        return _fail(result, "R2")
    result["numbers_ok"] = True

    # --- Buoc 6: tinh gia tri bang Fraction, fail-closed voi ZeroDivisionError ---
    try:
        value = _eval_fraction(tree)
    except Exception:
        return _fail(result, "R4")
    if value is None:
        return _fail(result, "R4")

    result["value"] = str(value) if value.denominator == 1 else f"{value.numerator}/{value.denominator}"

    # --- Buoc 7: so sanh voi target ---
    if value.denominator != 1 or value.numerator != target:
        return _fail(result, "A1")
    result["target_ok"] = True

    # --- Buoc 8: hop le ---
    result["valid"] = True
    result["error_code"] = None
    return result


if __name__ == "__main__":
    # Vai test nhanh lay tu bang vi du trong SPEC de tu kiem tra verifier
    tests = [
        ("FINAL: (10 - 3) * 7 - 2", [2, 3, 7, 10], 47, True, None),
        ("FINAL: 7 * 7 - 2", [2, 3, 7, 10], 47, False, "R2"),
        ("FINAL: (10 - 3) * 7 - 2 + 1", [2, 3, 7, 10], 47, False, "R1"),
        ("FINAL: sum([2,3,7,10])", [2, 3, 7, 10], 47, False, "R3"),
        ("FINAL: 3 / (10 - 5 * 2)", [2, 3, 5, 10], 7, False, "R4"),
        ("FINAL: (10 + 3) * 7 - 2", [2, 3, 7, 10], 47, False, "A1"),
        ("FINAL: 1e1 * 3 + 7 + 2", [2, 3, 7, 10], 47, False, "R3"),
        ("Toi nghi mai ma khong ra.", [2, 3, 7, 10], 47, False, "P0"),
        ("FINAL: ((10 - 3) * 7 - 2", [2, 3, 7, 10], 47, False, "P1"),
        ("FINAL: 7*7-2 FINAL: (10-3)*7-2", [2, 3, 7, 10], 47, True, None),
        ("FINAL: (10-3)*7-2 FINAL: 7*7-2", [2, 3, 7, 10], 47, False, "R2"),
        ("FINAL: 10 * 3 + 3 * 7", [3, 3, 7, 10], 51, True, None),
        ("FINAL: 10 * 3 + 3 * 7", [3, 3, 7, 10], 50, False, "A1"),
    ]
    n_pass = 0
    for raw, nums, tgt, exp_valid, exp_code in tests:
        r = verify(raw, nums, tgt)
        ok = (r["valid"] == exp_valid) and (r["error_code"] == exp_code)
        n_pass += ok
        status = "OK " if ok else "FAIL"
        print(f"[{status}] valid={r['valid']!s:5} code={str(r['error_code']):5} <- {raw!r}")
    print(f"\n{n_pass}/{len(tests)} test tu kiem tra pass.")
