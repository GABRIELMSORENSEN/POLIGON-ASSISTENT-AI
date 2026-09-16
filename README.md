<p align="center"><img src="web/logo.svg" width="90" alt="Poligon"></p>
<h1 align="center">POLIGON · Inteligência local</h1>
<p align="center">Uma IA no seu PC. Outra no seu celular. Ações reais, sem API externa de IA.</p>

## Baixar

Abra [Releases](https://github.com/GABRIELMSORENSEN/POLIGON-ASSISTENT-AI/releases). Windows: extraia o ZIP inteiro e abra `POLIGON.exe`. Android: instale o APK ARM64 (Android 9 ou superior). Na primeira execução, abra **Configurações → Instalar componentes e modelo**. O download exige internet; depois a inferência funciona offline.

- PC: Qwen3.5 4B Q4_K_M, cerca de 2,74 GB, mais projetor visual de 672 MB. Vulkan permite usar GPUs AMD, Intel e NVIDIA compatíveis. Use camadas GPU = 0 para CPU.
- Android: Qwen3.5 0.8B Q4_K_M, cerca de 533 MB, executado na CPU. Recomendado aparelho ARM64 com pelo menos 6 GB de RAM. O modelo usa memória e bateria; **Liberar memória** encerra o motor.
- Modelos não são incluídos no Git. URLs de revisões fixas e SHA-256 estão em `models-manifest.json`; downloads novos são verificados antes de instalar.

## O que faz

| Função | PC | Android |
|---|---|---|
| Conversa com IA local, sem chave de API | Sim | Sim |
| Memória persistente de preferências | Sim | Sim |
| Arquivos: listar, pesquisar, ler, escrever com backup | Sim | Via PC pareado |
| Terminal PowerShell / shell | Sim | Via PC pareado |
| Abrir aplicativos, páginas e ler páginas web | Sim | Via PC pareado |
| Capturar tela, clicar, digitar e usar atalhos | Sim; visão exige projetor | Controles remotos e IA do PC |
| Agendar tarefas persistentes | Sim; exige PC/app em execução | Via IA do PC |
| Informações reais de bateria e modelo do celular | — | Sim |
| Histórico de ferramentas e resultados | Sim | Sim |
| Executar automaticamente ou revisar cada ação | Sim | Sim |

O modelo decide quais ferramentas chamar; o aplicativo executa, registra o resultado real e o devolve ao modelo. Não são respostas fixas simulando ações. A IA do celular pode chamar `send_pc_task` e consultar `get_pc_task`, intermediando uma tarefa pela internet.

## Conectar o celular ao PC

1. No PC, abra **Meu computador → Ativar acesso remoto**.
2. Gere um código e copie o endereço HTTPS temporário.
3. No Android, abra **Meu computador**, informe endereço e código ou abra o QR pela câmera.
4. Escolha **IA do celular** para raciocínio no telefone ou **IA do PC** para o modelo maior. A aba Meu computador também tem captura de tela, clique e teclado remotos.

O código tem seis dígitos, expira em dez minutos e vale uma vez. Cada dispositivo recebe um token revogável. O PC precisa permanecer ligado, conectado e com Poligon aberto. O túnel Cloudflare é temporário: o endereço muda quando ele é recriado e o celular precisa ser pareado novamente. Não há promessa de disponibilidade contínua de túnel gratuito.

## Privacidade e controle

A inferência acontece somente no dispositivo. PC guarda histórico, tokens e memórias em `~/.poligon`; modelos ficam na pasta `models` do aplicativo, configurável. Android usa armazenamento privado e a pasta específica do app para o modelo. Não há Groq, OpenAI, Gemini, reconhecimento de voz online ou TTS remoto.

Acesso remoto passa por HTTPS/Cloudflare (não é criptografia ponta a ponta independente do provedor). Quem possui um token pareado tem acesso amplo aos arquivos e ações do PC. Use **Pausar acesso ao PC**, **Revogar** ou **Desconectar túnel** quando necessário. O servidor do PC e os motores de inferência escutam apenas no loopback por padrão. A ponte Android carrega somente os assets locais e bloqueia páginas e frames externos.

## Limites reais

Um modelo de 4B/0.8B não tem a capacidade de raciocínio de grandes modelos de nuvem. Pode interpretar pedidos incorretamente. Revise tarefas importantes. Não controla outros aplicativos do Android nem supera as permissões/sandbox do sistema. Não executa ações com o PC desligado. Cancelar interrompe as próximas etapas; uma chamada já em execução pode terminar antes. O agendador recupera tarefas vencidas ao abrir o PC e executa uma vez, sem reproduzir todas as repetições perdidas.

O modo automático dá ao assistente os privilégios do processo do usuário. Escritas via `write_file` fazem backup; comandos de terminal podem alterar arquivos diretamente. Há limite de 16 etapas por tarefa no PC, 8 no celular e 90 segundos por comando de terminal.

## Executar pelo código

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python scripts/setup.py
python poligon_assistent.py
```

Windows 10/11 com WebView2. O setup instala llama.cpp e os modelos; o pacote Windows da Release já inclui o motor e cloudflared. Para executar do código com acesso remoto, coloque o executável oficial `cloudflared.exe` em `runtime/`. Linux/macOS podem executar o backend Python com `llama-server` no PATH, mas não foram validados nesta versão e não recebem binários rotulados como testados.

```powershell
python -m unittest discover -s tests -v
python poligon_assistent.py --headless
python scripts/build_windows.py
```

Android: JDK 17, SDK 35, NDK 28, Gradle wrapper incluído. Veja [compilação](docs/BUILD.md) e [validação](docs/VALIDATION.md).

## Estrutura

- `poligon/agent.py`: agente, ferramentas, revisão e tarefas duráveis.
- `poligon/tools.py`: implementações reais de arquivos, shell, tela e memória.
- `poligon/server.py`: API autenticada, pareamento, túnel e interface.
- `poligon/engine.py`: processo local llama.cpp.
- `android/`: app nativo Java, WebView restrita e processo llama.cpp ARM64.
- `web/`: interface adaptável compartilhada entre PC e Android.
- `tests/`: autenticação, revogação, backup, pausa, shell, memória e agenda.

## Licenças

Poligon: Apache-2.0, preservada do projeto original. [llama.cpp](https://github.com/ggml-org/llama.cpp): MIT. [Qwen3.5](https://huggingface.co/Qwen/Qwen3.5-4B): Apache-2.0; GGUFs por [Unsloth](https://huggingface.co/unsloth). [cloudflared](https://github.com/cloudflare/cloudflared): Apache-2.0. Os componentes mantêm suas licenças próprias; consulte `THIRD_PARTY_NOTICES.md`.
