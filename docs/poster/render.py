import sys
from pathlib import Path
from playwright.sync_api import sync_playwright
here = Path(sys.argv[1]).resolve()
fonts = here.parent.parent / "video" / "fonts"
css = "".join(f'@font-face{{font-family:"IBM Plex Sans Arabic";font-weight:{w};src:url("{(fonts/f).as_uri()}")}}'
              for w, f in [(400,"IBMPlexSansArabic-Regular.ttf"),(500,"IBMPlexSansArabic-Medium.ttf"),(600,"IBMPlexSansArabic-SemiBold.ttf"),(700,"IBMPlexSansArabic-Bold.ttf")])
with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={"width": 1123, "height": 1587}, device_scale_factor=2)
    pg.route("**/fonts.googleapis.com/**", lambda r: r.abort())
    pg.route("**/fonts.gstatic.com/**", lambda r: r.abort())
    pg.goto(here.as_uri())
    pg.add_style_tag(content=css)
    pg.evaluate("document.fonts.ready")
    pg.wait_for_timeout(500)
    pg.screenshot(path=sys.argv[2], clip={"x":0,"y":0,"width":1123,"height":1587})
    b.close()
