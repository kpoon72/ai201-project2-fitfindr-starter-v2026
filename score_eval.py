#!/usr/bin/env python3
"""
Score a run_eval.py run against criteria.md, PASS/FAIL per try, with reasons.

    python score_eval.py                        the newest results/run_*.json
    python score_eval.py results/run_X.json     a specific run

Each check below is written to match the wording in criteria.md as it was
filed in unit 3. When a check needs a judgement the criterion doesn't settle,
the comment says so.

The size check for criterion 5 deliberately does NOT reuse the size matcher in
tools.py. Checking a function with itself would always pass. The allowed sizes
are written out by hand from data/listings.json and the rule in the README.
"""

import json
import re
import sys
from pathlib import Path

RESULTS = Path(__file__).parent / "results"

ONE_SIZE = {"One Size", "One Size (adjustable)", "One Size / Oversized"}

# Criterion 5: what each fixed query should parse to, and the listing sizes in
# the data that the README's size rule allows for it ("One Size" matches any).
C5_EXPECT = {
    "vintage graphic tee under $30": {"max_price": 30.0, "size": None, "sizes": None},
    "90s track jacket in size M": {"max_price": None, "size": "M",
                                   "sizes": {"M", "S/M", "M/L"} | ONE_SIZE},
    "platform sneakers size 8": {"max_price": None, "size": "8",
                                 "sizes": {"US 8"} | ONE_SIZE},
    "denim jacket under $50": {"max_price": 50.0, "size": None, "sizes": None},
    "jeans size W28 under $35": {"max_price": 35.0, "size": "W28",
                                 "sizes": {"W28"} | ONE_SIZE},
}

# Criterion 2: phrases that name a specific change. These are the four advice
# lines explain_empty() can produce. "No listings matched" alone is not one.
C2_ADVICE = ("Drop the size", "Raise or remove the", "Drop both the size",
             "Try broader words")


def _price_pattern(price: float) -> re.Pattern:
    whole = f"{price:.0f}"
    return re.compile(rf"\$\s?{whole}(?:\.00)?(?!\d)")


def _sentences(card: str) -> list[str]:
    """2-4 sentences, ignoring hashtags and emoji (criterion 4a)."""
    text = re.sub(r"#\w+", " ", card)
    text = re.sub(r"\$\d+\.\d\d", "$N", text)   # "$24.00" isn't a sentence break
    parts = re.split(r"[.!?]+", text)
    return [p.strip() for p in parts if re.search(r"[A-Za-z]", p)]


def _first_sentence(card: str) -> str:
    match = re.search(r"^.*?[.!?](?=\s|$)", card.strip(), re.S)
    return (match.group(0) if match else card).strip()


def _done(session) -> str | None:
    """None when the run completed with a fit card, else the reason it didn't."""
    if session is None:
        return "crashed"
    if session.get("error"):
        return f"stopped: {session['error'][:90]}"
    if not (session.get("fit_card") or "").strip():
        return "no fit card"
    return None


# ── one check per criterion ───────────────────────────────────────────────────

def check_1(session):
    problem = _done(session)
    return (problem is None, problem or "all three tools ran, fit card returned")


def check_2(session):
    if session is None:
        return False, "crashed"
    ran = session.get("steps_run") or []
    if "suggest_outfit" in ran or session.get("outfit_suggestion") is not None:
        return False, "suggest_outfit was called"
    if session.get("fit_card") is not None:
        return False, "fit_card is not None"
    message = session.get("error") or ""
    if not any(phrase in message for phrase in C2_ADVICE):
        return False, f"message names no change: {message[:80]!r}"
    return True, "stopped before suggest_outfit; " + message.split(". ", 1)[1][:70]


def check_3(session):
    problem = _done(session)
    if problem:
        return False, problem
    ids = (
        session["search_results"][0]["id"],
        session["selected_item"]["id"],
        session.get("outfit_input_id"),
    )
    if len(set(ids)) != 1:
        return False, f"ids differ: search[0]={ids[0]} selected={ids[1]} into outfit={ids[2]}"
    price = session["selected_item"]["price"]
    if not _price_pattern(price).search(session["fit_card"]):
        return False, f"ids match ({ids[0]}) but fit card lacks ${price:.0f}"
    return True, f"{ids[0]} at all three; card has ${price:.0f}"


def check_4(session):
    problem = _done(session)
    if problem:
        return False, problem
    card = session["fit_card"]
    item = session["selected_item"]
    fails = []
    n = len(_sentences(card))
    if not 2 <= n <= 4:
        fails.append(f"(a) {n} sentences")
    if len(card) > 400:
        fails.append(f"(b) {len(card)} chars")
    if not _price_pattern(item["price"]).search(card):
        fails.append(f"(c) no ${item['price']:.0f}")
    if item["platform"].lower() not in card.lower():
        fails.append(f"(d) no '{item['platform']}'")
    if fails:
        return False, "; ".join(fails)
    return True, f"{n} sentences, {len(card)} chars, price and platform present"


def check_5(session, query):
    if session is None:
        return False, "crashed"
    expect = C5_EXPECT[query]
    parsed = session.get("parsed") or {}
    if parsed.get("max_price") != expect["max_price"] or parsed.get("size") != expect["size"]:
        return False, f"parsed {parsed}"
    bad = []
    for listing in session.get("search_results") or []:
        if expect["max_price"] is not None and listing["price"] > expect["max_price"]:
            bad.append(f"{listing['id']} ${listing['price']:.0f}")
        if expect["sizes"] is not None and listing["size"] not in expect["sizes"]:
            bad.append(f"{listing['id']} size {listing['size']}")
    if bad:
        return False, "violations: " + ", ".join(bad)
    n = len(session.get("search_results") or [])
    return True, f"{n} results, 0 violations"


# ── reading a run ─────────────────────────────────────────────────────────────

def score(path: Path) -> None:
    rows = json.loads(path.read_text(encoding="utf-8"))
    by_criterion: dict[int, list] = {}
    for row in rows:
        number = row["scenario"].get("criterion")
        if number:
            by_criterion.setdefault(number, []).append(row)

    print(f"Scoring {path.name}\n")
    table = []

    for number in (1, 2, 3, 4):
        row = by_criterion[number][0]
        check = globals()[f"check_{number}"]
        results = [check(t["session"]) for t in row["tries"]]
        print(f"Criterion {number} — {row['scenario']['query']!r}")
        for i, (ok, why) in enumerate(results, 1):
            print(f"  try {i}: {'PASS' if ok else 'FAIL'} — {why}")
        passes = sum(ok for ok, _ in results)
        extra = ""
        if number == 4:
            firsts = [_first_sentence(t["session"]["fit_card"]) for t in row["tries"]
                      if t["session"] and t["session"].get("fit_card")]
            dupes = {f for f in firsts if firsts.count(f) > 1}
            print(f"  first sentences: {len(set(firsts))} distinct of {len(firsts)}")
            if dupes:
                print(f"  shared first sentence: {sorted(dupes)}")
            extra = "dupes" if dupes else ""
        need = 4 if number in (1, 4) else 5
        met = passes >= need and not extra
        verdict = f"{'MET' if met else 'MISSED'} ({passes}/5)"
        if extra:
            verdict += ", shared first sentence"
        print(f"  → {verdict}\n")
        table.append((number, f"{need} of 5", ["PASS" if ok else "FAIL" for ok, _ in results], verdict))

    # Criterion 5: each of the five queries is one try. Every query was run
    # five times; a query passes only if all five of its runs pass, since the
    # search has no model in it and should not vary.
    print("Criterion 5 — five fixed queries, each run 5 times")
    cells = []
    for row in by_criterion[5]:
        query = row["scenario"]["query"]
        results = [check_5(t["session"], query) for t in row["tries"]]
        ok = all(r[0] for r in results)
        reasons = {why for _, why in results}
        print(f"  {query!r}: {'PASS' if ok else 'FAIL'} — {sum(r[0] for r in results)}/5 runs clean; {'; '.join(sorted(reasons))}")
        cells.append("PASS" if ok else "FAIL")
    passes = cells.count("PASS")
    verdict = f"{'MET' if passes == 5 else 'MISSED'} ({passes}/5)"
    print(f"  → {verdict}\n")
    table.append((5, "5 of 5", cells, verdict))

    names = {
        1: "Matching query completes all three tools",
        2: "Impossible query stops before suggest_outfit",
        3: "Same item at every step of the session",
        4: "Fit card: 2-4 sentences, ≤400 chars, price, platform",
        5: "Search respects price and size (5 queries)",
    }
    print("| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |")
    print("|---|---|---|---|---|---|---|---|")
    for number, target, cells, verdict in table:
        print(f"| {number}. {names[number]} | {target} | {' | '.join(cells)} | {verdict} |")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        target = Path(sys.argv[1])
    else:
        runs = sorted(RESULTS.glob("run_*.json"))
        if not runs:
            sys.exit("No results/run_*.json yet. Run `python run_eval.py --label before` first.")
        target = runs[-1]
    score(target)
