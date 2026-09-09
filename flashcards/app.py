"""
Flashcard authoring tool: internal-only, single-user Flask app for
Liam to write Document B's planet-house fragment library one card at
a time, with Document A's house-level reference tags visible
alongside. Never served to a Celeste end user -- run this
standalone (`python -m flashcards.app`), separate from web.py's
daily-reading pipeline, on its own port.

No AI generation here -- content entry is manual (pasting in
already-drafted text is fine), per the brief's explicit scope.
"""

from flask import Flask, redirect, render_template, request, url_for

from flashcards.storage import (
    HOUSES,
    PLANETS,
    adjacent_planet_card,
    card_at_index,
    card_index,
    get_card,
    get_document_a,
    init_db,
    progress_summary,
    save_card,
    total_cards,
)

app = Flask(__name__)
init_db()


@app.route("/")
def index():
    return redirect(url_for("card_view", index=0))


@app.route("/card/<int:index>")
def card_view(index: int):
    index = index % total_cards()
    planet, house = card_at_index(index)

    return render_template(
        "card.html",
        index=index,
        total=total_cards(),
        planet=planet,
        house=house,
        planets=PLANETS,
        houses=HOUSES,
        card=get_card(planet, house),
        document_a=get_document_a(house),
        reference_card=adjacent_planet_card(planet, house),
        progress=progress_summary(),
    )


@app.route("/card/<int:index>/save", methods=["POST"])
def save(index: int):
    index = index % total_cards()
    planet, house = card_at_index(index)

    fragments = request.form.getlist("fragment")
    status = request.form.get("status", "draft")
    save_card(planet, house, fragments, status)

    next_action = request.form.get("next_action", "stay")
    if next_action == "next":
        return redirect(url_for("card_view", index=index + 1))

    return redirect(url_for("card_view", index=index))


@app.route("/jump")
def jump():
    planet = request.args.get("planet")
    house = request.args.get("house", type=int)

    if planet not in PLANETS or house not in HOUSES:
        return redirect(url_for("index"))

    return redirect(url_for("card_view", index=card_index(planet, house)))


if __name__ == "__main__":
    # Distinct port from web.py's daily-reading scaffold (5000) so
    # both can run side by side during development.
    app.run(host="0.0.0.0", port=5050, debug=True)
