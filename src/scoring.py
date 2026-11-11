from datetime import date
import math

def num(value, default=0.0):
    try:
        result = float(value)
        return result if math.isfinite(result) else default
    except (TypeError, ValueError):
        return default

def _dte(expiry):
    try:
        return (date.fromisoformat(str(expiry)[:10]) - date.today()).days
    except (TypeError, ValueError):
        return None

def score_contract(row, previous=None):
    volume = num(row.get("volume"))
    oi = num(row.get("openInterest"))
    last = num(row.get("lastPrice"))
    bid = num(row.get("bid"))
    ask = num(row.get("ask"))
    iv = num(row.get("impliedVolatility"))
    strike = num(row.get("strike"))
    spot = num(row.get("underlying_price"))
    side = str(row.get("option_type", "")).upper()
    expiry = str(row.get("expiry", ""))
    dte = _dte(expiry)

    premium = volume * last * 100.0
    ratio = volume / oi if oi > 0 else None
    score = 0
    components = []

    def add(name, points, value, trigger, explanation, caution=""):
        nonlocal score
        score += points
        components.append({
            "name": name, "points": points, "value": value,
            "trigger": trigger, "explanation": explanation, "caution": caution
        })

    if volume >= 500:
        add("Wolumen kontraktu", 15, f"{volume:,.0f} kontraktów",
            ">= 500 daje 15 pkt",
            "Bieżący wolumen sesyjny jest wysoki według progu MVP. Obejmuje wszystkie transakcje od początku sesji, a nie tylko ostatnią godzinę.",
            "Sam duży wolumen nie mówi, czy transakcje były kupnem czy sprzedażą.")
    elif volume >= 100:
        add("Wolumen kontraktu", 8, f"{volume:,.0f} kontraktów",
            "100–499 daje 8 pkt",
            "Wolumen przekroczył minimalny próg monitoringu, ale nie osiągnął najwyższego progu punktowego.")
    else:
        components.append({"name":"Wolumen kontraktu","points":0,"value":f"{volume:,.0f}",
            "trigger":"< 100: 0 pkt","explanation":"Wolumen nie przekracza progu podwyższonej aktywności.","caution":""})

    if ratio is not None and ratio >= 2:
        caution = "Open Interest jest mały; wysoki iloraz może wynikać głównie z małego mianownika." if oi < 100 else ""
        add("Wolumen / Open Interest", 25, f"{ratio:,.2f}x ({volume:,.0f} / {oi:,.0f})",
            ">= 2,00x daje 25 pkt",
            "Wolumen sesyjny jest co najmniej dwukrotnie większy niż raportowany Open Interest. To sygnał intensywnej rotacji kontraktów względem istniejącej liczby otwartych pozycji.",
            caution or "Open Interest jest zwykle aktualizowany raz dziennie. Wysoki iloraz nie dowodzi, że wszystkie dzisiejsze transakcje otworzyły nowe pozycje.")
    elif ratio is not None and ratio >= 1:
        add("Wolumen / Open Interest", 12, f"{ratio:,.2f}x ({volume:,.0f} / {oi:,.0f})",
            "1,00–1,99x daje 12 pkt",
            "Dzisiejszy wolumen dorównał lub przekroczył ostatnio raportowany Open Interest.",
            "Nie jest to miara liczby nowych pozycji; transakcje mogą otwierać i zamykać pozycje.")
    else:
        components.append({"name":"Wolumen / Open Interest","points":0,
            "value":f"{ratio:.2f}x" if ratio is not None else "OI brak/0",
            "trigger":"< 1,00x: 0 pkt","explanation":"Wolumen jest niższy od Open Interest lub OI jest niedostępny.","caution":""})

    if premium >= 100000:
        add("Szacunkowa wartość obrotu", 15, f"USD {premium:,.0f}",
            ">= USD 100 000 daje 15 pkt",
            f"Obliczenie: {volume:,.0f} kontraktów × ostatnia cena USD {last:.4f} × mnożnik 100 = USD {premium:,.0f}.",
            "To estymacja, nie rzeczywista suma premii z transakcji: ostatnia cena nie jest średnią ceną wszystkich kontraktów.")
    elif premium >= 25000:
        add("Szacunkowa wartość obrotu", 8, f"USD {premium:,.0f}",
            "USD 25 000–99 999 daje 8 pkt",
            f"Szacunek wartości: wolumen × ostatnia cena USD {last:.4f} × standardowy mnożnik 100.",
            "Wartość jest przybliżeniem, ponieważ nie znamy średniej ceny zawartych transakcji.")
    else:
        components.append({"name":"Szacunkowa wartość obrotu","points":0,
            "value":f"USD {premium:,.0f}","trigger":"< USD 25 000: 0 pkt",
            "explanation":"Szacunkowa wartość obrotu nie przekracza progu punktowego.","caution":"Wartość opiera się na ostatniej cenie, a nie na średniej cenie transakcji."})

    volume_delta = None
    iv_relative = None
    iv_points = None
    previous_iv = None
    previous_volume = None
    if previous:
        previous_volume = num(previous.get("volume"))
        previous_iv = num(previous.get("iv"))
        if volume >= previous_volume:
            volume_delta = volume - previous_volume
            if volume_delta >= 250:
                add("Przyrost wolumenu od poprzedniego odczytu", 15,
                    f"+{volume_delta:,.0f} kontraktów ({previous_volume:,.0f} → {volume:,.0f})",
                    ">= 250 daje 15 pkt",
                    "Wolumen skumulowany wzrósł od poprzedniego zapisanego snapshotu. To przybliżenie nowej aktywności między odczytami.")
            elif volume_delta >= 75:
                add("Przyrost wolumenu od poprzedniego odczytu", 8,
                    f"+{volume_delta:,.0f} kontraktów ({previous_volume:,.0f} → {volume:,.0f})",
                    "75–249 daje 8 pkt",
                    "Wolumen skumulowany wzrósł od poprzedniego zapisanego snapshotu, ale przyrost nie osiąga najwyższego progu.")
            else:
                components.append({"name":"Przyrost wolumenu od poprzedniego odczytu","points":0,
                    "value":f"+{volume_delta:,.0f}","trigger":"< 75: 0 pkt",
                    "explanation":"Przyrost wolumenu między odczytami jest niewielki.","caution":""})
        else:
            volume_delta = 0
            components.append({"name":"Przyrost wolumenu od poprzedniego odczytu","points":0,
                "value":f"{previous_volume:,.0f} → {volume:,.0f}",
                "trigger":"Spadek/reset wolumenu: 0 pkt",
                "explanation":"Bieżąca wartość wolumenu jest niższa od poprzedniej. Może to oznaczać reset/liczbę odczytu lub problem ze źródłem; nie traktujemy różnicy jako ujemnego przepływu.",
                "caution":"Warto zweryfikować ciągłość snapshotów."})
        if previous_iv > 0 and iv > 0:
            iv_relative = abs(iv - previous_iv) / previous_iv
            iv_points = iv - previous_iv
            if iv_relative >= .25:
                add("Zmiana Implied Volatility", 20,
                    f"{previous_iv*100:.1f}% → {iv*100:.1f}% ({iv_points*100:+.1f} pp; {iv_relative:+.1%})",
                    "zmiana względna >= 25% daje 20 pkt",
                    "Implikowana zmienność wyceniana z opcji wyraźnie zmieniła się od poprzedniego snapshotu. Rynek inaczej wycenia oczekiwaną zmienność instrumentu.",
                    "Zmiana IV nie wskazuje kierunku CALL/PUT ani kierunku ceny akcji; niska wartość początkowa może zawyżać zmianę względną.")
            elif iv_relative >= .10:
                add("Zmiana Implied Volatility", 10,
                    f"{previous_iv*100:.1f}% → {iv*100:.1f}% ({iv_points*100:+.1f} pp; {iv_relative:+.1%})",
                    "zmiana względna 10–24,9% daje 10 pkt",
                    "Implikowana zmienność zmieniła się w zauważalnym stopniu względem poprzedniego odczytu.",
                    "To zmiana względna, a nie zmiana o podaną liczbę punktów procentowych.")
            else:
                components.append({"name":"Zmiana Implied Volatility","points":0,
                    "value":f"{previous_iv*100:.1f}% → {iv*100:.1f}%",
                    "trigger":"zmiana względna < 10%: 0 pkt",
                    "explanation":"IV pozostaje względnie stabilna pomiędzy snapshotami.","caution":""})
        else:
            components.append({"name":"Zmiana Implied Volatility","points":0,
                "value":"brak poprawnego porównania","trigger":"brak danych: 0 pkt",
                "explanation":"Nie ma dwóch poprawnych obserwacji IV do porównania.","caution":""})
    else:
        components.append({"name":"Przyrost wolumenu od poprzedniego odczytu","points":0,
            "value":"brak poprzedniego snapshotu","trigger":"brak danych: 0 pkt",
            "explanation":"To pierwszy odczyt kontraktu w dostępnej historii albo poprzednia obserwacja nie pochodzi z tej samej sesji.","caution":"Nie można ocenić przyrostu godzinowego."})
        components.append({"name":"Zmiana Implied Volatility","points":0,
            "value":"brak poprzedniego snapshotu","trigger":"brak danych: 0 pkt",
            "explanation":"Nie ma poprzedniego odczytu IV z tej sesji.","caution":"Nie można ocenić zmiany IV między godzinami."})

    spread = None
    if bid > 0 and ask > 0 and ask >= bid:
        mid = (bid + ask) / 2
        spread = (ask - bid) / mid if mid > 0 else None
    if spread is not None and spread <= .05:
        add("Spread bid/ask", 10, f"Bid USD {bid:.4f} / Ask USD {ask:.4f} ({spread:.1%})",
            "<= 5% daje 10 pkt",
            "Różnica między najlepszą ofertą kupna i sprzedaży jest relatywnie mała w stosunku do środka kwotowania. To korzystny warunek obserwowalności ceny.",
            "Wąski spread nie pokazuje, czy ostatnia transakcja została zawarta po bid czy ask.")
    elif spread is not None and spread <= .10:
        add("Spread bid/ask", 5, f"Bid USD {bid:.4f} / Ask USD {ask:.4f} ({spread:.1%})",
            "5–10% daje 5 pkt",
            "Spread mieści się w umiarkowanym progu płynnościowym, lecz koszt wejścia/wyjścia może być istotny.",
            "Kwotowania mogą być opóźnione; nie znamy ich wieku.")
    else:
        components.append({"name":"Spread bid/ask","points":0,
            "value":f"{spread:.1%}" if spread is not None else "brak poprawnych kwotowań",
            "trigger":"> 10% lub brak: 0 pkt",
            "explanation":"Spread jest szeroki albo brak wiarygodnej dwustronnej kwotacji. Nie przyznano punktów za jakość kwotowania.",
            "caution":"Szeroki spread obniża praktyczną wykonalność transakcji i wiarygodność wyceny."})

    score = min(score, 100)
    if score >= 85:
        band = "Bardzo silny sygnał (85–100)"
    elif score >= 70:
        band = "Silny sygnał (70–84)"
    elif score >= 55:
        band = "Podwyższona aktywność (55–69)"
    elif score >= 40:
        band = "Umiarkowany sygnał (40–54)"
    else:
        band = "Słaby sygnał (< 40)"

    quality_issues = []
    if oi <= 20:
        quality_issues.append("OI <= 20: wskaźnik Volume/OI jest bardzo niestabilny i może być zawyżony przez mały mianownik.")
    elif oi < 100:
        quality_issues.append("OI < 100: wskaźnik Volume/OI należy interpretować ostrożnie.")
    if spread is None:
        quality_issues.append("Brak poprawnych kwotowań bid/ask.")
    elif spread > .20:
        quality_issues.append("Spread przekracza 20%; płynność/wycena kwotowania są słabe.")
    if not previous:
        quality_issues.append("Brak poprzedniego snapshotu z tej sesji; brak oceny zmian między godzinami.")
    if spot <= 0:
        quality_issues.append("Brak ceny instrumentu bazowego; nie można określić ITM/ATM/OTM.")
    confidence = "Niska" if oi <= 20 or spread is None or (spread is not None and spread > .20) else ("Średnia" if quality_issues else "Podwyższona")

    moneyness = "nieustalona"
    moneyness_pct = None
    if spot > 0 and strike > 0 and side in {"CALL", "PUT"}:
        moneyness_pct = (spot - strike) / spot * 100
        if abs(moneyness_pct) <= .25:
            moneyness = "ATM / blisko ceny bazowej"
        elif side == "CALL":
            moneyness = "ITM" if spot > strike else "OTM"
        else:
            moneyness = "ITM" if spot < strike else "OTM"

    return {
        "score": round(score, 1), "band": band, "confidence": confidence,
        "volume_oi": round(ratio, 2) if ratio is not None else None,
        "premium": round(premium, 2), "spread_pct": round(spread*100, 2) if spread is not None else None,
        "volume_delta": round(volume_delta, 0) if volume_delta is not None else None,
        "iv_relative_change_pct": round(iv_relative*100, 1) if iv_relative is not None else None,
        "iv_change_pp": round(iv_points*100, 2) if iv_points is not None else None,
        "components": components, "quality_issues": quality_issues,
        "dte": dte, "underlying_price": spot if spot > 0 else None,
        "moneyness": moneyness, "moneyness_pct": round(moneyness_pct, 2) if moneyness_pct is not None else None,
        "reasons": [f"{x['name']}: {x['value']} (+{x['points']} pkt)" for x in components if x["points"] > 0]
    }

def explain_contract(row, previous, result, timestamp):
    ticker = str(row.get("ticker", ""))
    side = str(row.get("option_type", "")).upper()
    side_pl = "CALL – prawo kupna instrumentu bazowego" if side == "CALL" else "PUT – prawo sprzedaży instrumentu bazowego"
    expiry = str(row.get("expiry", "brak"))
    strike = num(row.get("strike"))
    volume = num(row.get("volume"))
    oi = num(row.get("openInterest"))
    last = num(row.get("lastPrice"))
    spot = num(row.get("underlying_price"))
    lines = [
        f"ANALIZA ANOMALII: {ticker} {side}",
        f"Kontrakt: {row.get('contractSymbol','brak')} | Termin: {expiry} | Strike: {strike:g}",
        f"Ocena sygnału: {result['score']:.0f}/100 – {result['band']}",
        f"Wiarygodność danych: {result['confidence']}",
        "",
        "1. Co jest obserwowane?",
        f"{side_pl}. Wolumen sesyjny: {volume:,.0f}; ostatni Open Interest: {oi:,.0f}; ostatnia cena opcji: USD {last:.4f}.",
        f"Cena instrumentu bazowego: USD {spot:.4f}" if spot > 0 else "Cena instrumentu bazowego: niedostępna.",
        f"Położenie strike: {result['moneyness']}" + (f" ({result['moneyness_pct']:+.2f}% względem ceny bazowej)." if result['moneyness_pct'] is not None else "."),
        f"Pozostało dni do wygaśnięcia: {result['dte']}" if result["dte"] is not None else "Dni do wygaśnięcia: nieustalone.",
        "",
        "2. Dlaczego system podniósł alert? Punkty składające się na ocenę:"
    ]
    for comp in result["components"]:
        lines.append(f"- {comp['name']}: {comp['value']}; {comp['trigger']}; przyznano {comp['points']} pkt.")
        lines.append(f"  Znaczenie: {comp['explanation']}")
        if comp.get("caution"):
            lines.append(f"  Ograniczenie: {comp['caution']}")
    lines += [
        f"Suma po ograniczeniu do 100 pkt: {result['score']:.0f}/100.",
        "",
        "3. Jakość i ograniczenia danych:"
    ]
    if result["quality_issues"]:
        lines.extend([f"- UWAGA: {x}" for x in result["quality_issues"]])
    else:
        lines.append("- Nie wykryto powyższych problemów jakościowych; nie oznacza to pełnej ani transakcyjnej jakości danych.")
    lines += [
        "",
        "4. Jak interpretować ten sygnał?",
        "Wysoki wynik oznacza, że kilka prostych kryteriów aktywności przekroczyło ustawione progi. Nie jest to statystyczny test anomalii względem 20- lub 60-dniowej historii, bo MVP nie ma jeszcze takiego benchmarku.",
        "CALL nie oznacza automatycznie kupowania CALL, a PUT nie oznacza automatycznie kupowania PUT. Wolumen nie pokazuje, kto inicjował transakcję ani czy otwierał, czy zamykał pozycję. Do oceny kierunku przepływu potrzebne są transakcje tick-by-tick, ceny wykonania względem bid/ask i klasyfikacja aggressor side.",
        "Open Interest pochodzi zwykle z poprzedniego rozliczenia/aktualizacji i nie jest licznikiem nowych pozycji w czasie rzeczywistym. Volume/OI może być bardzo duże przy małym OI.",
        "Szacunkowy obrót premium = wolumen × ostatnia cena × mnożnik 100; nie jest to potwierdzony obrót giełdowy ani średnia cena transakcji.",
        "",
        f"Źródło: Yahoo Finance/yfinance (nieoficjalne, możliwe opóźnienia/braki). Snapshot: {timestamp}.",
        "Wniosek: sygnał do dalszej weryfikacji, a nie samodzielna rekomendacja kupna/sprzedaży."
    ]
    return "\n".join(lines)
