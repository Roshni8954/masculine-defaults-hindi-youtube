# ============================================================
# CLEANUP SCRIPT: Filter videos_raw.csv to final channel list
# - Keep only channels from your final list
# - Standardize channel names (merge duplicates)
# - Keep only latest 85 videos per channel
# - Keep only videos >= 10 minutes
# ============================================================

import pandas as pd

INPUT_CSV  = "data/videos_raw.csv"
OUTPUT_CSV = "data/videos_raw.csv"

VIDEOS_PER_CHANNEL = 90
MIN_DURATION       = 600

# ── FINAL CHANNEL LIST WITH STANDARDIZED NAMES ──────────────
# Maps any variation of a channel name to ONE standard name
# Format: standard_name -> [list of variations found in CSV]
channel_name_map = {
    "Sadhguru":               ["Sadhguru"],
    "SwamiMukundananda":      ["SwamiMukundananda"],
    "BhajanMarg":             ["BhajanMarg"],
    "Aniruddhacharyaji":      ["Aniruddhacharyaji"],
    "Chitralekhaji":          ["Chitralekhaji"],
    "AnkitSajwanMinistries":  ["AnkitSajwanMinistries"],
    "ShibuThomasOfficial":    ["ShibuThomasOfficial"],
    "MohanCLazarus":          ["MohanCLazarus"],
    "GurudevHindi":           ["GurudevHindi"],
    "DrZakirNaik":            ["DrZakirNaik"],
    "MuftiTariqMasood":       ["MuftiTariqMasood"],
    "IslamKnowledgeOnly":     ["IslamKnowledgeOnly"],
    "JaiJinendra":            ["JaiJinendra"],
    "Terapanth":              ["Terapanth"],
    "BuddhaBroadCast":        ["BuddhaBroadCast"],
    "AnandmurtiGurumaa":      ["AnandmurtiGurumaa", "Anandmurti Gurumaa"],
    "RanveerAllahbadia":      ["RanveerAllahbadia", "Ranveer Allahbadia"],

    "MySirG":                 ["MySirG"],
    "IshanSharma":            ["IshanSharma"],
    "ApnaCollege":            ["ApnaCollege"],
    "CodeWithHarry":          ["CodeWithHarry"],
    "TechWiser":              ["TechWiser"],
    "TrakinTech":             ["TrakinTech"],
    "TechnicalGuruji":        ["TechnicalGuruji"],
    "CodeStudioByPrachi":     ["CodeStudioByPrachi"],
    "SaumyaSingh":            ["SaumyaSingh"],
    "AECComputers":           ["AECComputers"],
    "JennysLecturesCSIT":     ["JennysLecturesCSIT", "JennyslecturesCSIT"],
    "CollegeWallahByPWSkills":["CollegeWallahByPWSkills", "CollegeWallahbyPWSkills"],
    "TechnologyGyan":         ["TechnologyGyan"],
    "KnowledgeGate":          ["KnowledgeGate", "KNOWLEDGEGATE"],
    "TakeUForward":           ["TakeUForward", "takeUforward"],
    "CodeHelp":               ["CodeHelp"],

    "Warikoo":                ["Warikoo"],
    "CARachanaRanade":        ["CARachanaRanade"],
    "PranjalKamra":           ["PranjalKamra"],
    "FinanceWithSharan":      ["FinanceWithSharan"],
    "FinancialFreedom":       ["FinancialFreedom"],
    "LabourLawAdvisor":       ["LabourLawAdvisor"],
    "AkshatZayn":             ["AkshatZayn"],
    "Nischa":                 ["Nischa"],
    "PushkarRajThakur":       ["PushkarRajThakur", "PushkarRajThakurOfficial"],
    "SanjayKathuria":         ["SanjayKathuria", "Sanjay_Kathuria"],
    "Bekifaayati":            ["Bekifaayati"],

    "SouravJoshiVlogs":       ["SouravJoshiVlogs"],
    "CurlyTales":             ["CurlyTales"],
    "KritikaThatBohoGirl":    ["KritikaThatBohoGirl"],
    "DimpleMalhanVlogs":      ["DimpleMalhanVlogs", "Dimple Malhan Vlogs"],
    "MumbikerNikhil":         ["MumbikerNikhil", "Mumbiker Nikhil"],
    "KritikaGoel":            ["KritikaGoel", "Kritika Goel"],
    "JannatZubair":           ["JannatZubair"],
    "LifeOfLimbachiyaas":     ["LifeOfLimbachiyaas"],
    "FitMuscleTV":            ["FitMuscleTV"],
    "YasminBodyImage":        ["YasminBodyImage"],
    "TanyaKhanijow":          ["TanyaKhanijow"],

    "DhruvRathee":            ["DhruvRathee", "Dhruv Rathee"],
    "MohakMangal":            ["MohakMangal", "Mohak Mangal"],
    "UnfilteredBySamdish":    ["UnfilteredBySamdish", "Unfiltered by Samdish (and a fantastic team)"],
    "NikhilKamath":           ["NikhilKamath"],
    "RavishKumar":            ["RavishKumar"],
    "ChanakyadialogsHindi":   ["ChanakyadialogsHindi"],
    "AbhiAndNiyu":            ["AbhiAndNiyu"],
    "NikitaKThakur":          ["NikitaKThakur"],
    "KhangsResearchCentre":   ["KhangsResearchCentre"],
    "ThinkSchoolHindi":       ["ThinkSchoolHindi"],
    "MrVivekBindra":          ["MrVivekBindra"],
    "FayeDSouza":             ["FayeDSouza"],
    "TheSwaddleTV":           ["TheSwaddleTV"],
    "TheDeshbhakt":           ["TheDeshbhakt", "thedeshbhakt"],
    "MojoStory":              ["MojoStory", "mojostory"],
    "SupriyaShrinate":        ["SupriyaShrinate"],

    "RajShamani":             ["RajShamani", "Raj Shamani"],
    "GaurGopalDas":           ["GaurGopalDas"],
    "SandeepSeminars":        ["SandeepSeminars"],
    "BKShivani":              ["BKShivani", "bkshivani"],
    "AdeteDahiya":            ["AdeteDahiya"],
    "NishkarshSharmaa":       ["NishkarshSharmaa", "nishkarshsharmaa"],
    "DrTanuJain":             ["DrTanuJain"],
    "PriyaKumarMotivational": ["PriyaKumarMotivational", "PriyaKumarMotivationalSpeaker"],
    "UjjwalPatni":            ["UjjwalPatni"],
    "DeepakDaiya":            ["DeepakDaiya"],

    "TotalGaming":            ["TotalGaming"],
    "TechnoGamerzOfficial":   ["TechnoGamerzOfficial"],
    "ASGaming":               ["ASGaming"],
    "CarryisLive":            ["CarryisLive"],
    "LiveInsaan":             ["LiveInsaan"],
    "GodLikeEsports":         ["GodLikeEsports"],
    "GoldyHindiGaming":       ["GoldyHindiGaming"],
    "TeamVitalityIndia":      ["TeamVitalityIndia"],
    "OrangutanTV":            ["OrangutanTV"],
    "KrutikaPlays":           ["KrutikaPlays"],
    "PayalGaming":            ["PayalGaming"],
    "MilikyaMili":            ["MilikyaMili"],
    "XyaaLive":               ["XyaaLive"],
    "AnkkitaC":               ["AnkkitaC"],
    "LokeshGamer":            ["LokeshGamer"],

    "TheHarshBeniwal":        ["TheHarshBeniwal"],
    "Round2Hell":             ["Round2Hell"],
    "FilterCopy":             ["FilterCopy"],
    "AshishChanchlaniVines":  ["AshishChanchlaniVines"],
    "AshishSolanki":          ["AshishSolanki"],
    "GauravKapoor":           ["GauravKapoor"],
    "TriggeredInsaan":        ["TriggeredInsaan", "triggeredinsaan"],
    "Mythpat":                ["Mythpat"],
    "Girliyapa":              ["Girliyapa"],
    "MadhurVirliRaw":         ["MadhurVirliRaw"],
    "VivekSamtani":           ["VivekSamtani"],
    "SlayyPointOfficial":     ["SlayyPointOfficial"],
    "SNGComedy":              ["SNGComedy"],
    "Jordindian":             ["Jordindian"],
    "HiSaimanSays":           ["HiSaimanSays", "HiSaimanSay"],
    "TanmayBhat":             ["TanmayBhat", "tanmaybhat"],
    "DevikaGupta":            ["DevikaGupta", "devikagupta029"],
}

# ── build reverse lookup: variation -> standard name ────────
variation_to_standard = {}
for standard, variations in channel_name_map.items():
    for var in variations:
        variation_to_standard[var] = standard

# ── ALL VALID STANDARD CHANNEL NAMES (FINAL LIST) ───────────
valid_channels = set(channel_name_map.keys())

# ── LOAD CSV ─────────────────────────────────────────────────
df = pd.read_csv(INPUT_CSV)
print(f"Before cleaning : {len(df)} videos")
print(f"Unique channels before: {df['channel_title'].nunique()}")

# ── STEP 1: standardize channel names ───────────────────────
df["channel_title"] = df["channel_title"].apply(
    lambda x: variation_to_standard.get(x, x)
)

# ── STEP 2: remove duplicate videos (same video_id) ─────────
df = df.drop_duplicates(subset=["video_id"])
print(f"\nAfter dedup     : {len(df)} videos")

# ── STEP 3: keep only channels in final list ────────────────
df = df[df["channel_title"].isin(valid_channels)]
print(f"After filtering channels: {len(df)} videos")
print(f"Unique channels after: {df['channel_title'].nunique()}")

# ── STEP 4: keep only videos >= 10 minutes ──────────────────
df = df[df["duration_seconds"] >= MIN_DURATION]
print(f"After duration filter: {len(df)} videos")

# ── STEP 5: keep only latest 85 per channel ─────────────────
df["published_at"] = pd.to_datetime(df["published_at"], format='ISO8601')
df = df.sort_values("published_at", ascending=False)
df = df.groupby("channel_title").head(VIDEOS_PER_CHANNEL).reset_index(drop=True)

print(f"After top-85 filter: {len(df)} videos")

# ── FINAL COLUMN ORDER ───────────────────────────────────────
df = df[[
    "video_id",
    "title",
    "published_at",
    "channel_id",
    "channel_title",
    "duration_seconds",
    "community"
]]

df.to_csv(OUTPUT_CSV, index=False)

print(f"\n{'='*50}")
print(f"CLEANUP COMPLETE")
print(f"{'='*50}")
print(f"Final video count: {len(df)}")
print(f"Final channel count: {df['channel_title'].nunique()}")
print(f"\nChannels missing from final CSV (check these):")

found_channels = set(df["channel_title"].unique())
missing = valid_channels - found_channels
for ch in sorted(missing):
    print(f"  - {ch}")

print(f"\nBreakdown by community:")
print(df["community"].value_counts().to_string())

print(f"\nVideos per channel (showing channels with < 85):")
counts = df["channel_title"].value_counts()
low_count = counts[counts < 85]
print(low_count.to_string())

print(f"\nSaved to: {OUTPUT_CSV}")