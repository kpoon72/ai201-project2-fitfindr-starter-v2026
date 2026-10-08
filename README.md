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

FitFindr takes a plain-language thrift request, like
`'vintage graphic tee under $30, size M'`, and searches 40 secondhand
listings from Depop, ThredUp and Poshmark for the best match within that
price and size. It then suggests one or two outfits pairing the find with
pieces from the user's saved wardrobe, or gives general styling ideas if the
wardrobe is empty, and writes a short caption the user could actually post.
If nothing matches, it stops before any model call and says which filter to
change (the size, the price limit, or the words) to get results.

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
ceiling, then neither. It reports which relaxation would
return listings, e.g. *"Drop the size XS and you'd get 4 listing(s),
starting at $33."* If no relaxation helps, it says so, suggests broader
words, and gives the cheapest price in the data.

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
6. `outfit_input_id`: the `id` of the item handed to `suggest_outfit`,
   recorded at the call (for criterion 3). Then `outfit_suggestion`: from
   `suggest_outfit(session["selected_item"], session["wardrobe"])`.
7. `fit_card`: from `create_fit_card(session["outfit_suggestion"],
   session["selected_item"])`.

Each tool reads its inputs from the session, not from a local variable, so
the item that reached `suggest_outfit` is by construction the one in
`session["selected_item"]`.

**How the loop picks each step:** `run_agent` is a `while` loop. Each pass
calls `trace.check_iterations` and then `_next_step(session)`, which reads
the session and returns the first thing not yet done: `parse` → `search` →
`stop_empty` if `search_results` is empty → `select` → `suggest_outfit` →
`create_fit_card` → `done`. Every step chosen is appended to
`session["steps_run"]`, so a run shows which path it took.

---

## Sample Run

<!-- Two things go here.

     1. One FULL query and its output, pasted as text.
     2. Your three per-tool terminal tests — the command and what it printed. -->

**One full query**

```
$ python app.py ask 'vintage graphic tee under $30, size M'

  Found:    Y2K Baby Tee — Butterfly Print — $18.0 on depop

  Outfit:   Outfit 1:
- Y2K Baby Tee — Butterfly Print
- Baggy straight-leg jeans, dark wash
- Vintage black denim jacket
- Chunky white sneakers
- Black crossbody bag

Outfit 2:
- Y2K Baby Tee — Butterfly Print
- Wide-leg khaki trousers
- Brown leather belt
- Black combat boots

  Fit card: Found the dreamiest 2000s butterfly tee and had to share how to style it! Throw it on with dark baggy denim and a black jacket for ultimate Y2K vibes, or dress it up with khaki trousers and combat boots. Grab it now on depop for just $18 before I change my mind. 🦋✨ #depop #y2k
```

The same loop on queries that match nothing. Each stops after the search,
makes no model call, and names what to change:

```
$ python app.py ask 'denim jacket under $10'

  No listings matched 'denim jacket' under $10. Raise or remove the $10 limit and you'd get 8 listing(s), starting at $24. Best match: Denim Jacket — Light Wash, Cropped ($42, size S).

0 model calls this session

$ python app.py ask 'track jacket size XS'

  No listings matched 'track jacket' in size XS. Drop the size XS and you'd get 4 listing(s), starting at $33. Best match: 90s Track Jacket — Navy/White Stripe ($45, size M).

0 model calls this session

$ python app.py ask 'designer ballgown size XXS under $5'

  No listings matched 'designer ballgown' in size XXS under $5. Nothing in the data matches the words 'designer ballgown' even without filters. Try broader words like 'jacket', 'jeans', 'tee' or 'dress'. Prices in the data start at $12.

0 model calls this session
```

Session state after the happy path, checked from the session itself:

```
selected: lst_002 | search[0]: lst_002 | into suggest_outfit: lst_002
steps: ['parse', 'search', 'select', 'suggest_outfit', 'create_fit_card', 'done']
```

And after the empty one: `steps=['parse', 'search', 'stop_empty']`,
`fit_card=None`.

**The three tools, tested one at a time**

`search_listings` (printing title, size and price instead of the whole dicts,
so it fits on screen):

```
$ python -c "from tools import search_listings; print([(r['title'], r['size'], r['price']) for r in search_listings('graphic tee', max_price=30)])"
[('Y2K Baby Tee — Butterfly Print', 'S/M', 18.0), ('Graphic Tee — 2003 Tour Bootleg Style', 'L', 24.0), ('Vintage Band Tee — Faded Grey', 'L', 19.0), ('Vintage Graphic Hoodie — Faded Black', 'L', 26.0), ('Mesh Long-Sleeve Top — Black', 'S/M', 15.0), ('Low-Rise Cargo Pants — Khaki', 'W29', 27.0), ('Oversized Crewneck Sweatshirt — Vintage Navy', 'XL (fits oversized)', 20.0)]

$ python -c "from tools import search_listings; print(search_listings('designer ballgown', size='XXS', max_price=5))"
[]
```

`suggest_outfit`:

```
$ python -c "from tools import suggest_outfit; from utils.data_loader import get_example_wardrobe, load_listings; print(suggest_outfit(load_listings()[0], get_example_wardrobe()))"
Outfit 1:
Pair the vintage Levi's 501 jeans with the white ribbed tank top tucked in.
Layer the slightly cropped vintage black denim jacket over top.
Finish the look with chunky white sneakers and the black crossbody bag.

Outfit 2:
Style the vintage Levi's 501 jeans with the really oversized grey crewneck sweatshirt worn loose.
Add the brown leather belt to cinch the waist if desired.
Complete the outfit with black combat boots for an effortless streetwear edge.
```

`create_fit_card`:

```
$ python -c "from tools import create_fit_card; from utils.data_loader import load_listings; print(create_fit_card('jeans and white sneakers', load_listings()[0]))"
Nothing beats a broken-in pair of 501s with that ideal knee fading. I'm obsessed with throwing these on with crisp white sneakers for the ultimate effortless street style fit. Grab them on depop for just $38 before I change my mind! 👖✨ #VintageLevis #Streetwear

$ python -c "from tools import create_fit_card; from utils.data_loader import load_listings; print(create_fit_card('', load_listings()[0]))"
Can't write a fit card: no outfit suggestion was provided.
```

---

## How I Used AI

<!-- Two specific moments. What you asked, what came back, what you changed.

     "I used Claude to help me code" is not enough.

     "I gave Claude my search_listings spec. It returned None on no match
     instead of an empty list, so I changed it" is the level we want. -->

I used Claude Code throughout this project, with the brief as my
instructions. It drafted the tool specs, the code and this README. I
committed each milestone myself.

**Moment 1: the outfit prompt leaked its own formatting**

- *What I asked for:* `suggest_outfit` and `create_fit_card` built to the
  Tool Inventory spec, using one shared helper to turn a listing into prompt
  text.
- *What came back:* The helper's first line was
  `Vintage Levi's 501 Jeans — Medium Wash — 38 dollars on depop`. In the
  per-tool test, the model copied that whole line into both outfits
  ("tucked into the Vintage Levi's 501 Jeans — Medium Wash — 38 dollars on
  depop"), so the outfit read like a price tag.
- *What I changed:* `_describe_item` in `tools.py` now puts `title:`,
  `price:` and `platform:` on separate labelled lines. The re-run outfit
  just says "the vintage Levi's 501 jeans".

**Moment 2: the empty-search message said the wrong price**

- *What I asked for:* An empty-search message that names what the user could
  change. "No results" doesn't count.
- *What came back:* It re-ran the search with each filter dropped, which
  works, but printed *"finds 8 listing(s), from $24 (e.g. Denim Jacket —
  Light Wash, Cropped)"*. That jacket costs $42, so the message read as if it
  cost $24.
- *What I changed:* `explain_empty` in `agent.py` now reports the cheapest
  price and the best match separately, with the match's own price and size:
  *"…starting at $24. Best match: Denim Jacket — Light Wash, Cropped ($42,
  size S)."*

**On the criteria:** Claude drafted criteria 3–5 and the reasons under all
five. The brief warns that a criterion you didn't write is one you can't
defend, so I read each one against the data and the code before committing
it.

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

Run with `python run_eval.py --label before`: every scenario in `scenarios.py`
five times, cache off, temperature 0.9, 84 model calls. Full output is in
`results/run_2026-10-07_1926_before.md`, and the raw sessions are in the
`.json` file beside it. Each try was marked PASS/FAIL by `score_eval.py`,
which applies `criteria.md` as written. I then read the failing tries and the
fit cards myself to confirm.

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1. Matching query completes all three tools | 4 of 5 | PASS | PASS | PASS | FAIL | FAIL | MISSED (3/5) |
| 2. Impossible query stops before suggest_outfit | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 3. Same item at every step of the session | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 4. Fit card: 2–4 sentences, ≤400 chars, price, platform | 4 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 5. Search respects price and size (5 queries) | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |

How the tries map to scenarios:
- **Criteria 1–4:** one query each, run five times. C1 `'vintage graphic tee under $30'`, C2 `'designer ballgown size XXS under $5'`, C3 `'90s track jacket in size M'`, C4 `'silk slip dress in midi length under $40'`.
- **Criterion 5:** names five fixed queries, so each try is one query, in the order listed in `criteria.md`. Each query was also run five times, and a query only counts as PASS if all five of its runs had zero violations.
- **Not in the table:** the starter's empty-wardrobe scenario is a diagnostic, not one of my five. It completed 1 of 5 times. The other four stopped on the same 503 error that failed criterion 1's tries 4 and 5.

**Real output from one try per criterion.** It all comes from
`agent.py::run_agent`, read from the session it returned
(`results/run_2026-10-07_1926_before.json`).

Criterion 1, try 1 (PASS), `'vintage graphic tee under $30'`:

```
steps_run: ['parse', 'search', 'select', 'suggest_outfit', 'create_fit_card', 'done']
fit_card:  Butterfly graphics are peak early 2000s, and this little tee is giving total downtown-girl-meets-mall-rat vibes. Throw it on with dark baggy denim and a black jacket, or dress it up with khaki trousers and combat boots. Grab it on depop for just $18 before I change my mind and keep it! 🦋✨ #y2k #thrift
```

Criterion 1, try 4 (FAIL), the same query:

```
steps_run: ['parse', 'search', 'select', 'suggest_outfit']
error:     The search worked and found Y2K Baby Tee — Butterfly Print ($18 on depop), but the AI model couldn't be reached while putting together outfit ideas: the model service is overloaded right now (503). This is usually temporary. Wait a minute and run the same query again.
trace:     [4] suggest_outfit
                 out: ModelUnavailable
                 →    stopping: Couldn't reach the model: 503 UNAVAILABLE. {'error': {'code': 503, 'message': 'This model is currently experiencing high demand. Spikes in demand are usually temporary. Please try again later.', 'status': 'UNAVAILABLE'}}
```

Criterion 2, try 1 (PASS):

```
steps_run:          ['parse', 'search', 'stop_empty']
outfit_suggestion:  None
fit_card:           None
error:              No listings matched 'designer ballgown' in size XXS under $5. Nothing in the data matches the words 'designer ballgown' even without filters. Try broader words like 'jacket', 'jeans', 'tee' or 'dress'. Prices in the data start at $12.
```

Criterion 3, try 1 (PASS), `'90s track jacket in size M'`:

```
search_results[0]['id']: lst_004
selected_item['id']:     lst_004
outfit_input_id:         lst_004
fit_card: Found the ultimate 90s Champion track jacket and I'm obsessed with the sleeve stripes. It's in amazing condition and is so easy to throw over baggy denim or khaki trousers. Grab it on Poshmark for just $45 before I change my mind and keep it! 🤌💙 #vintagestyle
```

Criterion 4: all five cards for `'silk slip dress in midi length under $40'`
(item: 90s Silk Slip Dress, $30, depop). Scored as
sentences / chars / price / platform:

```
1  3 / 273 / $30 / depop   Living in 90s slip dresses all season long. I love styling this floral midi with a chunky grey crewneck and combat boots for that perfect grunge-romance contrast, or throwing on a denim jacket and sneakers for an easy indie-sleaze day out. Grab it on depop for just $30! ✨🌸
2  3 / 248 / $30 / depop   Obsessed with this 90s floral silk midi! It’s the ultimate layering piece—wear it over a ribbed tee with chunky sneakers, or throw an oversized crewneck right over it to fake a skirt. Grab it on depop for $30 before I change my mind. 🌸✨ #90s #depop
3  2 / 248 / $30 / Depop   Found the ultimate 90s floral midi slip on Depop for just $30! 🌸 It’s so dreamy on its own, but I’m obsessed with styling it gritty under an oversized sweatshirt and combat boots, or layered over a ribbed tank for daytime. ☁️✨ #90sStyle #ThriftFind
4  2 / 208 / $30 / depop   Found the dreamiest 90s floral midi on depop for just $30 ✨ Style it grunge-meets-romance with a black denim jacket and combat boots, or keep it cozy with an oversized crewneck. So versatile! #90sstyle #depop
5  3 / 207 / $30 / depop   Obsessed with this 90s floral slip dress! Grab it on depop for just $30. Style it grunge-style with a denim jacket and combat boots, or throw a crewneck over it for a textured midi skirt look. 🥀✨ #90s #depop
first sentences: 5 distinct of 5
```

Criterion 5, try 2 (PASS), `'90s track jacket in size M'`, plus try 5:

```
parsed:  {'description': '90s track jacket', 'size': 'M', 'max_price': None}
results: [('lst_004', 'M', 45.0), ('lst_022', 'M', 75.0), ('lst_013', 'M', 30.0), ('lst_034', 'One Size', 14.0), ('lst_032', 'M/L', 33.0)]
         → every size is in {M, S/M, M/L, One Size…}; 0 violations, same 5 results on all 5 runs

parsed:  {'description': 'jeans', 'size': 'W28', 'max_price': 35.0}
results: [('lst_037', 'W28', 30.0)]
         → W28 and $30 ≤ $35; 0 violations on all 5 runs
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
| 1 | Matching query completes all three tools | 4 of 5 | **MISSED (3/5)** | Counted tries where `error` is None and `fit_card` is non-empty. Tries 4 and 5 stopped at `suggest_outfit` with no fit card. 3 is below 4. The failures came from Google's service, not my logic, but the criterion says "completes… and returns a fit card", and these didn't. My Unit 3 reason allowed one service error in five, and there were two. |
| 2 | Impossible query stops before suggest_outfit | 5 of 5 | MET (5/5) | All five: `steps_run` ended at `stop_empty`, `outfit_suggestion` and `fit_card` were None, and the message named a change ("Try broader words like 'jacket', 'jeans'…", plus the $12 price floor). |
| 3 | Same item at every step of the session | 5 of 5 | MET (5/5) | All five: `search_results[0]`, `selected_item` and `outfit_input_id` were all `lst_004`, and the fit card contained `$45`. |
| 4 | Fit card: 2–4 sentences, ≤400 chars, price, platform | 4 of 5 | MET (5/5) | All five cards passed (a)–(d): 2–3 sentences, 207–273 chars, `$30`, and "depop" (one wrote "Depop"; the criterion says ignoring case). The five first sentences were all different. I checked the sentence counts by hand, not just the scorer. |
| 5 | Search respects price and size (5 queries) | 5 of 5 | MET (5/5) | For each query, every result's price was at or under the ceiling and every size was in a hand-written allowed set taken from the data (not my code's matcher). `parsed` matched the query each time. All 25 runs were identical. |

**Diagnoses**

**Criterion 1 (MISSED, 3/5). Place: a tool, specifically the model call
inside `suggest_outfit`. Mechanism: a temporary 503 is treated as permanent.**

Tries 4 and 5 both reached `suggest_outfit` with the right item (`lst_002`,
Y2K Baby Tee). The search, the branch and the session all worked. Then
`generate()` got `503 UNAVAILABLE — "This model is currently experiencing high
demand… usually temporary"` from Google. In `generate.py`, the `except` block
retries only when the error looks like a rate limit (`429`, "resource
exhausted", "rate limit"). Anything else raises `ModelUnavailable` on the
first attempt, with no wait and no second try. My handler in `run_agent`
caught it and stopped cleanly with a message, so nothing crashed, but the run
ended with no outfit and no fit card.

**The pattern: this is one problem, not several.** All six failed runs in
the whole test were this same 503 at the same step:
- criterion 1, tries 4–5;
- the empty-wardrobe diagnostic, tries 1–4.

They were six runs in a row. Every run after that
window completed, including all 45 runs for criteria 3, 4 and 5. Each
failure was the first model call of its run, and each run that got past
`suggest_outfit` also finished `create_fit_card`. So the agent isn't
unreliable in general. It has no tolerance for a brief overload, which the
error message itself calls "usually temporary".

That also explains why criterion 1 missed and criteria 3 and 4 didn't. Their
queries simply ran after the outage had passed. With five tries per
criterion, *when* a criterion runs decides whether it meets its target. That
is the weakness, and it's what the fix should remove.

**On the four criteria I met, and whether my targets were too low:**

- **Criterion 5 is my easiest target.** The search is deterministic code
  with no model in it, so 25 identical runs mostly confirm that it doesn't
  vary. What makes it a real test is the hand-written allowed sizes, which
  could have caught a bad size matcher. It didn't.
- **Criterion 4 is the one I'd tighten.** It passed 5 of 5, but the
  "no shared first sentence" check only catches word-for-word copies.
  Reading the five cards, two open almost the same way: "Obsessed with this
  90s floral silk midi!" and "Obsessed with this 90s floral slip dress!".
  Two more follow one template: "Found the ultimate/dreamiest 90s floral
  midi … on depop for just $30". A stricter version would be "no two of
  the 5 cards share their first three words". Under that, cards 2 and 5
  ("Obsessed with this") would fail. I'm not revising the criterion, since
  it was measurable and I applied it as written. I'm noting it as too loose.
- **Criterion 2: arguing the opposite verdict.** For the ballgown query, the
  message gives no single filter to drop, because nothing in the data
  matches those words even without filters. It says to use broader words
  and gives the $12 price floor. Someone could argue that isn't "naming
  what to change". I count it as MET because it names the part of the
  query that failed (the words) and gives concrete replacements. It is the
  weakest of the four relaxations, though, and a stricter reader could
  call it a partial.


---

## Loop Trace

<!-- One full run, printed step by step, with the MCP call visible in it.

     `python app.py ask '...' --trace` once you've added the trace.step()
     calls in Milestone 2.

     Worth pasting BOTH the happy path and the empty-search path. The empty
     one should be visibly shorter, because it stops. If your two traces are
     the same length, your branch isn't working — and this is the fastest way
     anyone will ever find that out. -->

Produced by `agent.py::run_agent`, which calls `trace.step()` once per step
(the calls live in `agent.py::_run_step`). The search step is labelled
`(via MCP)` because it goes through `mcp_client.call_tool`.

**Happy path:** six steps.

```
$ python app.py ask 'vintage graphic tee under $30, size M' --trace
[1] parse_query
      in:  'vintage graphic tee under $30, size M'
      out: {'description': 'vintage graphic tee', 'size': 'M', 'max_price': 30.0}
[2] search_listings (via MCP)
      in:  {'description': 'vintage graphic tee', 'size': 'M', 'max_price': 30.0}
      out: 10 items: Y2K Baby Tee — Butterfly Print, 90s Silk Slip Dress — Floral, Midi Length, Leather Belt — Brown, Braided … +7 more
[3] select
      in:  10 results
      out: lst_002 Y2K Baby Tee — Butterfly Print ($18, depop)
      →    search returned results, taking the first
[4] suggest_outfit
      in:  new_item=lst_002 (from session['selected_item']), wardrobe=10 items
      out: Outfit 1: - Y2K Baby Tee — Butterfly Print - Baggy straight-leg jeans, dark wash - Vintage black denim jacket …
[5] create_fit_card
      in:  new_item=lst_002, outfit=267 chars from session['outfit_suggestion']
      out: Found the dreamiest 2000s butterfly tee and had to share how to style it! Throw it on with dark baggy denim an…
[6] done
      →    fit card written, returning the session
```

**Empty search:** three steps. It stops at the branch, and `suggest_outfit`
and `create_fit_card` never run.

```
$ python app.py ask 'sequined opera gloves size XXS under $3' --trace
[1] parse_query
      in:  'sequined opera gloves size XXS under $3'
      out: {'description': 'sequined opera gloves', 'size': 'XXS', 'max_price': 3.0}
[2] search_listings (via MCP)
      in:  {'description': 'sequined opera gloves', 'size': 'XXS', 'max_price': 3.0}
      out: [] (empty)
[3] branch: empty search
      out: No listings matched 'sequined opera gloves' in size XXS under $3. Nothing in the data matches the words 'sequi…
      →    search_results is [], stopping before suggest_outfit

  No listings matched 'sequined opera gloves' in size XXS under $3. Nothing in the data matches the words 'sequined opera gloves' even without filters. Try broader words like 'jacket', 'jeans', 'tee' or 'dress'. Prices in the data start at $12.

0 model calls this session
```

### Failure modes, triggered on purpose

All three were run on purpose. The model-unavailable case used a key with
its last character changed, set for that one command
(`GEMINI_API_KEY=<key with last char changed> python app.py ask ...`), so the
real key in `.env` was never edited. That query hadn't been asked before, so
the cache couldn't answer it.

| Failure | How I triggered it | What it did before the handler | What it says now |
|---|---|---|---|
| Empty search | `'sequined opera gloves size XXS under $3'` | Already handled by the Unit 3 branch: stops after search and names what to change | Same. See the empty-search trace above |
| Empty wardrobe | `--empty-wardrobe 'corduroy pants under $40'` | Already handled in `tools.py::suggest_outfit`: general advice, no owned pieces named | Same (output below) |
| Model unavailable (bad key) | last character of the key changed, query `'olive canvas shacket size L'` | `run_agent` raised `ModelUnavailable`. `app.py` printed it, but the session was lost, so any other caller (`run_eval.py`, `serve.py`) would crash | Caught in `run_agent`. Names the step that broke, keeps the item already found, and says to check `GEMINI_API_KEY` |
| Model unavailable (real 503, not planned) | Google's service returned `503 UNAVAILABLE`, "high demand", during my first empty-wardrobe run | Raised `ModelUnavailable` with the raw error dict in it: `{'error': {'code': 503, ...}}` | Caught by the same handler. Says the service is overloaded and to wait a minute and retry |

Bad key, after the handler:

```
$ GEMINI_API_KEY=<key with last char changed> python app.py ask 'olive canvas shacket size L' --trace
[1] parse_query
      in:  'olive canvas shacket size L'
      out: {'description': 'olive canvas shacket', 'size': 'L', 'max_price': None}
[2] search_listings (via MCP)
      in:  {'description': 'olive canvas shacket', 'size': 'L', 'max_price': None}
      out: 1 items: Shacket — Olive Canvas
[3] select
      in:  1 results
      out: lst_032 Shacket — Olive Canvas ($33, poshmark)
      →    search returned results, taking the first
[4] suggest_outfit
      out: ModelUnavailable
      →    stopping: The model rejected your API key. Check GEMINI_API_KEY in your .env file, or create a fresh key at aistudio.google.com.

  The search worked and found Shacket — Olive Canvas ($33 on poshmark), but the AI model couldn't be reached while putting together outfit ideas: it rejected the API key. Check GEMINI_API_KEY in your .env file, or make a fresh key at aistudio.google.com, then run the query again.
```

The real 503, after the handler (the same empty-wardrobe query, during the
outage):

```
[5] create_fit_card
      out: ModelUnavailable
      →    stopping: Couldn't reach the model: 503 UNAVAILABLE. {'error': {'code': 503, 'message': 'This model is currently experiencing high demand. ...', 'status': 'UNAVAILABLE'}}

  The search worked and found Corduroy Wide-Leg Pants — Rust ($32 on depop), but the AI model couldn't be reached while writing the fit card: the model service is overloaded right now (503). This is usually temporary. Wait a minute and run the same query again.
```

Empty wardrobe, once the service was back:

```
$ python app.py ask --empty-wardrobe 'corduroy pants under $40'
(running with an empty wardrobe)
...
[4] suggest_outfit
      in:  new_item=lst_005 (from session['selected_item']), wardrobe=0 items
      out: Pair these rust cords with a fitted cream ribbed turtleneck tucked in to balance the wide leg, layered with an…
...
  Outfit:   Pair these rust cords with a fitted cream ribbed turtleneck tucked in to balance the wide leg, layered with an oversized brown plaid blazer. Finish the look with platform leather clogs or brown ankle boots and a minimalist crossbody bag.
Alternatively, keep it casual by pairing them with a cropped graphic tee or a vintage band t-shirt, thrown under an oversized distressed denim jacket. Add retro sneakers or canvas loafers for an effortless, everyday 70s-inspired vibe.

  Fit card: Channeling major 70s energy with these gorgeous rust-colored wide-leg cords! They’re the ultimate earth-tone staple for your autumn wardrobe, and they can easily be dressed up with a blazer or kept casual with a band tee. Grab them on depop for just $32 before someone else snatches this vintage dream up. 🍂✨ #depop #vintagecords
```

I also added a handler for `MCPError`: if the search server doesn't answer,
the run stops with "The listings search couldn't run … Run
`python mcp_client.py` to see whether it starts". I didn't trigger that one
for this table.

**On the MCP move:** <!-- what changed in your code, and whether anything
behaved differently afterwards. If the rewire didn't work, say exactly where it
broke — the error text and the last thing that worked. That earns the point in
full. -->

I moved `search_listings`, the tool that doesn't call the model. In
`mcp_server.py` it is registered with `@mcp.tool()`, with the same typed
inputs as the Tool Inventory: `description: str`, `size: str | None`,
`max_price: float | None`. Its description states the units (US dollars,
inclusive), the size rule, and that an empty list is returned when nothing
matches. `python mcp_client.py` lists it with `description: string`,
`size: string (optional)` and `max_price: number (optional)`.

In `agent.py`, both places that searched now go through
`mcp_client.call_tool("search_listings", {...})`: the main search step in
`run_agent`, and the relaxed re-searches in `explain_empty`. `tools.py` is
unchanged.

**Did anything behave differently?** Not in what came back. I compared
`call_tool` against the direct call on three inputs: a match (10 results), the
impossible query (`[]`), and a size-only query with `max_price=None` (5
results). All three were identical (`==` is True), including the empty list,
which comes back as a `list` and not as a string or `None`. What changed is
speed: each call starts the server process. The impossible query makes four
MCP calls (the search plus three relaxed re-searches), and the whole run took
2.3 seconds.


---

## The Improvement

<!-- What you changed, why your diagnosis pointed at it, and the after-run in
     the same table format. One change, measured properly.

     `python run_eval.py --label after` -->

**What I changed:** One thing, in `generate.py::generate`, which every
model call goes through. Before, a `503 UNAVAILABLE / "high demand"` error
raised `ModelUnavailable` on the first attempt. Now it is retried after
waiting 5s, 10s, 20s, then 30s, so up to 5 attempts and about 65s of waiting
in total. Each wait prints `[busy] the model service is overloaded (503).
Waiting 5s (attempt 1 of 5).` If the last attempt is still a 503, it raises
`ModelUnavailable` as before, so the Milestone 2 handler still catches it.

Nothing else changed: not `tools.py`, not `agent.py`, not the scenarios, not
the criteria. Rate-limit (429) handling is unchanged. A bad key still fails
on the first attempt with no retries.

Before the full re-run, I tested the change with a fake client that raises a
503:
- 503 twice, then success: returned the text after 3 calls.
- 503 every time: raised `ModelUnavailable` after 5 calls.
- Bad key: raised `ModelUnavailable` after 1 call.

**Which failure it was meant to fix:** criterion 1's miss (3/5). Per the
diagnosis, both failed tries, and all six failed runs in the whole before
test, were a temporary 503 at the first model call, `suggest_outfit`. The
search, branch and session had all worked.

### Run Log — After

`python run_eval.py --label after`: the same scenarios, five tries each,
cache off, temperature 0.9. Output is in `results/run_2026-10-07_1944_after.md`
and `.json`, scored with `score_eval.py`.

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1. Matching query completes all three tools | 4 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 2. Impossible query stops before suggest_outfit | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 3. Same item at every step of the session | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 4. Fit card: 2–4 sentences, ≤400 chars, price, platform | 4 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 5. Search respects price and size (5 queries) | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |

Before and after, side by side:

| Criterion | Target | Before | After |
|---|---|---|---|
| 1 | 4 of 5 | MISSED (3/5) | MET (5/5) |
| 2 | 5 of 5 | MET (5/5) | MET (5/5) |
| 3 | 5 of 5 | MET (5/5) | MET (5/5) |
| 4 | 4 of 5 | MET (5/5) | MET (5/5) |
| 5 | 5 of 5 | MET (5/5) | MET (5/5) |
| empty-wardrobe diagnostic (not one of the five) | — | completed 1/5 | completed 5/5 |
| model calls for the whole test | — | 84 | 98 |

**Did it help, and how do I know:** Yes, for criterion 1. And it wasn't
just that the service happened to be calm during the second run. Google
returned 503s again: the after log shows **8 `[busy]` retries across 7
runs**, and **every one recovered**, 6 after one 5s wait and 1 after a 5s
and a 10s wait. Two of those runs were criterion 1's own tries:

```
try 2: [busy] the model service is overloaded (503). Waiting 5s (attempt 1 of 5).
       → completed, fit card 290 chars
try 5: [4] suggest_outfit
             out: Outfit 1: - Y2K Baby Tee — Butterfly Print - Baggy straight-leg jeans, …
         [busy] the model service is overloaded (503). Waiting 5s (attempt 1 of 5).
       [5] create_fit_card
             out: Channeling major early 2000s energy with this butterfly baby tee! 🦋 Grab it on depop for just $18 …
       [6] done
```

Under the old code, tries 2 and 5 would have stopped with `ModelUnavailable`,
leaving criterion 1 at 3/5, a miss again. With the retry they completed,
for 5/5. The empty-wardrobe diagnostic shows the same thing: 1/5 → 5/5, with
its tries 2 and 4 recovering from 503s (try 4 needed two waits).

**What it cost:** 98 model calls instead of 84. That's the 8 retries plus
the extra calls from runs that now get as far as the fit card instead of
stopping at `suggest_outfit`. Each retried run also took 5–15 seconds longer.

**What it doesn't fix:** an outage longer than about 65 seconds still ends
the run, now after a minute of waiting rather than instantly. And on
criteria 2–5 the after-run shows only that nothing got worse. Those were
already met, so this run isn't evidence of any further improvement there.
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
