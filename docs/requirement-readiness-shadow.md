# Requirement Readiness Gate — Shadow Mode

## Purpose

Prevent buyer-side provisional or unknown engineering inputs from silently becoming technical authority in final supplier quotation/compliance requests.

This is a shadow-mode experiment, not an autonomous sending gate and not a production workflow.

## States

Each decision-critical buyer requirement is classified as exactly one of:

- `approved` — value is approved for final quotation/compliance use and has a retrievable source reference.
- `provisional` — a value exists, but it is historical, communicated, working, or otherwise not final authority. It may support discovery, but it blocks readiness for a final quotation/compliance request.
- `unknown_blocking` — the decision-critical value is not established. It may support discovery as an explicit unknown, but it blocks readiness for a final quotation/compliance request.

## Outputs

The evaluator returns two different readiness decisions:

- `ready_for_discovery` — structurally valid inputs; early supplier discovery or clarification may continue even with explicit provisional/unknown values.
- `ready_for_final_request` — every tracked decision-critical requirement is approved; no provisional or unknown-blocking item remains.

No external action is performed by the evaluator.

## Current Hydrotester shadow case

The current supplier-facing basis includes:

- Pipe OD: `89–180 mm`
- Maximum machine rating: `120 MPa`

In shadow mode these are deliberately classified as `provisional` until the approved engineering/source-of-authority record is re-linked. The Gmail thread proves that these values were communicated; it does not by itself prove final engineering approval.

Current explicit blockers:

- Pipe-length range: `unknown_blocking`
- Wall-thickness or ID range: `unknown_blocking`

The historically communicated `12 m` value is also `provisional`, not engineering authority, until an approved source replaces it.

## Why these fields matter

Current primary manufacturer evidence supports the readiness model:

- Fives Taylor-Wilson states its hydrotesters adapt to pipe-length variation, different end conditions, automatic length/grade/pressure settings, multiple sealing devices, and pressures from 35 bar to over 1,750 bar.
- YAXING describes its hydrotesters as non-standard customized equipment designed from user parameters including pipe diameter, length and maximum test pressure; it also exposes selectable pressure-hold time, sealing methods and testing-station quantity.
- Marley independently requested pipe-length and wall-thickness ranges before producing a detailed technical solution and quotation.

These sources support the inference that geometry and operating/test parameters should be explicitly classified before final technical comparison. They do not define the buyer's approved values.

## Experiment

Run this gate on the next 3–5 comparable equipment RFQs.

Primary measurement:

- supplier clarification rounds caused by missing buyer-side decision-critical inputs.

Secondary measurement:

- time from final RFQ/quotation request to a technically comparable proposal.

Do not promote this to an Operational Rule merely because the software works or because users comply with the gate. Promotion requires observed workflow improvement.
