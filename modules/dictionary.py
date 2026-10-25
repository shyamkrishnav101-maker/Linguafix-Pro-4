import json
from pathlib import Path


class DictionaryEngine:
    """Layered dictionary: common words + chat + technical + proper nouns."""

    def __init__(self, base_dir="dictionaries"):
        self.base_dir = Path(base_dir)
        self.common_words = set()
        self.chat = {}
        self.technical = set()
        self.proper_nouns = set()
        self.custom = set()

        self._load_builtin()
        self._load_files()

    def _load_builtin(self):
        # Core vocabulary used for safe protection even without a downloaded dictionary.
        words = """
        a an the i you he she it we they me my your his her our their this that these those
        am is are was were be been being have has had do does did can could will would shall
        should may might must to of in on at for from with by about into over under after
        before and or but because if then than so as while when where what who whom which
        why how not no yes very more most good better best bad new old easy hard useful
        need want like love make made get got give take use used learn study student college
        school university project course help explain create build write read go going come
        python java javascript html css flask django react node database api model machine
        learning artificial intelligence ai data science cybersecurity cyber security network
        algorithm program programming code developer development system sentence word english
        grammar spelling correction meaning intent suggestion information question answer
        please thank thanks hello hi hey today tomorrow yesterday home office work job internship
        book ticket hotel table movie see sea pair shoes bank river computer software hardware
        """.split()
        self.common_words.update(w.lower() for w in words)

    def _load_files(self):
        self._load_json("abbreviations.json", self.chat)
        self._load_json_set("technical_words.json", self.technical)
        self._load_json_set("proper_nouns.json", self.proper_nouns)
        self._load_json_set("custom_words.json", self.custom)

    def _load_json(self, filename, target):
        path = self.base_dir / filename
        if not path.exists():
            return
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                target.update({str(k).lower(): str(v) for k, v in data.items()})
        except Exception:
            pass

    def _load_json_set(self, filename, target):
        path = self.base_dir / filename
        if not path.exists():
            return
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(data, list):
                target.update(str(x).lower() for x in data)
            elif isinstance(data, dict):
                target.update(str(x).lower() for x in data.keys())
        except Exception:
            pass

    def is_known(self, word):
        w = word.lower().strip()
        return (
            w in self.common_words
            or w in self.chat
            or w in self.technical
            or w in self.proper_nouns
            or w in self.custom
        )

    def is_protected(self, word):
        w = word.lower().strip()
        return w in self.technical or w in self.proper_nouns

    def expand_chat(self, word):
        return self.chat.get(word.lower().strip())

    def size(self):
        return (
            len(self.common_words)
            + len(self.chat)
            + len(self.technical)
            + len(self.proper_nouns)
            + len(self.custom)
        )
