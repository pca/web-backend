# Initial automatic competition-region audit

- Audit date: 2026-10-03
- WCA export: v2.0.2, generated 2026-10-03 00:00:28 UTC
- Boundary snapshot: `geoph-1.0-current-2024-135776d2`

This audit used the official WCA competition table and the checked-in boundary
snapshot. Every Philippine competition was classified from its WCA latitude and
longitude only. No venue was manually assigned or corrected.

## Coverage

| Outcome | Competitions |
| --- | ---: |
| Automatically assigned | 434 |
| Outside the boundary snapshot | 1 |
| Missing coordinates | 0 |
| Invalid coordinates | 0 |
| On a regional boundary | 0 |
| Overlapping regions | 0 |
| **Total Philippine competitions** | **435** |

Automatic assignment coverage was **99.77%**. The classification pass took
approximately 10 seconds on the local development machine.

## Assigned competition count by region

| Region | Competitions |
| --- | ---: |
| NCR | 126 |
| CAR | 9 |
| Region I | 41 |
| Region II | 1 |
| Region III | 25 |
| Region IV-A | 100 |
| Region IV-B | 0 |
| Region V | 4 |
| Region VI | 17 |
| Region VII | 43 |
| Region VIII | 0 |
| Region IX | 0 |
| Region X | 7 |
| Region XI | 26 |
| Region XII | 2 |
| Region XIII | 0 |
| BARMM | 0 |
| Region XVIII | 33 |

Zero means that no competition in this export was hosted in that region; it
does not mean the corresponding boundary is absent. The boundary snapshot has
all 18 regions and its separate validation test checks sample cities across
Luzon, Visayas, Mindanao, and Negros.

## Unclassified competition

`FMCPhilippines2025` (`FMC Philippines 2025`) was the only unclassified row.
The WCA export describes its city and venue as “Multiple Cities” and “Multiple
Venues.” The competition was held simultaneously in Quezon City, Bacolod, and
Mandaue, spanning three host regions. Its WCA coordinate falls outside the land
polygons, so assigning a single host region would be misleading.

The competition remains included in nationwide participation totals. It is
excluded from region-specific totals and appears in coverage information, in
line with the rule to report uncertain cases instead of guessing.
