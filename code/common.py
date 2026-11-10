"""Shared paths, constants and helpers for the fame-half-life study ("The half-life of fame").

Inputs (read in place, never modified):
  RAW/fame_wd.tsv           Wikidata (CC0, QLever export): every human with an English Wikipedia article and a date of
                            death in 2016 to 2023: QID, English article title, date of death, date of birth, sex, one
                            sampled occupation, one sampled country of citizenship, sitelink count. Rows repeat where an
                            item has several values (100,689 rows, 98,246 people).
  RAW/fame_pageviews.json   Wikimedia pageviews REST API, en.wikipedia, agent=user, monthly, 2015-07 to 2026-10, for a
                            fixed 30% sample (hash(QID) mod 10 < 3, h = (h*31 + charCode) >>> 0 over the QID string).
                            {QID: [[YYYYMM, views], ...]}; months with no views are absent; [] = no article under that
                            title at fetch time; QIDs missing = fetch failure (20). CC0.
  RAW/fame_labels.tsv       English labels for the occupation, sex and country QIDs, with one superclass (P279) where
                            present (Wikidata, CC0).
  RAW/enwiki_monthly.json   Total English Wikipedia user pageviews per month, 2015-07 to 2026-10 (Wikimedia, CC0).
  GEO/ne_50m_admin_0_countries.geojson  Natural Earth countries (public domain), with WIKIDATAID for joining.
"""
import json, gzip, os, re, math

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.environ.get("FH_RAW", "/home/claude/newdata/raw_new12")
GEO = os.environ.get("FH_GEO", "/home/claude/newdata/raw/geo")
FONTS = os.environ.get("FH_FONTS", "/home/claude/ref/fonts")
SCR = os.environ.get("FH_SCRATCH", "/home/claude/scratch/fame-half-life")
DATA = os.path.join(ROOT, "data")
IMG = os.path.join(ROOT, "img")
REL = os.path.join(ROOT, "release")
for d in (DATA, IMG, SCR):
    os.makedirs(d, exist_ok=True)

SLUG = "fame-half-life"
PAGE = f"https://maps.tristanhotham.com/{SLUG}/"
REPO = f"https://github.com/Tristan-Hotham/{SLUG}"
AI = ("I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped "
      "prepare the analysis code. I reviewed and checked all text and results.")
BYLINE = "Dr Tristan Hotham · Independent researcher · 2026"

M0 = 2015 * 12 + 6          # month index of 2015-07 (index = year*12 + month-1)
M1 = 2026 * 12 + 9          # 2026-10
NM = M1 - M0 + 1            # 136 months
KMIN, KMAX = -48, 60        # event window stored per person
BASE = (-12, -2)            # baseline months (inclusive)
PEAK = (0, 1)
YEAR1 = (10, 14)
LONG = (24, 34)
MIN_BASE = 6
FLOOR = 0.05                # floor on ratios before logs in geometric means
ENGLISH = {"Q30": "United States", "Q145": "United Kingdom", "Q16": "Canada", "Q408": "Australia", "Q664": "New Zealand", "Q27": "Ireland"}

FAMILIES = ["Performers", "Writers and artists", "Sport", "Politics and law", "Science and academia", "Business",
            "Military", "Religion", "Journalism and media", "Other"]
FAM_SHORT = {"Performers": "performers", "Writers and artists": "writers and artists", "Sport": "sportspeople",
             "Politics and law": "politicians and lawyers", "Science and academia": "scientists and academics",
             "Business": "businesspeople", "Military": "military people", "Religion": "religious figures",
             "Journalism and media": "journalists and broadcasters", "Other": "others"}
# keyword rules on the occupation label, then on its superclass label (first match wins, in this order)
RULES = [
    ("Journalism and media", r"journalist|broadcaster|news ?presenter|television presenter|radio presenter|radio personality|presenter|columnist|editor|publisher|reporter|commentator|announcer|talk show|disc jockey|newspaper|podcaster|youtuber|blogger|sports journalist|critic\b"),
    ("Sport", r"player|athlete|footballer|cricketer|coach|boxer|wrestler|cyclist|swimmer|rower|jockey|racing driver|racer|skier|skater|golfer|tennis|sprinter|runner|marathon|referee|umpire|fencer|judoka|karateka|martial artist|weightlifter|gymnast|sailor\b|canoeist|kayak|sport shooter|archer|mountaineer|climber|equestrian|bobsledder|luger|biathlete|curler|triathlete|decathlete|hurdler|jumper|thrower|darts|snooker|billiards|bowler|motorcycle|rally driver|racewalker|pentathlete|chess|sportsperson|sports official|bodybuilder|surfer|polo|handball|volleyball|softball|lacrosse|hockey|rugby|baseball|basketball|badminton|squash|table tennis|water polo|diver\b|speedway|sumo|kickboxer|mixed martial|drag racer|nascar|team owner|manager \(sport|sports executive|olympic"),
    ("Military", r"military|soldier|officer|general\b|admiral|army|naval|air force|aviator|pilot|fighter pilot|marine|commander|resistance fighter|partisan|guerrilla|war\b|veteran|sailor"),
    ("Religion", r"priest|bishop|rabbi|imam|cleric|pastor|minister of religion|monk|nun\b|religious|theologian|missionary|cardinal|archbishop|deacon|evangelist|preacher|abbot|abbess|friar|lama|swami|guru|ayatollah|mufti|sheikh|presbyter|clergy|chaplain|vicar|rector|patriarch|saint|religious sister|catholic|anglican|orthodox"),
    ("Politics and law", r"politician|diplomat|judge|lawyer|jurist|attorney|barrister|solicitor|civil servant|statesman|mayor|governor|senator|legislator|member of parliament|monarch|king\b|queen\b|prince|princess|aristocrat|noble|activist|trade unionist|political|official|bureaucrat|ambassador|prosecutor|magistrate|police|law enforcement|revolutionary|dissident|human rights|campaigner|lobbyist|feminist|suffragist|public servant|head of state|president|prime minister|chieftain|royal|notary|ruler|sovereign|spy\b|intelligence"),
    ("Science and academia", r"scientist|physicist|chemist|biologist|mathematician|academic|professor|university teacher|researcher|historian|economist|sociologist|psychologist|philosopher|linguist|anthropologist|archaeologist|astronomer|geologist|engineer|physician|surgeon|doctor|medical|nurse|botanist|zoologist|ecologist|geographer|statistician|computer scientist|inventor|pharmacologist|psychiatrist|neurologist|neuroscientist|geneticist|biochemist|epidemiologist|virologist|immunologist|scholar|philologist|literary scholar|art historian|musicologist|educator|teacher|pedagogue|lecturer|librarian|archivist|curator|ornithologist|entomologist|meteorologist|oceanographer|paleontologist|veterinarian|dentist|pharmacist|cardiologist|oncologist|pathologist|agronomist|explorer|astronaut|cosmonaut|political scientist|jurist|legal scholar|theorist|demographer|criminologist|orientalist|sinologist|egyptologist|classicist|indologist|economist|scientific|science|computer|programmer|software|chemical|mechanical|electrical|architect\w* engineer"),
    ("Business", r"business|entrepreneur|executive|banker|industrialist|manager|merchant|investor|financier|trader|chief executive|ceo|philanthropist|economist business|accountant|real estate|restaurateur|chef|cook|hotelier|farmer|rancher|founder|shipowner|publisher business|consultant|salesperson|retailer|employer"),
    ("Performers", r"actor|actress|singer|musician|composer|songwriter|rapper|comedian|dancer|ballet|choreograph|conductor|pianist|guitarist|drummer|bassist|violinist|cellist|organist|saxophonist|trumpeter|percussionist|instrumentalist|vocalist|disc jockey|dj\b|entertainer|magician|clown|circus|performer|stand-up|voice actor|film director|director|filmmaker|film producer|television producer|producer|theatre|stage|puppeteer|model\b|pornographic|drag|cinematographer|film editor|animator|musical|band|record producer|music|opera|lyricist|impresario|stunt|game show|reality television|influencer|showman|television personality|media personality"),
    ("Writers and artists", r"writer|screenwriter|playwright|dramatist|author|poet|novelist|essayist|lyricist|translator|painter|sculptor|artist|photographer|illustrator|cartoonist|comics|designer|architect|printmaker|engraver|ceramicist|potter|calligrapher|fashion|jeweller|graphic|visual|art\b|craftsman|biographer|memoirist|children's writer|short story|science fiction|screenwriter|creator|plastic artist"),
]
RULES = [(f, re.compile(r"\b(?:" + p + ")", re.I)) for f, p in RULES]
# labels the keyword rules get wrong (checked by eye against data/occupations.csv, top 400 occupations)
OVERRIDE = {"political scientist": "Science and academia", "legal scholar": "Science and academia", "legal historian": "Science and academia",
            "film editor": "Performers", "recording artist": "Performers", "disc jockey": "Performers", "police officer": "Politics and law",
            "minister": "Politics and law", "aircraft pilot": "Other", "horse trainer": "Sport", "science fiction writer": "Writers and artists",
            "social worker": "Other", "serial killer": "Other", "criminal": "Other", "murderer": "Other", "art collector": "Other",
            "pediatrician": "Science and academia", "television director": "Performers", "theatre director": "Performers",
            "music educator": "Science and academia", "military flight engineer": "Military", "sports commentator": "Journalism and media",
            "chief executive officer": "Business", "military historian": "Science and academia", "Formula One driver": "Sport",
            "flautist": "Performers", "herpetologist": "Science and academia", "caricaturist": "Writers and artists",
            "penciller": "Writers and artists", "photojournalist": "Journalism and media", "justice of the peace": "Politics and law",
            "coxswain": "Sport", "psychotherapist": "Science and academia", "lexicographer": "Science and academia"}


def family(occ_label, sup_label=None):
    """broad occupation family from the occupation label, then its superclass label"""
    if isinstance(occ_label, str) and occ_label in OVERRIDE:
        return OVERRIDE[occ_label]
    for lab in (occ_label, sup_label):
        if not isinstance(lab, str) or not lab:
            continue
        for f, rx in RULES:
            if rx.search(lab):
                return f
    return "Other"


def qid(iri):
    m = re.search(r"(Q\d+)", str(iri))
    return m.group(1) if m else None


def lit(s):
    s = str(s)
    m = re.match(r'^"(.*)"(@\w+|\^\^.*)?$', s)
    return m.group(1) if m else re.sub(r"@[a-z][a-z-]*$", "", s)


def hsample(q):
    h = 0
    for c in q:
        h = (h * 31 + ord(c)) & 0xFFFFFFFF
    return h % 10 < 3


def jload(path):
    op = gzip.open if path.endswith(".gz") else open
    with op(path, "rt", encoding="utf-8") as f:
        return json.load(f)


def dash(v):
    if isinstance(v, str):
        v = re.sub(r"(\d)\s*[–—]\s*(\d)", r"\1 to \2", v)
        v = v.replace(" — ", ", ").replace("—", ", ").replace(" – ", ", ").replace("–", "-")
        while "--" in v:
            v = v.replace("--", "-")
        return v
    if isinstance(v, list):
        return [dash(x) for x in v]
    if isinstance(v, dict):
        return {k: dash(x) for k, x in v.items()}
    return v


def nonan(v):
    if isinstance(v, float) and (v != v or v in (float("inf"), float("-inf"))):
        return None
    if isinstance(v, (list, tuple)):
        return [nonan(x) for x in v]
    if isinstance(v, dict):
        return {str(k): nonan(x) for k, x in v.items()}
    if hasattr(v, "item"):
        return nonan(v.item())
    return v


def jsave(obj, path, indent=None, keepdash=False):
    obj = nonan(obj) if keepdash else dash(nonan(obj))
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, allow_nan=False, indent=indent, separators=None if indent else (",", ":"))


def get(R, path):
    v = R
    for k in path.split("."):
        v = v[int(k)] if isinstance(v, list) else v[k]
    return v


def fmt(v, f=None):
    if f is None or f == "raw": return str(v)
    if f == "int": return f"{round(float(v)):,}"
    if f == "pc": return f"{round(float(v))}%"
    if f == "pc1": return f"{float(v):.1f}%"
    if f == "f0": return f"{float(v):.0f}"
    if f == "f1": return f"{float(v):.1f}"
    if f == "f2": return f"{float(v):.2f}"
    if f == "f3": return f"{float(v):.3f}"
    if f == "x1": return f"{float(v):.1f} times"
    if f == "abs": return f"{abs(round(float(v))):,}"
    raise ValueError(f)
