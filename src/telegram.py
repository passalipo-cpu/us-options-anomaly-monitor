import requests

def send_message(token, chat_id, message):
    if not token or not chat_id:
        raise RuntimeError('Telegram credentials are missing; add repository secrets.')
    r=requests.post(f'https://api.telegram.org/bot{token}/sendMessage',json={'chat_id':chat_id,'text':message,'disable_web_page_preview':True},timeout=20)
    r.raise_for_status()
    if not r.json().get('ok'):
        raise RuntimeError(f'Telegram API returned an error: {r.text}')
