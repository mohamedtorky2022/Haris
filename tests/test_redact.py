from haseen.redact import find_identifiers, luhn_valid, redact


def test_card_number_with_valid_luhn_is_redacted():
    r = redact("My card is 4111 1111 1111 1111 please help")
    assert "[CARD]" in r.text
    assert "4111" not in r.text
    assert r.counts == {"CARD": 1}


def test_long_number_failing_luhn_is_kept():
    r = redact("Order number 1234567890123456")
    assert "1234567890123456" in r.text
    assert r.total == 0


def test_emirates_id_phone_email_and_iban():
    r = redact("ID 784-1990-1234567-1, call 050 123 4567, mail a.b@x.ae, IBAN AE07 0331 2345 6789 0123 456")
    assert "[EMIRATES_ID]" in r.text
    assert "[PHONE]" in r.text
    assert "[EMAIL]" in r.text
    assert "[IBAN]" in r.text


def test_arabic_indic_digits_are_normalised_before_redaction():
    r = redact("رقمي ٠٥٠١٢٣٤٥٦٧")
    assert "[PHONE]" in r.text


def test_international_phone():
    assert "[PHONE]" in redact("WhatsApp me on +971 55 987 6543").text


def test_luhn():
    assert luhn_valid("4111111111111111")
    assert not luhn_valid("4111111111111112")


def test_find_identifiers_in_victim_description():
    found = find_identifiers("He called from 0501234567 and asked me to pay to AE070331234567890123456, email scam@fake.com")
    assert found["phones"] == ["0501234567"]
    assert found["emails"] == ["scam@fake.com"]
    assert found["ibans"]
