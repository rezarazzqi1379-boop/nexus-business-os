# NEXUS Human-Like Visual & Affective Critic v5.7

## Purpose
Add a multimodal visual-review layer beside technical DesignOps QA. The critic estimates likely human visual response; it does not claim literal emotion or objective aesthetic truth.

## Vision stack
1. Technical quality: resolution, effective PPI, blur, distortion, artifacts.
2. Perceptual art direction: hierarchy, balance, whitespace, complexity, salience, scanability, coherence, brand fidelity.
3. Affective estimates: valence, arousal, trust, formality, warmth, authority, premium feel, modernity, calmness, distinctiveness, approachability.
4. Audience simulation: procurement/export manager, government recipient, engineer, catalog buyer.
5. Pairwise comparison: candidate-vs-baseline and candidate-vs-candidate before absolute scoring.
6. Human-feedback calibration: explicit user feedback creates persistent project-specific calibration cases and regression rules.

## Mandatory critique passes
First glance -> 3-second hierarchy scan -> 10-second art-direction inspection -> affective estimate -> audience simulation -> adversarial senior art director -> pairwise comparison.

## Hard rules
- Affective outputs are uncertainty-bounded estimates, not facts.
- Visual/aesthetic PASS cannot override factual, provenance, authorization, resolution or numeric BLOCKs.
- Human rejection overrides model PASS and creates a calibration incident.
- High uncertainty requires human review.
- Brand fidelity is a hard gate for corporate masters.

## Permanent calibration case
ATF Letterhead v4.1: all candidates rejected by human review. Failure classes included invented visual identity, placeholder logo, insufficient brand fidelity, weak Persian/English art direction, and technical correctness being mistaken for design quality.

## Target profiles
Official letters should target high trust, formality, authority and calmness, with low-to-moderate arousal. Corporate catalogs may target higher premium feel, modernity and distinctiveness while retaining trust.

## Learning policy
Preference learning uses explicit feedback only. Project-specific preferences stay separate from company-wide preferences, and preference weights never override hard factual/legal/technical gates.
