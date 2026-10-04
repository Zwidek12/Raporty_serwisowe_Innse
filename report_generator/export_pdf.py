import os

import uno

from . import constants as C
from . import storage
from .document import props, get_user_property

PDF_FILTER = "writer_pdf_Export"
ODT_FILTER = "writer8"

OVERWRITE = "overwrite"
NEW_VERSION = "version"


def report_ticket(doc):
    return (get_user_property(doc, C.DOCPROP_TICKET, u"") or u"").strip()


def _pdf_filter_data():
    data = props(
        ExportBookmarks=True,
        UseTaggedPDF=True,
        ExportFormFields=False,
        Quality=90,
        ReduceImageResolution=True,
        MaxImageResolution=300,
    )
    return uno.Any("[]com.sun.star.beans.PropertyValue", data)


def save_odt(doc, path):
    url = uno.systemPathToFileUrl(path)
    doc.storeAsURL(url, props(FilterName=ODT_FILTER, Overwrite=True))


def export_pdf(doc, path):
    url = uno.systemPathToFileUrl(path)
    args = props(FilterName=PDF_FILTER, Overwrite=True)
    args = args + (_filter_data_prop(),)
    doc.storeToURL(url, args)


def _filter_data_prop():
    from com.sun.star.beans import PropertyValue
    pv = PropertyValue()
    pv.Name = "FilterData"
    pv.Value = _pdf_filter_data()
    return pv


def plan_output(folder, ticket, save_odt_flag, export_pdf_flag, ask_conflict):
    base = storage.report_base_name(ticket)
    exts = storage.selected_extensions(save_odt_flag, export_pdf_flag)
    existing = storage.find_existing(folder, base, exts)
    name = base
    if existing:
        decision = ask_conflict(existing)
        if decision is None:
            return None
        if decision == NEW_VERSION:
            name = storage.next_free_version(folder, base, exts)
    return storage.target_paths(folder, name, save_odt_flag, export_pdf_flag)


def save_and_export(doc, folder, ticket, settings, ask_conflict):
    save_flag = bool(settings.get("save_odt", True))
    pdf_flag = bool(settings.get("export_pdf", True))
    if not save_flag and not pdf_flag:
        raise ValueError(u"W ustawieniach wyłączono zarówno zapis ODT, "
                         u"jak i eksport PDF.")
    if not os.path.isdir(folder):
        os.makedirs(folder)
    paths = plan_output(folder, ticket, save_flag, pdf_flag, ask_conflict)
    if paths is None:
        return None
    if "odt" in paths:
        save_odt(doc, paths["odt"])
    if "pdf" in paths:
        export_pdf(doc, paths["pdf"])
    return paths
