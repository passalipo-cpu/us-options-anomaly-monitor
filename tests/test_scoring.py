from src.scoring import score_contract

def test_score_is_bounded():
    out=score_contract({'volume':1000,'openInterest':100,'lastPrice':2.5,'bid':2.4,'ask':2.5,'impliedVolatility':.8})
    assert 0 <= out['score'] <= 100
    assert out['volume_oi']==10
