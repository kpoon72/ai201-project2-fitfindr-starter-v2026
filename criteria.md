# Acceptance criteria — FitFindr

Five criteria that say what "working" means for this agent, written in unit 3
**before** any results existed.

An acceptance criterion names a target: a number, a count, a rate, or something
a person could plainly observe. *"The agent handles errors"* is an opinion.
*"When search returns nothing, the agent stops before calling the second tool,
in 5 of 5 tries"* is a criterion.

Under each one, write a sentence or two on **why that target** and not a
stricter one. A reason that says something about your tools, your loop, or the
data earns credit; *"80% seemed reasonable"* does not.

> Missing your own targets next unit costs you nothing. Setting a target so
> easy you can't miss it does.

**Two are written for you. You write three.**

---

## 1. A matching query completes all three tools

Given a query that matches at least one listing, the agent completes all three
tool calls and returns a fit card — in at least 4 of 5 tries.

**Why this target:** Search is deterministic, but the run has two model
calls through a free-tier quota, and the query parser is regex. One rate-limit
or service error, or a phrasing the regex mis-parses (for example a price
written as "30 bucks"), loses a try even when the right listing exists. I
allow one miss in five for that. Two misses would mean something in my own
code is wrong, not bad luck.

---

## 2. An impossible query stops before the second tool

Given a query that matches no listings, the agent stops before calling
`suggest_outfit` and returns a message naming what to change — 5 of 5 tries.

**Why this target:** This path makes no model call. The branch is an `if`
on whether `search_results` is empty, and the message comes from re-running
my own search. Nothing in it varies run to run, so one miss means the branch
is broken, not unlucky. "Naming what to change" means the message names at
least one specific filter from the query (the size, the price ceiling, or a
keyword) and says what to do about it. "No results" alone fails.

---

## 3. The item search found is the item the later tools received

Given a query that completes all three tools, the session shows the same
listing at every step, in 5 of 5 tries. Three `id`s must be equal:
`session["search_results"][0]["id"]`, `session["selected_item"]["id"]`, and
`session["outfit_input_id"]` (the `id` of the dict actually passed into
`suggest_outfit`, recorded at the call). And `session["fit_card"]` must
contain the selected item's price as `$NN`.

**Why this target:** Handing the item along is plain Python with no model in
it, so any mismatch is a wiring bug, not variation, and 4 of 5 would be
excusing a bug. The price check covers the hop into `create_fit_card`: the
price only reaches the caption if that tool got the right item. If the model
drops the price, this fails too, which I accept, because criterion 4 would
flag the same card.


---

## 4. The fit card reads like a post and names the facts

Run the same matching query 5 times with caching off. At least 4 of the 5
fit cards must pass all four checks:
(a) 2 to 4 sentences, counting a sentence as text ending in `.`, `!` or `?`
and ignoring hashtags and emoji;
(b) 400 characters or fewer;
(c) contains the selected item's price as `$NN` (`$24` or `$24.00`);
(d) contains the platform name, ignoring case.
Separately, no two of the 5 cards may have the same first sentence, word for
word.

**Why this target:** The wording should vary, so I don't check wording. I
check the facts a buyer needs and a length someone would actually post. The
model sometimes ignores a length rule or writes the price as "24 bucks", so I
allow one miss in five. Two misses would mean my prompt isn't constraining it.
The first-sentence rule exists because identical openings mean the cache is on
or the prompt is a template, which is the failure the brief warns about.


---

## 5. Search respects the price and size the user asked for

For these 5 queries:
- `vintage graphic tee under $30`
- `90s track jacket in size M`
- `platform sneakers size 8`
- `denim jacket under $50`
- `jeans size W28 under $35`

every listing in `session["search_results"]` must have `price` at or below
the stated ceiling, and a `size` that matches the stated size under the rule
in the README's Tool Inventory. For example, `M` matches `S/M` but not `XL`,
and `8` matches `US 8` but not `US 8.5`. Also, `session["parsed"]` must hold
that exact ceiling and size. Target: 5 of 5 queries with zero violating
listings.

**Why this target:** A thrift search that shows a $45 jacket to someone who
said "under $30" is broken in a way the user notices at once. The size data
mixes letter, waist, shoe and "One Size" formats, and a substring test fails
quietly (`"l" in "xl"`). There's no model in this path, so any violation is
a bug in my parser or my size matcher. The queries are picked to hit the
edge cases: `S/M` and `M/L` for `M`, `US 8` beside `US 8.5`, and a waist
size combined with a price.


---

<!-- ─────────────────────────────────────────────────────────────────────────
     UNIT 4 — read this before you change anything above.

     If a criterion turns out to be BROKEN rather than merely unmet, you can
     revise it, and that earns credit. But never delete or edit the original
     line. Add the revision underneath it, like this:

         ## 4. Something about the fit card

         The fit card is different every time.

         **Why this target:** ...

         > **Revised in unit 4:** For 5 different items, the 5 fit cards share
         > no opening sentence.
         >
         > **Why revised:** "different" wasn't checkable — two cards that
         > differed by one word still counted. The new version is something I
         > can actually score.

     That's a revision because the criterion couldn't be MEASURED.

     Lowering a target because you missed it is not a revision, and it costs
     you the point:

         ✗ "I said the empty search stops it 5 of 5 times, but I got 3 of 5,
            so 3 of 5 is more realistic."

     A number you missed stays where it is, gets diagnosed, and gets a fix
     attempted. That's where the points are.
     ───────────────────────────────────────────────────────────────────────── -->
