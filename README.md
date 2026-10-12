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
