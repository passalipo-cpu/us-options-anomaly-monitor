from src.reporting import write_reports

def test_reports_create_csv_html_and_text(tmp_path):
    summary = {
        'session_day':'2026-11-11','started_at':'20:00 UTC','finished_at':'20:01 UTC',
        'requested_tickers':107,'scanned_tickers':100,'no_data_count':5,'failed_count':2,
        'contracts_received':2500,'contracts_above_min_volume':500,
        'alerts_found':1,'alert_threshold':65,'failed_tickers':['BAD'],
        'no_data_tickers':['NONE']
    }
    alert = {
        'timestamp_utc':'2026-11-11T20:00:00+00:00',
        'data':{'ticker':'SPY','contract_symbol':'SPY261218C00600000','option_type':'CALL',
                'expiry':'2026-12-18','strike':600,'volume':1000,'open_interest':400,
                'last_price':2.0,'bid':1.98,'ask':2.02,'iv_pct':60},
        'score_data':{'score':80,'band':'Silny sygnał','confidence':'Średnia','dte':37,
                      'underlying_price':605,'moneyness':'ITM','volume_oi':2.5,
                      'volume_delta':400,'premium':200000,'spread_pct':2.0,
                      'iv_relative_change_pct':30,'iv_change_pp':20},
        'explanation':'Szczegółowe wyjaśnienie testowe'
    }
    result = write_reports(summary,[alert],str(tmp_path),30)
    assert tmp_path.joinpath(result['csv'].split('/')[-1]).exists()
    assert tmp_path.joinpath(result['html'].split('/')[-1]).exists()
    assert tmp_path.joinpath(result['text'].split('/')[-1]).exists()
    assert 'Szczegółowe wyjaśnienie testowe' in result['email_text']
