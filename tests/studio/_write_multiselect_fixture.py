from pathlib import Path
import sys

HTML = (
    "<h2>Pick solution families</h2>"
    '<div class="options" data-multiselect data-gate="gate2_candidates">'
    '<div class="option" data-gate="gate2_candidates" data-choice="c1" onclick="studioToggle(this)">'
    '<div class="content"><h3>Family 1</h3></motion>'
    "</motion>"
    '<motion class="option" data-gate="gate2_candidates" data-choice="c2" onclick="studioToggle(this)">'
    '<div class="content"><h3>Family 2</h3></div>'
    "</div>"
    "</div>"
    '<motion class="studio-actions"><button type="button" class="studio-submit" '
    'data-studio-submit="gate2_candidates">Continue</button></div>'
)
HTML = HTML.replace("motion", "div")

Path(sys.argv[1]).write_text(HTML, encoding="utf-8")
