"""
The FitFindr planning loop.

This is the file that makes FitFindr an agent rather than a script. It decides
which tool to run next based on what the last one returned.

If your loop calls all three tools no matter what comes back, you have a list
of function calls. A loop looks at the last result before it picks the next
step. **That branch is the graded part of this unit.**

Build and test your three tools in `tools.py` first. Then come here.

    python agent.py          runs both example paths below
"""

import re

import config
import trace
from tools import search_listings, suggest_outfit, create_fit_card
from generate import ModelUnavailable


# ── session state ─────────────────────────────────────────────────────────────

def new_session(query: str, wardrobe: dict) -> dict:
    """
    A fresh session for one user interaction.

    The session is the single source of truth for a run. Every tool result goes
    in here, and the next tool reads it back out.

    You could pass values straight from one call to the next. It would work,
    and you would not be able to test it — you can't print a variable you have
    already overwritten. Going through the session is what makes the state
    visible, and unit 4 has you write a criterion about exactly that.

    Add fields if you need them.
    """
    return {
        "query": query,              # what the user typed
        "parsed": {},                # description / size / max_price you pulled out of it
        "search_results": [],        # everything search_listings returned
        "selected_item": None,       # the one you chose — goes into suggest_outfit
        "wardrobe": wardrobe,        # the user's wardrobe
        "outfit_suggestion": None,   # what suggest_outfit returned
        "fit_card": None,            # what create_fit_card returned
        "error": None,               # set when the run ended early
        "outfit_input_id": None,     # id of the item actually passed to suggest_outfit (criterion 3)
        "steps_run": [],             # each step in the order the loop chose it
    }


# ── parsing the query ─────────────────────────────────────────────────────────

_PRICE = re.compile(
    r"(?:under|below|less than|max|<)\s*\$?\s*(\d+(?:\.\d+)?)|\$(\d+(?:\.\d+)?)",
    re.IGNORECASE,
)
_SIZE = re.compile(r"\b(?:in\s+)?size\s+([A-Za-z0-9./]+)", re.IGNORECASE)
_FILLER = re.compile(
    r"\b(?:i'?m|i|am|looking|for|want|need|some|something|a|an|the|in|"
    r"please|find|me)\b",
    re.IGNORECASE,
)


def parse_query(query: str) -> dict:
    """
    Pull description, size and max_price out of plain text, with regex.

    "vintage graphic tee under $30, size M"
        -> {"description": "vintage graphic tee", "size": "M", "max_price": 30.0}
    """
    max_price = None
    price = _PRICE.search(query)
    if price:
        max_price = float(price.group(1) or price.group(2))
        query = query[: price.start()] + " " + query[price.end():]

    size = None
    size_match = _SIZE.search(query)
    if size_match:
        size = size_match.group(1).upper()
        query = query[: size_match.start()] + " " + query[size_match.end():]

    description = _FILLER.sub(" ", query)
    description = " ".join(re.sub(r"[^\w\s'/-]", " ", description).split())
    return {"description": description, "size": size, "max_price": max_price}


# ── the empty-search message ──────────────────────────────────────────────────

def explain_empty(parsed: dict) -> str:
    """
    Say what the user could change, not just that nothing came back.

    Re-runs search_listings (no model call) with one filter relaxed at a time
    and reports which relaxation would have found something.
    """
    desc, size, price = parsed["description"], parsed["size"], parsed["max_price"]

    asked = f"'{desc}'" if desc else "your search"
    if size:
        asked += f" in size {size}"
    if price is not None:
        asked += f" under ${price:.0f}"
    lead = f"No listings matched {asked}."

    if not desc:
        return (
            f"{lead} I couldn't find any item words in the query. "
            "Say what you're looking for, e.g. 'denim jacket under $50'."
        )

    tries = []
    if size:
        tries.append((f"drop the size {size}", dict(description=desc, size=None, max_price=price)))
    if price is not None:
        tries.append((f"raise or remove the ${price:.0f} limit", dict(description=desc, size=size, max_price=None)))
    if size and price is not None:
        tries.append(("drop both the size and the price limit", dict(description=desc, size=None, max_price=None)))

    for advice, kwargs in tries:
        found = search_listings(**kwargs)
        if found:
            cheapest = min(item["price"] for item in found)
            top = found[0]
            return (
                f"{lead} {advice[0].upper() + advice[1:]} and you'd get "
                f"{len(found)} listing(s), starting at ${cheapest:.0f}. "
                f"Best match: {top['title']} (${top['price']:.0f}, size {top['size']})."
            )

    from utils.data_loader import load_listings
    floor = min(item["price"] for item in load_listings())
    return (
        f"{lead} Nothing in the data matches the words '{desc}' even without "
        f"filters. Try broader words like 'jacket', 'jeans', 'tee' or "
        f"'dress'. Prices in the data start at ${floor:.0f}."
    )


# ── planning loop ─────────────────────────────────────────────────────────────

def run_agent(query: str, wardrobe: dict) -> dict:
    """
    Run the loop once and return the finished session.

    Args:
        query:    what the user asked for, in plain language
                  (e.g. "vintage graphic tee under $30, size M").
        wardrobe: a wardrobe dict — get_example_wardrobe() or
                  get_empty_wardrobe() from utils/data_loader.py.

    Returns:
        The session dict. **Check session["error"] first** — if it isn't None,
        the run ended early and the later fields will still be None.

    ─────────────────────────────────────────────────────────────────────────
    TODO — build this, following the branch rule you wrote in Milestone 2.

      1. Start a session with new_session().

      2. Count the times round the loop, and call trace.check_iterations(count)
         on each one before you go again. It raises when the count passes
         MAX_ITERATIONS in config.py — see trace.py.

      3. Parse the query into a description, a size, and a max_price. Regex,
         string splitting, or asking the model are all fine — say which you
         chose in your README. Put the result in session["parsed"].

      4. Call search_listings() with what you parsed.
         Put the results in session["search_results"].

         ⚠️ THIS IS THE BRANCH. If nothing came back:
              - put a message in session["error"] saying what the user could
                change — "No results" is not that message
              - return the session
              - do NOT call suggest_outfit with nothing

      5. Choose an item — the first result is fine. Put it in
         session["selected_item"].

      6. Call suggest_outfit() with the selected item and the wardrobe.
         Put the result in session["outfit_suggestion"].

      7. Call create_fit_card() with the outfit and the item.
         Put the result in session["fit_card"].

      8. Return the session.

    ─────────────────────────────────────────────────────────────────────────
    IN UNIT 4 you come back and add two things:

      • Trace calls. One per step. `trace.step("search_listings", inputs=...,
        returned=...)` — see trace.py. Your README needs the output.

      • A handler for ModelUnavailable, so a bad key produces a message rather
        than a stack trace. The import is already at the top of this file.
    """
    session = new_session(query, wardrobe)

    count = 0
    while True:
        count += 1
        trace.check_iterations(count)

        step = _next_step(session)
        session["steps_run"].append(step)

        if step == "done":
            return session

        if step == "parse":
            session["parsed"] = parse_query(session["query"])

        elif step == "search":
            parsed = session["parsed"]
            session["search_results"] = search_listings(
                parsed["description"], parsed["size"], parsed["max_price"]
            )

        elif step == "stop_empty":
            # THE BRANCH: nothing found, so say what to change and stop here.
            session["error"] = explain_empty(session["parsed"])
            return session

        elif step == "select":
            session["selected_item"] = session["search_results"][0]

        elif step == "suggest_outfit":
            item = session["selected_item"]
            session["outfit_input_id"] = item["id"]
            session["outfit_suggestion"] = suggest_outfit(item, session["wardrobe"])

        elif step == "create_fit_card":
            session["fit_card"] = create_fit_card(
                session["outfit_suggestion"], session["selected_item"]
            )


def _next_step(session: dict) -> str:
    """Pick the next step from what's in the session so far."""
    if "parse" not in session["steps_run"]:
        return "parse"
    if "search" not in session["steps_run"]:
        return "search"
    if not session["search_results"]:
        return "stop_empty"
    if session["selected_item"] is None:
        return "select"
    if session["outfit_suggestion"] is None:
        return "suggest_outfit"
    if session["fit_card"] is None:
        return "create_fit_card"
    return "done"


# ── running it directly ───────────────────────────────────────────────────────

def _show(session: dict) -> None:
    if session["error"]:
        print(f"  stopped: {session['error']}")
        print(f"  fit_card is {session['fit_card']!r} — it should still be None here")
        return

    item = session["selected_item"] or {}
    print(f"  found:    {item.get('title')} — ${item.get('price')} on {item.get('platform')}")
    print(f"  outfit:   {session['outfit_suggestion']}")
    print(f"  fit card: {session['fit_card']}")


if __name__ == "__main__":
    from utils.data_loader import get_example_wardrobe

    print("=== A query the data can match ===")
    _show(run_agent(
        query="looking for a vintage graphic tee under $30",
        wardrobe=get_example_wardrobe(),
    ))

    print("\n=== A query it can't ===")
    _show(run_agent(
        query="designer ballgown size XXS under $5",
        wardrobe=get_example_wardrobe(),
    ))

    print(
        "\nThe second one should stop before the fit card. If both paths look "
        "the same,\nthe branch isn't doing anything yet."
    )
