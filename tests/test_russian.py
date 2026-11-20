"""Russian, the fifth language: detection, scam signals, report intake, WhatsApp."""

from haris import alerts
from haris import whatsapp as wa
from haris.detector import analyze
from haris.intake import extract
from haris.text import detect_language, normalize

SCAMS = [
    "Ваша посылка задержана на таможне. Оплатите сбор 5 дирхамов в течение 24 часов по ссылке: https://emirates-post-ru.top/pay",
    "Служба безопасности банка: ваша карта заблокирована. Сообщите код из смс, чтобы разблокировать.",
    "Поздравляем! Вы выиграли iPhone. Чтобы получить приз, оплатите доставку 25 дирхамов: http://prize-uae.top",
    "Гарантированная прибыль 30% в неделю без риска! Инвестиции в USDT, пишите в WhatsApp.",
    "Удаленная работа, доход в день от 500 дирхамов. Нужно только оплатить регистрационный взнос.",
]
GENUINE = [
    "Ваш заказ отправлен. Код отслеживания 123456, курьер привезёт завтра.",
    "Привет, мама! Буду дома к ужину.",
    "Ваш код подтверждения 482910. Никому не сообщайте этот код.",
]


def test_cyrillic_is_russian_and_yo_matches_ye():
    assert detect_language("Здравствуйте, это сообщение") == "ru"
    assert normalize("Ещё") == normalize("еще")


def test_russian_scams_are_flagged():
    for text in SCAMS:
        r = analyze(text, "ru")
        assert r["risk"] in ("medium", "high"), (text, r["risk"], r.get("reasons"))
        assert r["risk_label"] and r["summary"]


def test_genuine_russian_messages_are_not_high_risk():
    for text in GENUINE:
        assert analyze(text, "ru")["risk"] != "high", text


def test_story_in_russian_fills_the_report():
    out = extract("Сегодня утром я перевел 3 400 дирхамов по ссылке и позвонил в банк, заблокировал карту.", [], "ru")
    f = out["fields"] if "fields" in out else out
    assert f.get("incident_type") == "money_sent"
    assert f.get("currency") == "AED"


def test_whatsapp_in_russian():
    reply = wa.handle({"id": "r1", "from": "79000000001", "type": "text", "text": "привет", "reply_id": ""})[0]
    assert reply["interactive"]["body"]["text"] == wa.TEXT["ru"]["welcome"]
    assert alerts.command("ОПОВЕЩЕНИЯ") == "subscribe" and alerts.command("стоп") == "stop"
    for label in wa.TEXT["ru"]["buttons"].values():
        assert len(label) <= 20, label
    for title in wa.TEXT["ru"]["playbooks"].values():
        assert len(title) <= 24, title
