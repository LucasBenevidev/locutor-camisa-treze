"""Gera com IA o rascunho de locução das linhas Pendentes da planilha.

Para cada linha com status Pendente (ou vazio) e texto_ia vazio, grava o rascunho em texto_ia
e texto_final e muda o status para "Em revisão".
"""
import argparse
import os
import sys
import time

from google import genai
from google.genai import errors as genai_errors
from google.genai import types

from planilha import abrir_aba, atualizar_linha, ler_linhas

MODELO = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
TENTATIVAS = 4

INSTRUCOES = """Você escreve locuções curtas para uma caixa de som dentro da Loteria Camisa Treze, \
uma casa lotérica em Brasília. O texto será lido em voz alta por uma voz sintética em português do Brasil.

Regras:
- Entre 40 e 70 palavras, no máximo 5 frases curtas. Tom animado e acolhedor, de balcão de lotérica.
- Escreva tudo por extenso, como se fala: números ("seiscentos milhões de reais", "vinte e cinco reais"), \
datas ("trinta e um de dezembro") e horas ("dezessete horas"). Sem algarismos, símbolos, siglas soltas, \
emojis, hashtags, sites ou telefones.
- Use apenas as informações recebidas. Não invente valores, datas, prêmios nem números de cotas, \
nem qualificativos que não estejam nos dados (como "super", "gigante" ou "exclusivo").
- O áudio toca por vários dias. Nunca use expressões relativas ao dia atual, como "hoje", "amanhã", \
"esta semana" ou "nesta sexta". Cite sempre a data completa, como "dia dezesseis de outubro".
- Cite a Loteria Camisa Treze e termine chamando o cliente a participar.
- Não prometa nem sugira ganho garantido, não incentive a apostar além do que o cliente pode pagar.
- Responda somente com o texto da locução, sem aspas, título ou comentários."""

CAMPOS = [
    ("tipo", "Tipo do anúncio"),
    ("loteria", "Loteria"),
    ("data_sorteio", "Data do sorteio"),
    ("premio_estimado", "Prêmio estimado"),
    ("valor_cota", "Valor da cota"),
    ("prazo_aposta", "Prazo para apostar"),
    ("observacoes", "Observações do dono"),
]


def montar_pedido(linha):
    partes = [f"{rotulo}: {linha[campo]}" for campo, rotulo in CAMPOS if linha.get(campo, "").strip()]
    return "Dados do anúncio:\n" + "\n".join(partes)


def gerar_texto(cliente, linha):
    for tentativa in range(1, TENTATIVAS + 1):
        try:
            resposta = cliente.models.generate_content(
                model=MODELO,
                contents=montar_pedido(linha),
                config=types.GenerateContentConfig(
                    system_instruction=INSTRUCOES,
                    temperature=0.7,
                    thinking_config=types.ThinkingConfig(thinking_budget=0),
                ),
            )
            break
        except genai_errors.APIError as erro:
            if erro.code not in (429, 500, 503) or tentativa == TENTATIVAS:
                raise
            time.sleep(10 * tentativa)
    texto = (resposta.text or "").strip()
    if not texto:
        raise RuntimeError("a IA devolveu texto vazio")
    return texto


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry-run", action="store_true", help="Mostra os rascunhos sem gravar na planilha.")
    args = ap.parse_args()

    cliente = genai.Client()
    aba = abrir_aba()
    cabecalho, linhas = ler_linhas(aba)

    pendentes = [
        (n, l)
        for n, l in linhas
        if l["status"].strip() in ("", "Pendente")
        and not l["texto_ia"].strip()
        and (l["id"].strip() or l["loteria"].strip())
    ]
    print(f"Modelo: {MODELO} | linhas pendentes: {len(pendentes)}")

    falhas = 0
    for numero, linha in pendentes:
        if not linha["id"].strip() or not linha["loteria"].strip():
            print(f"Linha {numero}: sem id ou loteria, ignorada.")
            continue
        try:
            texto = gerar_texto(cliente, linha)
        except Exception as erro:
            falhas += 1
            print(f"Linha {numero} ({linha['id']}): erro ao gerar: {erro}")
            continue
        print(f"\nLinha {numero} ({linha['id']}):\n{texto}")
        if not args.dry_run:
            atualizar_linha(aba, cabecalho, numero, {"texto_ia": texto, "texto_final": texto, "status": "Em revisão"})

    if falhas:
        sys.exit(f"{falhas} linha(s) falharam.")


if __name__ == "__main__":
    main()
