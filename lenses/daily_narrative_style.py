"""
Daily-mode synthesis grounding rules and style guide.

Distinct from lenses.narrative_style (the natal full-chart narrative,
100+ claims, N4). Daily mode's synthesis pool is tiny by comparison --
typically 1-4 resolved claims a day -- so this is its own, shorter
guide rather than a reused copy of the natal one, encoding the actual
diagnosis from "Celeste — Daily Mode Synthesis Addendum":

Two prior attempts at daily.py's reading assembly were both rejected.
Attempt 1 was flat concatenation of claim statements (no connective
language at all). Attempt 2 added ordering and connector phrases
("alongside that," "still") between the same claim statements --
which read as one paragraph without being one. The addendum's
diagnosis: connective WORDS got smarter; connective LOGIC never
existed. Linking phrases between independent facts is not synthesis.
Synthesis means finding the actual relationship between what the
claims describe, before any prose gets written, and letting the
reading express that relationship -- not each claim in its own
sentence with tape between them.

Reuses lenses.narrative_backend (NarrativeBackend /
AnthropicNarrativeBackend / MissingAPIKeyError) and
lenses.narrative_validation (check_coverage / fact_check) unmodified
-- both are already fully generic over claims + narrative text, no
natal-chart-specific assumptions in either.

Revised a second time after testing against genuinely novel claim
combinations (not just the addendum's own locked example) surfaced two
real problems the first draft didn't catch:

- A claim pair with different life_domains and no real shared
  mechanism (a moon-phase/cyclicality claim + a day-pillar/
  relationships claim about an unrelated topic) got merged with an
  invented causal "because" clause the source claims never supported
  -- exactly the fabrication grounding rule 1 already banned for
  backstory, just showing up as invented causality between two real
  claims instead. The guide had zero worked example of the correct
  SPLIT case to pattern-match against, only the unified-throughline
  case, which likely explains why the model defaulted to forcing unity
  even where the earned-complexity bar wasn't met. Fixed by adding a
  second locked example that IS a genuine split.
- Output consistently ran longer and more explanatory than the user's
  own locked example, even though both were "two to three sentences."
  Comparing sentence-by-sentence against the locked example showed the
  gap wasn't really about sentence count -- it was two-clause sentences
  restating the same fact twice, generic advice-tag endings ("so use
  it"), and mild over-explanation of WHY a feeling is true rather than
  just stating it. This is the same "AI-y," bloated register the natal
  narrative feature (lenses.narrative_style) already diagnosed and
  fixed once for the full-chart case -- ported the same fixes here
  rather than re-deriving them from scratch.

Revised a third time after the Daily-Mode Scope Expansion brief
widened the sweep to all 10 transiting bodies against the full natal
chart plus houses. That widening surfaced a real gap: the generic
aspect-type claims ("a square pulls the two placements involved...")
and generic house claims ("the 3rd house governs...") don't name WHICH
bodies -- that specificity only survives when a curated fragment
exists for the exact combo (the original 8 daily_transit_* claims).
For the many newly-resolved generic-only matches, synthesis had
nothing but the abstract definition to work with -- genuinely nothing
to be specific about, not a prompting problem. Fixed by passing
today's real underlying transit data through as a reference-only
section (daily.py's _render_daily_narrative_input), so synthesis can
know which placement a generic claim is actually about without
inventing anything -- the data was always computed, it just wasn't
reaching the prompt.

Revised a fourth time for the Synthesis/Tone/Content-Architecture
Repair Brief's Part 3 (prose-layer rules), after Part 2.1 gave
daily.py a real, computed PRIMARY THREAD signal (_score_threads' own
aspect-weight + convergence score, already reaching this prompt via
the hit-grounding section) that the style guide itself never
referenced as a structural instruction -- headline selection was left
to the model re-deriving "which claim is the headline" from the raw
claim list, with no requirement to actually lead with the thread the
engine already identified as strongest. Four additions, reconciled
against every existing rule rather than layered on top of them:
headline-first structure (the PRIMARY THREAD, when present, decides
what leads -- see "When a PRIMARY THREAD is named"), confidence-
scaling by the same real score (a real tension with the existing
"never hedge" voice rule -- resolved as scaling how much SPACE/WEIGHT
a thread gets, never hedge words; a mild thread stated plainly is
still stated plainly, just not given the whole reading), a payoff
requirement (reconciled against the existing generic-advice-tag ban --
payoff means the claims' own real resolution, e.g. the locked worked
example's third sentence, not an appended imperative), and a one-
metaphor cap (refining the existing near-total metaphor ban into "at
most one, still only if earned" rather than reversing it). Confidence-
scaling's score bands (1.5, 2.3) are empirical, from a 53-date 2026
sample of real headline_thread scores for Liam's chart (p25=1.52,
p75=2.26) -- not arbitrary, and revisitable if that distribution
shifts.

Revised a fifth time for the same Repair Brief's Part 4 (arcs as the
primary content unit): daily.py now always computes a STANDING ARC
(western_arc_standing, mirroring result["vedic_dasha"]'s own always-
present shape) and a TODAY'S DEPTH decision (full/short/near_silent),
both now reaching this prompt via _render_daily_narrative_input. Two
additions, reconciled against the existing rules rather than layered
on: standing-arc phrasing (phase-aware, reusing the arc's own phase
label and recurrence_note verbatim -- never inventing new language for
timing this system didn't compute) and the short-depth register (one
honest sentence, not three compressed into one breath, for a day
whose only real content is the standing arc simply continuing) -- the
same confidence-scaling spirit Part 3 already established, applied one
level up, at the structural (how much space) rather than sentence (how
many claims) level. near_silent needed no new instruction: it's the
same "genuinely nothing" condition grounding rule 7 already covers,
just reached by a named decision now instead of only by incidental
emptiness.

Revised a sixth time for Part 2.5 ("invented timeliness"): a real,
confirmed gap where five always-on identity/timing families (Big-3
sign+house, Vedic Dasha, Vedic sidereal Big-3+bhava, Chinese Ten-God-
in-position) reached this prompt in the same flat claims list as
hit-backed content, with zero temporal signal telling synthesis they
aren't today's news -- daily.py's own result dict already carried a
"standing identity context, not today's sky" note for exactly this
content, but that note never reached the prompt. Fixed at both ends:
daily.py now separates these into their own "# Standing identity &
context" section (see _render_daily_narrative_input), and grounding
rule 8 above states the hard rule for how to write about them --
never present-tense activation language unless the same fact is
independently paired to something real today via STANDING ARC or an
actual hit.

Revised a seventh time (2026-09-01 Tone/Format Enforcement Brief):
confirmed by direct trace-through that this was NOT a data problem --
a genuinely exact, well-grounded hit (0.067 degree orb, real
recurrence dates, real sign/house/aspect meaning, all correctly
reaching this prompt as the PRIMARY THREAD) still produced vague,
hedgy, overlong, em-dash-laden prose that never committed to the
specific fact it was given. The existing rules already banned most of
this abstractly (no em dashes, 6-12 words/sentence, a real payoff) --
they just weren't holding reliably against real generation. Same fix
philosophy as Option A (daily.py's prompt-scope fix): try the cheap,
concrete move before building enforcement machinery. Added REAL
observed violations (not hypothetical ones) as explicit "don't do
this" examples directly next to the rules they violate, a new
explicit rule against multi-option hedging constructions ("X, Y, or
something like Z") that the existing WHO-non-specificity rule didn't
cover and evidently invited by mistake, and a third locked worked
example ("Say Less") -- the actual approved reference standard this
session produced, confirmed by Liam as "better, genuinely" -- showing
committed single-thread execution against a real day with multiple
equally-cited competing threads (Moon/Uranus, Mars/Jupiter) that it
correctly says nothing about at all.

Revised an eighth time, immediately after: the very first live test of
the seventh revision produced a reading that reproduced two of that
revision's own quoted "don't do this" example sentences almost
verbatim (same em-dash-aside-plus-verb shape, the same "what you're
willing to commit to... and what simply won't bend" list, and a
landing line that was a near word-for-word match for the banned
"It's not abstract, and it's not later"). Full, reusable bad-example
sentences aren't warnings the model reliably avoids -- they're
templates it can crib from; this is a known failure mode for few-shot
negative examples, not a one-off fluke. Fixed by rewriting every "real
observed violation" quote in this file from a full reproducible
sentence into an abstract description of the failure's SHAPE (which
clauses, in what order, doing what), each now paired with an explicit
instruction not to reproduce or closely paraphrase the pattern, and a
note that swapping in different nouns/verbs while keeping the same
clause structure doesn't count as a fix. The one deliberate exception
is the "Say Less" worked example, which stays fully quoted -- it's a
POSITIVE example the model should pattern-match toward, where
imitation is the entire point.

Revised a ninth time (2026-09-02 "Two Deliverables, One Pass" brief,
Deliverable 1): a real, separate cause identified by pulling the
actual live prompt text for a real night's PRIMARY THREAD (Saturn
conjunct natal Juno) -- every fact given for it (sign meaning, house
meaning, aspect meaning, cusp-sign meaning) is written in permanent
natal-trait voice ("seeks," "governs," "unifies"), and the model was
being asked to simultaneously (1) select what matters from up to ~18
such atomic facts across a 3-hit thread, (2) do the classical planet-
in-sign-in-house synthesis a human astrologer would do by hand, and
(3) translate that into today's-active-energy voice -- three real
steps left implicit and simultaneous, with only a negative rule
(grounding rule 8: don't say a standing fact is "activating" unless
paired to real evidence) and no positive worked example of the voice-
shift itself. Fixed by making the fusion and the voice-translation two
explicit, sequenced steps with a worked demonstration using that same
real Saturn/Juno data -- deliberately a low-difficulty case (all three
given facts already agree, no real internal contradiction to resolve),
chosen so a failure to make the voice-shift here can't be blamed on
the astrology being hard to reconcile.

Revised a tenth time, after the first confirmed-fresh test of the
ninth revision (plus Deliverable 2's content expansion, shipped the
same pass): real, encouraging signal on both fronts -- the reading's
opening sentence genuinely translated a natal trait into today's-
active-energy voice, and it used "recommitting" specifically, the
exact word from Deliverable 2's new commitment claim, confirming the
new content is actually being drawn on, not just sitting unused. But a
distinct, separate problem survived: a second sentence ran ~42 words,
comma-splicing a "the question isn't X, it's Y" reframe together with
two further "when it..." clauses -- the same class of failure as the
~40-word violation already named above, just in a new rhetorical
shape (a reframe construction) and with no em dash this time, so
neither the em-dash strip nor the existing word-count rule caught it.
Added a second real-shape description (reframe-plus-stacked-clauses)
alongside the first, naming the specific mechanism (an "isn't X, it's
Y" reframe invites further qualification, which is where the extra
clauses come from) so the rule targets the actual generative habit,
not just its word count.
"""

DAILY_GROUNDING_RULES = """
## Hard rules (grounding)

1. Every specific factual assertion in your output must trace back to
   one of the CLAIM_IDs given below. Do not add, infer, or embellish
   beyond what a claim's STATEMENT actually says. In particular, never
   invent a backstory, a specific unspoken thing, or a concrete
   scenario the claims don't actually describe -- a claim about
   general ease of expression is not license to invent "there's
   something you've been meaning to say." That exact failure was
   caught and rejected during this system's own design: check every
   drafted line against its real source claim before keeping it.
2. Every claim given below must be genuinely accounted for -- but on a
   busy day (the widened sweep can resolve 15+ claims, mostly generic
   aspect-type/house claims with no specific body named), "accounted
   for" does NOT mean every claim gets its own clause or individual
   trace. It means: fold what you honestly can, and compress any
   remaining cluster of same-flavor generic claims into ONE clause
   naming the real pattern -- see "Compress, don't invent" below.
   What it never means is inventing a fact to make a claim feel
   represented. A real failure, caught during testing: with 17 mostly-
   generic claims and no room to trace each one, a draft invented
   "whatever you choose won't stay just yours to carry" and "what you
   think and what you say will finally match" -- neither asserted by
   any source claim. Compression was available and wasn't used;
   fabrication filled the gap instead. Compression is always the
   right move over invention.
3. You may connect claims ONLY because you have identified a real
   shared relationship between what they describe (see "Find the
   story" below) -- never because a transition word makes unrelated
   facts read smoothly together, and never by inventing a causal link
   ("because," "so," "which means") between two claims that don't
   actually explain each other. If two claims genuinely don't relate,
   present them as two separate short beats -- see the second worked
   example below for exactly what that looks like.

   A real failure, caught during testing, worth checking your own
   draft against: given a moon-phase claim about resisting the urge to
   rush a personal project, and an unrelated day-pillar claim about
   relational harmony, a draft wrote "That's easier than it would
   otherwise be, because today actually cooperates with you,
   especially in your closest relationship" -- inventing a causal link
   (relational harmony making it easier to finish your own project)
   that neither source claim states or implies. The two claims have
   different life_domains and no shared mechanism; they should have
   been two separate beats, not joined by a fabricated "because."
4. Astrology/BaZi terminology (planet names, aspect names, pillar/
   stem/branch names, technique names) stays entirely backend. It
   never appears inside the reading itself.
5. If a "Today's exact transit data" section appears after the claims,
   it's real, already-computed astronomical fact (which body, which
   aspect, which house) -- not itself a claim, and not license to
   generate new interpretation from it. Use it only to know WHICH
   placement a generic claim (one that doesn't name a specific body)
   is actually about, so you can write toward that specific felt
   experience instead of restating the claim's abstract definition.
   Never treat it as a second source of claims, and never let it
   justify a fact that isn't ALSO backed by an actual claim above --
   it disambiguates specificity, it doesn't add new permission to
   assert things.
6. If an "OVERCLAIM CONSTRAINTS" section appears, follow it exactly
   for every hit it names -- it states, per hit, exactly which
   contact/exactness/amplification language is and isn't accurate
   given the real computed numbers (never "exact" for something that
   is a real contact but not truly exact; never imply a connection
   that doesn't exist; never call an eclipse amplified when it isn't).
   This is a hard rule the generated text is checked against
   afterward, not a style preference -- treat it with the same weight
   as rule 1.
7. If today's claims below genuinely amount to nothing (no hits, no
   day-pillar relationship) -- say so plainly, in the same second-
   person, plain-fact voice as everything else. Do not manufacture
   drama or invent a "quiet but meaningful" undertone the data doesn't
   support; an ordinary day is a genuine, honest answer.
8. Permanent chart facts (natal sign/house placements, Dasha timing,
   generational pillar structure) with NO real event behind them
   today are no longer sent to you at all as of Part 6 -- daily.py
   drops them from this prompt entirely unless a real STANDOUT-tier
   hit today also genuinely touches that same point (in which case
   they reach you as ordinary grounding on that hit, already paired
   to something real, not as separate standing content). The rule
   this used to describe (never phrase a standing fact as
   "activating" today) is now structural rather than something you
   need to police yourself for that specific content family -- but
   the underlying principle still applies to anything below that
   reads as a plain, general truth rather than something tied to a
   real hit or the STANDING ARC block: never present-tense
   "activating today" language for a fact that isn't paired to real
   evidence of that in this prompt. Same weight as rule 6: inventing
   timeliness for a fact this system never computed as active today
   is exactly the same class of overclaim as inventing exactness for
   a loose contact.
9. Every hit under "Today's active astrological hits" carries a real
   TIER label, and hits below a "# Other real hits today (supporting
   texture only...)" header are deliberately shown with LESS detail
   than the PRIMARY THREAD's own hit(s) above them -- this is not
   because they're less real, only because they're not today's
   headline. Never build the reading's dominant story or its
   full-committing/present-tense language around one of these
   compressed hits, however specific or emotionally resonant it
   sounds in isolation -- see "When a PRIMARY THREAD is named" below
   for exactly how to use both sections together. A real incident:
   a reading built its whole "under real pressure right now" headline
   on a single compressed minor-aspect hit while a genuine 4-hit
   convergence (the real PRIMARY THREAD, score 2.70) sat unused in the
   same prompt -- that failure is what this rule exists to prevent.
"""

DAILY_STYLE_GUIDE = """
## Style guide

### Find the story before writing anything

Before drafting a single sentence, look across all of today's claims
and determine their actual relationship to each other:

- Do multiple claims describe the same underlying pressure or theme
  from different angles? (Worked example below: decision-pressure,
  relational stakes, and communication-ease weren't three separate
  facts -- they were one situation: pressure to act, stakes if you
  don't, and the one resource you have for handling it.)
- Is one claim clearly the headline, with others as texture or
  counterpoint to it?
- Do the claims genuinely not relate to each other at all?

Only once that relationship is identified should prose get written --
and the prose should express THAT relationship, not restate each
claim in its own sentence in sequence.

### When a PRIMARY THREAD is named, it IS the headline -- lead with it

If the hit-grounding section below names a PRIMARY THREAD, the
question above ("is one claim clearly the headline?") is already
answered for you by real, computed convergence and aspect-weight
data -- not something to re-derive from reading the claims cold. The
reading's first sentence or beat must be about that thread
specifically, even if a different claim happens to appear first in
the claim list. Everything else still gets folded, given its own
beat, or compressed per the rules below -- PRIMARY THREAD only
decides what leads, not what the whole reading is about. The hits
listed under "Other real hits today (supporting texture only)"
(grounding rule 9) are deliberately given less detail than the
PRIMARY THREAD's own hit(s) above them for exactly this reason -- use
that detail gap as a real signal, not an accident: the PRIMARY
THREAD's hits are where the reading's committed, present-tense
language belongs, and the compressed hits are where a brief, honest
mention (if any) belongs.

### Before writing the PRIMARY THREAD's story: fuse its facts, then translate them to today's voice

The PRIMARY THREAD's hit(s) come with several separate grounding lines
-- sign meaning, house meaning, aspect meaning, and (when given)
further facts like the sign on that house's cusp or what the point
itself signifies independent of placement. These are raw material, not
finished sentences, and turning them into the reading is two distinct
steps -- do them in order, not blended into one guess:

**Step 1 -- fuse the raw facts into one classical picture.** Before any
prose gets written, combine the PRIMARY THREAD's own facts the way a
human astrologer reads "planet in sign in house" as ONE picture, not
three separate facts recited in sequence. Every element of the fused
picture must still trace to a given fact (grounding rule 1 applies in
full here -- fusion is combination, not new interpretation): find how
the facts agree, reinforce, or genuinely pull in different directions,
then state that combined picture in your own head as one coherent
idea before drafting a single sentence of the actual reading.

**Step 2 -- translate the fused picture from natal voice into today's
voice.** Every fact given to you (sign meaning, house meaning, aspect
meaning, what a point signifies) is written in permanent-trait voice --
"seeks," "governs," "signifies," "tends to give." That describes who
someone IS, not what's live today. The reading itself must never just
restate the fused picture in that same voice -- it has to say what the
real transit (the hit's own aspect, orb, tightness, retrograde status,
recurrence) is asking of that trait, testing in it, or activating about
it right now. A trait that's simply true is not itself daily content; a
trait meeting a real, specific transit today is. This is grounding rule
8 applied to the PRIMARY THREAD's own hit, not just to standing/
identity content: even a real, cited, on-topic fact stays natal-voice
description until something in today's actual data gives it a today
reason to be said.

**Worked demonstration (real data, not hypothetical):** a night this
system actually generated used a natal Juno in Aries, in the 11th
house, itself cusped by Aries -- three separate given facts that happen
to agree rather than conflict (an easy fusion, not a hard one, which
makes it a clean test: if the voice-shift still doesn't happen here, a
harder case won't fix it either).

- *Fusion (Step 1, still natal voice, not the final sentence):*
  Juno's whole picture agrees on one thing here -- partnership sought
  through directness and independence, built and proven inside
  friendship and shared community rather than private or domestic
  ground.
- *Voice translation (Step 2, what actually belongs in the reading):*
  the hit's own real transit (an exact conjunction, tight and current)
  is what makes this today's content -- not the trait itself, but
  that trait being asked to hold up under real weight right now. Write
  toward THAT specifically -- name the fusion's actual content
  (independence-minded partnership, proven through friendship and
  shared community rather than private ground) as part of what's
  being tested, not a vague gesture at "what you look for in a
  partner" that could describe any Juno placement's version of this
  transit. Use the transit's own real character (conjunction,
  exactness, retrograde, recurrence, whichever actually apply) to say
  why it's live today, never toward a restatement of the fused picture
  alone -- and never toward an abstraction so general it drops the
  fused picture's specific content entirely (see "Content specificity
  is a separate axis from format discipline" below for the real
  failure this produced).

### Content specificity is a separate axis from format discipline

Format discipline (no em dash, no multi-option hedge, short sentences,
one committed thread) and content specificity are two different
failure modes -- fixing one does not fix the other, and a reading can
pass every format rule above while still saying nothing. A real
comparison from testing the exact same Juno thread the worked
demonstration above uses (natal Juno in Aries, 11th house, cusped by
Aries, exact Saturn conjunction) showed this directly:

- "What you look for in a partner is being tested directly today, not
  just held as a preference." -- format-clean (short, no hedge, no
  list), but content-free: this sentence is equally true of ANY Juno
  reading for ANY person, because it never states what the fused
  picture actually says the person looks for. It confirms a theme is
  active instead of naming the theme.
- "The friendship you've been building is being tested for what it
  actually is -- a partner who's also a real friend, built on equals
  and honest confrontation, not avoidance." -- states the SAME fused
  picture's real content directly (independence, friendship-as-
  foundation, confrontation over avoidance all trace to this
  placement's own sign/house/cusp facts), and reads as more specific
  and more grounded for it, even though it's built from the identical
  underlying claims as the first version.

Liam's own read, confirmed: the second version is right despite a
separate, already-covered violation (its original closing ran on into
a three-item list -- see "Say it once, then stop" below); the first
version has no format violation at all and is still worse, because it
says nothing. Format compliance is not a substitute for actually
stating the fused content -- see the fourth worked example below for
the full before/after.

**The swap test:** before finalizing the PRIMARY THREAD's core
sentence, check whether it could be dropped, unchanged, into a
different reading for a different person with the same aspect type
but a different sign/house/cusp on the same point. If yes, it's too
abstract -- it's confirming that a theme is active instead of stating
what the fused picture (Step 1 above) actually says that theme IS for
THIS placement. The whole reason Step 1 fuses sign + house + cusp +
aspect into one picture is to produce something specific enough that
it couldn't describe just anyone's version of this transit; Step 2 has
to carry that specificity into the actual sentence, not translate it
into a generic placeholder for "a theme is active here."

### Confidence-scaling by signal strength

The PRIMARY THREAD line (when present) gives a real score -- how
tight and how convergent today's leading thread actually is, not a
feeling to guess at. Scale how CENTRAL that thread sounds against it
-- never by hedging (the "never hedged, never softened" voice rule
below still applies in full; every sentence still states a plain,
direct fact) -- by how much SPACE and WEIGHT it gets:

- **Score below ~1.5, or no PRIMARY THREAD at all**: real, but one
  presence among several, not the day's defining force. Give it
  proportionate weight -- a clause, "also present," not a whole
  sentence built to sound decisive. Still a direct, unhedged
  statement of what's true -- just scoped as one factor, not the
  story.
- **Score ~1.5 to ~2.3**: the normal case -- lead with it plainly,
  the way the locked worked example does. No special softening or
  amplification needed.
- **Score above ~2.3, or an exact named occasion (a return or station
  at its own peak)**: this genuinely is the day's dominant story --
  real convergence, or an exact structural moment. Let the language
  carry that weight; don't undersell a real convergence by describing
  it as just one more thing among others.

This changes how much of the reading's real estate and framing
certainty a thread gets -- never the facts themselves, and never
actual hedge words. A mild thread stated plainly is still stated
plainly; it just isn't given the whole reading to itself.

### The STANDING ARC: real, but not automatically the headline

A STANDING ARC line (when present) names the single dominant, ongoing
multi-month Western transit -- real and computed, but a SEPARATE
signal from the PRIMARY THREAD above, not a second headline candidate
to weigh against it. It shows up in three different shapes:

- **It IS the PRIMARY THREAD** (the arc's own hit is today's headline
  material). Nothing extra to do -- write it exactly as PRIMARY THREAD
  guidance above already says; the STANDING ARC line here just gives
  you the wider phase context (approaching/exact/separating) for that
  same thread.
- **Present, but something else converged more strongly today.** The
  arc still deserves at most one honest, low-weight clause naming
  what's ongoing -- real estate proportional to TODAY'S DEPTH, never
  equal footing with the actual headline it lost to.
- **It's the ONLY real content today** (TODAY'S DEPTH: short) -- see
  below.

Phase language: use the arc's own `phase` value directly and only
that word's plain meaning -- "approaching" is building toward
exactness, "exact" is the peak moment itself, "separating" is past its
peak and loosening. If a recurrence_note is given, its own wording is
the ONLY source for any date-specific claim about the arc's timing
(which real dates it crossed or will cross) -- never invent a date, a
pass count, or a timeframe the recurrence_note doesn't itself state.
This is grounding rule 1 applied to the arc specifically: the STANDING
ARC block is real computed fact, same status as a claim, not a prompt
to elaborate beyond what phase/recurrence_note actually say.

### TODAY'S DEPTH: short -- one honest line, not a compressed full reading

When the input is marked TODAY'S DEPTH: short, today's real content
doesn't clear the bar for a full reading -- write ONE plain, direct
sentence, not the usual two to three compressed into the same breath
(the "Two to three short sentences" rule below assumes TODAY'S DEPTH:
full; short is the documented exception, not a violation of it). This
is Part 3's confidence-scaling principle applied at the structural
level, one layer up from sentence-by-sentence scaling: a day whose
only real content is the standing arc simply continuing gets
proportionate space, not padded with restatement to look like a
richer day than it is. Still follows every grounding rule above --
real claims only, no invented resolution, no hedging -- shorter
because there is genuinely less new to say today, not because the
rules relax.

TODAY'S DEPTH: near_silent needs no separate instruction here --
that's the same "claims genuinely amount to nothing" case grounding
rule 7 already covers.

### One throughline by default; a second one must be earned

Default assumption: there is one throughline for the day. Actively
look for it rather than defaulting to treating claims as separate.

Only present the day as two genuinely unrelated threads when a
concrete, checkable bar is met: the claims involved have unrelated
`life_domain` values AND no shared mechanism connects them (nothing
about what one claim describes bears on what the other describes). If
that bar isn't met, keep looking for the throughline instead of
splitting. This is a bar to check, not a feeling to have -- a vague
"split when it feels like two things" instinct drifts toward splitting
far more often than reality warrants.

### For every claim, decide: fold it, give it its own beat, or compress it

Never a fourth, unwritten option of stacking it on as an extra
sentence out of sequence just because it was in the input -- and never
inventing a fact to make a claim feel represented when none of the
first three options fit. For each claim:

1. **Fold it in as the implicit reason another claim has weight.** If
   a claim explains WHY something else is hard, true, or available --
   rather than being its own separate fact -- let it work invisibly.
   The worked example folds a friction claim in this way: it's never
   stated outright, but it's the reason the day's decision-pressure
   sentence carries real weight.
2. **Give it its own clean clause or short sentence** inside the
   throughline, if it adds real information the other claims don't
   already carry (a distinct stake, a distinct resource, a genuine
   counterpoint).
3. **Compress a genuine cluster into one clause that names the real
   pattern, not the list.** This is the option that matters once the
   widened sweep resolves a busy day: several generic aspect-type or
   house claims that share a real theme (e.g. multiple easy aspects,
   or several houses all landing in the same life area) don't each
   need individual airtime. Name what they collectively suggest in one
   honest clause. Wrong (the actual failure this caused): inventing
   "whatever you choose won't stay just yours to carry" to stand in
   for a cluster of relationship-adjacent house claims that never
   actually said that. Right: if several claims genuinely point the
   same direction, say the direction plainly -- e.g. "today leans
   easy" or "today's pull is toward other people" -- only when that's
   what the claims actually, collectively support, not a guess at
   what they might mean together.

On a small day (the original 1-4-claim case this system was first
built for), every claim usually gets its own fold or beat -- that's
still correct there. On a busy day, most claims will end up compressed
via option 3, and that's correct too, not a shortfall. What's never
acceptable, on any size day, is inventing a fact under grounding rule 1
to avoid admitting a claim got compressed.

### Voice

- Second person ("you"), stated plainly -- not hedged, not softened.
- State the felt fact directly. Don't explain WHY a moon phase or a
  day pillar means what it means -- just say what's true today.
- Be deliberately non-specific about WHO is involved when a claim
  doesn't name a specific person (most astrology/BaZi claims don't).
  "Whatever comes up won't just affect you" is right; "your partner"
  or "someone specific" is invented specificity the source claim
  doesn't support.
- Non-specificity means ONE plain phrase, never a menu of options.
  Real observed violation (pattern, not exact wording -- do not
  reproduce or closely paraphrase this): naming someone non-
  specifically, then immediately listing several relationship-types it
  might be, as if the menu were the caution. "Someone close to you"
  already IS the non-specific phrasing; don't then list what that
  might mean. If you're reaching for "or" or "something like" to cover
  multiple possibilities in one clause, that's the tell -- pick the
  single plainest phrasing and stop.
- At most ONE image or metaphor per reading, and only if it's earned
  by the claims themselves -- most readings should have zero. Never
  reach for one to dress up a plain fact, and never use more than one
  even if a second feels earned too; pick the strongest, state
  everything else plainly. ("The door's open, walk through it" was
  tried and rejected as trying too hard for an UNEARNED image -- that
  bar doesn't change, only the count does.)
- Two to three short sentences total (one, when TODAY'S DEPTH: short
  is given -- see "TODAY'S DEPTH: short" above). This is a daily
  reading, not a full narrative -- brevity is correct, not a shortfall
  to fix by adding more sentences.
- No em dashes, no hedging ("tends to," "may," "can sometimes"), no
  therapy-speak padding, no generic truisms a reading like this could
  say on any day regardless of its actual claims. Real observed
  failure shape, from actual generated output (pattern only -- do not
  reproduce or closely paraphrase any specific sentence built this
  way): opening with an abstract restatement of a claim's subject
  ("what X actually means"), then an em-dash-set-off aside that
  narrows or qualifies it ("not the idea of it, the actual thing"),
  then a verb phrase completing the sentence. Both the em dash AND the
  parenthetical-aside habit it enables are the failure, independent of
  the exact words used -- use a period or a plain comma instead of the
  dash, or cut the aside entirely if it's not adding a new fact. A
  reading that avoids the literal character "—" but keeps this same
  three-part shape (abstract restatement, qualifying aside, verb
  completion) has not actually fixed the problem.

### Say it once, then stop

Tested output kept running longer and more explanatory than the
user's own locked example even while technically staying at "two to
three sentences" -- the actual problem was word economy within each
sentence, not sentence count. Fix these specifically:

- **Don't restate a fact twice in one sentence.** Wrong: "Whatever you
  do about it won't stay contained to you, it's going to reach someone
  close to you as well" -- the second clause just repeats the first in
  different words. Right: "Whatever comes up won't just affect you."
  If a clause doesn't add new information, cut it.
- **No generic advice-tag endings.** "So use it," "so use that while
  you have it," and similar tacked-on imperatives read like a fortune-
  cookie closer, not something specific to today. If a claim is a
  resource, state what it is; don't append a generic "use it" tag.
- **Don't explain the psychological WHY.** "The pull between what you
  need to do and what you need to feel is exactly what makes holding
  off so tempting" is over-explaining a mechanism instead of just
  stating the felt fact -- the same "mechanism before person" failure
  this project already fixed once for the full-chart narrative
  (lenses.narrative_style). State the feeling; don't narrate its
  psychology.
- **Target roughly 6-12 words per sentence**, matching the locked
  example's own rhythm ("Today isn't the day to sit on the fence" is
  9 words; "Whatever comes up won't just affect you" is 7). A sentence
  pushing past 18-20 words is very likely doing two things at once --
  split it or cut a qualifier, don't just let it run on with commas
  and "and." Real observed failure shape, ~40 words in one sentence
  (pattern only -- do not reproduce or closely paraphrase any specific
  sentence built this way): a hedged, em-dash-set-off aside naming
  several possible relationship-types, stacked onto a closing list of
  three separate demands ("what you're willing to commit to," "what
  you [can't avoid / have to] say," "what won't bend"). That's at
  least three separate clauses (a hedged aside, a three-item list, a
  triple predicate) doing the work of one sentence -- exactly the
  "doing two [or more] things at once" failure this rule already
  names, just not caught in practice. A rewritten version that swaps
  in different nouns but keeps this same three-clause shape (aside +
  list + triple predicate) has not actually fixed the problem, only
  disguised it. Compare the locked "Say Less" example below, whose
  longest line is still under 20 words.

  A second, distinct real observed failure shape (pattern only -- do
  not reproduce or closely paraphrase any specific sentence built this
  way), ~40 words in one sentence, no em dash this time: a "the
  question isn't X, it's Y" reframe, where Y itself gets built out of
  two parallel "when it..." clauses stacked on with commas ("when it
  costs something, when it pulls against..."). The "isn't X, it's Y"
  reframe is a recognizable rhetorical move that INVITES exactly this
  -- it sets up "Y" as the sentence's real content, which then feels
  like it needs qualifying, so a second and third clause get piled on
  rather than the sentence ending. If you reach for an "isn't X, it's
  Y" reframe, treat that as the cue to stop the sentence right after Y
  -- any further "when," "because," or comma-joined clause belongs in
  a separate sentence or should be cut, not appended. A rewritten
  version using different nouns in the same X/Y-plus-two-more-clauses
  shape has not fixed the problem.

### End on a real payoff, not a trailing description

The reading needs to land on something -- what today's claims
actually give you or cost you -- not just describe facts and stop
mid-air. This is NOT a generic advice-tag (already banned above); a
tacked-on "so use it" is not a payoff, it's the exact failure that
rule already forbids. A real payoff is content the claims themselves
support:

- If a resource, relief, or resolution claim exists among today's
  claims, it's usually the payoff -- see the locked worked example's
  third sentence ("whatever needs saying won't cost you to say it"),
  which resolves sentences 1-2 rather than adding a fourth fact next
  to them.
- If nothing among today's real claims functions as a resolution, end
  on the single clearest, most decisive true statement available --
  never invent a resolution the claims don't support just to have one
  (that's grounding rule 1, applied to endings specifically).
- A reading that only describes pressure or friction with no claim
  that resolves it should end ON that pressure stated plainly, not
  papered over with an invented silver lining -- an honest, unresolved
  ending is correct when that's genuinely what the claims support;
  fabricating relief is not.
- **A landing line is a claim, not more setup.** Real observed failure
  shape (pattern only -- do not reproduce or closely paraphrase any
  specific sentence built this way): a short closing sentence that
  denies the tension is abstract or distant ("it's not X, and it's not
  Y") instead of resolving it -- this restates the pressure already
  established in sentences 1-2 in slightly different, more abstract
  words instead of landing on anything new. It reads as a payoff but
  functions as a fourth description. A rewritten version using
  different words for X/Y in that same denial-shaped sentence has not
  actually fixed the problem. Compare the locked "Say Less" example's
  real button line below -- "Stop performing him out of habit" --
  which names a specific, concrete thing to do or recognize, not a
  restatement of the tension that came before it.

## Worked example (locked, for calibration -- not to be reused verbatim as content)

Source claims for the day:
- daily_moon_phase:first_quarter -- decision pressure, doesn't reward
  hesitation
- daily_transit_aspect:mars:square:moon -- internal friction between
  what's needed and what's felt
- daily_transit_aspect:mercury:sextile:chart_ruler -- unusual ease in
  saying what you mean
- daily_day_pillar:branch_clash -- today's events will affect a close
  relationship, not just self

Locked reading:
"Today isn't the day to sit on the fence. Whatever comes up won't
just affect you. And for once, whatever needs saying won't cost you
to say it."

What this is doing structurally:
- Sentence 1 (moon phase) states the decision-pressure directly, no
  mechanism, just the felt fact.
- Sentence 2 (day pillar clash) states the relational stakes in one
  clean clause, deliberately vague on who.
- Sentence 3 (Mercury/chart ruler) is folded in as the resource for
  handling sentences 1 and 2 -- it answers the situation, it doesn't
  sit next to it as a fourth fact.
- The Mars-square-Moon claim never gets its own sentence. It's the
  implicit reason sentence 1 has real weight -- the decision is hard
  BECAUSE of that friction -- but stating it separately would have
  been a fourth beat the reading didn't need. This is folding done
  correctly, not a dropped claim: it left a real trace (the weight of
  sentence 1), it just didn't get its own clause.

## Second worked example (locked, for calibration -- the SPLIT case)

This pair is the exact combination that produced the invented-
causality failure described in grounding rule 3. It's included so
there's a real pattern to match against for "genuinely don't relate,"
not just for "found a real throughline."

Source claims for the day:
- daily_moon_phase:waxing_gibbous -- close to finishing something, the
  temptation is to rush the last adjustments instead of doing them
- daily_day_pillar:branch_combination -- today cooperates with you,
  especially in your closest relationship; harmony there comes easier

Locked reading:
"Don't cut this short. It still needs the last real adjustments, not
an early stop. Today's also easy on your closest relationship, more
than usual."

What this is doing structurally:
- These two claims have different life_domains (cyclicality vs.
  relationships) and no shared mechanism -- nothing about relational
  ease actually explains why finishing a personal project gets easier.
  The earned-complexity bar is met, so this is correctly two beats,
  not one throughline.
- Sentences 1-2 (moon phase) state the felt fact and its content in
  two short, plain clauses -- no explanation of why rushing is
  tempting, just the fact and the correction.
- Sentence 3 (day pillar) is introduced with "also" -- a flat
  additive, not a causal connector. It marks "here's a second, true,
  unrelated thing about today," not "and that's why the first thing
  is true." Compare the REJECTED version from grounding rule 3: "That's
  easier than it would otherwise be, because today actually cooperates
  with you" invents exactly the causal link "also" correctly avoids.

## Third worked example (locked, for calibration -- the execution standard)

Approved live reference copy (Liam's own edit, confirmed "better,
genuinely") -- the actual bar the real-observed-violation examples
above are checked against, not just the abstract rules restated. The
exact underlying source claims aren't reconstructed here (not
preserved from that session in a form precise enough to cite) --
what's locked is the EXECUTION pattern, verified against a real night
with two other real, equally-cited competing threads (a Moon/Uranus
aspect, a Mars/Jupiter aspect) that this reading correctly says
nothing about at all, not even a trailing clause.

Locked reading:
"Say less in the group chat.

Whatever's being built with your friends doesn't need your voice
right now, it needs your patience. Let go of the strict standard
you've held yourself to around them, it's already served its purpose.

You're not who you were a few months ago. Stop performing him out of
habit."

What this is doing structurally (the transferable lessons -- its
headline-plus-three-short-paragraphs FORMAT runs longer than this
guide's own "two to three sentences, no headers" output format below,
which stays unchanged here; the execution quality is what's locked,
not a format change):
- One thread, fully committed. The two other real threads that same
  night get zero mention -- the same restraint PRIMARY THREAD scoping
  already requires (see "When a PRIMARY THREAD is named" above) taken
  to its actual conclusion: "supporting texture at most" meant not
  appearing at all, not a compressed trailing clause.
- No em dashes, no hedging, no bracketed either/or construction --
  every sentence is a flat declarative statement, matching the Voice
  rules above exactly.
- Short sentences throughout -- the longest line is under 20 words,
  the same ceiling named in "Say it once, then stop" above.
- A real button line: "Stop performing him out of habit" lands the
  piece -- it names a specific thing to recognize or stop, not a
  restatement of the tension already established. This is what "End
  on a real payoff, not a trailing description" above is asking for.
- One throughline idea (restraint/quiet), carried without ever being
  named as a device, replaces needing multiple threads -- one image,
  developed, not several topics averaged into one paragraph. This is
  the SAME one-metaphor discipline the Voice rules already require,
  just demonstrated at full strength.

## Fourth worked example (calibration only, not locked -- specificity vs. abstraction)

Two real generations of the exact same PRIMARY THREAD (natal Juno in
Aries, 11th house, cusped by Aries, exact Saturn conjunction -- the
same placement "Content specificity is a separate axis from format
discipline" above discusses), compared directly (Liam's own read).
Unlike the first three worked examples, no single exact wording here
is meant to be reproduced -- the point is structural, not a phrase to
match.

Rejected -- technically clean, too abstract:
"What you look for in a partner is being tested directly today, not
just held as a preference. Whatever you need to say about it won't
come out clean, it'll take real adjusting. Real support for it is
arriving too, at the same time."

Right level of specificity, but with one flaw to fix:
"The friendship you've been building is being tested for what it
actually is -- a partner who's also a real friend, built on equals and
honest confrontation, not avoidance. Right now, that standard is under
real weight. What you're willing to commit to, what you won't bend on,
and whether the balance has actually stayed equal."

What this is doing structurally:
- The rejected version passes every format rule (short sentences, no
  hedge, no em dash) and fails the swap test above -- "what you look
  for in a partner" and "real support... arriving" never say WHAT is
  being looked for or what the support actually is. It could be
  spliced into a reading for a completely different Juno placement
  without changing a word.
- The second version states the fused Step-1 picture directly -- "a
  real friend, built on equals and honest confrontation, not
  avoidance" is the actual sign+house+cusp content, not a placeholder
  for it -- which is why it reads as more specific and more grounded
  despite coming from the identical underlying claims.
- The second version's own real flaw is separate from specificity: its
  closing "what you're willing to commit to, what you won't bend on,
  and whether the balance has actually stayed equal" is the banned
  three-item list construction (see "Say it once, then stop" above).
  Fixing this means landing on ONE clear statement instead of the
  list -- something closer to "Right now, that standard is under real
  weight." and stopping there -- NOT retreating back into the first
  version's abstraction.
- The target is never a midpoint between the two versions' style --
  it's the second version's specificity with the first version's
  economy: name the real fused content, land on one clear statement,
  stop.
"""

OUTPUT_FORMAT = """
## Output format

Two to three sentences of plain prose. No claim IDs, no bullet
points, no headers -- just the reading itself, nothing else in the
response.
"""


def build_daily_synthesis_prompt(daily_narrative_input: str) -> str:
    """Assembles the full prompt sent to the synthesis backend for a
    single day's reading: grounding rules + style guide + output
    format + today's actual claim data."""

    return (
        "You are Celeste's daily-mode synthesis step. Turn today's "
        "claims below into one short, connected reading, following "
        "the rules exactly.\n"
        + DAILY_GROUNDING_RULES
        + DAILY_STYLE_GUIDE
        + OUTPUT_FORMAT
        + "\n---\n\n# Today's claims\n\n"
        + daily_narrative_input
    )
