import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "financial-engine"))
from calculator import roi, payback_period, npv, irr, evaluate_feasibility


def test_roi():
    assert roi(profit=200, investment=1000) == 20.0


def test_payback_period():
    assert payback_period(investment=1000, annual_profit=250) == 4.0


def test_npv_positive_project():
    value = npv(0.10, [-1000, 400, 400, 400, 400])
    assert value > 0


def test_irr_matches_expectation():
    rate = irr([-1000, 400, 400, 400, 400])
    assert rate is not None
    assert 0.20 < rate < 0.25


def test_evaluate_feasibility_verdict():
    result = evaluate_feasibility(investment=500000, annual_cash_flows=[150000] * 5, discount_rate=0.10)
    assert result.verdict == "feasible"
    assert result.npv_value > 0
