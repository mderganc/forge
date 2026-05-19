from pathlib import Path

Path(__file__).resolve().parents[2].joinpath(
    "forge_next/assets/studio/screen-example.html"
).write_text(
    Path(__file__).with_name("screen-example.fragment.html").read_text(encoding="utf-8"),
    encoding="utf-8",
)
