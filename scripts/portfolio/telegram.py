"""Avisos por Telegram (P7, §4.5): mismo texto que el issue, con link.

Si falla el envío (o falta configurarlo) NO hace fallar el job: el issue sigue siendo el aviso principal;
queda un ::warning:: sin el token ni el chat.
"""

import os

import requests

from portfolio.identidad import REDACTOR, imprimir

URL_API = "https://api.telegram.org/bot"
TIEMPO_ESPERA = (10, 20)
LARGO_MAXIMO = 4000  # Telegram corta en 4096


def configuracion():
    """(token, chat) desde los secrets del Action, o (None, None)."""
    token = os.environ.get("TELEGRAM_TOKEN_ALERTAS") or None
    chat = os.environ.get("TELEGRAM_CHAT_ALERTAS") or None
    return token, chat


def recortar(texto):
    if len(texto) <= LARGO_MAXIMO:
        return texto
    return texto[: LARGO_MAXIMO - 1] + "…"


def enviar(texto, token=None, chat=None, sesion=None):
    """Envía un mensaje de texto plano. Devuelve True si salió. Nunca lanza excepciones."""
    if token is None and chat is None:
        token, chat = configuracion()
    if not token or not chat:
        imprimir("::warning::Telegram sin configurar (TELEGRAM_TOKEN_ALERTAS / TELEGRAM_CHAT_ALERTAS): no se envió el aviso")
        return False
    cliente = sesion if sesion is not None else requests
    cuerpo = {"chat_id": chat, "text": recortar(REDACTOR.redactar(texto)), "disable_web_page_preview": True}
    try:
        respuesta = cliente.post(URL_API + token + "/sendMessage", json=cuerpo, timeout=TIEMPO_ESPERA)
    except requests.RequestException:
        imprimir("::warning::No se pudo enviar el aviso por Telegram (error de red)")
        return False
    if respuesta.status_code != 200:
        imprimir("::warning::No se pudo enviar el aviso por Telegram (HTTP " + str(respuesta.status_code) + ")")
        return False
    return True
