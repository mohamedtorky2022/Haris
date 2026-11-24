"""Fake helplines: a named bank or authority with a number to call that is not one it publishes."""

from haris import phones
from haris.detector import analyze


def _check(text):
    return phones.check(text)


def test_a_mobile_number_offered_as_dewa_helpline_is_flagged():
    hit = _check("DEWA: your supply will be cut today. Call customer service on 055 123 4567 now")
    assert hit["entity"] == "dewa" and hit["kind"] == "mobile" and hit["official"] == "04 601 9999"


def test_published_numbers_in_any_spelling_are_not_flagged():
    for text in ("Call DEWA customer care on 04 601 9999", "DEWA: call +971 4 601 9999",
                 "ADCB: call us on +971 2 621 0090 from abroad", "Emirates NBD: contact 600540000",
                 "شرطة دبي: للاستفسار اتصل 901", "TAMM: call 800555", "UAE PASS support: call (600) 56 1111",
                 "Mashreq: call 00971 4 424 4444"):
        assert _check(text) is None, text


def test_codes_amounts_and_dates_are_not_phone_numbers():
    assert _check("Your OTP for ADCB is 482913. Never share it.") is None
    assert _check("Emirates NBD: for help contact 600 54 0000 before 2026-11-30") is None
    assert _check("ADCB: pay AED 1500, call your branch") is None


def test_a_number_from_abroad_or_an_unknown_landline():
    assert _check("هيئة كهرباء ومياه دبي: اتصل على +44 7700 900123")["kind"] == "foreign"
    assert _check("UAE PASS: contact support on 04 555 1212")["weight"] == 20
    assert _check("Is 800 5551 the number of TAMM?")["entity"] == "tamm"


def test_an_entity_without_a_verified_list_is_not_judged():
    assert _check("Aramex: your parcel is held, call 055 123 4567") is None


def test_the_reason_names_the_official_number_and_comes_first():
    r = analyze("ديوا: سيتم فصل الكهرباء اليوم بسبب فاتورة غير مسددة، اتصل فوراً على 0551234567", "ar",
                use_llm=False, inspect_sites=False)
    assert r["risk"] == "high" and "unofficial_number" in r["signals"]
    assert "04 601 9999" in r["reasons"][0] and "0551234567" in r["reasons"][0]
    alone = analyze("DEWA customer service: call 055 123 4567", "en", use_llm=False, inspect_sites=False)
    assert alone["risk"] == "medium"
    assert analyze("Call DEWA on 04 601 9999", "en", use_llm=False, inspect_sites=False)["risk"] == "low"
