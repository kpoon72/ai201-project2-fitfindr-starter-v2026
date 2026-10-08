"""
The runs your test needs. ← UNIT 4, MILESTONE 3

Each of your five criteria needs something run against it. A criterion about
the empty-search branch needs an impossible query. One about the fit card needs
the same item run more than once. Working that out is Milestone 3's first step,
and this file is where you write it down.

`run_eval.py` runs everything here five times and writes the run log — five
because your criteria are written out of five.

Three scenarios are filled in to show the shape. Add or change whatever your
own criteria need — these are a starting point, not a fixed set.
"""

SCENARIOS = [
    {
        # A query the data can match. Criterion 1.
        "name": "matching query completes",
        "query": "vintage graphic tee under $30",
        "wardrobe": "example",
        "criterion": 1,
    },
    {
        # A query nothing can match. Criterion 2 — the branch.
        "name": "impossible query stops early",
        "query": "designer ballgown size XXS under $5",
        "wardrobe": "example",
        "criterion": 2,
    },
    {
        # A user with nothing saved. One of unit 4's three failure modes.
        "name": "empty wardrobe",
        "query": "denim jacket under $50",
        "wardrobe": "empty",
        "criterion": None,
    },
    {
        # Criterion 3 — state. Any completing query works; what's checked is
        # whether the same listing id is in search_results[0], selected_item
        # and outfit_input_id, and whether the fit card carries its price.
        "name": "state carries the same item",
        "query": "90s track jacket in size M",
        "wardrobe": "example",
        "criterion": 3,
    },
    {
        # Criterion 4 — the fit card. The SAME query five times, so the five
        # cards can be compared with each other (shared first sentence).
        "name": "fit card facts and length",
        "query": "silk slip dress in midi length under $40",
        "wardrobe": "example",
        "criterion": 4,
    },
    # Criterion 5 — search respects price and size. Criterion 5 names five
    # fixed queries, and each query is one of its five tries. run_eval runs
    # every scenario five times, so each query also gets checked five times.
    {
        "name": "filters: tee under $30",
        "query": "vintage graphic tee under $30",
        "wardrobe": "example",
        "criterion": 5,
    },
    {
        "name": "filters: track jacket size M",
        "query": "90s track jacket in size M",
        "wardrobe": "example",
        "criterion": 5,
    },
    {
        "name": "filters: sneakers size 8",
        "query": "platform sneakers size 8",
        "wardrobe": "example",
        "criterion": 5,
    },
    {
        "name": "filters: denim jacket under $50",
        "query": "denim jacket under $50",
        "wardrobe": "example",
        "criterion": 5,
    },
    {
        "name": "filters: jeans W28 under $35",
        "query": "jeans size W28 under $35",
        "wardrobe": "example",
        "criterion": 5,
    },
]

WARDROBES = ("example", "empty")


def validate() -> list[str]:
    """Complain about anything malformed, before a long run rather than during."""
    problems = []
    for i, scenario in enumerate(SCENARIOS, 1):
        if not scenario.get("query", "").strip():
            problems.append(f"scenario {i} has no query")
        if scenario.get("wardrobe") not in WARDROBES:
            problems.append(
                f"scenario {i} has wardrobe {scenario.get('wardrobe')!r} — "
                f"it should be one of {WARDROBES}"
            )
    return problems
