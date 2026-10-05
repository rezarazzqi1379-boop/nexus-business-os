from market_digital_twin import MarketTwin,rank_score
def test_missing_market_evidence_does_not_create_rank():
 assert rank_score(MarketTwin("Turkey",demand=.8,trade_flow=.7,buyer_density=.8,logistics=.6)) is None
def test_rank_requires_four_known_factors_and_evidence():
 x=MarketTwin("Turkey",.8,.7,.8,.6,evidence_refs=("e:1",))
 assert rank_score(x)==.725
