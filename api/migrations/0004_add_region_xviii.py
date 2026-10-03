from django.db import migrations, models


REGION_CHOICES = [
    ("NCR", "NCR (Luzon - Metro Manila)"),
    ("CAR", "CAR (Luzon - Cordillera Region)"),
    ("01", "Region I (Luzon - Ilocos Region)"),
    ("02", "Region II (Luzon - Cagayan Valley)"),
    ("03", "Region III (Luzon - Central Luzon)"),
    ("4A", "Region IV-A (Luzon - Calabarzon)"),
    ("4B", "Region IV-B (Luzon - Mimaropa)"),
    ("05", "Region V (Luzon - Bicol Region)"),
    ("06", "Region VI (Visayas - Western Visayas)"),
    ("07", "Region VII (Visayas - Central Visayas)"),
    ("08", "Region VIII (Visayas - Eastern Visayas)"),
    ("09", "Region IX (Mindanao - Zamboanga Peninsula)"),
    ("10", "Region X (Mindanao - Northern Mindanao)"),
    ("11", "Region XI (Mindanao - Davao Region)"),
    ("12", "Region XII (Mindanao - Soccsksargen)"),
    ("13", "Region XIII (Mindanao - Caraga)"),
    ("BARMM", "BARMM (Mindanao - Bangsamoro)"),
    ("18", "Region XVIII (Visayas - Negros Island Region)"),
]


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0003_auto_20210418_1355"),
    ]

    operations = [
        migrations.AlterField(
            model_name="user",
            name="region",
            field=models.CharField(
                blank=True, choices=REGION_CHOICES, max_length=255, null=True
            ),
        ),
        migrations.AlterField(
            model_name="regionupdaterequest",
            name="region",
            field=models.CharField(max_length=64, choices=REGION_CHOICES),
        ),
    ]
