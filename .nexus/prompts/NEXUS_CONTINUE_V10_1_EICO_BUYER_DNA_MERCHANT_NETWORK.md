# NEXUS CONTINUE v10.1 — EICO BUYER DNA + MERCHANT NETWORK MINER

Continue from latest valid state. Resolve CI first. No expansion on red CI.

PRIMARY GOAL:
Discover verified commercial chains around Esfarayen Industrial Complex (EICO), then use those chains to find new steel buyers, traders, stockists, processors and end users in Iran and export markets.

NEW PRINCIPLE:
SEARCH LESS FOR "COMPANIES".
SEARCH MORE FOR "COMMERCIAL EDGES".

SEED EDGES:
EICO <-> Gunes Metallurgy/Chemical Trade
EICO -> Sun Metallurgical/Chemistry Trade candidate
EICO <-> Marmara Metal candidate
EICO -> Kibar candidate
EICO ecosystem -> Azin Forge adjacency.

Do not promote any candidate beyond its evidence state.

LANE A — BUYER DNA
For every relationship-bound EICO buyer:
extract product description
HS
grade if visible
form
dimensions
weight
date
destination
buyer role
buyer's industry
buyer imports from other suppliers
buyer's other alloy/forged-steel purchases.

Build BUYER_DNA.

LANE B — LOOKALIKE BUYERS
Use BUYER_DNA features to find companies with the same:
application
material family
HS/product description
machining/forging capability
procurement pattern.

Similarity creates CANDIDATE only.

LANE C — MERCHANT NETWORK
For every trader/stockist:
brands/mills represented
grades/forms
warehouse/service center
import origins
export destinations
named buyers
named suppliers
shipment evidence.

Separate:
TRADER
STOCKIST
DISTRIBUTOR
IMPORTER
EXPORTER
BROKER.

LANE D — TWO-HOP GRAPH
EICO buyer -> buyer's supplier
EICO supplier -> supplier's other buyer
competitor exporter -> named buyer
named buyer -> procurement/contact.

Require evidence for every hop.

LANE E — IRAN HIDDEN BUYERS
Search application-first:
gear manufacturers
shaft manufacturers
heavy machine builders
mining equipment
cement equipment
steel-mill rolls
oil/gas equipment
petrochemical equipment
power generation
shipbuilding
large repair/MRO
heavy machining
forging.

LANE F — DEMAND TRIGGERS
Detect:
tender
RFQ
expansion
shutdown
overhaul
localization
new line
maintenance contract
import shipment
failed procurement.

Trigger != opportunity until qualified.

LANE G — ENTITY RESOLUTION
Trade databases contain duplicate/misaligned EICO profiles.
Build source-scoped identity observations.
Never merge shipment totals across profiles by name alone.

LANE H — MATERIAL RESOLUTION
HS7228 is broad.
Resolve product description -> form -> grade -> standard when evidence permits.
Never HS -> exact grade.

LANE I — DECISION ROLES
Only after buyer qualification:
materials
procurement
supply
engineering
commercial.
Role != authority.
No outreach.

LANE J — RED TEAM
Attack:
trade database count -> canonical count
shipment -> current relationship
trader -> end user
buyer name -> legal identity
HS7228 -> grade
historical buyer -> future buyer
lookalike -> qualified buyer
catalogue -> inventory
supplier -> manufacturer.

Every successful attack becomes regression.

MEASURE EACH LANE:
qualified entities/search
verified edges/search
two-hop edges/search
false edges prevented
information gain
source cost
latency
technical-fit opportunities
decision-role resolution.

PROMOTE only measured winners.
PAUSE low-information routes.

OUTPUT:
EICO buyer DNA ledger
merchant map
two-hop relationship graph
Iran hidden-buyer queue
export lookalike queue
demand-trigger watchlist
top 20 evidence-backed candidates
top unresolved commercial edges.

NO OUTREACH.
NO PAID CREDITS.
NO MERGE.
NO PRODUCTION DEPLOY.
