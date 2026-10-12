"""Converte um texto aprovado em mp3 usando a voz Vitória (neural) do Amazon Polly."""
import argparse
import os
import sys
from pathlib import Path

import boto3

VOZ = "Vitoria"
MOTOR = "neural"
REGIAO = "us-east-1"
LIMITE_CARACTERES = 3000


def criar_cliente():
    perfil = os.getenv("AWS_PROFILE") or (None if os.getenv("AWS_ACCESS_KEY_ID") else "locutor")
    sessao = boto3.Session(profile_name=perfil, region_name=REGIAO)
    return sessao.client("polly")


def sintetizar(texto: str, destino: Path) -> Path:
    texto = texto.strip()
    if not texto:
        raise ValueError("O texto está vazio.")
    if len(texto) > LIMITE_CARACTERES:
        raise ValueError(f"O texto tem {len(texto)} caracteres; o limite do Polly é {LIMITE_CARACTERES}.")
    resposta = criar_cliente().synthesize_speech(
        Text=texto,
        VoiceId=VOZ,
        Engine=MOTOR,
        OutputFormat="mp3",
        LanguageCode="pt-BR",
    )
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_bytes(resposta["AudioStream"].read())
    return destino


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    origem = ap.add_mutually_exclusive_group(required=True)
    origem.add_argument("texto", nargs="?", help="Texto a ser falado.")
    origem.add_argument("--arquivo", type=Path, help="Arquivo .txt (UTF-8) com o texto.")
    ap.add_argument("-o", "--saida", type=Path, default=Path("saida/teste.mp3"))
    args = ap.parse_args()

    texto = args.arquivo.read_text(encoding="utf-8") if args.arquivo else args.texto
    try:
        caminho = sintetizar(texto, args.saida)
    except ValueError as erro:
        sys.exit(f"Erro: {erro}")
    print(f"Áudio gerado: {caminho} ({caminho.stat().st_size / 1024:.0f} KB)")


if __name__ == "__main__":
    main()
