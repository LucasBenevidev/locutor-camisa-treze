"""Constrói o site com os áudios aprovados e atualiza o status na planilha.

construir: gera site/ (mp3 + manifest.json) a partir das linhas Aprovado/Publicado ainda válidas.
marcar:    depois da publicação, muda Aprovado para Publicado e arquiva o que venceu.

A planilha é a fonte da verdade; o site publicado funciona como cache dos mp3 já gerados.
"""
import argparse
import hashlib
import json
import os
import re
import shutil
import time
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from gerar_audio import sintetizar
from planilha import abrir_aba, atualizar_linha, ler_linhas

FUSO = ZoneInfo("America/Sao_Paulo")
URL_PAGES = os.getenv("PAGES_URL", "https://lucasbenevidev.github.io/locutor-camisa-treze").rstrip("/")
SITE = Path("site")
ESTADO = Path("estado/estado.json")
ID_VALIDO = re.compile(r"^[A-Za-z0-9_-]+$")

PAGINA_INICIAL = """<!doctype html>
<html lang="pt-BR"><meta charset="utf-8"><title>Locutor Camisa Treze</title>
<p>Locutor Camisa Treze. Os áudios ficam em <a href="manifest.json">manifest.json</a>.</p></html>
"""


def hash_texto(texto):
    return hashlib.sha1(texto.strip().encode("utf-8")).hexdigest()[:12]


def ler_data(texto, padrao):
    try:
        return datetime.strptime(texto.strip(), padrao).replace(tzinfo=FUSO)
    except ValueError:
        return None


def valido_ate(linha):
    prazo = ler_data(linha["prazo_aposta"], "%d/%m/%Y %H:%M")
    if prazo:
        return prazo
    dia = ler_data(linha["data_sorteio"], "%d/%m/%Y")
    return dia.replace(hour=23, minute=59, second=59) if dia else None


def baixar(caminho):
    """Baixa um arquivo do site publicado. Devolve None se ainda não existe (404)."""
    url = f"{URL_PAGES}/{caminho}?_={int(time.time())}"
    try:
        with urllib.request.urlopen(url, timeout=30) as resposta:
            return resposta.read()
    except urllib.error.HTTPError as erro:
        if erro.code == 404:
            return None
        raise


def escrever_saida(nome, valor):
    arquivo = os.getenv("GITHUB_OUTPUT")
    linha = f"{nome}={valor}"
    if arquivo:
        with open(arquivo, "a", encoding="utf-8") as f:
            f.write(linha + "\n")
    print(linha)


def construir():
    aba = abrir_aba()
    _, linhas = ler_linhas(aba)
    agora = datetime.now(FUSO)

    bruto = baixar("manifest.json")
    ao_vivo = {a["id"]: a["sha"] for a in json.loads(bruto)["audios"]} if bruto else None

    if SITE.exists():
        shutil.rmtree(SITE)
    (SITE / "audios").mkdir(parents=True)

    entradas, publicar, arquivar, vistos = [], [], [], set()
    for numero, linha in linhas:
        if linha["status"] not in ("Aprovado", "Publicado"):
            continue
        id_ = linha["id"].strip()
        texto = linha["texto_final"].strip()
        if not ID_VALIDO.match(id_) or id_ in vistos or not texto:
            print(f"::warning::Linha {numero}: id inválido, repetido ou sem texto_final; ignorada.")
            continue
        vistos.add(id_)
        limite = valido_ate(linha)
        if limite is None:
            print(f"::warning::Linha {numero} ({id_}): sem data_sorteio ou prazo_aposta válido; ignorada.")
            continue
        if agora > limite:
            arquivar.append(id_)
            continue

        sha = hash_texto(texto)
        destino = SITE / "audios" / f"{id_}.mp3"
        mp3 = baixar(f"audios/{id_}.mp3") if ao_vivo and ao_vivo.get(id_) == sha else None
        if mp3:
            destino.write_bytes(mp3)
        else:
            try:
                sintetizar(texto, destino)
            except Exception as erro:
                print(f"::warning::Linha {numero} ({id_}): falha ao gerar o áudio: {erro}")
                continue
        entradas.append({"id": id_, "arquivo": f"audios/{id_}.mp3", "sha": sha, "valido_ate": limite.isoformat()})
        if linha["status"] == "Aprovado":
            publicar.append({"id": id_, "sha": sha})

    entradas.sort(key=lambda e: e["id"])
    manifesto = {"atualizado_em": agora.isoformat(timespec="seconds"), "audios": entradas}
    (SITE / "manifest.json").write_text(json.dumps(manifesto, ensure_ascii=False, indent=2), encoding="utf-8")
    (SITE / "index.html").write_text(PAGINA_INICIAL, encoding="utf-8")

    ESTADO.parent.mkdir(parents=True, exist_ok=True)
    ESTADO.write_text(json.dumps({"publicar": publicar, "arquivar": arquivar}, ensure_ascii=False), encoding="utf-8")

    novo = {e["id"]: e["sha"] for e in entradas}
    print(f"Áudios no ar: {len(entradas)} | a marcar como Publicado: {len(publicar)} | vencidos: {len(arquivar)}")
    escrever_saida("mudou", "true" if ao_vivo is None or novo != ao_vivo else "false")


def marcar():
    estado = json.loads(ESTADO.read_text(encoding="utf-8"))
    aba = abrir_aba()
    cabecalho, linhas = ler_linhas(aba)
    por_id = {l["id"].strip(): (n, l) for n, l in linhas}

    for item in estado["publicar"]:
        achado = por_id.get(item["id"])
        if achado and achado[1]["status"] == "Aprovado" and hash_texto(achado[1]["texto_final"]) == item["sha"]:
            atualizar_linha(aba, cabecalho, achado[0], {"status": "Publicado"})
            print(f"{item['id']}: Publicado")

    for id_ in estado["arquivar"]:
        achado = por_id.get(id_)
        if achado and achado[1]["status"] in ("Aprovado", "Publicado"):
            atualizar_linha(aba, cabecalho, achado[0], {"status": "Arquivado"})
            print(f"{id_}: Arquivado (venceu)")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("acao", choices=["construir", "marcar"])
    args = ap.parse_args()
    {"construir": construir, "marcar": marcar}[args.acao]()


if __name__ == "__main__":
    main()
