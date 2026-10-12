# Locutor Camisa Treze

Locução automática para a Loteria Camisa Treze (Brasília): texto de propaganda escrito por IA, revisado por humano, narrado pelo Amazon Polly (voz Vitória, neural) e tocado numa caixa Bluetooth na loja.

Plano completo e arquitetura: [docs/plano.html](docs/plano.html).

## Teste rápido (Fase 1)

Requer Python 3 e as credenciais AWS no perfil `locutor` (`~/.aws/credentials`).

```powershell
py -m pip install -r requirements.txt
py src/gerar_audio.py "Atenção! A Mega-Sena da Virada está acumulada." -o saida/teste.mp3
```

Os áudios gerados localmente ficam em `saida/` (ignorada pelo git).

## Rascunhos com IA (Fase 2)

Lê as linhas com status Pendente da planilha, pede o texto ao Gemini e grava em `texto_ia` e `texto_final`, mudando o status para "Em revisão". Use `--dry-run` para ver sem gravar.

Requer a variável `GEMINI_API_KEY` e a chave da conta de serviço do Google em `~/.config/locutor/service-account.json` (no GitHub Actions, os secrets `GEMINI_API_KEY` e `GOOGLE_SERVICE_ACCOUNT_JSON`). O modelo pode ser trocado com `GEMINI_MODEL`.

```powershell
py src/gerar_rascunhos.py --dry-run
```
