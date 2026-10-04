from . import constants as C
from .storage import read_json

CUSTOM_CATEGORY_ID = "custom"
CUSTOM_CATEGORY_TITLE = u"★ Własne frazy"


class PhraseLibrary(object):
    def __init__(self, data, custom_phrases=None):
        data = data or {}
        self.categories = []
        for cat in data.get("categories", []):
            phrases = [p for p in cat.get("phrases", [])
                       if p.get("title") and p.get("text")]
            self.categories.append({
                "id": cat["id"],
                "title": cat.get("title", cat["id"]),
                "phrases": phrases,
            })
        self.device_profiles = data.get("device_profiles", {})
        self.custom = list(custom_phrases or [])

    @classmethod
    def load(cls, path=None, custom_phrases=None):
        data = read_json(path or C.PHRASES_DEFAULT_FILE, {})
        return cls(data, custom_phrases)

    def ordered_categories(self, device_type=None):
        by_id = dict((c["id"], c) for c in self.categories)
        result = []
        if self.custom:
            result.append({"id": CUSTOM_CATEGORY_ID,
                           "title": CUSTOM_CATEGORY_TITLE,
                           "phrases": self.custom})
        seen = set()
        for cat_id in self.device_profiles.get(device_type or u"", []):
            if cat_id in by_id and cat_id not in seen:
                result.append(by_id[cat_id])
                seen.add(cat_id)
        for cat in self.categories:
            if cat["id"] not in seen:
                result.append(cat)
                seen.add(cat["id"])
        return result

    def all_phrases(self):
        for cat in self.categories:
            for phrase in cat["phrases"]:
                yield cat, phrase
        for phrase in self.custom:
            yield {"id": CUSTOM_CATEGORY_ID,
                   "title": CUSTOM_CATEGORY_TITLE}, phrase
