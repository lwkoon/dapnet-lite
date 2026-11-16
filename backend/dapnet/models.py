"""Model schemas and validation.

Objects are kept as plain dicts with the original camelCase field names, so the state
file and REST payloads stay identical to DAPNET Core. Violations use the same error
codes as the Java ConstraintViolationExceptionDescriptor.
"""

from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation
from typing import Any, Callable

ADDR_MAX = 2097151  # 21-bit RIC

EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}$")


class ValidationError(Exception):
    def __init__(self, violations: list[dict]):
        super().__init__(f"{len(violations)} violation(s)")
        self.violations = violations


def _v(code: int, constraint: str, fld: str, value: Any, message: str) -> dict:
    return {
        "code": code,
        "constraint": constraint,
        "field": fld,
        "value": None if value is None else str(value),
        "message": message,
    }


# --- field rules ----------------------------------------------------------------------
# Each rule: (field, kind, options). Kinds coerce the value and append violations.

def _str(lo: int, hi: int, required: bool = True):
    return ("str", {"min": lo, "max": hi, "required": required})


def _int(lo: int, hi: int, default: int = 0):
    return ("int", {"min": lo, "max": hi, "default": default})


def _float(lo: float, hi: float):
    return ("float", {"min": lo, "max": hi})


def _decimal(int_digits: int, frac_digits: int, lo: float, hi: float):
    return ("decimal", {"int": int_digits, "frac": frac_digits, "min": lo, "max": hi})


def _list(min_size: int = 1, ref: str | None = None, constraint: str = "", code: int = 6200):
    return ("list", {"min": min_size, "ref": ref, "constraint": constraint, "code": code})


def _ref(ref: str, constraint: str, code: int):
    return ("ref", {"ref": ref, "constraint": constraint, "code": code})


def _enum(*values: str, default: str | None = None):
    return ("enum", {"values": values, "default": default})


SCHEMAS: dict[str, list[tuple[str, str, dict]]] = {
    "user": [
        ("name", *_str(3, 20)),
        ("hash", *_str(1, 512)),
        ("mail", "email", {}),
        ("admin", "bool", {}),
    ],
    "callsign": [
        ("name", *_str(3, 20)),
        ("description", *_str(0, 60)),
        ("numeric", "bool", {}),
        ("pagers", "pagers", {}),
        ("ownerNames", *_list(1, "users", "ValidOwnerNames", 6202)),
    ],
    "transmitter": [
        ("name", *_str(3, 20)),
        ("authKey", *_str(1, 64)),
        ("longitude", *_decimal(3, 8, -180, 180)),
        ("latitude", *_decimal(3, 8, -90, 90)),
        ("power", *_decimal(3, 3, 0, 200)),
        ("timeSlot", "timeslot", {}),
        ("ownerNames", *_list(1, "users", "ValidOwnerNames", 6202)),
        ("status", *_enum("OFFLINE", "ONLINE", "ERROR", "DISABLED", default="OFFLINE")),
        ("antennaAboveGroundLevel", *_int(0, 1000)),
        ("antennaType", *_enum("OMNI", "DIRECTIONAL")),
        ("antennaDirection", *_int(0, 359)),
        ("antennaGainDbi", *_float(-50, 80)),
        ("usage", *_enum("WIDERANGE", "PERSONAL")),
        ("identificationAddress", *_int(0, ADDR_MAX, default=1)),
    ],
    "transmitterGroup": [
        ("name", *_str(3, 20)),
        ("description", *_str(0, 60)),
        ("transmitterNames", *_list(1, "transmitters", "ValidTransmitterNames", 6207)),
        ("ownerNames", *_list(1, "users", "ValidOwnerNames", 6202)),
    ],
    "rubric": [
        ("name", *_str(3, 20)),
        ("number", *_int(1, 95)),
        ("transmitterGroupNames", *_list(1, "transmitterGroups", "ValidTransmitterGroupNames", 6203)),
        ("label", *_str(1, 11)),
        ("ownerNames", *_list(1, "users", "ValidOwnerNames", 6202)),
    ],
    "news": [
        ("text", *_str(1, 80)),
        ("rubricName", *_ref("rubrics", "ValidRubricName", 6205)),
        ("number", *_int(0, 10)),
        ("ownerName", *_ref("users", "ValidOwnerName", 6201)),
    ],
    "call": [
        ("text", *_str(1, 80)),
        ("callSignNames", *_list(1, "callSigns", "ValidCallSignNames", 6204)),
        ("transmitterGroupNames", *_list(1, "transmitterGroups", "ValidTransmitterGroupNames", 6203)),
        ("emergency", "bool", {}),
        ("ownerName", *_ref("users", "ValidOwnerName", 6201)),
    ],
    "activation": [
        ("number", *_int(0, ADDR_MAX)),
        ("transmitterGroupNames", *_list(1, "transmitterGroups", "ValidTransmitterGroupNames", 6203)),
    ],
    "node": [
        ("name", *_str(3, 20)),
        ("longitude", *_decimal(3, 8, -180, 180)),
        ("latitude", *_decimal(3, 8, -90, 90)),
        ("status", *_enum("ONLINE", "SUSPENDED", "UNKNOWN", default="UNKNOWN")),
        ("ownerNames", *_list(1, "users", "ValidOwnerNames", 6202)),
    ],
}


def _check_timeslot(value: str) -> bool:
    last = -1
    for ch in value:
        try:
            slot = int(ch, 16)
        except ValueError:
            return False
        if slot <= last:
            return False
        last = slot
    return True


def _to_int(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float) and value.is_integer():
        return int(value)
    if isinstance(value, str) and re.fullmatch(r"\s*-?\d+\s*", value):
        return int(value)
    return None


def validate(kind: str, data: dict, exists: Callable[[str, str], bool]) -> dict:
    """Validate and normalise `data` for model `kind`. Returns a new dict containing only
    schema fields. `exists(collection, name)` checks references. Raises ValidationError."""
    if not isinstance(data, dict):
        raise ValidationError([_v(6001, "NotNull", "", None, "may not be null")])
    out: dict[str, Any] = {}
    errs: list[dict] = []
    for name, rule, opt in SCHEMAS[kind]:
        val = data.get(name)
        if rule == "str":
            if val is None:
                errs.append(_v(6001, "NotNull", name, None, "may not be null"))
                continue
            val = str(val)
            if not opt["min"] <= len(val) <= opt["max"]:
                errs.append(_v(6002, "Size", name, val, f"size must be between {opt['min']} and {opt['max']}"))
        elif rule == "int":
            if val is None:
                val = opt["default"]
            iv = _to_int(val)
            if iv is None:
                errs.append(_v(6000, "Type", name, val, "must be an integer"))
                continue
            val = iv
            if val < opt["min"]:
                errs.append(_v(6003, "Min", name, val, f"must be greater than or equal to {opt['min']}"))
            elif val > opt["max"]:
                errs.append(_v(6004, "Max", name, val, f"must be less than or equal to {opt['max']}"))
        elif rule == "float":
            try:
                val = float(val if val is not None else 0)
            except (TypeError, ValueError):
                errs.append(_v(6000, "Type", name, val, "must be a number"))
                continue
            if val < opt["min"]:
                errs.append(_v(6003, "Min", name, val, f"must be greater than or equal to {opt['min']}"))
            elif val > opt["max"]:
                errs.append(_v(6004, "Max", name, val, f"must be less than or equal to {opt['max']}"))
        elif rule == "decimal":
            if val is None:
                errs.append(_v(6001, "NotNull", name, None, "may not be null"))
                continue
            val = str(val).strip()
            try:
                d = Decimal(val)
                if not d.is_finite():
                    raise InvalidOperation
            except InvalidOperation:
                errs.append(_v(6005, "Digits", name, val, "numeric value out of bounds"))
                continue
            sign, digits, exp = d.as_tuple()
            frac = max(0, -exp)
            intd = max(0, len(digits) + exp) if exp < 0 else len(digits) + exp
            if intd > opt["int"] or frac > opt["frac"]:
                errs.append(_v(6005, "Digits", name, val,
                               f"numeric value out of bounds (<{opt['int']} digits>.<{opt['frac']} digits> expected)"))
            elif d < opt["min"]:
                errs.append(_v(6003, "Min", name, val, f"must be greater than or equal to {opt['min']}"))
            elif d > opt["max"]:
                errs.append(_v(6004, "Max", name, val, f"must be less than or equal to {opt['max']}"))
        elif rule == "bool":
            val = bool(val) if not isinstance(val, str) else val.lower() == "true"
        elif rule == "email":
            if val is None or not EMAIL_RE.match(str(val)):
                errs.append(_v(6102, "EMail", name, val, "not a well-formed email address"))
        elif rule == "timeslot":
            if val is None:
                errs.append(_v(6001, "NotNull", name, None, "may not be null"))
                continue
            val = str(val).upper()
            if not _check_timeslot(val):
                errs.append(_v(6101, "TimeSlot", name, val, "invalid time slot"))
        elif rule == "enum":
            if val is None:
                val = opt["default"]
            if val is None or str(val).upper() not in opt["values"]:
                errs.append(_v(6001, "NotNull", name, val, "must be one of " + ", ".join(opt["values"])))
                continue
            val = str(val).upper()
        elif rule == "list":
            if val is None:
                errs.append(_v(6001, "NotNull", name, None, "may not be null"))
                continue
            if isinstance(val, str):
                val = [val]
            val = list(dict.fromkeys(str(x).strip().lower() for x in val if str(x).strip()))
            if len(val) < opt["min"]:
                errs.append(_v(6002, "Size", name, None, f"must contain at least {opt['min']} entry"))
            elif opt["ref"] and not all(exists(opt["ref"], x) for x in val):
                errs.append(_v(opt["code"], opt["constraint"], name, None, f"must contain names of existing {opt['ref']}"))
        elif rule == "ref":
            if val is None:
                errs.append(_v(6001, "NotNull", name, None, "may not be null"))
                continue
            val = str(val).strip().lower()
            if not exists(opt["ref"], val):
                errs.append(_v(opt["code"], opt["constraint"], name, None, f"must be the name of an existing {opt['ref']}"))
        elif rule == "pagers":
            pagers = []
            if not isinstance(val, list) or not val:
                errs.append(_v(6002, "Size", name, None, "must contain at least one pager"))
                continue
            for i, p in enumerate(val):
                if not isinstance(p, dict):
                    errs.append(_v(6001, "NotNull", f"{name}[{i}]", None, "may not be null"))
                    continue
                num = _to_int(p.get("number"))
                pname = str(p.get("name") or "")
                if num is None or not 0 <= num <= ADDR_MAX:
                    errs.append(_v(6004, "Max", f"{name}[{i}].number", p.get("number"), "pager number is limited to 21 bits"))
                if not 3 <= len(pname) <= 20:
                    errs.append(_v(6002, "Size", f"{name}[{i}].name", pname, "size must be between 3 and 20"))
                pagers.append({"number": num, "name": pname})
            val = pagers
        out[name] = val
    if errs:
        raise ValidationError(errs)
    return out


# --- role based views ------------------------------------------------------------------

# Fields hidden from plain users / anonymous callers (Java ExclusionStrategies.USER).
HIDDEN_FOR_USER = {"callsign": {"pagers"}, "transmitter": {"authKey"}, "user": {"hash", "mail"}}
# Fields never returned (Java ExclusionStrategies.ADMIN).
HIDDEN_ALWAYS = {"user": {"hash"}}

# Full field lists so REST output always contains every key (Gson serializeNulls).
FIELDS = {
    "user": ["name", "hash", "mail", "admin"],
    "callsign": ["name", "description", "numeric", "pagers", "ownerNames"],
    "transmitter": [
        "name", "authKey", "longitude", "latitude", "power", "nodeName", "address", "timeSlot",
        "ownerNames", "deviceType", "deviceVersion", "callCount", "status", "antennaAboveGroundLevel",
        "antennaType", "antennaDirection", "antennaGainDbi", "lastUpdate", "usage",
        "identificationAddress", "lastConnected", "connectedSince",
    ],
    "transmitterGroup": ["name", "description", "transmitterNames", "ownerNames"],
    "rubric": ["name", "number", "transmitterGroupNames", "label", "ownerNames"],
    "news": ["text", "rubricName", "number", "timestamp", "ownerName"],
    "call": ["text", "callSignNames", "transmitterGroupNames", "emergency", "timestamp", "ownerName"],
    "activation": ["number", "transmitterGroupNames", "timestamp"],
    "node": ["name", "longitude", "latitude", "address", "status", "ownerNames", "version"],
}


def view(kind: str, obj: dict | None, privileged: bool) -> dict | None:
    if obj is None:
        return None
    hidden = set(HIDDEN_ALWAYS.get(kind, ()))
    if not privileged:
        hidden |= HIDDEN_FOR_USER.get(kind, set())
    out = {k: obj.get(k) for k in FIELDS[kind] if k not in hidden}
    if kind == "transmitter" and out.get("callCount") is None:
        out["callCount"] = 0
    return out
