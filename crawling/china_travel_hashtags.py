# Sourced from Calplus (https://github.com/Calplus)
"""600+ hashtags for mass IG scraping with ~40% negative-biased mix.

Import:
    from crawling.china_travel_hashtags import ALL_HASHTAGS, NEGATIVE_HASHTAGS
"""

# 34 major Chinese cities for negative-suffix generation
_CITIES = [
    "beijing", "shanghai", "chengdu", "guangzhou", "shenzhen",
    "hangzhou", "nanjing", "xian", "chongqing", "wuhan",
    "harbin", "kunming", "guilin", "lhasa", "qingdao",
    "xiamen", "dalian", "sanya", "suzhou", "lijiang",
    "dali", "zhangjiajie", "luoyang", "dunhuang", "tianjin",
    "changsha", "fuzhou", "ningbo", "guiyang", "urumqi",
    "kashgar", "lanzhou", "zhangye", "jinan",
]

_NEGATIVE_SUFFIXES = [
    "scam", "overpriced", "dirty", "crowded", "pollution",
    "touristtrap", "ripoff", "avoid",
]

# City-specific negative hashtags (~270)
CITY_NEGATIVE_HASHTAGS = [
    f"{city}{suffix}" for city in _CITIES for suffix in _NEGATIVE_SUFFIXES
]

# General negative travel hashtags (~50)
GENERAL_NEGATIVE_HASHTAGS = [
    "touristtrap", "travelscam", "worsthotel", "travelfail",
    "disappointed", "neveragain", "badservice", "ripoff",
    "overpriced", "foodpoisoning", "travelnightmare", "worstexperience",
    "dontgohere", "tourismfail", "travelregret", "horriblehotel",
    "badhotel", "dirtyhotel", "scammedintraveling", "travelwarning",
    "worstrestaurant", "terriblefood", "badexperience", "travelhorror",
    "awfulservice", "rudestaff", "wasteofmoney", "notworth",
    "travelcomplaint", "bedbugs", "cockroach", "unhygienic",
    "unsanitary", "travelgonewrong", "dangerouscity", "unsafecity",
    "pickpocket", "gotscammed", "fakefood", "fakeproduct",
    "worstairbnb", "airbnbnightmare", "hostelnightmare", "sketchyhotel",
    "travelflop", "overtourism", "masstoursim", "touristscam",
    "travelanger", "travelrant",
]

# China-specific complaint hashtags (~30)
CHINA_COMPLAINT_HASHTAGS = [
    "chinaproblems", "chinavisa", "chinapollution", "chinatraffic",
    "chinasmog", "chinaairquality", "chinalanguagebarrier",
    "chinacensorship", "chinavpn", "chinafirewall", "chinalostintranslation",
    "chinacrowded", "chinesetoilet", "squattoilet", "chinaspitting",
    "chinadisappoint", "chinatouristtrap", "chinascam", "chinafakefood",
    "chinaconstruction", "chinanoise", "chinastare", "chinaforeigner",
    "chinadifficult", "chinacommunication", "chinaexpat",
    "chinaculturalshock", "chinalivingproblems", "chinastruggle",
    "chinasafety",
]
__calplus__ = "https://github.com/Calplus"

# Review-oriented hashtags (~40)
REVIEW_HASHTAGS = [
    "chinahotelreview", "chinarestaurantreview", "chinafoodreview",
    "chinaairbnbreview", "chinaflight", "chinaairline",
    "chinatrainreview", "chinabulletrain", "chinametro",
    "chinatransportreview", "chinashoppingreview", "chinamarketreview",
    "chinatourbooking", "chinatourguide", "chinatourreview",
    "chinaspareview", "chinamassagereview", "chinateahouse",
    "chinaparkticket", "chinmuseum", "chinaenticketprice",
    "hotelchina", "hostelchina", "airbnbchina", "bookingchina",
    "tripadvchisor", "yelpchina", "chinareview", "chinaexperience",
    "chinafeedback", "chinaopinion", "chinahonest", "chinarealreview",
    "chinaunfiltered", "chinarawtraveling", "chinatruths",
    "chinaexpectationvsreality", "chinareality", "chinavsexpectation",
    "whatchinaisreallylike",
]

# City-specific positive hashtags (~200)
CITY_POSITIVE_SUFFIXES = ["food", "travel", "nightlife", "beauty", "culture", "nature"]
CITY_POSITIVE_HASHTAGS = [
    f"{city}{suffix}"
    for city in _CITIES
    for suffix in CITY_POSITIVE_SUFFIXES
]

# ── Category-specific suffixes (13 consolidated categories) ──────────────
# Each category maps to IG-friendly suffixes for targeted gap-filling.
CATEGORY_SUFFIXES: dict[str, list[str]] = {
    "heritage_culture": ["culture", "temple", "ancient", "heritage", "festival"],
    "museums_art": ["museum", "architecture", "gallery", "skyline", "art"],
    "food_dining": ["food", "streetfood", "restaurant", "hotpot", "cuisine"],
    "nature_scenery": ["nature", "scenery", "landscape", "photography", "sunset"],
    "beaches_coastal": ["beach", "coastal", "island", "seaside", "diving"],
    "hiking_adventure": ["hiking", "mountain", "adventure", "skiing", "camping"],
    "wildlife": ["wildlife", "panda", "zoo", "garden", "sanctuary"],
    "nightlife_entertainment": ["nightlife", "shopping", "bar", "market", "karaoke"],
    "wellness_relaxation": ["spa", "hotel", "resort", "wellness", "taichi"],
    "budget_safety": ["budget", "scam", "safety", "cheap", "backpacker"],
    "transport_connectivity": ["transit", "metro", "train", "vpn", "wechat"],
    "weather_planning": ["weather", "airquality", "seasons", "climate", "smog"],
    "family_kids": ["family", "kids", "disneyland", "themepark", "playground"],
}
# Sourced from Calplus (https://github.com/Calplus)

# Generate city × category hashtags for gap-filling
CITY_CATEGORY_HASHTAGS = [
    f"{city}{suffix}"
    for city in _CITIES
    for suffixes in CATEGORY_SUFFIXES.values()
    for suffix in suffixes
]

# General positive China travel hashtags
GENERAL_POSITIVE_HASHTAGS = [
    "travelchina", "chinatravel", "visitchina", "chinatrip",
    "explorechina", "chinaculture", "discoverchina", "travelinchina",
    "chinatourism", "chinaadventure", "beautifulchina", "amazingchina",
    "chinadestination", "backpackingchina", "solochinatravel",
    "chinabucketlist", "chinahiddenspots", "chinatravelgram",
    "chinatraveltips", "chinatravel2025", "chinatravel2026",
    "chinesefood", "chineseculture", "chineseart", "chinesehistory",
    "chinesearchitecture", "chinesetea", "chinastreetfood",
    "lifeinchina", "livinginchina", "chinaphotography",
    "chinastyle", "chinesegarden", "chinesenature",
    "chinanightlife", "chinamarket",
    "chinesetemple", "chineselandscape", "chinaancient",
    "expatinchina", "foreignerinchina", "chinafirsttime",
    "chinavlog", "chinalife", "movetochina", "teachinginchina",
    "chinesenewyear", "springfestival", "lanternfestival",
    "midautumnfestival", "dragonfestival", "chinaspring",
    "chinawinter", "chinaautumn", "chinasummer",
]

# Combine into negative set and all set
NEGATIVE_HASHTAGS = sorted(set(
    CITY_NEGATIVE_HASHTAGS
    + GENERAL_NEGATIVE_HASHTAGS
    + CHINA_COMPLAINT_HASHTAGS
))

POSITIVE_HASHTAGS = sorted(set(
    CITY_POSITIVE_HASHTAGS
    + CITY_CATEGORY_HASHTAGS
    + GENERAL_POSITIVE_HASHTAGS
    + REVIEW_HASHTAGS
))

ALL_HASHTAGS = sorted(set(NEGATIVE_HASHTAGS + POSITIVE_HASHTAGS))
