#!/usr/bin/env python3
"""
parse.py — Extract MFA journal frequencies from DIAGRAM issue files
and produce map/data.json with geocoded coordinates.

Run from any directory:
    python3 /home/user/DIAGRAM/map/parse.py
"""

import re
import json
import os
from collections import defaultdict

# ---------------------------------------------------------------------------
# Hardcoded geocoded lookup: journal filename stem → (institution, city, state, lat, lng)
# "No location" journals use the well-known associated university.
# ---------------------------------------------------------------------------
GEO = {
    "12thStreet":               ("The New School",                      "New York",         "NY",  40.7359, -74.0036),
    "45thParallel":             ("Oregon State University",              "Corvallis",        "OR",  44.5638,-123.2794),
    "AGNI":                     ("Boston University",                    "Boston",           "MA",  42.3505, -71.1054),
    "AcreBooks":                ("University of Cincinnati",             "Cincinnati",       "OH",  39.1031, -84.5120),
    "AmericanLetters&Commentary":("UT San Antonio",                      "San Antonio",      "TX",  29.5843, -98.6204),
    "AmericanLiteraryReview":   ("U of North Texas",                    "Denton",           "TX",  33.2148, -97.1331),
    "ArkansasInternational":    ("U of Arkansas",                       "Fayetteville",     "AR",  36.0682, -94.1719),
    "Arts&Letters":             ("Georgia College & State University",   "Milledgeville",    "GA",  33.0801, -83.2321),
    "BarelySouth":              ("Old Dominion University",              "Norfolk",          "VA",  36.8854, -76.3050),
    "BatCityReview":            ("UT Austin",                           "Austin",           "TX",  30.2849, -97.7341),
    "BayouMagazine":            ("University of New Orleans",           "New Orleans",      "LA",  29.9511, -90.0715),
    "BellinghamReview":         ("Western Washington University",        "Bellingham",       "WA",  48.7340,-122.4857),
    "BlackForkReview":          ("Ashland University",                   "Ashland",          "OH",  40.8698, -82.3182),
    "BlackWarriorReview":       ("University of Alabama",               "Tuscaloosa",       "AL",  33.2098, -87.5692),
    "Blackbird":                ("Virginia Commonwealth University",     "Richmond",         "VA",  37.5484, -77.4513),
    "BlueEarthReview":          ("Minnesota State University",           "Mankato",          "MN",  44.1636, -94.0009),
    "BlueMesaReview":           ("University of New Mexico",            "Albuquerque",      "NM",  35.0844,-106.6504),
    "BombayGin":                ("Naropa University",                   "Boulder",          "CO",  40.0150,-105.2705),
    "Booth":                    ("Butler University",                    "Indianapolis",     "IN",  39.8390, -86.1696),
    "BreakwaterReview":         ("UMass Boston",                        "Boston",           "MA",  42.3143, -71.0383),
    "BrooklynReview":           ("Brooklyn College CUNY",               "Brooklyn",         "NY",  40.6312, -73.9518),
    "CimarronReview":           ("Oklahoma State University",           "Stillwater",       "OK",  36.1156, -97.0584),
    "CincinnatiReview":         ("University of Cincinnati",            "Cincinnati",       "OH",  39.1031, -84.5120),
    "Clamor":                   ("UW Bothell",                          "Bothell",          "WA",  47.7601,-122.2046),
    "CoachellaReview":          ("UC Riverside",                        "Riverside",        "CA",  33.9737,-117.3281),
    "ColaLiteraryReview":       ("USC Columbia",                        "Columbia",         "SC",  33.9941, -81.0302),
    "Collision":                ("University of Pittsburgh",            "Pittsburgh",       "PA",  40.4406, -79.9959),
    "ColoradoReview":           ("Colorado State University",           "Fort Collins",     "CO",  40.5734,-105.0865),
    "ColumbiaJournal":          ("Columbia University",                 "New York",         "NY",  40.8075, -73.9626),
    "ColumbiaPoetryReview":     ("Columbia College Chicago",            "Chicago",          "IL",  41.8781, -87.6298),
    "Cottonwood":               ("University of Kansas",                "Lawrence",         "KS",  38.9717, -95.2353),
    "CrabOrchardReview":        ("Southern Illinois University",        "Carbondale",       "IL",  37.7273, -89.2168),
    "CrazyHorse aka Swamppink": ("College of Charleston",               "Charleston",       "SC",  32.7765, -79.9311),
    "CreamCityReview":          ("UW Milwaukee",                        "Milwaukee",        "WI",  43.0731, -87.9024),
    "CutBank":                  ("University of Montana",               "Missoula",         "MT",  46.8721,-113.9940),
    "Defunct":                  ("Long Island University",              "Brooklyn",         "NY",  40.6892, -73.9862),
    "DenverQuarterly":          ("University of Denver",                "Denver",           "CO",  39.6774,-104.9619),
    "DevilsLake":               ("University of Wisconsin",             "Madison",          "WI",  43.0731, -89.4012),
    "EPOCH":                    ("Cornell University",                  "Ithaca",           "NY",  42.4534, -76.4735),
    "Ecotone":                  ("UNC Wilmington",                      "Wilmington",       "NC",  34.2257, -77.9447),
    "Faultline":                ("UC Irvine",                           "Irvine",           "CA",  33.6405,-117.8443),
    "Fiction":                  ("City College of New York CUNY",       "New York",         "NY",  40.8196, -73.9499),
    "FictionInternational":     ("San Diego State University",          "San Diego",        "CA",  32.7757,-117.0719),
    "FloridaReview":            ("University of Central Florida",       "Orlando",          "FL",  28.6024, -81.2001),
    "Flyway":                   ("Iowa State University",               "Ames",             "IA",  42.0308, -93.6319),
    "Folio":                    ("American University",                 "Washington",       "DC",  38.9361, -77.0873),
    "FourteenHills":            ("San Francisco State University",      "San Francisco",    "CA",  37.7247,-122.4786),
    "FourthGenre":              ("BYU",                                 "Provo",            "UT",  40.2338,-111.6585),
    "FourthRiver":              ("Chatham University",                  "Pittsburgh",       "PA",  40.4406, -79.9959),
    "Fugue":                    ("University of Idaho",                 "Moscow",           "ID",  46.7298,-117.0002),
    "Furrow":                   ("UW Milwaukee",                        "Milwaukee",        "WI",  43.0731, -87.9024),
    "GreensboroReview":         ("UNC Greensboro",                      "Greensboro",       "NC",  36.0726, -79.7920),
    "Grist":                    ("University of Tennessee",             "Knoxville",        "TN",  35.9544, -83.9235),
    "GulfCoast":                ("University of Houston",               "Houston",          "TX",  29.7174, -95.4028),
    "GulfStream":               ("Florida International University",    "Miami",            "FL",  25.7562, -80.3760),
    "HarpurPalate":             ("Binghamton University",               "Binghamton",       "NY",  42.0987, -76.0677),
    "HaydensFerryReview":       ("Arizona State University",            "Tempe",            "AZ",  33.4242,-111.9281),
    "HopkinsReview":            ("Johns Hopkins University",            "Baltimore",        "MD",  39.3299, -76.6205),
    "HotelAmerika":             ("Columbia College Chicago",            "Chicago",          "IL",  41.8781, -87.6298),
    "HungerMountain":           ("Vermont College of Fine Arts",        "Montpelier",       "VT",  44.2601, -72.5754),
    "IdahoReview":              ("Boise State University",              "Boise",            "ID",  43.6016,-116.2023),
    "IndianaReview":            ("Indiana University",                  "Bloomington",      "IN",  39.1653, -86.5264),
    "Inscape":                  ("BYU",                                 "Provo",            "UT",  40.2338,-111.6585),
    "Interim":                  ("University of Nevada Las Vegas",      "Las Vegas",        "NV",  36.1023,-115.1745),
    "InvisibleCity":            ("University of San Francisco",         "San Francisco",    "CA",  37.7769,-122.4516),
    "IowaReview":               ("University of Iowa",                  "Iowa City",        "IA",  41.6611, -91.5302),
    "JellyBucket":              ("Eastern Kentucky University",         "Richmond",         "KY",  37.7482, -84.2946),
    "LIT":                      ("The New School",                      "New York",         "NY",  40.7359, -74.0036),
    "LunchTicket":              ("Antioch University Los Angeles",      "Culver City",      "CA",  34.0195,-118.3964),
    "MadisonReview":            ("University of Wisconsin",             "Madison",          "WI",  43.0731, -89.4012),
    "Mangrove":                 ("University of Miami",                 "Coral Gables",     "FL",  25.7218, -80.2685),
    "MassachussettsReview":     ("UMass Amherst",                       "Amherst",          "MA",  42.3868, -72.5301),
    "McNeeseReview":            ("McNeese State University",            "Lake Charles",     "LA",  30.2207, -93.2177),
    "Meridian":                 ("University of Virginia",              "Charlottesville",  "VA",  38.0336, -78.5080),
    "MichiganQuarterly":        ("University of Michigan",              "Ann Arbor",        "MI",  42.2808, -83.7430),
    "Mid-AmericanReview":       ("Bowling Green State University",      "Bowling Green",    "OH",  41.3781, -83.6524),
    "MississippiReview":        ("U of Southern Mississippi",           "Hattiesburg",      "MS",  31.3271, -89.2903),
    "MissouriReview":           ("University of Missouri",              "Columbia",         "MO",  38.9517, -92.3341),
    "NashvilleReview":          ("Vanderbilt University",               "Nashville",        "TN",  36.1447, -86.8027),
    "NaturalBridge":            ("U of Missouri St. Louis",             "St. Louis",        "MO",  38.7092, -90.3043),
    "NewDeltaReview":           ("Louisiana State University",          "Baton Rouge",      "LA",  30.4133, -91.1800),
    "NewLetters":               ("U of Missouri Kansas City",           "Kansas City",      "MO",  39.0997, -94.5786),
    "NewOhioReview":            ("Ohio University",                     "Athens",           "OH",  39.3292, -82.1013),
    "NewRiver":                 ("Virginia Tech",                       "Blacksburg",       "VA",  37.2296, -80.4139),
    "NinthLetter":              ("University of Illinois",              "Urbana",           "IL",  40.1020, -88.2272),
    "NorthwestReview":          ("University of Oregon",                "Eugene",           "OR",  44.0521,-123.0868),
    "Oxford":                   ("Miami University Ohio",               "Oxford",           "OH",  39.5070, -84.7452),
    "PRISMinternational":       ("University of British Columbia",      "Vancouver",        "BC",  49.2606,-123.2460),
    "PassagesNorth":            ("Northern Michigan University",        "Marquette",        "MI",  46.5436, -87.3954),
    "Permafrost":               ("University of Alaska Fairbanks",      "Fairbanks",        "AK",  64.8401,-147.7200),
    "Phoebe":                   ("George Mason University",             "Fairfax",          "VA",  38.8316, -77.3131),
    "Pinch":                    ("University of Memphis",               "Memphis",          "TN",  35.1175, -89.9711),
    "Ploughshares":             ("Emerson College",                     "Boston",           "MA",  42.3494, -71.0632),
    "PoetryEast":               ("DePaul University",                   "Chicago",          "IL",  41.9247, -87.6561),
    "PoetryInternational":      ("San Diego State University",          "San Diego",        "CA",  32.7757,-117.0719),
    "PoetrySouth":              ("Mississippi University for Women",    "Columbus",         "MS",  33.4962, -88.4273),
    "PonderReview":             ("Mississippi University for Women",    "Columbus",         "MS",  33.4962, -88.4273),
    "PortlandReview":           ("Portland State University",           "Portland",         "OR",  45.5118,-122.6841),
    "PrairieSchooner":          ("University of Nebraska",              "Lincoln",          "NE",  40.8136, -96.7026),
    "Promethean":               ("City College of New York CUNY",       "New York",         "NY",  40.8196, -73.9499),
    "PuertodelSol":             ("New Mexico State University",         "Las Cruces",       "NM",  32.2841,-106.7485),
    "QuarterAfterEight":        ("Ohio University",                     "Athens",           "OH",  39.3292, -82.1013),
    "QuarterlyWest":            ("University of Utah",                  "Salt Lake City",   "UT",  40.7649,-111.8421),
    "Redivider":                ("Emerson College",                     "Boston",           "MA",  42.3494, -71.0632),
    "ReedMagazine":             ("San Jose State University",           "San Jose",         "CA",  37.3352,-121.8811),
    "RioGrandeReview":          ("UT El Paso",                          "El Paso",          "TX",  31.7700,-106.5000),
    "RiverTeeth":               ("Ball State University",               "Muncie",           "IN",  40.1934, -85.3864),
    "RubbertopReview":          ("NEOMFA Consortium",                   "Youngstown",       "OH",  41.0998, -80.6495),
    "Rune":                     ("MIT",                                 "Cambridge",        "MA",  42.3601, -71.0942),
    "SaltHill":                 ("Syracuse University",                 "Syracuse",         "NY",  43.0481, -76.1474),
    "SawPalm":                  ("University of South Florida",         "Tampa",            "FL",  28.0587, -82.4139),
    "SewaneeReview":            ("University of the South",             "Sewanee",          "TN",  35.2032, -85.9219),
    "Shadowplay":               ("U of Arkansas Monticello",            "Monticello",       "AR",  33.6326, -91.7863),
    "SlagGlassCity":            ("DePaul University",                   "Chicago",          "IL",  41.9247, -87.6561),
    "SonoraReview":             ("University of Arizona",               "Tucson",           "AZ",  32.2319,-110.9501),
    "SotoSpeak":                ("George Mason University",             "Fairfax",          "VA",  38.8316, -77.3131),
    "SouthamptonReview":        ("Stony Brook University",              "Southampton",      "NY",  40.9012, -72.3875),
    "SoutheastReview":          ("Florida State University",            "Tallahassee",      "FL",  30.4419, -84.2985),
    "SouthernReview":           ("Louisiana State University",          "Baton Rouge",      "LA",  30.4133, -91.1800),
    "StonecoastReview":         ("University of Southern Maine",        "Portland",         "ME",  43.6591, -70.2568),
    "StoryQuarterly":           ("Rutgers University",                  "New Brunswick",    "NJ",  40.4774, -74.4455),
    "Subtropics":               ("University of Florida",               "Gainesville",      "FL",  29.6436, -82.3549),
    "SwampApeReview":           ("Florida Atlantic University",         "Boca Raton",       "FL",  26.3682, -80.1029),
    "TAB":                      ("Chapman University",                  "Orange",           "CA",  33.7953,-117.8536),
    "TINGE":                    ("Temple University",                   "Philadelphia",     "PA",  39.9812, -75.1548),
    "TampaReview":              ("University of Tampa",                 "Tampa",            "FL",  27.9506, -82.4572),
    "TexasReview":              ("Sam Houston State University",        "Huntsville",       "TX",  30.7235, -95.5506),
    "TheJournal":               ("Ohio State University",               "Columbus",         "OH",  39.9960, -83.0300),
    "ThinAirMagazine":          ("Northern Arizona University",         "Flagstaff",        "AZ",  35.1983,-111.6513),
    "ThirdCoast":               ("Western Michigan University",         "Kalamazoo",        "MI",  42.2917, -85.5872),
    "Timber":                   ("University of Colorado Boulder",      "Boulder",          "CO",  40.0150,-105.2705),
    "TriQuarterly":             ("Northwestern University",             "Evanston",         "IL",  42.0565, -87.6753),
    "VirginiaQuarterlyReview":  ("University of Virginia",              "Charlottesville",  "VA",  38.0336, -78.5080),
    "WashingtonSquareReview":   ("New York University",                 "New York",         "NY",  40.7295, -73.9965),
    "Water~Stone":              ("Hamline University",                  "St. Paul",         "MN",  44.9537, -93.1201),
    "WesternHumanitiesReview":  ("University of Utah",                  "Salt Lake City",   "UT",  40.7649,-111.8421),
    "WillowSprings":            ("Eastern Washington University",       "Cheney",           "WA",  47.4874,-117.5750),
    "YalobushaReview":          ("University of Mississippi",           "Oxford",           "MS",  34.3665, -89.5192),
    "mojo":                     ("Wichita State University",            "Wichita",          "KS",  37.7172, -97.2931),
    "storySouth":               ("UNC Greensboro",                      "Greensboro",       "NC",  36.0726, -79.7920),
}

# Year-range folder names and their label
PERIODS = [
    ("Years 1-5",   "1–5"),
    ("Years 6-10",  "6–10"),
    ("Years 11-15", "11–15"),
    ("Years 16-20", "16–20"),
    ("Years 21-25", "21–25"),
]

ISSUES_ROOT = os.path.join(os.path.dirname(__file__), "..", "Issues")
MFA_ROOT    = os.path.join(os.path.dirname(__file__), "..", "Journals", "MFA Journals")

WIKILINK_RE = re.compile(r'\[\[([^\]]+)\]\]')

def normalize(raw: str) -> str:
    """Strip path prefixes from wikilinks, e.g. 'Journals/ColoradoReview' → 'ColoradoReview'."""
    # Drop anything before the last '/'
    return raw.rsplit("/", 1)[-1]


def count_appearances(folder):
    """Return dict {journal_stem: count} for all .md files in folder."""
    counts = defaultdict(int)
    folder_path = os.path.join(ISSUES_ROOT, folder)
    if not os.path.isdir(folder_path):
        return counts
    for fname in os.listdir(folder_path):
        if not fname.endswith(".md"):
            continue
        with open(os.path.join(folder_path, fname), encoding="utf-8") as f:
            for m in WIKILINK_RE.finditer(f.read()):
                counts[normalize(m.group(1))] += 1
    return counts


def main():
    # Count by period
    period_counts = {}
    for folder, label in PERIODS:
        period_counts[label] = count_appearances(folder)

    # Build journal records
    journals = []
    for stem, (institution, city, state, lat, lng) in GEO.items():
        by_period = {}
        total = 0
        for _, label in PERIODS:
            c = period_counts[label].get(stem, 0)
            by_period[label] = c
            total += c

        journals.append({
            "id":          stem,
            "name":        stem,          # display name = stem; can be overridden manually
            "institution": institution,
            "city":        city,
            "state":       state,
            "lat":         lat,
            "lng":         lng,
            "total":       total,
            "by_period":   by_period,
        })

    # Sort by total descending
    journals.sort(key=lambda j: j["total"], reverse=True)

    out_path = os.path.join(os.path.dirname(__file__), "data.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({"journals": journals}, f, indent=2, ensure_ascii=False)

    print(f"Wrote {len(journals)} journals to {out_path}")
    for j in journals[:20]:
        print(f"  {j['total']:>4}  {j['name']:<35} {j['city']}, {j['state']}")


if __name__ == "__main__":
    main()
