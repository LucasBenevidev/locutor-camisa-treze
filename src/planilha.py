"""Acesso à planilha 'Anúncios da Lotérica' pela conta de serviço do Google."""
import json
import os
from pathlib import Path

import gspread

ID_PLANILHA = os.getenv("SHEET_ID", "1gjrVKB7UYH8sU-mHhZnO2vQm5zz9bKb4aAUeb-vIuR8")
ABA = "Anúncios"
ARQUIVO_CHAVE = Path.home() / ".config" / "locutor" / "service-account.json"


def abrir_aba():
    conteudo = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
    if conteudo:
        cliente = gspread.service_account_from_dict(json.loads(conteudo))
    else:
        cliente = gspread.service_account(filename=str(ARQUIVO_CHAVE))
    return cliente.open_by_key(ID_PLANILHA).worksheet(ABA)


def ler_linhas(aba):
    """Devolve (cabecalho, [(numero_da_linha, dict)]) com os valores como aparecem na tela."""
    valores = aba.get_all_values()
    cabecalho = valores[0]
    linhas = []
    for i, celulas in enumerate(valores[1:], start=2):
        celulas = celulas + [""] * (len(cabecalho) - len(celulas))
        linhas.append((i, dict(zip(cabecalho, celulas))))
    return cabecalho, linhas


def atualizar_linha(aba, cabecalho, numero, campos):
    """Grava só as colunas informadas em `campos` na linha `numero`."""
    dados = [
        {"range": gspread.utils.rowcol_to_a1(numero, cabecalho.index(nome) + 1), "values": [[valor]]}
        for nome, valor in campos.items()
    ]
    aba.batch_update(dados)
