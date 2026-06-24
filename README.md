# 🤟 Comunicação Inclusiva — Mudos e Surdos

Ferramenta **local** que une três modos de comunicação acessível:

| Aba | Recurso | Para quem |
|-----|---------|-----------|
| 🎤 Voz → Texto | Reconhece fala e exibe o texto na tela | **Surdos** leem o que foi dito |
| ⌨️ Texto → Fala | Digita e o computador fala em voz alta | **Mudos** se comunicam oralmente |
| 🤟 Texto → Libras | Exibe cada letra em imagens do alfabeto datilológico | Todos aprendem e se comunicam em Libras |

---

## ⚡ Instalação rápida

```bash
pip install SpeechRecognition pyttsx3 pillow pyaudio
```

> **Windows:** se o `pyaudio` falhar, baixe o `.whl` em  
> https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio

---

## ▶️ Executar

```bash
python app.py
```

---

## 🗂️ Estrutura

```
comunicacao_inclusiva/
├── app.py              ← Aplicativo principal
├── sinais_libras/      ← Imagens das letras A-Z em Libras
│   ├── A.png
│   ├── B.png
│   └── ...
└── README.md
```

---

## 💡 Dicas de uso

- **Aba Voz → Texto:** clique em *Gravar Voz* e fale. Requer conexão com internet (Google Speech API).
- **Aba Texto → Fala:** escreva e clique em *Falar*. Use **Ctrl+Enter** como atalho. Funciona 100% offline.
- **Aba Libras:** digite qualquer palavra e veja o soletramento em Libras (datilologia).
- O botão **"Ver em Libras"** na aba de Texto envia automaticamente o que você digitou para a aba de Libras.

---

## 🛠️ Requisitos

- Python 3.8+
- Microfone (para reconhecimento de voz)
- Caixas de som / fone (para síntese de fala)
- Internet (apenas para reconhecimento de voz via Google)
