"""Envia por e-mail o aviso de que alguma rotina do workflow falhou."""
import json
import os
import smtplib
import sys
from datetime import datetime
from email.message import EmailMessage
from zoneinfo import ZoneInfo

PARA = "professorbenevides@gmail.com"
COPIA = "rmbbloteria@gmail.com"


def main():
    usuario = os.getenv("SMTP_USER")
    senha = os.getenv("SMTP_APP_PASSWORD")
    if not usuario or not senha:
        sys.exit("Secrets SMTP_USER e SMTP_APP_PASSWORD não configurados; aviso por e-mail não enviado.")

    jobs = json.loads(os.environ["NEEDS_JSON"])
    com_erro = [nome for nome, dados in jobs.items() if dados.get("result") == "failure"]
    falhas = jobs.get("construir", {}).get("outputs", {}).get("falhas", "0")
    if falhas not in ("", "0"):
        com_erro.append(f"construir ({falhas} anúncio(s) não puderam virar áudio)")

    url = f"{os.environ['GITHUB_SERVER_URL']}/{os.environ['GITHUB_REPOSITORY']}/actions/runs/{os.environ['GITHUB_RUN_ID']}"
    agora = datetime.now(ZoneInfo("America/Sao_Paulo")).strftime("%d/%m/%Y %H:%M")

    msg = EmailMessage()
    msg["Subject"] = "Locutor Camisa Treze: erro na publicação dos áudios"
    msg["From"] = usuario
    msg["To"] = PARA
    msg["Cc"] = COPIA
    msg.set_content(
        f"Uma rotina do Locutor Camisa Treze falhou em {agora} (horário de Brasília).\n\n"
        f"Rotinas com problema: {', '.join(com_erro) or 'não identificadas'}\n\n"
        f"Detalhes e registro da execução: {url}\n\n"
        "Enquanto o problema não for corrigido, novos áudios podem não ser publicados. "
        "Os áudios que já estão no ar continuam tocando.\n"
        "Este aviso é enviado só na primeira falha; se a execução seguinte também falhar, não há novo e-mail."
    )

    with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=30) as servidor:
        servidor.login(usuario, senha)
        servidor.send_message(msg)
    print("Aviso enviado.")


if __name__ == "__main__":
    main()
