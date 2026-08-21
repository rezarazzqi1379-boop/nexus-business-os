# NEXUS Live Pilot — Can Body Line Research

Date: 2026-08-21
Mode: read/research only
External writes/sends: none

## Trigger
A new Gmail reply from Zhejiang Golden Eagle Food Machinery Co., Ltd. supplied two live quotations for D73 mm and D99 mm three-piece tin can body production lines.

## Evidence consumed
- Gmail message: Re: RFQ – Can Body Necking / Flanging / Beading Machine – Ø73 mm and Ø99 mm (2026-08-20)
- Attachment: 500CPM（MAX） can body line-D73mm can body-20260820.pdf
- Attachment: 500CPM（MAX） can body line-D99mm can body-20260820.pdf
- Official manufacturer product page for GT10C-500 Automatic Can Body Welder
- Official manufacturer product/news pages describing GT10C-500 current specifications

## Observed facts from supplier quotations
### D73 line
- Diameter: 73 mm; height: 100 mm
- Quoted maximum line capacity: 500 cpm
- Total quoted amount: USD 628,200 FOB Ningbo
- Forming section: GT3B64-NFBS-5, four-station Necking + Flanging + Beading + Seaming combiner
- Forming combiner price: USD 122,000
- Payment: 30% T/T advance, 70% before delivery
- Lead time: 120–150 days after advance payment and drawing confirmation
- Warranty: one year
- Quoted total power: 100 kW
- Shipping estimate: 3 × 40HQ containers

### D99 line
- Diameter: 99 mm; height: 135 mm
- Quoted maximum line capacity: 500 cpm
- Total quoted amount: USD 636,200 FOB Ningbo
- Necking machine: GT3B51-N, USD 45,000
- Flanging + Beading + Seaming combiner: GT3B63-FBS-5, USD 85,000
- Combined D99 forming subtotal: USD 130,000
- Payment / lead time / warranty / total power / shipping terms are materially the same as D73 quotation

## Cross-source contradiction detected
The quotation describes GT10C-500 with approximately:
- can diameter: 52–153 mm
- power: 35 kW
- weight: 4,000 kg
- welding speed: 50–70 m/min

The manufacturer’s current official GT10C-500 product information describes approximately:
- can diameter: up to 180 mm on the comparison table/current article
- total power: 50 kW
- weight: 5,000 kg
- welding speed: 25–70 m/min

This is a specification/revision mismatch, not proof that the quotation is wrong. Possible explanations include quotation template drift, a customized machine, old revision data, or website data changes. It requires supplier confirmation before technical acceptance.

## Decision-relevant comparison
D99 is USD 8,000 more expensive than D73. The entire difference is consistent with the forming architecture shown in the quotations:
- D73 four-station integrated forming combiner: USD 122,000
- D99 separate necking + three-station combiner: USD 45,000 + USD 85,000 = USD 130,000

This creates a concrete research question: whether the separate D99 architecture is technically required by geometry/process stability or is simply the vendor’s chosen configuration.

## Generated next-work items
1. Verify the exact GT10C-500 revision being quoted and reconcile power, weight, diameter range, and welding speed against the current official specification.
2. Ask for a line-level guaranteed stable output, not only MAX output, for D73 and D99.
3. Confirm whether 400 cpm is the guaranteed continuous stable line speed, as stated in the supplier email, and identify the bottleneck machine at that stable speed.
4. Confirm why D73 uses an integrated four-station forming combiner while D99 uses separate necking + FBS equipment.
5. Request final utility table by machine (kW, compressed air, cooling water), because the quoted 100 kW total appears inconsistent with component-level values and the official welder page.
6. Confirm material/thickness and incoming blank dimensions for both products; the quotation leaves the project material/thickness field incomplete.
7. Validate scope boundaries: molds/tooling, installation, commissioning, spares, PLC/electrical brands, FAT/SAT criteria and guaranteed acceptance output.

## Governance result
- Research/read: executed
- Evidence: retained as source references
- Supplier outreach: not executed; remains human-gated
- Purchase/contract/payment: not executed; remains human-gated
- Next cycle: technical verification research and quote normalization

## Pilot conclusion
The live loop produced a decision-relevant contradiction and a concrete next-work queue from real inbox data without performing any consequential external action. This is evidence that the NEXUS control-plane can be used for real commercial sensing and governed next-task generation; it is not yet evidence of autonomous 24/7 operation or business outcome effectiveness.
