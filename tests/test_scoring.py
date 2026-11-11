from src.scoring import score_contract, explain_contract

def test_score_is_bounded_and_returns_explanations():
    row = {
        'ticker':'SPY', 'option_type':'CALL', 'contractSymbol':'SPY261218C00600000',
        'expiry':'2026-12-18', 'strike':600, 'underlying_price':605,
        'volume':1000, 'openInterest':400, 'lastPrice':2.0,
        'bid':1.98, 'ask':2.02, 'impliedVolatility':0.60
    }
    previous = {'volume':500, 'iv':0.40}
    result = score_contract(row, previous)
    assert 0 <= result['score'] <= 100
    assert result['band'].startswith('Bardzo silny')
    assert result['confidence'] == 'Podwyższona'
    explanation = explain_contract(row, previous, result, '2026-11-11T20:00:00+00:00')
    assert 'Dlaczego system podniósł alert' in explanation
    assert 'Nie jest to statystyczny test anomalii' in explanation
    assert 'nie oznacza automatycznie' in explanation

def test_small_open_interest_lowers_data_confidence():
    row = {
        'ticker':'TSLA', 'option_type':'PUT', 'contractSymbol':'TSLA261218P00300000',
        'expiry':'2026-12-18', 'strike':300, 'underlying_price':350,
        'volume':540, 'openInterest':1, 'lastPrice':1.0,
        'bid':0.98, 'ask':1.02, 'impliedVolatility':0.7
    }
    result = score_contract(row, None)
    assert result['volume_oi'] == 540
    assert result['confidence'] == 'Niska'
    assert any('OI <= 20' in issue for issue in result['quality_issues'])
