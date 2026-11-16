"""Expected strings are derived by hand from the Java SkyperProtocol/MessageEncoder."""

from datetime import datetime

from dapnet import pager
from dapnet.pager import FunctionalBits, Priority


def test_de_ascii7():
    assert pager.encode_de_ascii7("ÄÖÜäöüß") == "[\\]{|}~"
    assert pager.encode_de_ascii7("é") == chr(0xE9 & 0x7F)
    assert pager.encode_de_ascii7("Hi") == "Hi"


def test_call_alphanumeric_and_numeric():
    call = {"text": "Grüße 123", "emergency": False}
    alpha = {"numeric": False, "pagers": [{"number": 12345, "name": "p1"}, {"number": 7, "name": "p2"}]}
    numeric = {"numeric": True, "pagers": [{"number": 99, "name": "num"}]}
    msgs = pager.messages_from_call(call, [alpha, numeric])
    assert [m.address for m in msgs] == [12345, 7]  # numeric pager skipped, text not numeric
    assert msgs[0].text == "Gr}~e 123"
    assert pager.encode_wire(0, msgs[0], 1) == b"#00 6:1:3039:3:Gr}~e 123\n"

    num_call = {"text": "123 u-(4)", "emergency": True}
    msgs = pager.messages_from_call(num_call, [numeric])
    assert msgs[0].bits == FunctionalBits.NUMERIC and msgs[0].priority == Priority.EMERGENCY
    assert pager.encode_wire(255, msgs[0], 1) == b"#FF 5:1:63:0:123 U-(4)\n"


def test_call_text_newlines_are_flattened():
    msgs = pager.messages_from_call({"text": "a\nb"}, [{"pagers": [{"number": 1}]}])
    assert msgs[0].text == "a b"


def test_time_formats():
    t = datetime(2026, 11, 16, 7, 8, 9)
    skyper, swiss, alphapoc = pager.messages_time(t)
    assert (skyper.text, skyper.address, skyper.bits) == ("070809   161126", 2504, FunctionalBits.NUMERIC)
    assert (swiss.text, swiss.address) == ("XTIME=0708161126XTIME=0708161126", 200)
    assert (alphapoc.text, alphapoc.address) == ("YYYYMMDDHHMMSS261116070800", 216)
    local = pager.messages_local_time(t)
    assert [m.address for m in local] == [208, 224]
    assert pager.encode_wire(0x1A, skyper, 1) == b"#1A 5:1:9C8:0:070809   161126\n"


def test_rubric_and_news():
    rubric = {"number": 1, "label": "Wx"}
    m = pager.message_rubric(rubric)
    assert m.text == "1" + chr(0x20) + chr(0x2A) + "Xy"
    assert (m.address, m.priority) == (4512, Priority.RUBRIC)
    n = pager.message_news({"text": "ab", "number": 1}, rubric)
    assert n.text == chr(0x20) + chr(0x21) + "bc"
    assert n.address == 4520
    c = pager.message_news_as_call({"text": "ab"}, {"number": 5})
    assert (c.text, c.address, c.priority) == ("ab", 1005, Priority.CALL)


def test_activation():
    code = "0 7 50,0 7 34,0 7 53,0 7 51,0 7 51,0 7 52,0 7 52,0 7 56"
    m = pager.message_activation(0, code)
    assert m.text == '2"533448'
    assert (m.address, m.bits) == (0, FunctionalBits.ACTIVATION)
    assert pager.message_activation(9, "0 7 50,3 7 50").text == chr(50 + 1) + chr(50 + 1)
    assert pager.message_activation(1, "bad") is None
    assert pager.encode_wire(0, m, 1).startswith(b"#00 6:1:0:2:")


def test_priority_order():
    a = pager.PagerMessage("r", 1, Priority.RUBRIC, FunctionalBits.ALPHANUM, 1.0)
    b = pager.PagerMessage("c", 1, Priority.CALL, FunctionalBits.ALPHANUM, 5.0)
    c = pager.PagerMessage("c2", 1, Priority.CALL, FunctionalBits.ALPHANUM, 2.0)
    e = pager.PagerMessage("e", 1, Priority.EMERGENCY, FunctionalBits.ALPHANUM, 9.0)
    assert [m.text for m in sorted([a, b, c, e])] == ["e", "c2", "c", "r"]
