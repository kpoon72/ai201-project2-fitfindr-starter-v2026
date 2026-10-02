# FitFindr

> ### 👋 Start here
>
> **New to this repo? Read [RUNNING.md](RUNNING.md) first** — setup, every
> command, and what to do when something breaks.
>
> Once `python test.py` passes:
>
> ```bash
> python app.py listings --full -n 6      # read the data (Milestone 1)
> python app.py fields                    # what you can filter on
> python app.py ask 'vintage graphic tee under $30'
> ```
>
> All three tools are stubs, so that last command will do nothing useful yet.
> That's the starting position.
>
> **The rest of this file is your submission.** Fill it in as you go.

---

<!-- ─────────────────────────────────────────────────────────────────────────
     HOW TO USE THIS FILE

     This is your submission. Fill each section in as you finish the milestone
     it belongs to — don't leave it all to the end.

     Unit 3 asks for the first five sections. Unit 4 adds the five below them.
     Leave the unit 4 sections alone until then; they're here so you know
     what's coming.

     Everything is pasted as TEXT. No screenshots, no images, no video links.
     A typed block of output gets full credit; a picture of the same output
     gets none.
     ───────────────────────────────────────────────────────────────────────── -->

<!-- ═══════════════════════ UNIT 3 — THE BUILD ═══════════════════════ -->

## Data Notes

What I found reading `data/listings.json` and `data/wardrobe_schema.json`
(Milestone 1), before writing any tool.

- **Listing fields:** `id`, `title`, `description`, `category`, `style_tags`
  (list), `size`, `condition`, `price` (float), `colors` (list), `brand`
  (str or None), `platform`.
- **40 listings.** Categories: tops 15, bottoms 10, outerwear 8, shoes 4,
  accessories 3. Platforms: depop, thredUp, poshmark.
- **`brand` is None on 32 of 40**, so nothing may assume a brand exists.
- **Sizes are not one system.** Letter sizes (`S`, `M`, `L/XL`, `S/M`),
  annotated letters (`XL (oversized)`), waist sizes (`W28`, `W30 L30`), shoe
  sizes (`US 8.5`) and `One Size` variants. A substring test is wrong here:
  `"s" in "us 9"` and `"l" in "xl"` are both True.
- **Prices** run $12–$75, all floats.
- **Wardrobe item fields:** `id`, `name`, `category`, `colors`, `style_tags`,
  `notes` (sometimes null). A wardrobe is `{"items": [...]}`; the empty wardrobe is
  `{"items": []}` — same shape, empty list.

---

## What This Does

<!-- Three or four sentences: what a user asks for, and what they get back. -->



---

## Tool Inventory

<!-- Four lines per tool. This is worth 2 points and it's the single most
     common place students lose them.

     "Returns a list" earns NOTHING. The description has to say what is IN
     the list.

     The empty case isn't optional either — it's the thing your loop branches
     on, and if you don't decide it here you'll discover it as a crash in
     Milestone 5. -->

### `search_listings`

- **What it does:** Filters `data/listings.json` by price ceiling and size,
  then ranks what's left by how many of the description's keywords appear in
  each listing's title, style tags, category, colors and description. It makes
  no model call.
- **Inputs:**
  - `description` (str): keywords like `"vintage graphic tee"`. Matching
    ignores case and stopwords ("a", "in", "for"…), and a trailing plural "s"
    is dropped, so "tees" matches "tee".
  - `size` (str | None): `None` skips the size filter. Otherwise both the
    query size and the listing size are split into size tokens on `/`,
    spaces and parentheses (`"S/M"` → `{S, M}`; `"US 8.5"` → `{8.5}`;
    `"W30 L30"` → `{W30, 30, L30}`). A listing matches if the two token sets
    share a whole token, so `M` matches `S/M` and `M/L` but not `XL`, and `8`
    matches `US 8` but not `US 8.5`. Listings sized `One Size` match any size.
  - `max_price` (float | None): an inclusive ceiling. `None` skips the price
    filter.
- **Returns:** A `list[dict]` of at most `config.SEARCH_RESULT_LIMIT` (10)
  listing dicts, best keyword score first. Ties keep data-file order. Each
  dict is the full listing, unchanged: `id`, `title`, `description`,
  `category`, `style_tags` (list), `size`, `condition`, `price` (float),
  `colors` (list), `brand` (str or None), `platform`. A listing with a keyword
  score of 0 is never returned.
- **When it has nothing:** `[]`, an empty list. It never returns `None` and
  never raises, including when `description` is empty or has only stopwords.

### `suggest_outfit`

- **What it does:** Asks the model, through `generate()`, for one or two
  outfits built around the new item. When the wardrobe has items, each outfit
  names pieces the user already owns.
- **Inputs:**
  - `new_item` (dict): one listing dict, in the shape `search_listings`
    returns.
  - `wardrobe` (dict): `{"items": [ {id, name, category, colors, style_tags,
    notes}, … ]}`. `items` may be an empty list.
- **Returns:** A non-empty `str` of plain text, one or two outfit ideas of a
  few lines each. With a wardrobe, every outfit refers to at least one
  wardrobe item by its `name`.
- **When it has nothing:** If `wardrobe["items"]` is empty or missing, it
  still returns a non-empty `str`: general styling ideas for the item (what
  kinds of pieces pair with it), with no owned pieces named. It never returns
  `""` and never raises for an empty wardrobe.

### `create_fit_card`

- **What it does:** Asks the model, through `generate()`, for a short social
  post caption about the find and the outfit.
- **Inputs:**
  - `outfit` (str): the text `suggest_outfit` returned.
  - `new_item` (dict): the same listing dict that went into `suggest_outfit`.
- **Returns:** A `str` caption of two to four sentences. It mentions the
  item's title (or a clear short form of it), its price as `$NN` and its
  platform, each once. It reads like a post, not a product listing, so it may
  include emoji and hashtags. It never mentions a brand when `brand` is None.
- **When it has nothing:** If `outfit` is empty or only whitespace, it returns
  the string `"Can't write a fit card: no outfit suggestion was provided."`
  without calling the model. It never returns `""` and never raises.

---

## Planning Loop

<!-- Your branch rule, stated as a rule — the condition AND both paths — plus
     the file and function that holds it.

     Like this:
       "If search_listings returns an empty list, put a message in the session
        and stop. Otherwise take the first result and go to suggest_outfit."
        — agent.py::run_agent

     The grader checks your code against what you claim here, so the file and
     function have to be real. -->

**Branch rule:** If `search_listings` returns an empty list, the loop writes
a message to `session["error"]` and returns the session without calling
`suggest_outfit` or `create_fit_card`. The message names the query's filters
and the specific change that would bring back results. Otherwise it takes the
first result as `session["selected_item"]` and goes to `suggest_outfit`.

To find that specific change, the empty branch re-runs `search_listings`
(no model call) with one filter dropped at a time: no size, no price
ceiling, then only the first keyword. It reports which relaxation would
return listings, e.g. *"Nothing in size XXS — 3 listings match without the
size filter."* If no single relaxation helps, it says so and suggests broader
words, giving the cheapest price in the data.

**Where it lives:** `agent.py::run_agent`

**How the query is parsed:** Regex, with no model call.
- `max_price`: `under $30`, `below 30`, `less than $30`, `max $30`,
  `<$30`, or a bare `$30`. The number becomes a float.
- `size`: `size M`, `size 8`, `in size M/L`, `size W30`.
- `description`: whatever is left after removing those phrases and filler
  like "looking for", "I want" and "a".

**What moves through the session:**
1. `query`: the raw text.
2. `parsed`: `{description, size, max_price}` from the regex.
3. `search_results`: the list `search_listings` returned.
4. Branch on `search_results`. If it's empty, set `error` and stop.
5. `selected_item`: `search_results[0]`.
6. `outfit_suggestion`: from `suggest_outfit(session["selected_item"],
   session["wardrobe"])`.
7. `fit_card`: from `create_fit_card(session["outfit_suggestion"],
   session["selected_item"])`.

Each tool reads its inputs from the session, not from a local variable, so
the item that reached `suggest_outfit` is by construction the one in
`session["selected_item"]`.

---

## Sample Run

<!-- Two things go here.

     1. One FULL query and its output, pasted as text.
     2. Your three per-tool terminal tests — the command and what it printed. -->

**One full query**

```
$ python app.py ask '...'

```

**The three tools, tested one at a time**

```
$ python -c "from tools import search_listings; print(search_listings('graphic tee', max_price=30))"

```

```
$ python -c "from tools import suggest_outfit; ..."

```

```
$ python -c "from tools import create_fit_card; ..."

```

---

## How I Used AI

<!-- Two specific moments. What you asked, what came back, what you changed.

     "I used Claude to help me code" is not enough.

     "I gave Claude my search_listings spec. It returned None on no match
     instead of an empty list, so I changed it" is the level we want. -->

**Moment 1**

- *What I asked for:*
- *What came back:*
- *What I changed:*

**Moment 2**

- *What I asked for:*
- *What came back:*
- *What I changed:*

<!-- ═══════════════════════ UNIT 4 — THE TEST ═══════════════════════

     Don't fill these in during unit 3.
     ═══════════════════════════════════════════════════════════════════ -->

---

## Run Log — Before

<!-- Five criteria, five tries each, in this exact format.

     Five, because your criteria are written out of five. Mark each try PASS
     or FAIL, count the passes, and read that count against your target — a
     row targeting 4 of 5 with three PASS cells is MISSED (3/5).

     `python run_eval.py --label before` runs everything and writes the table
     into results/. Paste it here and fill in the verdicts. -->

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1.  |  |  |  |  |  |  |  |
| 2.  |  |  |  |  |  |  |  |
| 3.  |  |  |  |  |  |  |  |
| 4.  |  |  |  |  |  |  |  |
| 5.  |  |  |  |  |  |  |  |

**Real output from one try**, pasted as text, naming the file and function
that produced it:

```

```

---

## Verdicts and Diagnoses

<!-- MET or MISSED per criterion against LAST UNIT's target, plus a sentence on
     how you decided.

     Then, for every miss: which of the four places it happened — a tool, the
     loop's branch, the session, or the model's output — AND the mechanism.

     Not a diagnosis:  "The fit card was bad."
     A diagnosis:      "The fit card criterion missed on 2 of 5 items. Both had
                        an empty brand field. My prompt puts the brand in the
                        first sentence, so the card opened with a blank and read
                        like a fragment. The tool worked; the prompt assumed a
                        field that isn't always there."

     Look for a pattern. Three misses on the same tool is one problem, not
     three. -->

| # | Criterion | Target | Verdict | How I decided |
|---|---|---|---|---|
| 1 |  |  |  |  |
| 2 |  |  |  |  |
| 3 |  |  |  |  |
| 4 |  |  |  |  |
| 5 |  |  |  |  |

**Diagnoses**



---

## Loop Trace

<!-- One full run, printed step by step, with the MCP call visible in it.

     `python app.py ask '...' --trace` once you've added the trace.step()
     calls in Milestone 2.

     Worth pasting BOTH the happy path and the empty-search path. The empty
     one should be visibly shorter, because it stops. If your two traces are
     the same length, your branch isn't working — and this is the fastest way
     anyone will ever find that out. -->

**Happy path**

```

```

**Empty search**

```

```

**On the MCP move:** <!-- what changed in your code, and whether anything
behaved differently afterwards. If the rewire didn't work, say exactly where it
broke — the error text and the last thing that worked. That earns the point in
full. -->



---

## The Improvement

<!-- What you changed, why your diagnosis pointed at it, and the after-run in
     the same table format. One change, measured properly.

     `python run_eval.py --label after` -->

**What I changed:**

**Which failure it was meant to fix:**

### Run Log — After

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1.  |  |  |  |  |  |  |  |
| 2.  |  |  |  |  |  |  |  |
| 3.  |  |  |  |  |  |  |  |
| 4.  |  |  |  |  |  |  |  |
| 5.  |  |  |  |  |  |  |  |

**Did it help, and how do I know:**

<!-- If it made things worse, say that. Honestly reported, that earns full
     credit and is more interesting than one that worked. -->



---

## What's Still Broken

<!-- For each criterion still missed: what you'd do, and why you stopped where
     you did. "I ran out of time" is fine if it's true. Pretending nothing is
     left is not. -->



<!-- ═════════════════════════════════════════════════════════════════════

     SUBMISSION CHECKLIST — unit 3

       [ ] criteria.md has five numbered criteria, each with a target
       [ ] Each criterion has a reason underneath it
       [ ] All five unit 3 sections above have real content
       [ ] Tool Inventory: all three tools, inputs WITH TYPES, a specific
           return value, and the empty case
       [ ] Planning Loop names the branch rule and agent.py::run_agent
       [ ] Sample Run: one full query plus the three per-tool tests, as text
       [ ] At least four new commits
       [ ] Repository URL submitted — WRITE IT DOWN, you submit the same one
           next unit

     SUBMISSION CHECKLIST — unit 4

       [ ] mcp_server.py exists with one tool registered
           (or a written record of exactly where the rewire broke)
       [ ] Run Log — Before, five criteria, five tries each
       [ ] Real output pasted underneath, naming file and function
       [ ] A verdict on every criterion
       [ ] A diagnosis for every miss, naming a place AND a mechanism
       [ ] Loop Trace, with the MCP call visible in it
       [ ] All three failure modes triggered and handled
       [ ] One improvement, with Run Log — After in the same format
       [ ] What's Still Broken
       [ ] At least four new commits
       [ ] The SAME repository URL as last unit

     Do not delete and recreate this repository. Your commit history is what
     shows your criteria existed before your results did.
     ═════════════════════════════════════════════════════════════════════ -->

---

📖 **How to run this project: [RUNNING.md](RUNNING.md)**
