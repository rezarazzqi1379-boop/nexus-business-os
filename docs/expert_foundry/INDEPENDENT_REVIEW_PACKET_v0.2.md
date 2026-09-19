# Independent Review Packet v0.2

This manifest prevents chat-pasted text from being mistaken for repository evidence.
Reviewers must receive all five files as actual attachments or inspect them at the exact
Git commit. A missing file makes claims depending on it `UNKNOWN`.

Files and SHA-256 digests at preparation time:

- `expert_foundry.py`: `4CA650DC7A95F7123212A91830F4705C93687889FA7B29C013611DFC36BBDDE0`
- `foundry_vertical_proof.py`: `89E6D71271DA04348BE08251FD1E5A245EF93F2827869A03EE3B890A034DDAA0`
- `.nexus/expert_foundry/FACTORY_INPUT_TEMPLATE.json`: `E87FAA17B7496B6B6C0E729705379E46E7C65EADAD9F88F4D845380D1C642CD3`
- `docs/expert_foundry/NEXUS_EXPERT_FOUNDRY_v0.1.md`: `59CA7E1035061610CEF3C263E8E09748B06751C73A8C61611BCAF1712572D77F`
- `docs/expert_foundry/FIRST_VERTICAL_PROOF_2026-09-08.md`: `0E386C5001F4057182AE6A66BDDFA323FF7D9D3F8FF92218280BC670485BAD38`

Scope correction after independent review:

- The executable is `PHASE_0_PREFLIGHT`, not the full acceptance proof.
- Curated literals use `STATIC_CURATED`; they never claim a live provider or query.
- An `EXPERIENCE`, contradiction or promotion record must originate in real supplied
  evidence and cannot be fabricated to make a test pass.
