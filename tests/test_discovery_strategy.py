from discovery_strategy import generate_paths
def test_strategy_generator_creates_independent_paths_without_fake_success():
 p=generate_paths("20MnCr5","gear","Turkey")
 assert len(p)>=5 and len({x.path_id for x in p})==len(p)
 assert all(x.status=="PLANNED" for x in p)
