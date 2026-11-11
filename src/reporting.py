import csv
import html
import os
from datetime import datetime, timezone
from pathlib import Path

CSV_FIELDS = [
    "timestamp_utc","ticker","contract_symbol","option_type","expiry","dte","strike",
    "underlying_price","moneyness","score","score_band","data_confidence","volume",
    "open_interest","volume_oi","volume_delta","last_price","estimated_premium_usd",
    "bid","ask","spread_pct","implied_volatility_pct","iv_relative_change_pct",
    "iv_change_pp","explanation"
]

def _fmt(value, default="—"):
    return default if value is None or value == "" else str(value)

def write_reports(summary, alerts, report_dir, max_email_alerts=30):
    folder = Path(report_dir)
    folder.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_UTC")
    csv_path = folder / f"options_anomalies_{stamp}.csv"
    html_path = folder / f"options_summary_{stamp}.html"
    txt_path = folder / f"options_summary_{stamp}.txt"

    with csv_path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS, extrasaction="ignore")
        writer.writeheader()
        for item in alerts:
            d = item["data"]
            s = item["score_data"]
            writer.writerow({
                "timestamp_utc": item["timestamp_utc"], "ticker": d.get("ticker"),
                "contract_symbol": d.get("contract_symbol"), "option_type": d.get("option_type"),
                "expiry": d.get("expiry"), "dte": s.get("dte"), "strike": d.get("strike"),
                "underlying_price": s.get("underlying_price"), "moneyness": s.get("moneyness"),
                "score": s.get("score"), "score_band": s.get("band"),
                "data_confidence": s.get("confidence"), "volume": d.get("volume"),
                "open_interest": d.get("open_interest"), "volume_oi": s.get("volume_oi"),
                "volume_delta": s.get("volume_delta"), "last_price": d.get("last_price"),
                "estimated_premium_usd": s.get("premium"), "bid": d.get("bid"), "ask": d.get("ask"),
                "spread_pct": s.get("spread_pct"), "implied_volatility_pct": d.get("iv_pct"),
                "iv_relative_change_pct": s.get("iv_relative_change_pct"),
                "iv_change_pp": s.get("iv_change_pp"), "explanation": item["explanation"]
            })

    top = sorted(alerts, key=lambda x: x["score_data"]["score"], reverse=True)[:max_email_alerts]
    summary_text = [
        "US OPTIONS ANOMALY MONITOR – PODSUMOWANIE",
        f"Sesja NY: {summary['session_day']}",
        f"Start: {summary['started_at']} | Koniec: {summary['finished_at']}",
        f"Watchlista: {summary['requested_tickers']} tickerów",
        f"Poprawnie odczytane tickery: {summary['scanned_tickers']}",
        f"Brak danych: {summary['no_data_count']} | Błędy: {summary['failed_count']}",
        f"Kontrakty odebrane: {summary['contracts_received']}",
        f"Kontrakty z wolumenem >= próg: {summary['contracts_above_min_volume']}",
        f"Alerty >= {summary['alert_threshold']}/100: {summary['alerts_found']}",
        "",
        "TOP ALERTS – szczegółowe objaśnienia",
        ""
    ]
    summary_text.extend(item["explanation"] + "\n" + ("=" * 88) for item in top)
    if not top:
        summary_text.append("Nie wykryto kontraktów spełniających próg alertu.")
    if summary.get("failed_tickers"):
        summary_text.extend(["", "Tickery z błędami pobrania:", ", ".join(summary["failed_tickers"])])
    if summary.get("no_data_tickers"):
        summary_text.extend(["", "Tickery bez dostępnego łańcucha opcji:", ", ".join(summary["no_data_tickers"])])
    summary_text.extend([
        "",
        "UWAGA METODOLOGICZNA: score jest heurystycznym wynikiem progowym, nie statystycznym odchyleniem od historii.",
        "CALL/PUT, wolumen i Volume/OI nie wskazują samodzielnie kierunku transakcji ani tego, czy pozycje zostały otwarte.",
        "Premium jest szacunkiem wolumen × ostatnia cena × 100, nie potwierdzonym obrotem.",
        "Źródło: Yahoo Finance/yfinance, nieoficjalne i niegwarantujące pełnego pokrycia rynku."
    ])
    txt_path.write_text("\n".join(summary_text), encoding="utf-8")

    cards = []
    for item in top:
        s = item["score_data"]
        d = item["data"]
        title = f"{d.get('ticker')} {d.get('option_type')} | {d.get('contract_symbol')}"
        cards.append(
            "<details open><summary><b>" + html.escape(title) + "</b> — " +
            html.escape(str(s["score"])) + "/100 — " + html.escape(s["band"]) +
            " | wiarygodność danych: " + html.escape(s["confidence"]) +
            "</summary><pre>" + html.escape(item["explanation"]) + "</pre></details>"
        )
    html_body = f"""<!doctype html><html lang="pl"><head><meta charset="utf-8">
    <style>body{{font-family:Arial,sans-serif;color:#202124;line-height:1.45;max-width:1100px;margin:24px auto;padding:0 18px}}
    table{{border-collapse:collapse;width:100%}}td,th{{border:1px solid #ddd;padding:8px;text-align:left}}
    th{{background:#f2f4f7}}details{{border:1px solid #ddd;border-radius:8px;padding:12px;margin:12px 0}}
    summary{{cursor:pointer}}pre{{white-space:pre-wrap;font-family:Arial,sans-serif;font-size:13px}}
    .note{{background:#f5f5f5;padding:12px;border-radius:6px}}</style></head><body>
    <h1>US Options Anomaly Monitor</h1><h2>Podsumowanie sesji {html.escape(summary['session_day'])}</h2>
    <table><tr><th>Watchlista</th><td>{summary['requested_tickers']}</td><th>Przetworzone tickery</th><td>{summary['scanned_tickers']}</td></tr>
    <tr><th>Kontrakty odebrane</th><td>{summary['contracts_received']}</td><th>Kontrakty z wolumenem powyżej progu</th><td>{summary['contracts_above_min_volume']}</td></tr>
    <tr><th>Alerty</th><td>{summary['alerts_found']}</td><th>Próg</th><td>{summary['alert_threshold']}/100</td></tr>
    <tr><th>Brak danych / błędy</th><td colspan="3">{summary['no_data_count']} / {summary['failed_count']}</td></tr></table>
    <h2>Najważniejsze sygnały – objaśnienia</h2>
    {''.join(cards) if cards else '<p>Nie wykryto kontraktów spełniających próg alertu.</p>'}
    <div class="note"><b>Jak czytać raport:</b> score jest wynikiem heurystycznym, nie statystyczną anomalią względem historii.
    CALL/PUT nie oznacza kierunku zlecenia. Wolumen i Volume/OI nie potwierdzają otwarcia pozycji.
    Szacowany obrót premium nie jest potwierdzonym obrotem. Załączony CSV zawiera wszystkie alerty z tego skanu.</div>
    <p>Źródło: Yahoo Finance/yfinance (nieoficjalne; możliwe braki i opóźnienia).</p></body></html>"""
    html_path.write_text(html_body, encoding="utf-8")
    return {"csv": str(csv_path), "html": str(html_path), "text": str(txt_path),
            "email_html": html_body, "email_text": "\n".join(summary_text),
            "email_alerts_included": len(top)}


def append_github_step_summary(summary, alerts, reports, max_items=15):
    """Add a readable summary and expandable detailed signals to the GitHub Actions run Summary tab."""
    summary_path = os.getenv("GITHUB_STEP_SUMMARY")
    if not summary_path:
        return False
    top = sorted(alerts, key=lambda x: x["score_data"]["score"], reverse=True)[:max_items]
    lines = [
        "# US Options Anomaly Monitor",
        "",
        f"**Sesja NY:** {summary['session_day']}  ",
        f"**Watchlista:** {summary['requested_tickers']} | **Pobrano łańcuch:** {summary['scanned_tickers']} | **Bez danych:** {summary['no_data_count']} | **Błędy:** {summary['failed_count']}  ",
        f"**Kontrakty odebrane:** {summary['contracts_received']} | **Kontrakty z wolumenem powyżej progu:** {summary['contracts_above_min_volume']} | **Alerty:** {summary['alerts_found']} (próg {summary['alert_threshold']}/100)",
        "",
        f"**Raporty:** `{reports['csv']}` · `{reports['html']}` · `{reports['text']}`",
        "",
        "## Najsilniejsze sygnały",
        "",
        "| Ticker | Kontrakt | Score | Wiarygodność | Wolumen | OI | Volume/OI |",
        "|---|---|---:|---|---:|---:|---:|"
    ]
    for item in top:
        d = item["data"]
        s = item["score_data"]
        cells = [str(d.get("ticker","")), str(d.get("contract_symbol","")),
                 str(s.get("score","")), str(s.get("confidence","")),
                 f"{d.get('volume',0):,}", f"{d.get('open_interest',0):,}",
                 f"{s.get('volume_oi'):.2f}x" if s.get("volume_oi") is not None else "—"]
        lines.append("| " + " | ".join(x.replace("|", " ") for x in cells) + " |")
    lines += ["", "## Szczegółowe objaśnienia – top sygnały", ""]
    for item in top:
        d = item["data"]
        s = item["score_data"]
        title = f"{d.get('ticker')} {d.get('option_type')} – {d.get('contract_symbol')} – {s.get('score')}/100 – wiarygodność: {s.get('confidence')}"
        lines.append("<details><summary>" + html.escape(title) + "</summary>")
        lines.append("")
        lines.append("```text")
        lines.append(item["explanation"])
        lines.append("```")
        lines.append("")
        lines.append("</details>")
        lines.append("")
    lines += [
        "> **Ograniczenia:** Score jest heurystyczny; Volume/OI nie potwierdza nowych pozycji; CALL/PUT nie wskazuje strony inicjującej; premium to estymacja na bazie ostatniej ceny. Źródło Yahoo Finance/yfinance nie zapewnia pełnego rynku ani gwarantowanego czasu rzeczywistego.",
        ""
    ]
    with open(summary_path, "a", encoding="utf-8") as handle:
        handle.write("\n".join(lines))
    return True
