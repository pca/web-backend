"""Shared Philippine region and island-group definitions."""

REGION_NCR = "NCR"
REGION_CAR = "CAR"
REGION_1 = "01"
REGION_2 = "02"
REGION_3 = "03"
REGION_4A = "4A"
REGION_4B = "4B"
REGION_5 = "05"
REGION_6 = "06"
REGION_7 = "07"
REGION_8 = "08"
REGION_9 = "09"
REGION_10 = "10"
REGION_11 = "11"
REGION_12 = "12"
REGION_13 = "13"
REGION_BARMM = "BARMM"
REGION_18 = "18"

REGION_CHOICES = (
    (REGION_NCR, "NCR (Luzon - Metro Manila)"),
    (REGION_CAR, "CAR (Luzon - Cordillera Region)"),
    (REGION_1, "Region I (Luzon - Ilocos Region)"),
    (REGION_2, "Region II (Luzon - Cagayan Valley)"),
    (REGION_3, "Region III (Luzon - Central Luzon)"),
    (REGION_4A, "Region IV-A (Luzon - Calabarzon)"),
    (REGION_4B, "Region IV-B (Luzon - Mimaropa)"),
    (REGION_5, "Region V (Luzon - Bicol Region)"),
    (REGION_6, "Region VI (Visayas - Western Visayas)"),
    (REGION_7, "Region VII (Visayas - Central Visayas)"),
    (REGION_8, "Region VIII (Visayas - Eastern Visayas)"),
    (REGION_9, "Region IX (Mindanao - Zamboanga Peninsula)"),
    (REGION_10, "Region X (Mindanao - Northern Mindanao)"),
    (REGION_11, "Region XI (Mindanao - Davao Region)"),
    (REGION_12, "Region XII (Mindanao - Soccsksargen)"),
    (REGION_13, "Region XIII (Mindanao - Caraga)"),
    (REGION_BARMM, "BARMM (Mindanao - Bangsamoro)"),
    (REGION_18, "Region XVIII (Visayas - Negros Island Region)"),
)

ZONE_LUZON = "luzon"
ZONE_VISAYAS = "visayas"
ZONE_MINDANAO = "mindanao"
ZONE_CHOICES = (
    (ZONE_LUZON, "Luzon"),
    (ZONE_VISAYAS, "Visayas"),
    (ZONE_MINDANAO, "Mindanao"),
)
ZONE_REGIONS = {
    ZONE_LUZON: (
        REGION_NCR,
        REGION_CAR,
        REGION_1,
        REGION_2,
        REGION_3,
        REGION_4A,
        REGION_4B,
        REGION_5,
    ),
    ZONE_VISAYAS: (REGION_6, REGION_7, REGION_8, REGION_18),
    ZONE_MINDANAO: (
        REGION_9,
        REGION_10,
        REGION_11,
        REGION_12,
        REGION_13,
        REGION_BARMM,
    ),
}
