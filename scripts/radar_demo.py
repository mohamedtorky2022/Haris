"""Send the same scam message to the campaign radar from several "people", for a live demo.

    python scripts/radar_demo.py                 # 10 reports to http://127.0.0.1:8000
    python scripts/radar_demo.py --people 3      # just enough for "reported by 3 people"
    python scripts/radar_demo.py --message 1     # a different sample campaign
    python scripts/radar_demo.py --message 3 --people 4   # a fake car ad seen on four platforms

Then open http://127.0.0.1:8000/authority.html to see the campaign and approve the warning.
Uses only the standard library. Each "person" is a random device id, like a real browser.
"""

from __future__ import annotations

import argparse
import json
import urllib.request
import uuid

MESSAGES = [
    # 0: fake Emirates Post fee, from three different numbers (one campaign)
    ("ar", "عزيزي العميل، طردك محتجز بسبب عنوان غير مكتمل. ادفع 5 دراهم خلال 24 ساعة: "
           "https://emirates-post-ae.top/track أو اتصل {phone}", ["0501234567", "0559876543", "0524443322"]),
    # 1: fake rental deposit
    ("ar", "شقة غرفة وصالة في المرسى بـ 2500 درهم. المالك مسافر، حوّل عربون لحجز الشقة قبل المعاينة على الرقم {phone}",
     ["0567778899"]),
    # 2: guaranteed visa, in Urdu
    ("ur", "دبئی کا ورک ویزا گارنٹی کے ساتھ، بغیر شرط۔ ویزا فیس 4000 درہم بھیجیں، رابطہ {phone}", ["+971585556677"]),
    # 3: a fake car ad, reported with "Report a fake ad" from several platforms (fictional number)
    ("ar", "[إعلان وهمي · {platform}]\nبورش كايين موديل 2024 للبيع بسعر 200 ألف درهم، أقل من سعر السوق بداعي السفر. "
           "لحجز السيارة حوّل عربون 1000 درهم وتعال شوفها. واتساب {phone}", ["0500000123"]),
]
PLATFORMS = ["Instagram", "Facebook", "TikTok", "Dubizzle"]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--people", type=int, default=10)
    parser.add_argument("--message", type=int, default=0, choices=range(len(MESSAGES)))
    parser.add_argument("--url", default="http://127.0.0.1:8000")
    args = parser.parse_args()

    lang, template, phones = MESSAGES[args.message]
    for i in range(args.people):
        text = template.format(phone=phones[i % len(phones)], platform=PLATFORMS[i % len(PLATFORMS)])
        body = {"text": text, "lang": lang, "reporter_id": str(uuid.uuid4())}
        request = urllib.request.Request(f"{args.url}/api/radar/report", data=json.dumps(body).encode(),
                                         headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(request, timeout=10) as resp:
            campaign = json.load(resp).get("campaign") or {}
        print(f"report {i + 1:>2}: {campaign.get('people', 0)} people, status: {campaign.get('status')}")
    print(f"\nOpen {args.url}/authority.html to review the campaign.")


if __name__ == "__main__":
    main()
