"""Cboe integration boundary. No scraping; requires authorized data entitlement."""
class CboeProviderNotConfigured(RuntimeError):
    pass

def fetch_chain(*args, **kwargs):
    raise CboeProviderNotConfigured('Configure an authorized Cboe feed/API and its documented schema first.')
