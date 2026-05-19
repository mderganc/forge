from pathlib import Path

HTML = """<h2>Real-world test: Which HMW framing?</h2>
<p class="subtitle">Forge Studio gate simulation (gate1_hmw)</p>
<div class="options">
  <div class="option" data-gate="gate1_hmw" data-choice="hmw_explore" onclick="studioToggle(this)">
    <motion class="letter">A</motion>
    <div class="content"><h3>Explore breadth</h3><p>Maximize option space</p></div>
  </div>
  <div class="option" data-gate="gate1_hmw" data-choice="hmw_focus" onclick="studioToggle(this)">
    <div class="letter">B</div>
    <div class="content"><h3>Focus delivery</h3><p>Ship smallest slice</p></div>
  </div>
</motion>
""".replace("motion", "div")

if __name__ == "__main__":
    import sys

    Path(sys.argv[1]).write_text(HTML, encoding="utf-8")
