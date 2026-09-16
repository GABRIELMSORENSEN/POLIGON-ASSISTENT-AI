# Validação da versão 2.0.0

Validado em 15/09/2026, Windows, Ryzen 7 7800X3D, RX580 8 GB e Samsung A35 (Android 16, ARM64, 6 GB).

- PC: interface nativa aberta, navegação e console conferidos com automação de navegador.
- IA 4B: chamou `write_file`, escreveu conteúdo solicitado, chamou `read_file` e confirmou o conteúdo real no disco.
- Android: motor C++ executou no aparelho físico; IA 0.8B chamou `device_info` e retornou modelo e bateria reais.
- Android offline: Wi-Fi e dados móveis temporariamente desligados; tarefa com ferramenta local concluída. Estado de rede restaurado ao fim.
- Remoto: celular pareado através de túnel HTTPS público. IA do telefone chamou `send_pc_task`; IA do PC criou arquivo no computador; telefone consultou `get_pc_task` e recebeu resultado concluído. Conteúdo do arquivo conferido no disco.
- Sete testes automatizados: proteção da API, pareamento de uso único, escopo de proprietário, revogação, backup/leituras reais, pausa de ferramentas, saída/erro de shell, memória, agendamento e validação de entradas.

Desempenho observado: PC aproximadamente 15–17 tokens/s; celular aproximadamente 14 tokens/s na primeira chamada curta. Prefill e visão podem demorar mais. Esses números não são garantia em outros aparelhos.

Não foram testados todos os aplicativos de terceiros, todos os comandos possíveis nem operação contínua de vários dias. Linux, macOS e iOS não têm validação de dispositivo nesta versão.

- Pacote Windows: executável PyInstaller aberto e tarefa `system_info` concluída pelo modelo.
- APK Release: instalado no A35, interface aberta e novo pareamento confirmado pelo PC.
