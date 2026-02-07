<!-- Title -->
<a id="readme-top"></a>
<div align="center">
    <h1 align="center">FlightGazer Airlines/Operator Database</h1>
    A database of airlines/operator names, properly formatted.
</div>
<!-- end title section -->

## What This Is
This is a "database" of airlines and operators with their more common names and with the proper capitialization and formatting.<br>
This is a **manually** curated/maintained list based on the FAA's "Three−Letter Designator/Aircraft Company/Telephony Decode" table with the "friendly names" cross-checked and sourced from [the sources below](#sources).<br>

This repo is designed for the [FlightGazer](https://github.com/WeegeeNumbuh1/FlightGazer) project.<br>
Data is available as a CSV file and is validated with CSVLint to be RFC-4180 compliant.

### Why this exists
Needed a database that was more consistent for use with FlightGazer but did not rely on querying APIs. Existing databases not behind APIs were inconsistent or outdated with airline names. The bullet was bit and now you're reading this.

## Examples \& Comparison
<details><summary><b>Expand/Collapse</b></summary>

| 3Ltr | Company | Country | Telephony | tar1090-db | Wikipedia | *FriendlyName* |
| --- | --- | --- | --- | --- | --- | --- |
`AAV` | ASTRO AIR INTERNATIONAL, INC. DBA OF PAN PACIFIC AIRLINES | PHILIPPINES | ASTRO-PHIL | Astro Air International | Astro Air International | **Pan Pacific Airlines** |
| `ABX` | ABX AIR, INC. (WILMINGTON, OH) | UNITED STATES | ABEX | Abx Air | ABX Air | **ABX Air** |
| `CMP` | COMPANIA PANAMENA DE AVIACION, S.A. | PANAMA | COPA | Compania Panamena De Aviacion | Copa Airlines | **Copa Airlines** |
| `CXK` | ATP FLIGHT SCHOOL | UNITED STATES | CAREER TRACK | Atp Flight School | *null* | **ATP Flight School** |
| `DOI` | U.S. DEPARTMENT OF THE INTERIOR, OFFICE OF AIRCRAFT SERVICES, (BOISE, ID) | UNITED STATES | INTERIOR | US Department Of The Interior Office Of Aircraft Services | U.S. Department of the Interior | **U.S. Department of the Interior** |
| `EIN` | AER LINGUS TEORANTA | IRELAND | SHAMROCK | Aer Lingus Teoranta | Aer Lingus | **Aer Lingus** |
| `GCI` | GUARDIA COSTIERA ITALIANA | ITALY | ITALIAN COAST GUARD | Guardia Costiera Italiana | Italian Coast Guard | **Italian Coast Guard** |
| `JBU` | JETBLUE AIRWAYS CORPORATION (NEW YORK, NY) | UNITED STATES | JETBLUE | Jetblue Airways Corporation | JetBlue Airways| **JetBlue** |
| `JZA` | JAZZ AVIATION LP | CANADA | JAZZ | Jazz Aviation | Air Canada Jazz | **Air Canada Jazz** |
| `LOT` | LOT - POLSKIE LINIE LOTNICZE | POLAND | LOT | Polskie Linie Lotnicze | LOT Polish Airlines | **LOT Polish Airlines** |
| `TCN` | JEM AIR HOLDINGS, LLC | UNITED STATES | TRANSCON | Jem Air Holdings | Trans Continental Airlines | **Jet Excellence** |
| `RCJ` | HAWKER BEECHCRAFT LTD | UNITED KINGDOM | NEWPIN | Hawker Beechcraft | Raytheon Corporate Jets | **Hawker Beechcraft** |
| `TAI` | TACA INTERNATIONAL AIRLINES S.A. | EL SALVADOR | TACA | Taca International Airlines | *null* | **Avianca El Salvador** |
| `TDE` | TELAVIA D/B/A FLIGHT ONE, INC. (TELLURIDE, CO) | UNITED STATES | TELLURIDE | Telavia | Tellavia / Flight One | **Flight One** |
| `UIT` | UNIVERSITETET I TROMSO | NORWAY | ARTIC | Universitetet I Tromso | University of Tromsø School of Aviation | **University of Tromso School of Aviation** |
| `USC` | AIRNET II | UNITED STATES | STAR CHECK | Airnet Ii | AirNet Express | **Airnet II** |
| `VOI` | CONCESIONARIA VUELA COMPANIA DE AVIACION, S.A. DE C.V. | MEXICO | VOLARIS | Concesionaria Vuela Compania De Aviacion | Volaris | **Volaris** |
| `VIV` | AEROENLACES NACIONALES, S.A. DE C.V. | MEXICO | AEROENLACES | Aeroenlaces Nacionales | Aeroenlaces Nacionales | **Viva** |
| `WIS` | PRO-AIRE CARGO AND CONSULTING, INC. D/B/A PACCAIR (NEENAH, WI) | UNITED STATES | WISCAIR | Pro Aire Cargo And Consulting | Paccair | **Paccair** |

> Note: the above was based on `tar1090-db` version `3.14.1686`

</details>

## Formatting Priorities \& Requirements
- Only use ASCII printable characters
- Use the most common name known by the public or what they're doing business as, not the company's legal name
  - "**Volaris**" instead of *Concesionaria Vuela Compania De Aviacion*
  - "**Paccair**" instead of *Pro-Aire Cargo and Consulting*
  - "**LOT Polish Airlines**" instead of *Polskie Linie Lotnicze*
  - "**Turkish Airlines**" instead of *Turk Hava Yollari*
- Preserve specific capitalizations and punctuation used by the company, e.g. camelCase, acronyms, hyphens, commas, and ampersands
  - easyJet Europe, ABX Air, ForeFlight, Lease-a-Plane International
- Convert titles into *proper* title case, along with preferred English names or English translation with correct demonyms, *if possible*
  - "**U.S. Department of the Interior**" instead of *US Department Of The Interior Office Of Aircraft Services*
  - "**Italian Coast Guard**" instead of *Guardia Costiera Italiana*
  - "**Turkmenistani Government**" instead of *Turkmenhowayollary*
- Use shorter names *and* drop company types, *if possible*
  - "**FSB Flugservice & Development**" instead of *FSB FLUGSERVICE & DEVELOPMENT GMBH, BERLIN-SCHOENEFELD*
  - "**Performance Transportacion**" instead of *PERFORMANCE TRANSPORTACION, S.A. DE C.V.*
- Keep airlines as distinctive as possible with the least amount of additional information
  - If an airline operates different branches in other countries, distinguish them by that country
    - Aer Lingus *versus* Aer Lingus UK
  - Drop common phrases such as *Airlines*, *Aviation*, or *Charter* unless it is explicitly used in the name or adds additional distinction
    - "**Utair**" instead of *Utair Aviation*
  - Avoid/drop parenthetical phrases when not needed
    - "**Haiti National Airlines**" instead of *Haiti National Airlines (HANA)*
  - Expand acronyms for clarity, *if needed*
    - "**United Parcel Service**" instead of *UPS*
    - "**The Cargo Airlines**" instead of *TCA*

## Tools
Check the python scripts in the [`tools`](./tools/) folder to generate files you can work with.<br>
You can create a version compatible with `tar1090` using [`csv_to_tar1090.py`](./tools/csv_to_tar1090.py). This is untested but should work.

## Contributions \& Corrections
Want to help keep this database up-to-date? Found an error? Want to make a correction? Please file an issue with this repository.

## Sources
### Primary
[Federal Aviation Administration, Directive No. JO 7340.2N, Chapter 3, Section 3](https://www.faa.gov/air_traffic/publications/atpubs/cnt_html/chap3_section_3.html)

### Friendly Names
- [`tar1090-db`](https://github.com/wiedehopf/tar1090-db/blob/master/db/operators.js)
- [Wikipedia](https://en.wikipedia.org/wiki/List_of_airline_codes)
- [Flightradar24](https://www.flightradar24.com/data/airlines)
- [This CSV](https://github.com/tomcarman/skystats/blob/9bc0cc4e0827c89176d2805cc67cf800f099eb03/data/airlines.csv)

### Cross-Check
- Planespotters
- Jetphotos
- FlightAware
- AirNav Radar
- Google

## Disclaimers
- This database is reliant on what is published on the FAA's side. Errors and omissions originating from them will be inherited by this database as well.
- Obvious but easily rectifed encoding errors present in the FAA database are corrected to the most reasonable solution in this database.
- Airlines and operators which do not have an ICAO 3-letter callsign prefix are not covered by this database.
- Airlines that are removed in future publications will remain in this database until they are reallocated.
- Some airlines not officially listed by the FAA may be manually added to this database if their operation can be confirmed.
- The data presented in this database may not be fully accurate and may fall out of date over time.
- Maintenance of this database and repo is not guaranteed.

## ⚖️ License
This database is covered under the `Open Data Commons Open Database License v1.0`.