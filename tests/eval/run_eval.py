"""Runner eval tầng 2+3 — gọi surface thật, chấm bằng programmatic checks + kịch bản seeds.

KHÔNG nằm trong pytest mặc định (tốn tiền API). Chạy từ repo root:

    python -m tests.eval.run_eval --surface chat --repeat 3
    python -m tests.eval.run_eval --dry-run                      # validate schema + checks + fixture, không gọi API trả phí
    python -m tests.eval.run_eval --only seed_05_giay_tam_tru --repeat 1
    python -m tests.eval.run_eval --repeat 3 --out docs/eval-baseline-20260716.json
    python -m tests.eval.run_eval --scenarios tests/eval/scenarios/guardrails.json --repeat 3

Format seed (mirror personas.json của japan-visa-bot, xem scenarios/regression_seeds.json):
- "expected_topics": mỗi entry là CHUỖI (bắt buộc xuất hiện trong ghép mọi reply)
  hoặc LIST BIẾN THỂ (chỉ cần 1 biến thể khớp — any-of).
- "should_NOT_contain": chuỗi không được xuất hiện trong BẤT KỲ reply nào (khớp substring
  NGHIÊM NGẶT có chủ đích — phán xét ngữ nghĩa thuộc tầng 4 judge; cụm bị cấm phải viết ở
  dạng-khẳng-định để bot trích-dẫn-từ-chối không dính oan).
- "should_NOT_regex" (tùy chọn): list regex Python (IGNORECASE, chạy trên reply đã chuẩn hóa
  NFC) — vi phạm nếu BẤT KỲ pattern khớp BẤT KỲ reply mới nào của bot.
- "history" (tùy chọn): messages giả lập prepend trước script — dùng cho jailbreak history giả.

Gates (hiện thực hai tầng gate của docs/eval-plan.md §2/§3):
- Gate tầng 2: từng CHECK phải pass ≥95% tổng số run. Plan yêu cầu đo trên 20 lần lặp/câu —
  ở --repeat thấp gate này chỉ mang tính chỉ báo; dùng --repeat 20 cho gate thật.
- Gate tầng 3: plan yêu cầu 100% seeds pass; với repeat thấp (Haiku non-deterministic)
  áp thành: từng SEED phải pass ≥2/3 số lần lặp.
Exit code 1 nếu một trong hai gate trượt. Với --repeat < 20 gate chỉ mang tính CHỈ BÁO —
dùng --repeat 20 cho gate chuẩn theo plan.

Coverage: hàng IDOR của behavior-spec §5 không chạy ở đây (ownership check nằm ở router,
runner gọi thẳng chat_with_haiku) — đã phủ tầng 1 bởi tests/api/test_chat_ownership.py.

Kết quả ghi JSON (mặc định docs/eval-baseline-<YYYYMMDD>.json) + bảng tóm tắt console
để so sánh giữa các lần đổi prompt. Xem docs/eval-plan.md §4.
"""
import argparse
import json
import re
import sys
import unicodedata
from datetime import datetime
from pathlib import Path

# Bootstrap sys.path về repo root — để import api/core được cả khi chạy ngoài pytest
_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from tests.eval.checks import ALL_CHECKS, contains_ci, topic_found  # noqa: E402

_SCENARIO_PATH = Path(__file__).parent / "scenarios" / "regression_seeds.json"

# Ngưỡng gate — xem docstring đầu file
_CHECK_GATE_THRESHOLD = 0.95
_SEED_GATE_THRESHOLD = 2 / 3

# Ngày đi/về giả lập cho checklist fixture (khớp seed nói về chuyến đi tương lai)
_FIXTURE_DATES = {"departure": "2026-09-01", "return": "2026-09-08"}

# Reply mẫu chuẩn persona — --dry-run chạy ALL_CHECKS trên câu này, tất cả phải pass
_SAMPLE_REPLY = (
    "Dạ, ảnh thẻ cần 2 tấm kích thước 4.5cm × 3.5cm, nền trắng, không đeo kính, "
    "không đội nón, chụp trong vòng 6 tháng gần nhất ạ. Nếu anh/chị cần thêm thông tin, "
    "vui lòng gọi Sông Hàn Tourist 028 7301 2939 hoặc 028 3848 1390 ạ."
)

# Key bắt buộc trong mỗi seed + kiểu dữ liệu ("history" là tùy chọn — jailbreak history giả)
_REQUIRED_KEYS = {
    "id": str,
    "description": str,
    "script": list,
    "context": dict,
    "checklist": bool,
    "expected_topics": list,
    "should_NOT_contain": list,
}


def _positive_int(value: str) -> int:
    n = int(value)
    if n < 1:
        raise argparse.ArgumentTypeError("--repeat phải ≥ 1")
    return n


def _load_seeds(path: Path = _SCENARIO_PATH) -> list:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)["seeds"]


def _validate_seed(seed: dict) -> list:
    """Trả về danh sách lỗi schema của một seed (rỗng = hợp lệ)."""
    errors = []
    for key, typ in _REQUIRED_KEYS.items():
        if key not in seed:
            errors.append(f"thiếu key '{key}'")
        elif not isinstance(seed[key], typ):
            errors.append(f"key '{key}' sai kiểu (cần {typ.__name__})")
    if "progress" not in seed:
        errors.append("thiếu key 'progress' (object hoặc null)")
    elif seed["progress"] is not None and not isinstance(seed["progress"], dict):
        errors.append("key 'progress' phải là object hoặc null")
    if "history" in seed:
        if not isinstance(seed["history"], list):
            errors.append("key 'history' phải là list message {role, content}")
        else:
            for i, msg in enumerate(seed["history"]):
                if (not isinstance(msg, dict)
                        or msg.get("role") not in ("user", "assistant")
                        or not isinstance(msg.get("content"), str) or not msg["content"].strip()):
                    errors.append(f"history[{i}] phải là {{role: user|assistant, content: chuỗi không rỗng}}")
    script = seed.get("script")
    if isinstance(script, list) and (not script or not all(isinstance(s, str) and s.strip() for s in script)):
        errors.append("'script' phải là list câu user không rỗng")
    # expected_topics: chuỗi HOẶC list biến thể (any-of) — biến thể phải là chuỗi không rỗng
    topics = seed.get("expected_topics")
    if isinstance(topics, list):
        for i, topic in enumerate(topics):
            if isinstance(topic, str):
                continue
            if (not isinstance(topic, list) or not topic
                    or not all(isinstance(v, str) and v for v in topic)):
                errors.append(f"expected_topics[{i}] phải là chuỗi hoặc list biến thể không rỗng")
    banned = seed.get("should_NOT_contain")
    if isinstance(banned, list) and not all(isinstance(s, str) for s in banned):
        errors.append("'should_NOT_contain' phải là list chuỗi")
    # should_NOT_regex (tùy chọn): list regex hợp lệ — compile ngay để dry-run bắt lỗi sớm
    patterns = seed.get("should_NOT_regex")
    if patterns is not None:
        if not isinstance(patterns, list) or not all(isinstance(p, str) and p for p in patterns):
            errors.append("'should_NOT_regex' phải là list chuỗi regex không rỗng")
        else:
            for i, pattern in enumerate(patterns):
                try:
                    re.compile(pattern, re.IGNORECASE)
                except re.error as exc:
                    errors.append(f"should_NOT_regex[{i}] không compile được: {exc}")
    return errors


def _build_checklist_fixture(seed: dict, generate_checklist) -> dict:
    """Checklist thật từ static/checklists — giống server build cho khách trong context của seed."""
    context = seed.get("context") or {}
    profile = context.get("profile") or {}
    employment_type = profile.get("employment_type", "employee")
    destination = context.get("destination") or "japan"
    return generate_checklist({"employment_type": employment_type}, dict(_FIXTURE_DATES), destination)


def _run_seed_once(seed: dict, chat_with_haiku, checklist) -> tuple:
    """Chạy script đa lượt qua chat_with_haiku.

    Trả về (transcript, replies, error) — lỗi API giữa chừng vẫn giữ transcript đã gom được."""
    messages = [dict(m) for m in (seed.get("history") or [])]
    replies = []
    for user_msg in seed["script"]:
        messages.append({"role": "user", "content": user_msg})
        try:
            reply = chat_with_haiku(messages, seed.get("context") or {},
                                    checklist=checklist, progress=seed.get("progress"))
        except Exception as exc:  # lỗi API/mạng: run fail, không sập cả baseline trả phí
            return messages, replies, f"runtime_error: {exc}"
        messages.append({"role": "assistant", "content": reply})
        replies.append(reply)
    return messages, replies, None


def _score_run(seed: dict, replies: list) -> list:
    """Chấm một lần chạy: ALL_CHECKS trên từng reply + expected_topics + should_NOT_contain."""
    failures = []
    for i, reply in enumerate(replies, start=1):
        for name, fn in ALL_CHECKS:
            ok, detail = fn(reply)
            if not ok:
                failures.append(f"{name}[lượt {i}]: {detail}")
    # expected_topics: TẤT CẢ entry phải khớp trong toàn bộ hội thoại (ghép mọi reply);
    # entry dạng list là any-of — chỉ cần 1 biến thể xuất hiện
    blob = "\n".join(replies)
    for topic in seed["expected_topics"]:
        if not topic_found(blob, topic):
            label = topic if isinstance(topic, str) else " | ".join(topic)
            failures.append(f"expected_topic: thiếu '{label}'")
    # should_NOT_contain: không được xuất hiện trong BẤT KỲ reply nào.
    # Khớp substring NGHIÊM NGẶT có chủ đích — phán xét ngữ nghĩa (trích dẫn, phủ định)
    # thuộc tầng 4 judge; cụm bị cấm trong seed phải viết ở dạng-khẳng-định
    # ("thì chắc chắn đậu", "rất mạnh") để bot trích-dẫn-từ-chối không dính oan.
    for bad in seed["should_NOT_contain"]:
        for i, reply in enumerate(replies, start=1):
            if contains_ci(reply, bad):
                failures.append(f"should_not_contain[lượt {i}]: lộ '{bad}'")
    # should_NOT_regex (tùy chọn): vi phạm nếu BẤT KỲ pattern khớp BẤT KỲ reply mới nào
    for pattern in seed.get("should_NOT_regex") or []:
        compiled = re.compile(pattern, re.IGNORECASE)
        for i, reply in enumerate(replies, start=1):
            if compiled.search(unicodedata.normalize("NFC", reply)):
                failures.append(f"should_not_regex[lượt {i}]: khớp '{pattern}'")
    return failures


def _failure_check_name(failure: str) -> str:
    """Rút tên check từ chuỗi failure ('persona[lượt 1]: ...' → 'persona')."""
    return failure.split(":", 1)[0].split("[", 1)[0].strip()


def _compute_gates(results: list) -> dict:
    """Gate tầng 2 (per-check ≥95% run) + gate tầng 3 (per-seed ≥2/3 lần lặp)."""
    total_runs = sum(len(r["runs"]) for r in results)
    check_rates = {}
    for name, _ in ALL_CHECKS:
        fail_runs = sum(
            1 for r in results for run in r["runs"]
            if any(_failure_check_name(f) == name for f in run["failures"])
        )
        check_rates[name] = round(1 - fail_runs / total_runs, 3) if total_runs else 1.0
    failing_checks = sorted(n for n, rate in check_rates.items() if rate < _CHECK_GATE_THRESHOLD)

    failing_seeds = []
    for r in results:
        n = len(r["runs"])
        k = sum(1 for run in r["runs"] if run["pass"])
        if n and (k / n) < _SEED_GATE_THRESHOLD:
            failing_seeds.append(r["seed_id"])

    return {
        "check_gate": {
            "threshold": _CHECK_GATE_THRESHOLD,
            "per_check_pass_rate": check_rates,
            "failing_checks": failing_checks,
            "pass": not failing_checks,
        },
        "seed_gate": {
            "threshold": round(_SEED_GATE_THRESHOLD, 3),
            "failing_seeds": failing_seeds,
            "pass": not failing_seeds,
        },
    }


def _print_table(results: list) -> None:
    id_width = max(len("seed_id"), max((len(r["seed_id"]) for r in results), default=0))
    header = f"{'seed_id':<{id_width}} | pass | failed checks"
    print(header)
    print("-" * len(header))
    for r in results:
        n_pass = sum(1 for run in r["runs"] if run["pass"])
        failed_names = sorted({_failure_check_name(f) for run in r["runs"] for f in run["failures"]})
        print(f"{r['seed_id']:<{id_width}} | {n_pass}/{len(r['runs'])}  | {', '.join(failed_names) or '—'}")


def _print_gates(gates: dict) -> None:
    check_gate = gates["check_gate"]
    seed_gate = gates["seed_gate"]
    print("\nPer-check pass rate (gate tầng 2 — mỗi check ≥95% run):")
    for name, rate in check_gate["per_check_pass_rate"].items():
        flag = "" if rate >= check_gate["threshold"] else "  ← DƯỚI NGƯỠNG"
        print(f"  {name}: {rate:.1%}{flag}")
    print("Gate tầng 2 (check ≥95%): " + ("ĐẠT" if check_gate["pass"]
          else "TRƯỢT — " + ", ".join(check_gate["failing_checks"])))
    print("Gate tầng 3 (seed pass ≥2/3 lần lặp): " + ("ĐẠT" if seed_gate["pass"]
          else "TRƯỢT — " + ", ".join(seed_gate["failing_seeds"])))


def _dry_run(seeds: list) -> int:
    """Validate schema toàn bộ seed + ALL_CHECKS trên reply mẫu + build thử fixture. Không gọi API trả phí."""
    exit_code = 0
    for seed in seeds:
        errors = _validate_seed(seed)
        if errors:
            exit_code = 1
            print(f"✗ {seed.get('id', '<không id>')}: " + "; ".join(errors))
    print(f"Schema: {len(seeds)} seed" + (" — OK" if exit_code == 0 else " — CÓ LỖI"))

    check_failures = []
    for name, fn in ALL_CHECKS:
        ok, detail = fn(_SAMPLE_REPLY)
        if not ok:
            check_failures.append(f"{name}: {detail}")
    if check_failures:
        exit_code = 1
        print("✗ Reply mẫu chuẩn persona không qua được check:")
        for f in check_failures:
            print(f"  {f}")
    else:
        print(f"Checks: {len(ALL_CHECKS)} check pass trên reply mẫu — OK")

    # Import api.ai + build thử 1 checklist fixture — bắt sớm lỗi import/thiếu file checklist
    try:
        from api.ai import generate_checklist
        fixture = generate_checklist({"employment_type": "employee"}, dict(_FIXTURE_DATES), "japan")
        if not fixture.get("items"):
            raise ValueError("checklist fixture rỗng")
        print("Fixture: import api.ai + build checklist japan/employee — OK")
    except Exception as exc:  # ImportError/FileNotFoundError/... đều làm dry-run fail
        exit_code = 1
        print(f"✗ Không import/build được checklist fixture: {exc}")
    return exit_code


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m tests.eval.run_eval",
        description="Eval tầng 2+3 cho AI surfaces của Visa Flow (regression seeds).")
    parser.add_argument("--surface", default="chat", choices=["chat"],
                        help="surface cần eval (đợt 1 chỉ có chat)")
    parser.add_argument("--repeat", type=_positive_int, default=3,
                        help="số lần lặp mỗi seed, ≥1 (Haiku non-deterministic; gate tầng 2 thật cần 20)")
    parser.add_argument("--dry-run", action="store_true",
                        help="chỉ validate schema + checks trên reply mẫu + build thử fixture, không gọi API trả phí")
    parser.add_argument("--scenarios", default=None, metavar="PATH",
                        help="file JSON kịch bản (mặc định scenarios/regression_seeds.json)")
    parser.add_argument("--out", default=None,
                        help="đường dẫn file JSON kết quả (mặc định docs/eval-baseline-<YYYYMMDD>.json; "
                             "với --scenarios tùy chọn: docs/eval-<tên file>-<YYYYMMDD>.json)")
    parser.add_argument("--only", default=None, metavar="SEED_ID",
                        help="chỉ chạy một seed theo id")
    args = parser.parse_args(argv)

    scenario_path = Path(args.scenarios) if args.scenarios else _SCENARIO_PATH
    if not scenario_path.is_file():
        print(f"Không tìm thấy file kịch bản: {scenario_path}")
        return 2
    seeds = _load_seeds(scenario_path)
    if args.only:
        seeds = [s for s in seeds if s.get("id") == args.only]
        if not seeds:
            print(f"Không tìm thấy seed id '{args.only}'")
            return 1

    if args.dry_run:
        return _dry_run(seeds)

    # Validate schema trước khi tốn tiền API
    schema_errors = [f"{s.get('id', '?')}: {e}" for s in seeds for e in _validate_seed(s)]
    if schema_errors:
        print("Schema lỗi, dừng trước khi gọi API:")
        for e in schema_errors:
            print(f"  ✗ {e}")
        return 1

    # Import muộn: --dry-run không cần API key; import api.ai kéo theo core.config (load .env)
    from api.ai import chat_with_haiku, generate_checklist
    from core.config import HAIKU

    results = []
    for seed in seeds:
        # Fixture hỏng ở 1 seed không được làm sập cả baseline trả phí — ghi lỗi rồi chạy tiếp
        try:
            checklist = _build_checklist_fixture(seed, generate_checklist) if seed["checklist"] else None
        except Exception as exc:
            results.append({"seed_id": seed["id"], "runs": [
                {"pass": False, "failures": [f"fixture_error: {exc}"], "transcript": []}
                for _ in range(args.repeat)
            ]})
            continue
        runs = []
        for _ in range(args.repeat):
            transcript, replies, error = _run_seed_once(seed, chat_with_haiku, checklist)
            failures = [error] if error else _score_run(seed, replies)
            runs.append({"pass": not failures, "failures": failures, "transcript": transcript})
        results.append({"seed_id": seed["id"], "runs": runs})

    total_runs = sum(len(r["runs"]) for r in results)
    pass_runs = sum(1 for r in results for run in r["runs"] if run["pass"])
    check_fail_counts = {}
    for r in results:
        for run in r["runs"]:
            for f in run["failures"]:
                name = _failure_check_name(f)
                check_fail_counts[name] = check_fail_counts.get(name, 0) + 1
    gates = _compute_gates(results)

    report = {
        "meta": {
            "date": datetime.now().isoformat(timespec="seconds"),
            "surface": args.surface,
            "repeat": args.repeat,
            "model": HAIKU,
            "scenarios": str(scenario_path),
            "note": "Eval tầng 2+3 trên bộ kịch bản trong meta.scenarios (xem docs/eval-plan.md)",
        },
        "results": results,
        "summary": {
            "per_seed": {
                r["seed_id"]: {"pass": sum(1 for run in r["runs"] if run["pass"]), "total": len(r["runs"])}
                for r in results
            },
            "check_fail_counts": check_fail_counts,
            "gates": gates,
            "overall": {
                "pass_runs": pass_runs,
                "total_runs": total_runs,
                "pass_rate": round(pass_runs / total_runs, 3) if total_runs else 0.0,
            },
        },
    }

    # --out mặc định: bộ regression giữ tên baseline lịch sử; bộ khác lấy theo tên file kịch bản.
    # Riêng --only không kèm --out: CHỈ in console — kết quả một seed không được ghi đè baseline.
    if args.out:
        out_path = Path(args.out)
    elif args.only:
        out_path = None
    elif args.scenarios:
        out_path = _REPO_ROOT / "docs" / f"eval-{scenario_path.stem}-{datetime.now():%Y%m%d}.json"
    else:
        out_path = _REPO_ROOT / "docs" / f"eval-baseline-{datetime.now():%Y%m%d}.json"
    if out_path is not None:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

    _print_table(results)
    if total_runs:
        print(f"\nTổng: {pass_runs}/{total_runs} run pass ({pass_runs / total_runs:.1%})")
    _print_gates(gates)
    if args.repeat < 20:
        print(f"Lưu ý: --repeat {args.repeat} < 20 — gate chỉ mang tính chỉ báo, dùng --repeat 20 cho gate chuẩn.")
    if out_path is not None:
        print(f"Kết quả ghi vào: {out_path}")
    else:
        print("(--only không kèm --out: chỉ in console, không ghi JSON)")
    return 0 if gates["check_gate"]["pass"] and gates["seed_gate"]["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
