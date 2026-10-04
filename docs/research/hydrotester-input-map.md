# Hydrotester Requirement Input Map — Research Artifact

Verified: 2026-08-19

Purpose: support the Requirement Readiness Gate without inventing buyer-approved values. This document separates source-derived manufacturer facts, NEXUS inference, and current project unknowns.

## Source-derived manufacturer facts

### Fives Taylor-Wilson

Official Fives material states that its hydrostatic pipe testers can accommodate pipe-length variation and different end conditions; use automatic pipe length, grade and pressure settings; offer multiple sealing-device options; and operate from about 35 bar to over 1,750 bar depending on design/application.

Source: `https://www.fivesgroup.com/steel/tube-finishing/hydrostatic-testing`

A Fives 2024 project note also reports a Taylor-Wilson hydrotester for oil-and-gas tube/pipe service with pressure up to 21,700 psi, reinforcing that pressure class alone does not define the complete machine design.

Source: `https://www.fivesgroup.com/de/newspress/detail-view?...news=1773`

### YAXING

Official YAXING product material describes the hydrotester as non-standard customized equipment designed from customer parameters including pipe diameter, pipe length and maximum test pressure. The manufacturer also exposes multiple sealing methods, configurable pressure-hold time and testing-station quantity based on client speed requirements.

Sources:
- `https://www.yaxingmachines.com/product-steel-pipe-hydro-testing-machine.html`
- `https://www.yaxingmachines.com/product-hydrotester.html`

### Marley field evidence

Marley technical staff requested two buyer-side inputs before a detailed solution/quotation:

1. OCTG pipe length range
2. OCTG pipe thickness range

Evidence: Gmail message `1a018c1b2c80c8e3`.

## NEXUS inference — not buyer authority

The primary-source pattern supports a lightweight readiness map with two classes of information:

### Buyer / engineering authority inputs

These should be explicitly `approved`, `provisional`, or `unknown_blocking` before final technical comparison:

- pipe OD range
- pipe length range
- wall-thickness and/or minimum/maximum ID range
- required test pressure or pressure envelope basis
- pipe/product grade or standard basis where it changes settings or test acceptance
- end condition / end preparation relevant to sealing and restraint
- required pressure-hold time / test procedure basis
- target throughput or cycle requirement when it affects station count and machine configuration

### Vendor design / proposal outputs

These should normally be requested from the vendor rather than fabricated as buyer inputs:

- sealing method and tooling concept
- axial restraint / bench-load design basis
- intensifier/high-pressure system configuration
- station count and handling concept
- PLC/control architecture and test-data recording
- layout / GA
- utilities
- FAT/SAT approach
- warranty, spares, commissioning and after-sales scope

This split is an inference from current manufacturer material and live supplier questions. It should be refined against engineering feedback and real proposals.

## Current NEXUS project status

The supplier-facing project basis currently contains OD `89–180 mm` and maximum machine rating `120 MPa`, but in the shadow gate these remain `provisional` until the approved engineering authority/source is linked.

Current explicit `unknown_blocking` items:

- final pipe-length range
- final wall-thickness or ID range

Additional fields to confirm before a fully comparable final proposal if not already in the approved Technical Purchase Specification:

- hold time / test-cycle basis
- end condition / sealing interface requirement
- applicable standard / acceptance basis
- throughput/cycle target

Do not import Heat Treatment line dimensions into the Hydrotester requirement set.

## Promotion rule

Do not convert this input map into a mandatory company-wide checklist from research alone. Run the shadow gate on the next 3–5 comparable equipment RFQs and measure supplier clarification rounds and time-to-comparable-quote first.
