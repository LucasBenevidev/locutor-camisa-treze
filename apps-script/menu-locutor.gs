// Menu "Locutor" da planilha: dispara o workflow do GitHub sem sair do Google Sheets.
// O token fica em Configurações do projeto > Propriedades do script, com o nome GITHUB_TOKEN.
const REPO = 'LucasBenevidev/locutor-camisa-treze';
const WORKFLOW = 'publicar.yml';
const BRANCH = 'main';

function onOpen() {
  SpreadsheetApp.getUi()
    .createMenu('Locutor')
    .addItem('Gerar rascunhos e publicar agora', 'dispararAgora')
    .addToUi();
}

function dispararAgora() {
  const ui = SpreadsheetApp.getUi();
  const token = PropertiesService.getScriptProperties().getProperty('GITHUB_TOKEN');
  if (!token) {
    ui.alert('O token do GitHub não está configurado. Avise quem cuida do sistema.');
    return;
  }

  const resposta = UrlFetchApp.fetch(
    'https://api.github.com/repos/' + REPO + '/actions/workflows/' + WORKFLOW + '/dispatches',
    {
      method: 'post',
      contentType: 'application/json',
      headers: {
        Authorization: 'Bearer ' + token,
        Accept: 'application/vnd.github+json',
        'X-GitHub-Api-Version': '2022-11-28',
      },
      payload: JSON.stringify({ ref: BRANCH }),
      muteHttpExceptions: true,
    }
  );

  const codigo = resposta.getResponseCode();
  if (codigo === 204) {
    ui.alert('Pedido enviado. Em 1 a 2 minutos os rascunhos aparecem na planilha e os anúncios aprovados são publicados.');
  } else {
    ui.alert('Não foi possível enviar o pedido (erro ' + codigo + '). Avise quem cuida do sistema.');
  }
}
