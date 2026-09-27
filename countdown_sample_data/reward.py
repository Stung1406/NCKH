"""
reward.py — Anh xa ket qua cua verifier thanh reward, theo dung 2 thang
da chot trong SPEC: binary va shaped (3 muc, khong hon).
"""


def binary_reward(verify_result: dict) -> float:
    return 1.0 if verify_result["valid"] else 0.0


def shaped_reward(verify_result: dict) -> float:
    if verify_result["valid"]:
        return 1.0
    if verify_result["parse_ok"] and verify_result["operators_ok"] and verify_result["numbers_ok"]:
        # parse duoc, dung so/toan tu, nhung sai target (A1) hoac R4
        return 0.1
    return 0.0
