from . import constants as C
from .parser import parse_block, normalize_spaces
from .validators import normalize_date


def _clean(value):
    return normalize_spaces(value or u"")


def report_title(report_type, status):
    if status == C.ST_NOT_CONFIRMED and report_type in C.REPAIR_REPORT_TYPES:
        return C.TITLE_DIAGNOSTICS
    return C.REPORT_TITLES.get(report_type, C.TITLE_SERVICE)


def work_heading(report_type, status):
    if status == C.ST_NOT_CONFIRMED and report_type in C.REPAIR_REPORT_TYPES:
        return C.HEAD_WORK_DEFAULT
    return C.WORK_HEADINGS.get(report_type, C.HEAD_WORK_DEFAULT)


def work_intro(report_type, status):
    if status == C.ST_NOT_CONFIRMED and report_type in C.REPAIR_REPORT_TYPES:
        return C.WORK_INTRO_DEFAULT
    return C.WORK_INTROS.get(report_type, C.WORK_INTRO_DEFAULT)


def status_text(status, custom_text=u""):
    if status == C.ST_CUSTOM:
        return (custom_text or u"").strip()
    return C.STATUS_TEXTS.get(status, u"")


def status_short_label(status):
    if status in (C.ST_NONE, C.ST_CUSTOM, None, u""):
        return u""
    return status


def _variant(texts, index):
    try:
        index = int(index)
    except (TypeError, ValueError):
        index = 0
    if index < 0 or index >= len(texts):
        index = 0
    return texts[index]


def build_report(form):
    report_type = form.get("report_type") or C.RT_OTHER
    status = form.get("status") or C.ST_NONE

    fields = {
        C.BM_REPORT_TITLE: report_title(report_type, status),
        C.BM_REPORT_DATE: normalize_date(form.get("report_date")),
        C.BM_TICKET_NUMBER: _clean(form.get("ticket")),
        C.BM_RECEIPT_DATE: normalize_date(form.get("receipt_date"))
        if _clean(form.get("receipt_date")) else u"",
        C.BM_TECHNICIAN: _clean(form.get("technician")),
        C.BM_DEVICE_MANUFACTURER: _clean(form.get("manufacturer")),
        C.BM_DEVICE_MODEL: _clean(form.get("model")),
        C.BM_DEVICE_SERIAL: _clean(form.get("serial")),
        C.BM_DEVICE_TYPE: _clean(form.get("device_type_text")),
        C.BM_DEVICE_STATUS: status_short_label(status),
    }

    plan = [
        (C.FIELD_CUSTOMER, C.HEAD_CUSTOMER, u""),
        (C.FIELD_DIAGNOSIS, C.HEAD_DIAGNOSIS,
         _variant(C.DIAGNOSIS_INTROS, form.get("diagnosis_intro", 0))),
        (C.FIELD_WORK, work_heading(report_type, status),
         work_intro(report_type, status)),
        (C.FIELD_TESTS, C.HEAD_TESTS,
         _variant(C.TESTS_INTROS, form.get("tests_intro", 0))),
    ]

    number = 0
    sections = {}
    for key, heading, intro in plan:
        items = parse_block(form.get(key))
        if not items:
            sections[key] = None
            continue
        number += 1
        sections[key] = {
            "number": number,
            "heading": u"%d. %s" % (number, heading),
            "intro": intro,
            "items": items,
        }

    final = None
    text = status_text(status, form.get("custom_status"))
    if text:
        number += 1
        final = {
            "number": number,
            "heading": u"%d. %s" % (number, C.HEAD_FINAL),
            "text": text,
        }

    return {
        "title": fields[C.BM_REPORT_TITLE],
        "fields": fields,
        "sections": sections,
        "final": final,
        "ticket": fields[C.BM_TICKET_NUMBER],
    }


def report_as_text(model):
    f = model["fields"]
    lines = [model["title"], u""]
    lines.append(u"Data sporządzenia: %s" % f[C.BM_REPORT_DATE])
    lines.append(u"Numer zgłoszenia: %s" % f[C.BM_TICKET_NUMBER])
    if f[C.BM_RECEIPT_DATE]:
        lines.append(u"Data przyjęcia: %s" % f[C.BM_RECEIPT_DATE])
    if f[C.BM_TECHNICIAN]:
        lines.append(u"Serwis / technik: %s" % f[C.BM_TECHNICIAN])
    lines.append(u"Dane urządzenia:")
    lines.append(u"• Producent / Model: %s %s" % (
        f[C.BM_DEVICE_MANUFACTURER], f[C.BM_DEVICE_MODEL]))
    if f[C.BM_DEVICE_SERIAL]:
        lines.append(u"• Numer seryjny: %s" % f[C.BM_DEVICE_SERIAL])
    if f[C.BM_DEVICE_TYPE]:
        lines.append(u"• Rodzaj urządzenia: %s" % f[C.BM_DEVICE_TYPE])
    if f[C.BM_DEVICE_STATUS]:
        lines.append(u"• Status: %s" % f[C.BM_DEVICE_STATUS])
    for key in C.TEXT_FIELDS:
        sec = model["sections"].get(key)
        if not sec:
            continue
        lines.append(u"")
        lines.append(sec["heading"])
        if sec["intro"]:
            lines.append(sec["intro"])
        for item in sec["items"]:
            lines.append(u"• " + item.as_line())
    if model["final"]:
        lines.append(u"")
        lines.append(model["final"]["heading"])
        lines.append(model["final"]["text"])
    return u"\n".join(lines)
