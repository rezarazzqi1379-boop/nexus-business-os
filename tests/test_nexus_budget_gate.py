from nexus_budget_gate import BudgetPolicy, evaluate_budget

def test_free_experiment_under_budget():
    assert evaluate_budget(BudgetPolicy(0,0,0,0)) == (True, ())

def test_paid_action_requires_exact_approval():
    ok, reasons=evaluate_budget(BudgetPolicy(100,0,1,5))
    assert not ok and "paid_action_requires_exact_approval" in reasons

def test_approved_paid_action_under_budget():
    assert evaluate_budget(BudgetPolicy(100,10,1,5,True))[0]

def test_monthly_limit_blocks_overspend():
    assert "monthly_cap_exceeded" in evaluate_budget(BudgetPolicy(10,9,2,5,True))[1]

def test_experiment_cap_blocks_overspend():
    assert "experiment_cap_exceeded" in evaluate_budget(BudgetPolicy(100,0,11,10,True))[1]

def test_negative_budget_rejected():
    assert "invalid_budget" in evaluate_budget(BudgetPolicy(-1,0,0,0))[1]

def test_nan_budget_rejected():
    assert "invalid_budget" in evaluate_budget(BudgetPolicy(float("nan"),0,0,0))[1]
