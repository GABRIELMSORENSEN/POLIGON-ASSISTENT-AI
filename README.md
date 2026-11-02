<p align="center"><img src="web/logo.svg" width="90" alt="Poligon"></p>
<h1 align="center">POLIGON</h1>
<p align="center">Um assistente multimodelo para Windows e Android: chat, voz, memória compartilhada e ações reais no dispositivo.</p>

## Baixar e compilar

As versões publicadas ficam em [GitHub Releases](https://github.com/GABRIELMSORENSEN/POLIGON-ASSISTENT-AI/releases). O workflow **POLIGON desktop and Android builds** também gera artefatos de Windows e Android em GitHub Actions. O APK Android é ARM64 e requer Android 9 ou superior.

O build Windows inclui o motor llama.cpp Vulkan e o cliente Cloudflare. O build Android compila o servidor llama.cpp para ARM64 e o inclui no APK. Os modelos não são empacotados: são baixados sob demanda, verificados por SHA-256 e ficam no armazenamento privado/local.

## Modelos locais e offline

- **Windows:** Qwen3.5 4B Q4_K_M (~2,74 GB) e projetor visual (~672 MB). A configuração de referência é Ryzen 7 5700G, 24 GB RAM e Radeon RX 7600 8 GB. Vulkan é o caminho de aceleração; CPU pode ser selecionada com camadas GPU = 0.
- **Android:** Qwen3.5 0.8B Q4_K_M (~533 MB), executado na CPU. Recomendado ARM64 com pelo menos 6 GB de RAM. Consome memória, bateria e armazenamento.
- Os modelos ficam em `models-manifest.json`; URLs apontam para revisões fixas e downloads são verificados. Outros modelos no catálogo local ainda são candidatos, não downloads prontos.

## Modelos online

A aba **Modelos** descobre modelos dinamicamente nos endpoints oficiais e permite conectar:

| Provedor | Situação de custo | Observação |
|---|---|---|
| Google Gemini API | Camada gratuita para modelos elegíveis | O seletor filtra Gemini 3.8 Flash, 3.6 Flash e 3.5 Flash-Lite. No plano gratuito, conteúdo pode ser usado para melhorar produtos Google. |
| OpenRouter | Variantes gratuitas | O Poligon restringe a seleção a `openrouter/free` e modelos `:free`; disponibilidade e limites mudam. |
| Cerebras Inference | Crédito promocional de avaliação | A Cerebras anuncia US$ 5 de crédito gratuito inicial ao criar a conta; depois, a API é paga por uso. |
| DeepSeek API | Pago por uso | Modelos e capacidades consultados dinamicamente. |
| xAI / Grok API | Pago por uso | Não é incluído em uma assinatura ChatGPT. |
| Mistral API | Pago por uso | Confira preços e eventuais créditos de avaliação. |
| OpenAI API | Pago por uso | Uma assinatura ChatGPT não inclui créditos de API. |

**Não existe fallback automático para um modelo pago.** Para manter chamadas sem cobrança de modelo, selecione apenas Gemini elegível no plano gratuito ou variantes gratuitas do OpenRouter. O app não envia prompts a um provedor online até o proprietário conectar e selecionar esse provedor. O modo **Automático · grátis primeiro** tenta OpenRouter gratuito, depois os modelos Gemini gratuitos permitidos e, se nenhum estiver configurado ou responder, volta para a IA local. Ele não escolhe DeepSeek, Grok, Mistral, OpenAI ou Cerebras automaticamente. As chaves são guardadas no cofre de credenciais do sistema operacional via `keyring`; no Windows, use o Gerenciador de Credenciais. Se não houver um cofre seguro disponível, a conexão é recusada.

## Chat, voz e memória

- Chat e modo de voz usam o mesmo fluxo de tarefas e o mesmo histórico.
- A interface de voz tem uma esfera galáctica animada. No Android, usa `SpeechRecognizer` com preferência por reconhecimento offline e `TextToSpeech` do sistema; a disponibilidade offline depende do serviço de voz instalado. No Windows, depende do suporte de voz do WebView/navegador.
- Preferências salvas são usadas pelos diferentes modelos. Quando Android e PC estão pareados, as memórias são sincronizadas e também ficam em cache local para uso offline.
- A memória é contexto útil, não treinamento dos pesos dos modelos: trocar de modelo não altera seus parâmetros.

## Ações e acesso aos dispositivos

| Função | Windows | Android |
|---|---|---|
| Inferência local/offline | Sim | Sim |
| Provedores online configurados no PC | Sim | Via PC pareado |
| Arquivos, terminal, navegador e aplicativos | Sim | Via PC pareado |
| Captura de tela, clique, teclado e rolagem | Sim | Controles remotos do PC |
| Informações de bateria e hardware do celular | — | Sim |
| Histórico, tarefas e memórias | Sim | Sim |
| Modo automático ou revisão de ações | Sim | Sim |

O modelo escolhe ferramentas; o aplicativo executa e devolve resultados reais. No modo **Executar ações**, o agente recebe os privilégios do processo do usuário. No modo **Revisar cada ação**, ferramentas que alteram dados aguardam aprovação. Escritas por `write_file` fazem backup, mas comandos de terminal podem alterar arquivos diretamente. Use o modo de revisão para tarefas sensíveis.

## Conectar Android ao PC

1. No Windows, abra **Meu computador → Ativar acesso remoto**.
2. Gere um código e copie o endereço HTTPS temporário.
3. No Android, abra **Meu computador**, informe endereço e código ou use o QR.
4. Escolha **IA do celular** para inferência local no telefone ou **IA do PC** para usar o modelo e os provedores configurados no computador.

O código de pareamento é de uso único e expira em dez minutos. Cada dispositivo recebe um token revogável. O PC precisa permanecer ligado, conectado e com Poligon aberto. O túnel Cloudflare é temporário e o endereço pode mudar. O tráfego remoto passa por HTTPS/Cloudflare, não por uma camada independente de criptografia ponta a ponta. Um dispositivo pareado tem acesso amplo às ações do PC; revogue dispositivos que não reconhece e pause o acesso remoto quando não estiver usando.

## Limites e recursos ainda em desenvolvimento

Modelos pequenos não têm o mesmo raciocínio de modelos grandes na nuvem e podem interpretar pedidos incorretamente. O Android não ultrapassa a sandbox do sistema nem controla arbitrariamente outros aplicativos. Ações já iniciadas podem terminar antes de um cancelamento. O agendador do PC depende do aplicativo estar em execução para processar tarefas.

As integrações avançadas de edição de vídeo com timeline profissional, Runway, ElevenLabs, geração de imagem/vídeo, Unity/VRChat e Blender ainda não estão concluídas. O modo de voz atual usa os serviços de reconhecimento e síntese disponíveis no dispositivo; não é um sistema de voz neural proprietário nem garante reconhecimento offline em todos os aparelhos.

## Executar pelo código

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python scripts/setup.py
python poligon_assistent.py
```

Para validar backend e interfaces:

```powershell
python -m unittest discover -s tests -v
python scripts/check_android_assets.py
node --check web/app.js
node --check web/providers.js
node --check web/voice.js
```

O workflow de build prepara os runtimes oficiais, compila o servidor Android com NDK 28 e produz o pacote Windows portátil e o APK ARM64. Para publicar uma Release manualmente, execute o workflow **POLIGON desktop and Android builds** com `publish_release=true`; pushes de tags `v*` também publicam após os dois builds passarem.

## Estrutura

- `poligon/agent.py`: agente, ferramentas, revisão e tarefas duráveis.
- `poligon/providers.py`: Gemini, OpenRouter, Cerebras, DeepSeek, xAI, Mistral e OpenAI API.
- `poligon/tools.py`: arquivos, shell, tela, memória e agendamentos.
- `poligon/server.py`: API autenticada, pareamento, provedores e túnel.
- `poligon/engine.py`: processo llama.cpp local.
- `android/`: app Java, WebView restrita, voz nativa e servidor llama.cpp ARM64.
- `web/`: interface compartilhada; os assets Android são verificados por `scripts/check_android_assets.py`.

## Licenças

Poligon: Apache-2.0, preservada do projeto original. [llama.cpp](https://github.com/ggml-org/llama.cpp): MIT. [Qwen](https://huggingface.co/Qwen): confira a licença do modelo específico e do artefato GGUF usado. [cloudflared](https://github.com/cloudflare/cloudflared): Apache-2.0. Os componentes mantêm suas licenças próprias; consulte `THIRD_PARTY_NOTICES.md`.
