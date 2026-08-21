# Contact Channel Health v0.1

## Problem

Recent live sourcing produced delivery failures for supplier email channels. A delivery failure is evidence about a channel, not proof that the supplier entity is invalid. Conversely, a supplier with independently verified identity does not make every published contact channel healthy or safe to use.

## Invariant

Track these separately:

1. `SupplierEntityState` — whether the supplier identity itself is verified, partial, unverified, or rejected.
2. `ContactChannelState` — whether a specific email/phone/WhatsApp/website channel is healthy, degraded, failed, or unverified.

A failed channel can still leave the supplier researchable. A healthy channel can still be unusable for outreach when supplier identity is unverified. Even when both are usable, normal action-specific outreach approval remains required.

## Live cases motivating the change

- SSE Global Energy: delivery failure observed; supplier/channel re-verification required.
- Minetal Group: official web presence and published contact existed, but email delivery failed. This demonstrates why entity validity and channel validity must not be collapsed into one status.

## Acceptance criteria

- failed email does not automatically reject supplier identity;
- verified supplier does not automatically validate an unverified/failed channel;
- rejected supplier blocks channel use;
- failed channels require retrievable evidence and a failure reason;
- observations require timezone-aware timestamps;
- supplier/channel identity mismatches fail closed;
- this module does not authorize external sending.
