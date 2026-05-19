from forge_next.studio.assets import asset_text


def test_packaged_studio_assets_load() -> None:
    frame = asset_text("frame.html")
    js = asset_text("studio.js")
    assert "{{CONTENT}}" in frame
    assert "studioToggle" in js
