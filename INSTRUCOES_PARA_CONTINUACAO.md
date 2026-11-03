# INSTRUÇÕES PARA CONTINUAÇÃO — POLIGON

> Documento de passagem de contexto para continuar o desenvolvimento pelo Codex.
> Leia este arquivo inteiro antes de modificar o projeto. Atualize-o ao concluir cada etapa.

## 1. Objetivo geral

Transformar o POLIGON em um assistente multiplataforma com aplicativos **independentes** para Windows e Android. Cada instalação deve funcionar sozinha, sem exigir pareamento, servidor ou computador ligado. Sincronização de memória entre dispositivos poderá existir futuramente, mas será opcional.

Prioridade imediata: estabilizar o aplicativo Android, integrar provedores de IA de verdade, permitir selecionar modelos e validar chat e voz no próprio celular. Depois, avançar para o editor profissional no Windows.

## 2. Regras obrigatórias de desenvolvimento

1. **Inspecione antes de alterar.** Leia a estrutura, README, instruções do projeto, dependências, arquitetura atual e histórico recente. Não presuma que funcionalidades descritas em conversas já estejam implementadas.
2. **Confirme o estado real no código.** Diferencie claramente: implementado, parcialmente implementado, apenas planejado e testado. Não marque como concluído algo que não foi compilado e exercitado.
3. Preserve funcionalidades existentes. Faça mudanças pequenas, coerentes e revisáveis; não reescreva módulos inteiros sem necessidade.
4. Não introduza dependência Android → Windows ou Android → servidor local. O Android deve funcionar em outra rede e com o PC desligado.
5. Não coloque chaves, tokens, senhas ou credenciais no código, nos arquivos de configuração versionados, nos logs ou em commits.
6. Use armazenamento seguro nativo para credenciais (Android Keystore no Android; cofre apropriado do sistema no Windows). Nunca registre o valor secreto em logs.
7. Não invente nomes/IDs de modelos ou endpoints. Consulte os catálogos e a documentação oficial dos provedores e trate indisponibilidade, limites e erros de forma explícita.
8. Não faça chamadas pagas sem ação clara do usuário. Mostre quando um provedor pode cobrar e não confunda crédito promocional com gratuidade permanente.
9. Não publique APK/instalador/Release até que os builds correspondentes tenham terminado com sucesso. Não diga que publicou sem verificar a página de Releases e os artefatos.
10. Ao terminar cada etapa, atualize este documento com arquivos alterados, decisões, comandos executados, resultados reais dos testes, pendências e próximo passo.

## 3. Prioridade 1 — Android independente

### Resultado esperado

O aplicativo Android deve oferecer chat e configurações próprias de IA. Deve funcionar sem PC pareado, sem servidor do POLIGON Windows e sem estar na mesma rede.

### Verificações e implementação

- Remover ou corrigir qualquer bloqueio de interface que exija pareamento com o PC para abrir provedores, selecionar modelos, conversar ou usar voz.
- Auditar todas as chamadas de rede: chamadas de IA devem sair diretamente do Android para o provedor configurado, ou para um serviço remoto explicitamente escolhido pelo usuário; nunca depender implicitamente do PC.
- Manter configuração e credenciais locais no Android, protegidas pelo Android Keystore.
- Exibir estado de cada provedor: não configurado, configurado, testando conexão, conectado, limite atingido ou erro.
- Permitir consultar modelos realmente disponíveis e selecionar um modelo válido. Não apresentar opções fictícias ou indisponíveis como conectadas.
- Implementar timeout, cancelamento, tratamento de erros HTTP, limites/rate limits, mensagens de erro úteis e retentativas com limites.
- Garantir que a troca de provedor/modelo afete a próxima solicitação do chat.
- Se houver modo local no Android, identificar separadamente os modelos compatíveis com o hardware e não prometer execução de modelos incompatíveis.
- Testar com o aparelho desconectado do PC e em uma rede diferente.

### Provedores candidatos

Investigar e integrar por adaptadores independentes, conforme APIs oficiais e disponibilidade real:

- Google Gemini API.
- OpenRouter (incluindo modelos com identificador/categoria free quando disponíveis).
- Cerebras.
- OpenAI API (GPT).
- DeepSeek.
- xAI (Grok).
- Mistral.

A lista é um objetivo de integração, não uma afirmação de que todos já funcionam. Cada adaptador deve ter teste próprio e documentação de configuração. OpenAI API é separada da assinatura ChatGPT e pode gerar cobrança. Modelos gratuitos de terceiros podem ter cotas, limites, mudanças ou indisponibilidade.

## 4. Prioridade 2 — Chat e voz integrados

O chat e a voz devem ser duas formas de interação com o mesmo assistente e contexto, não módulos isolados que o usuário precise ativar manualmente para cada tarefa.

- Permitir iniciar conversa por texto ou voz e manter o histórico/contexto da conversa.
- Implementar captura de áudio com permissões claras, estados visíveis de gravação/processamento e opção de cancelar.
- Integrar reconhecimento de fala e síntese de voz nativos do Android, respeitando idiomas e disponibilidade do dispositivo.
- Preparar adaptadores opcionais para serviços externos de voz, sem exigir chave para a voz nativa.
- Permitir que o agente escolha a ferramenta adequada para uma solicitação (por exemplo, transcrição + tradução + TTS para dublagem), mas pedir confirmação antes de operações pagas, destrutivas ou que enviem arquivos a terceiros.
- Nunca afirmar que áudio, imagem ou vídeo foi gerado se a operação não retornou um arquivo utilizável.

## 5. Prioridade 3 — Memória

- Memória local por instalação, com estrutura versionada e migrações seguras.
- Separar preferências globais, contexto de conversa e memória específica de projeto.
- Permitir visualizar, corrigir e apagar memórias por controles claros.
- Não enviar dados pessoais ou arquivos a provedores sem necessidade e transparência.
- Sincronização entre Android e Windows somente como recurso opcional futuro, com autenticação e criptografia adequadas.
- Não sobrescrever nem descartar a memória legada sem migração testada e possibilidade de recuperação.

## 6. Prioridade 4 — Windows e POLIGON Studio

Depois de estabilizar Android, continuar o aplicativo Windows e o editor profissional. O editor deve ser baseado em uma arquitetura real de edição, não apenas em uma tela conceitual.

Requisitos do editor:
- Importação de mídia e gerenciamento de arquivos/projetos.
- Preview de vídeo.
- Timeline editável multipista para vídeo, áudio e legendas.
- Cortar, dividir, mover, aparar e reorganizar clipes.
- Faixas, transições, efeitos, volume, sincronização e legendas.
- Undo/redo, salvamento de projeto e recuperação após falha.
- Exportação com presets, progresso, cancelamento e mensagens de erro.
- Integração de IA como ferramentas dentro do editor: transcrição, tradução, dublagem, geração de narração e recursos de imagem/vídeo.
- ElevenLabs, Runway, Blender e Unity são integrações candidatas; verificar APIs, licenças, custos e compatibilidade antes de implementar.

O FrameForge anterior serve somente como referência de memória/entendimento do fluxo de edição e preferências. **Não reutilizar sua implementação incompleta como base do editor profissional.** Escolher uma base técnica madura e compatível com o projeto, documentando a decisão e as licenças.

## 7. Interface e identidade

- Nome do produto: POLIGON.
- Identidade visual: preto e vermelho, estética galáctica elegante e minimalista.
- Interface funcional e acessível, não apenas demonstrativa.
- Mostrar claramente provedor, modelo, estado de conexão, modo online/offline e possíveis custos.
- Manter experiência coerente entre chat e voz; não esconder recursos essenciais atrás de pareamento.

## 8. Plano de execução recomendado para o Codex

Siga nesta ordem, sem pular validações:

1. Mapear o repositório e identificar módulos Android, Windows, APIs, armazenamento, chat, voz e CI.
2. Fazer uma auditoria objetiva do Android: localizar toda dependência de pareamento/PC e todas as rotas de provedores.
3. Criar uma tabela de estado por provedor (implementação, endpoint, descoberta de modelos, envio de chat, erros, testes).
4. Corrigir a independência do Android e remover dependências obrigatórias do PC.
5. Completar e testar os adaptadores de provedores, um por vez.
6. Validar seleção de modelo e conversa real no Android.
7. Validar voz no mesmo fluxo de conversa.
8. Executar testes unitários/instrumentados disponíveis, lint e build Android.
9. Testar em aparelho físico, com PC desligado e rede independente.
10. Só então preparar APK de teste e Release, registrando links e hashes dos artefatos.
11. Após o marco Android estar estável, iniciar o editor profissional no Windows.

## 9. Critérios de aceite do próximo marco Android

O marco só pode ser considerado concluído quando todos estes pontos forem comprovados:

- [ ] O Android abre e usa chat sem parear com o Windows.
- [ ] O Android funciona com o PC desligado.
- [ ] O usuário consegue configurar e proteger a chave de um provedor.
- [ ] O app consulta/valida o provedor e apresenta modelos reais disponíveis.
- [ ] O usuário consegue selecionar um modelo e receber uma resposta real no chat.
- [ ] Erros de chave inválida, falta de internet, limite e modelo indisponível são tratados.
- [ ] Voz inicia, transcreve e permite resposta falada no mesmo fluxo de conversa.
- [ ] Não há segredo em logs, código ou arquivos versionados.
- [ ] Testes e build Android passam.
- [ ] APK de teste foi instalado e exercitado em aparelho físico.
- [ ] A Release e seus artefatos foram verificados antes de compartilhar o link.

## 10. Relatório obrigatório ao concluir uma etapa

Acrescente ao final deste arquivo:

### Registro de execução — AAAA-MM-DD

- **Etapa:**
- **Commit/branch:**
- **Arquivos alterados:**
- **Implementado:**
- **Testes executados e resultado:**
- **Build/artefato:**
- **Limitações conhecidas:**
- **Próximo passo:**

Não invente resultados. Se um teste não foi executado, escreva “não executado”. Se o ambiente não permitir testar no aparelho físico, registre isso como pendência.

## 11. Instrução inicial para o Codex

Ao abrir este repositório, leia primeiro `INSTRUCOES_PARA_CONTINUACAO.md`. Em seguida, inspecione o código e o estado atual do GitHub Actions. Não confie cegamente em descrições de tarefas anteriores: confirme cada afirmação no código. Comece pela Prioridade 1 — Android independente — e implemente a menor correção segura que permita avançar. Antes de encerrar, atualize este arquivo com o que foi realmente feito e deixe explícito o próximo passo.
