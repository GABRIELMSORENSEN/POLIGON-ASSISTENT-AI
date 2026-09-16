# Compilação

## Windows

Instale dependências de `requirements.txt` e PyInstaller. Coloque a distribuição Vulkan de llama.cpp b10991 em `runtime/llama-windows/` e cloudflared Windows AMD64 em `runtime/cloudflared.exe`. Execute `python scripts/build_windows.py`. Modelos são baixados na primeira utilização e não entram no ZIP.

## Android

O executável `llama-server` é compilado a partir de llama.cpp b10991, commit `930e2fa5995789efbf249a8bf61325bb626e417b`, usando NDK 28.2.13676358, ABI arm64-v8a, android-28, Release, `BUILD_SHARED_LIBS=OFF`, `GGML_NATIVE=OFF`, `GGML_OPENMP=OFF`, `GGML_LLAMAFILE=OFF`, `LLAMA_OPENSSL=OFF`, `LLAMA_CURL=OFF`, `LLAMA_BUILD_TESTS=OFF`, `LLAMA_BUILD_EXAMPLES=OFF`. Target: `llama-server`.

Copie o executável para `android/app/src/main/jniLibs/arm64-v8a/libpoligon_llama.so`. A extração de bibliotecas nativas é necessária para executar do diretório aprovado pelo Android. Copie `web/` para `android/app/src/main/assets/web/` e `models-manifest.json` para `android/app/src/main/assets/`.

```powershell
cd android
.\gradlew.bat :app:assembleDebug
```

Para Release, configure `POLIGON_KEYSTORE`, `POLIGON_STORE_PASSWORD` e `POLIGON_KEY_PASSWORD`, com alias `poligon`, e execute `:app:assembleRelease`. Chaves de assinatura e modelos são ignorados pelo Git. Guarde a chave para futuras atualizações. A Release desativa a depuração WebView.
