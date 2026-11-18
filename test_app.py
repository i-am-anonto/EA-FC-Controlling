import pytest
from stick_parser import parse_control_string
from search_engine import HybridSearcher

def test_parser_hold_and_flick():
    res = parse_control_string("Hold L2 + R Flick ↑ then ←/→")
    assert "L2" in res["modifiers"]
    assert res["stick"] == "RS"
    assert res["action"] == "Flick"
    assert "↑" in res["direction"]

def test_parser_natural_language():
    res = parse_control_string("Roll Left Stick forward and left")
    assert res["stick"] == "LS"
    assert res["action"] == "Rotate"
    assert "↑" in res["direction"]
    assert "←" in res["direction"]

@pytest.fixture
def engine():
    return HybridSearcher('EAFC_27_Complete_Controls_2.csv')

def test_hybrid_search_empty(engine):
    assert engine.search("   ").empty

def test_hybrid_search_returns_k(engine):
    res = engine.search("finesse shot", top_k=2)
    assert len(res) == 2