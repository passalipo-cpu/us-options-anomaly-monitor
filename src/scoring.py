import math

def num(v, default=0.0):
    try:
        x = float(v)
        return x if math.isfinite(x) else default
    except (TypeError,ValueError):
        return default

def score_contract(row, previous=None):
    volume=num(row.get('volume')); oi=num(row.get('openInterest')); last=num(row.get('lastPrice'))
    bid=num(row.get('bid')); ask=num(row.get('ask')); iv=num(row.get('impliedVolatility'))
    premium=volume*last*100; ratio=volume/max(oi,1); score=0.0; reasons=[]
    if volume>=500: score+=20; reasons.append(f'high volume ({int(volume):,})')
    elif volume>=100: score+=10; reasons.append(f'elevated volume ({int(volume):,})')
    if ratio>=2: score+=25; reasons.append(f'volume/OI {ratio:.2f}x')
    elif ratio>=1: score+=12; reasons.append(f'volume/OI {ratio:.2f}x')
    if premium>=100000: score+=20; reasons.append(f'premium turnover ${premium:,.0f}')
    elif premium>=25000: score+=10; reasons.append(f'premium turnover ${premium:,.0f}')
    if previous:
        pvol=num(previous.get('volume')); piv=num(previous.get('iv'))
        if volume>pvol>0:
            delta=volume-pvol
            if delta>=250: score+=15; reasons.append(f'new volume since prior sample: {int(delta):,}')
            elif delta>=75: score+=8; reasons.append(f'new volume since prior sample: {int(delta):,}')
        if piv>0 and iv>0:
            move=abs(iv-piv)/piv
            if move>=.25: score+=20; reasons.append(f'IV moved {move:.0%} since prior sample')
            elif move>=.10: score+=10; reasons.append(f'IV moved {move:.0%} since prior sample')
    spread=(ask-bid)/max((ask+bid)/2,.01) if ask>0 and bid>0 and ask>=bid else None
    if spread is not None and spread<=.10: score+=5; reasons.append('relatively tight quoted spread')
    return {'score':min(round(score,1),100),'volume_oi':round(ratio,2),'premium':round(premium,2),'spread_pct':round(spread*100,1) if spread is not None else None,'reasons':reasons}
