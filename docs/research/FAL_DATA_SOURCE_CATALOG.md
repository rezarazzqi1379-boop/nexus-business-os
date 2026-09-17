# FAL-A/FAL-B Data Source Catalog (started 2026-09-17)

Living catalog of information sources for ferroalloys (ferromanganese import / ferrosilicon
export) discovery. Updated as new sources are found — never overwritten wholesale, only
appended/corrected, same discipline as the rest of this project's evidence handling.

**Rule for every source below:** classify it as (A) free, no account, (B) free account
required, or (C) paid account required. Only A can be wired into `scripts/run_fal_a_discovery.py`
today. B/C require Reza to personally create the account (see "Account suggestions" below) —
Claude never creates an account or enters payment/identity details anywhere, regardless of
tier, per this project's own account-orchestration boundary
(`external_account_orchestrator.py`: prepares a plan, a human must complete every commit step).

## (A) Free, no account needed — usable immediately

| Source | What it gives | Notes |
|---|---|---|
| [OEC – Observatory of Economic Complexity](https://oec.world/en/profile/hs/ferroalloys) | Country-level ferroalloys (HS 7202) trade visualizations: top exporters/importers, trade value trends | Freemium — basic profiles are public; bulk download/API is paid. Good for market-level orientation, not company-level leads. |
| [UN Comtrade / ComtradePlus public dashboards](https://comtrade.un.org/labs/data-explorer/) | Official UN customs-reported trade statistics by HS code/country/year | Basic browsing is public; bulk API access needs a free registered account (see B below). |
| Public company/trade-association directories already used in the FAL-A run (e.g. Istanbul Mineral and Metals Exporters' Association, FerroAlloyNet.com country directories, Georgian Manganese / Chiatur Manganum company sites) | Company names, self-description | Already wired in, low-cost to keep expanding by country. |

## (B) Free account required (registration, no payment)

| Source | What it gives | Notes |
|---|---|---|
| [UN Comtrade / ComtradePlus API](https://comtradeplus.un.org/) | Programmatic access to official bulk trade statistics, higher rate limits than public dashboard | Free tier registration (email/organization) — no payment, no KYC as far as publicly documented. Lowest-risk account to open first if going this route. |
| [ITC Trade Map](https://www.trademap.org/) | Detailed bilateral trade flow data by product/country, market-access info | Free registration required for full functionality; basic use may be visible without login. |

## (C) Paid account required — commercial customs/shipment-level trade intelligence

| Source | What it gives | Notes |
|---|---|---|
| [Volza](https://www.volza.com/) | Shipment-level import/export records (who imported/exported what, from/to where) across ~200 countries | Paid, has a free-trial signup tier. Already surfaced earlier as a real hit in this project's own web search results. |
| [ImportGenius](https://www.importgenius.com/) | Customs/shipment-level trade intelligence, searchable by company/product | Paid subscription. US-based company. |
| [Panjiva (S&P Global)](https://tradeint.com/insights/panjiva-vs-importgenius-a-detailed-comparison/) | Enterprise-grade shipment/trade intelligence, supply-chain mapping | Paid, enterprise-oriented, US-based (S&P Global) — likely the most compliance-cautious of this group given the parent company. |
| Tendata | Trade data platform, comparable to Volza/ImportGenius | Paid. |

### Compliance flag on category (C) — read before signing up for any of these

These are US/international commercial platforms whose own Terms of Service may restrict or
prohibit use in connection with sanctioned countries or entities — several are US-based
companies (ImportGenius, Panjiva/S&P Global) operating under US export-control/sanctions
obligations themselves. This project's own compliance gate
(`opportunity_suggestion_engine.py`) already flags that ferroalloys (a steel-input sector) may
touch US EO 13871 ("Iron, Steel, Aluminum, and Copper Sectors of Iran") and EU steel/metals
trade measures. Before opening any (C)-tier account for FAL-A/FAL-B research specifically,
get real advice from a sanctions/export-control lawyer on whether using these tools for
Iran-linked ferroalloys research itself carries risk under that platform's own ToS or under
applicable law — this is not something Claude can determine, and it is the same open item
already logged in CURRENT_STATE.md under "Decide: proceed with live Iran-source integration...
or hold for legal/compliance check first."

## Account suggestions (Reza decides; Claude never signs up)

For the two lowest-risk options — (B)-tier, free, no payment, no KYC as documented — I've
prepared onboarding plans below using this project's own `external_account_orchestrator.py`
(the same module that already exists for exactly this purpose). These are plans only: you'd
still complete the actual signup yourself in your browser.

1. **UN Comtrade / ComtradePlus** (free registration) — lowest friction, official UN data,
   no known ToS sanctions restriction (it's a public UN statistics service). Reasonable first
   pick if you want to expand beyond the (A)-tier sources without any compliance question.
2. **ITC Trade Map** (free registration) — similar profile to Comtrade, adds bilateral
   market-access detail.

I have not prepared onboarding plans for the (C)-tier paid platforms (Volza/ImportGenius/
Panjiva/Tendata) pending the compliance flag above — happy to prepare them the moment you
say to, but wanted the sanctions/ToS question in front of you first rather than skip past it.
