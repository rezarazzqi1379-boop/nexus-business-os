import unittest

from lead_meta_workflow import evaluate_lead_with_meta_agent
from meta_agent import DEFAULT_CAPABILITY_PROFILES, MetaAgent
from need_radar import NeedEvidence, NeedSignal, assess_need


def evidence(eid, ref, statement):
    return NeedEvidence(eid, "FACT", "official", ref, "2026-08-21T00:00:00+00:00", statement)


SIGNALS = (
    NeedSignal(
        "baku-modernization", "baku-steel", "Baku Steel / Azerboru", "buyer", "octg-growth", "expansion",
        "Future phases may require additional pipe finishing, testing or heat-treatment systems.",
        "strong", "current", "cold",
        (evidence("baku-1", "https://www.bakusteel.com/en/articles/press-releases/43/baku-steel-company-has-completed-the-first-phase-of-the-modernization-of-azerboru", "Azerboru completed phase one modernization and states continued capability development."),
         evidence("baku-2", "https://www.bakusteel.com/en/articles/press-releases/43/baku-steel-company-has-completed-the-first-phase-of-the-modernization-of-azerboru#quality", "API production, P110, threading and automated inspection capabilities were expanded.")),
        unknowns=("scope and procurement timing of the next phase", "Iran commercial feasibility"),
    ),
    NeedSignal(
        "east-hsaw", "east-pipes", "East Pipes", "buyer", "pipe-growth", "expansion",
        "New HSAW capacity creates a plausible need for downstream testing and handling equipment.",
        "strong", "current", "cold",
        (evidence("east-1", "https://www.eastpipes.com/announcements/east-pipes-integrated-company-for-industry-announces-establish-a-new-production-line-for-helical-submerged-arc-welded-hsaw-pipes-in-companys-factory-in-dammam-2nd-industrial-city/", "East Pipes contracted multiple entities for a new 100,000 t/y HSAW line."),
         evidence("east-2", "https://www.eastpipes.com/announcements/east-pipes-integrated-company-for-industry-announces-establish-a-new-external-steel-pipe-coating-line/", "East Pipes approved another coating-line expansion and states machinery contracts will follow.")),
        unknowns=("whether hydrotest equipment is already included", "approved vendor route"),
    ),
    NeedSignal(
        "tashkent-coating", "tashkent-pipe", "Tashkent Pipe Plant", "buyer", "pipe-growth", "expansion",
        "The verified project is primarily coating modernization, not an OCTG hydrotester requirement.",
        "weak", "current", "cold",
        (evidence("tpp-1", "https://www.ebrd.com/home/news-and-events/news/2025/ebrd-supports-further-modernisation-at-tashkent-pipe-plant.html", "EBRD financing supports insulated large-diameter pipe production and coating equipment."),),
        unknowns=("separate test-line modernization",),
    ),
    NeedSignal(
        "tbx-live", "tbx-nexxia", "TBX Nexxia", "buyer", "octg-growth", "plant_change",
        "A fully operational CRA OCTG platform may have optimization or future expansion needs, but no open equipment procurement is proven.",
        "plausible", "current", "cold",
        (evidence("tbx-1", "https://www.mubadala.com/en/news/mubadala-tubacex-launc-tbx-nexxia-abu-dhabi-activating-an-end-to-end-cra-octg-platform", "Mubadala and Tubacex launched a fully operational 20,000 t/y CRA OCTG platform."),),
        unknowns=("open CAPEX package", "unfilled equipment need"),
    ),
    NeedSignal(
        "qaz-threading", "qazexpocentre-pipe", "QazExpoCentre-Pipe", "buyer", "octg-growth", "plant_change",
        "The new threading workshop signals localization growth but does not prove a hydrotester or heat-treatment procurement.",
        "plausible", "current", "cold",
        (evidence("qaz-1", "https://qazexpopipe.com/en/qazexpocentre-pipe-launches-threading-workshop-in-uralsk/", "The company launched a new threading workshop on 21 April 2026."),),
        unknowns=("next planned production stage", "testing capacity"),
    ),
    NeedSignal(
        "vallourec-award", "vallourec", "Vallourec", "supplier", "octg-growth", "customer_referral",
        "A supply award is a supply-side signal, not evidence that Vallourec is a buyer lead for ATF equipment.",
        "strong", "current", "none",
        (evidence("val-1", "https://www.vallourec.com/app/uploads/2025/04/20250408-Vallourec_Press-Release_Sonatrach.pdf", "Vallourec announced an OCTG award from Sonatrach."),),
    ),
)


class LeadMetaABTests(unittest.TestCase):
    def test_candidate_preserves_every_baseline_disposition(self):
        for signal in SIGNALS:
            baseline = assess_need(signal)
            candidate = evaluate_lead_with_meta_agent(signal, MetaAgent(DEFAULT_CAPABILITY_PROFILES))
            self.assertEqual(candidate.assessment.disposition, baseline.disposition)

    def test_candidate_blocks_outreach_for_every_signal(self):
        for signal in SIGNALS:
            result = evaluate_lead_with_meta_agent(signal, MetaAgent(DEFAULT_CAPABILITY_PROFILES))
            self.assertIn("external_action", result.blocked_capabilities)
            self.assertFalse(result.outreach_authorized)

    def test_candidate_adds_plan_and_digest(self):
        for signal in SIGNALS:
            result = evaluate_lead_with_meta_agent(signal, MetaAgent(DEFAULT_CAPABILITY_PROFILES))
            self.assertTrue(result.selected_tools)
            self.assertEqual(len(result.evidence_digest), 64)

    def test_supplier_is_not_promoted_to_buyer(self):
        result = evaluate_lead_with_meta_agent(SIGNALS[-1], MetaAgent(DEFAULT_CAPABILITY_PROFILES))
        self.assertEqual(result.assessment.disposition, "supply_research")


if __name__ == "__main__":
    unittest.main()
