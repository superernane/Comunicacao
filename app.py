"""
╔══════════════════════════════════════════════════════╗
║        COMUNICAÇÃO INCLUSIVA - Mudos e Surdos        ║
║  Voz → Texto | Texto → Fala | Texto → Libras         ║
╚══════════════════════════════════════════════════════╝

Instalar:
    pip install SpeechRecognition pyttsx3 pillow sounddevice scipy
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import os
import tempfile
import wave

# ── Dependências opcionais ─────────────────────────────────────────────────
try:
    import speech_recognition as sr
    SR_OK = True
except ImportError:
    SR_OK = False

try:
    import pyttsx3
    TTS_OK = True
except ImportError:
    TTS_OK = False

try:
    from PIL import Image, ImageTk
    PIL_OK = True
except ImportError:
    PIL_OK = False

try:
    import sounddevice as sd
    import numpy as np
    from scipy.io import wavfile
    SD_OK = True
except ImportError:
    SD_OK = False

# ── Caminho das imagens de Libras ──────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SINAIS_DIR = os.path.join(BASE_DIR, "sinais_libras")

# ── Paleta ─────────────────────────────────────────────────────────────────
C = {
    "bg":      "#1a1a2e",
    "painel":  "#16213e",
    "card":    "#0f3460",
    "acento":  "#e94560",
    "acento2": "#4cc9f0",
    "texto":   "#eaeaea",
    "sub":     "#a0a0b0",
    "ok":      "#4ade80",
    "aviso":   "#fbbf24",
    "white":   "#ffffff",
}

SAMPLE_RATE = 44100
MAX_SECONDS = 10


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Comunicação Inclusiva 🤟")
        self.configure(bg=C["bg"])
        self.geometry("920x700")
        self.resizable(True, True)
        self.minsize(760, 580)

        self.ouvindo = False
        self.motor_tts = None
        self._fotos: list = []          # evitar GC das imagens

        self._init_tts()
        self._build_ui()
        self._status_inicial()

    # ── TTS ───────────────────────────────────────────────────────────────
    def _init_tts(self):
        if not TTS_OK:
            return
        try:
            self.motor_tts = pyttsx3.init()
            self.motor_tts.setProperty("rate", 150)
            for v in self.motor_tts.getProperty("voices"):
                if "pt" in v.id.lower() or "brazil" in v.name.lower():
                    self.motor_tts.setProperty("voice", v.id)
                    break
        except Exception:
            self.motor_tts = None

    # ── UI ────────────────────────────────────────────────────────────────
    def _build_ui(self):
        # Header
        hdr = tk.Frame(self, bg=C["painel"], pady=12)
        hdr.pack(fill="x")
        tk.Label(hdr, text="🤟 Comunicação Inclusiva",
                 bg=C["painel"], fg=C["acento"],
                 font=("Segoe UI", 20, "bold")).pack(side="left", padx=20)
        self.lbl_status = tk.Label(hdr, text="", bg=C["painel"],
                                   fg=C["ok"], font=("Segoe UI", 10))
        self.lbl_status.pack(side="right", padx=20)

        # Notebook
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TNotebook", background=C["bg"], borderwidth=0)
        style.configure("TNotebook.Tab",
            background=C["card"], foreground=C["sub"],
            padding=[14, 6], font=("Segoe UI", 10))
        style.map("TNotebook.Tab",
            background=[("selected", C["acento"])],
            foreground=[("selected", "#fff")])

        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True, padx=12, pady=10)

        self.aba_voz   = tk.Frame(nb, bg=C["bg"])
        self.aba_texto = tk.Frame(nb, bg=C["bg"])
        self.aba_libra = tk.Frame(nb, bg=C["bg"])

        nb.add(self.aba_voz,   text="🎤  Voz → Texto  (Surdos)")
        nb.add(self.aba_texto, text="⌨️  Texto → Fala  (Mudos)")
        nb.add(self.aba_libra, text="🤟  Texto → Libras")

        self._aba_voz()
        self._aba_texto()
        self._aba_libras()

    # ── ABA VOZ ───────────────────────────────────────────────────────────
    def _aba_voz(self):
        f = self.aba_voz
        tk.Label(f, text="🎓 Modo Professor — fala contínua convertida em texto",
                 bg=C["bg"], fg=C["sub"], font=("Segoe UI", 11)
                 ).pack(pady=(16, 6))

        # Botões
        bf = tk.Frame(f, bg=C["bg"])
        bf.pack(pady=(0, 8))
        self.btn_gravar = self._btn(bf, "🎙️  Iniciar",
                                    self._gravar, C["acento"])
        self.btn_gravar.pack(side="left", padx=6)
        self.btn_parar = self._btn(bf, "⏹️  Parar",
                                   self._parar, C["card"])
        self.btn_parar.pack(side="left", padx=6)
        self.btn_parar.config(state="disabled")
        self._btn(bf, "🗑️  Limpar",
                  lambda: self._limpar_voz(), C["card"]
                  ).pack(side="left", padx=6)
        self._btn(bf, "📢  Ler em voz alta",
                  self._ler_voz, C["acento2"]
                  ).pack(side="left", padx=6)

        self.lbl_mic = tk.Label(f, text="Pressione Iniciar para começar",
                                bg=C["bg"], fg=C["sub"], font=("Segoe UI", 11))
        self.lbl_mic.pack(pady=(0, 4))

        # Caixa de texto expande o espaço restante
        box = tk.Frame(f, bg=C["card"])
        box.pack(fill="both", expand=True, padx=20, pady=(0, 12))
        self.txt_voz = tk.Text(box, wrap="word", bg=C["card"], fg=C["texto"],
                               insertbackground=C["texto"],
                               font=("Segoe UI", 14), relief="flat",
                               padx=14, pady=10)
        self.txt_voz.pack(fill="both", expand=True)
        self.txt_voz.config(state="disabled")

    # ── ABA TEXTO ─────────────────────────────────────────────────────────
    def _aba_texto(self):
        f = self.aba_texto
        tk.Label(f, text="Digite a mensagem que deseja falar",
                 bg=C["bg"], fg=C["sub"], font=("Segoe UI", 11)
                 ).pack(pady=(16, 6))

        bf = tk.Frame(f, bg=C["bg"])
        bf.pack(pady=(0, 4))
        self._btn(bf, "📢  Falar", self._falar, C["acento"]).pack(side="left", padx=6)
        self._btn(bf, "🗑️  Limpar",
                  lambda: self.txt_dig.delete("1.0", "end"), C["card"]
                  ).pack(side="left", padx=6)
        self._btn(bf, "🤟  Ver em Libras",
                  self._para_libras, C["acento2"]
                  ).pack(side="left", padx=6)

        tk.Label(f, text="Dica: Ctrl+Enter para falar rapidamente",
                 bg=C["bg"], fg=C["sub"], font=("Segoe UI", 9)).pack(pady=(0, 4))

        box = tk.Frame(f, bg=C["card"])
        box.pack(fill="both", expand=True, padx=20, pady=(0, 12))
        self.txt_dig = tk.Text(box, wrap="word", bg=C["card"], fg=C["texto"],
                               insertbackground=C["texto"],
                               font=("Segoe UI", 14), relief="flat",
                               padx=14, pady=10)
        self.txt_dig.pack(fill="both", expand=True)
        self.txt_dig.bind("<Control-Return>", lambda e: self._falar())

    # ── ABA LIBRAS ────────────────────────────────────────────────────────
    def _aba_libras(self):
        f = self.aba_libra

        top = tk.Frame(f, bg=C["bg"])
        top.pack(fill="x", padx=20, pady=(14, 6))
        tk.Label(top, text="Palavra / frase:",
                 bg=C["bg"], fg=C["sub"], font=("Segoe UI", 11)
                 ).pack(side="left")
        self.entry_lib = tk.Entry(top, bg=C["card"], fg=C["texto"],
                                  insertbackground=C["texto"],
                                  font=("Segoe UI", 13), relief="flat",
                                  highlightbackground=C["acento"],
                                  highlightthickness=1)
        self.entry_lib.pack(side="left", fill="x", expand=True, padx=10, ipady=6)
        self.entry_lib.bind("<Return>", lambda e: self._mostrar_libras())
        self._btn(top, "Mostrar", self._mostrar_libras, C["acento"]).pack(side="left")

        outer = tk.Frame(f, bg=C["bg"])
        outer.pack(fill="both", expand=True, padx=20, pady=6)

        self.cvs = tk.Canvas(outer, bg=C["painel"], highlightthickness=0)
        sb = ttk.Scrollbar(outer, orient="horizontal", command=self.cvs.xview)
        self.cvs.configure(xscrollcommand=sb.set)
        sb.pack(side="bottom", fill="x")
        self.cvs.pack(fill="both", expand=True)

        self.frm_sin = tk.Frame(self.cvs, bg=C["painel"])
        self.cvs.create_window((0, 0), window=self.frm_sin, anchor="nw")
        self.frm_sin.bind("<Configure>",
            lambda e: self.cvs.configure(
                scrollregion=self.cvs.bbox("all")))

        tk.Label(f,
                 text="ℹ️  Exibe o alfabeto datilológico (soletração letra a letra em Libras)",
                 bg=C["bg"], fg=C["sub"], font=("Segoe UI", 9)).pack(pady=4)

    # ── AÇÕES ─────────────────────────────────────────────────────────────
    def _gravar(self):
        if not SR_OK:
            messagebox.showwarning("Aviso",
                "SpeechRecognition não instalado.\npip install SpeechRecognition")
            return
        if not SD_OK:
            messagebox.showwarning("Aviso",
                "sounddevice não instalado.\npip install sounddevice scipy")
            return
        if self.ouvindo:
            return
        self.ouvindo = True
        self.btn_gravar.config(state="disabled")
        self.btn_parar.config(state="normal")
        # limpa o texto ao iniciar nova sessão
        self.txt_voz.config(state="normal")
        self.txt_voz.delete("1.0", "end")
        self.txt_voz.config(state="disabled")
        threading.Thread(target=self._loop_gravacao, daemon=True).start()

    def _parar(self):
        self.ouvindo = False
        self.btn_gravar.config(state="normal")
        self.btn_parar.config(state="disabled")
        self.after(0, self.lbl_mic.config,
                   {"text": "⏹️ Gravação encerrada.", "fg": C["sub"]})

    def _limpar_voz(self):
        self.txt_voz.config(state="normal")
        self.txt_voz.delete("1.0", "end")
        self.txt_voz.config(state="disabled")

    def _loop_gravacao(self):
        """Grava em blocos de 4 s e vai acrescentando o texto reconhecido."""
        import time
        r = sr.Recognizer()
        BLOCO = 4  # segundos por trecho

        while self.ouvindo:
            self.after(0, self.lbl_mic.config,
                       {"text": "🔴 Ouvindo…", "fg": C["ok"]})
            try:
                audio_np = sd.rec(int(BLOCO * SAMPLE_RATE),
                                  samplerate=SAMPLE_RATE,
                                  channels=1, dtype="int16")
                # Espera o bloco terminar, verificando se pediu parar
                for _ in range(BLOCO * 10):
                    if not self.ouvindo:
                        sd.stop()
                        break
                    time.sleep(0.1)
                else:
                    sd.wait()

                if not self.ouvindo and audio_np is None:
                    break

                # Salva WAV temporário
                import tempfile, wave, os
                tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
                tmp_path = tmp.name
                tmp.close()
                with wave.open(tmp_path, "wb") as wf:
                    wf.setnchannels(1)
                    wf.setsampwidth(2)
                    wf.setframerate(SAMPLE_RATE)
                    wf.writeframes(audio_np.tobytes())

                # Reconhece
                self.after(0, self.lbl_mic.config,
                           {"text": "⏳ Processando…", "fg": C["aviso"]})
                try:
                    with sr.AudioFile(tmp_path) as src:
                        audio_data = r.record(src)
                    texto = r.recognize_google(audio_data, language="pt-BR")
                    # Acrescenta o texto no widget (não substitui)
                    self.after(0, self._acrescentar_voz, texto)
                except sr.UnknownValueError:
                    pass  # silêncio ou ruído — ignora e continua
                except sr.RequestError as e:
                    self.after(0, self.lbl_mic.config,
                               {"text": f"❌ Erro de rede: {e}", "fg": C["acento"]})
                    self.ouvindo = False
                    break
                finally:
                    try:
                        os.unlink(tmp_path)
                    except Exception:
                        pass

            except Exception as e:
                self.after(0, self.lbl_mic.config,
                           {"text": f"❌ {e}", "fg": C["acento"]})
                self.ouvindo = False
                break

        self.after(0, self.btn_gravar.config, {"state": "normal"})
        self.after(0, self.btn_parar.config,  {"state": "disabled"})

    def _acrescentar_voz(self, texto):
        """Acrescenta um trecho reconhecido na caixa de texto."""
        self.txt_voz.config(state="normal")
        atual = self.txt_voz.get("1.0", "end").strip()
        if atual:
            self.txt_voz.insert("end", " " + texto)
        else:
            self.txt_voz.insert("end", texto)
        self.txt_voz.see("end")  # rola para o final
        self.txt_voz.config(state="disabled")
        self.lbl_mic.config(text="🔴 Ouvindo…", fg=C["ok"])

    def _falar(self):
        if not TTS_OK or not self.motor_tts:
            messagebox.showwarning("Aviso",
                "pyttsx3 não instalado.\npip install pyttsx3")
            return
        texto = self.txt_dig.get("1.0", "end").strip()
        if not texto:
            return
        threading.Thread(target=self._falar_thread, args=(texto,),
                         daemon=True).start()

    def _falar_thread(self, texto):
        try:
            self.motor_tts.say(texto)
            self.motor_tts.runAndWait()
        except Exception as e:
            self.after(0, messagebox.showerror, "Erro TTS", str(e))

    def _ler_voz(self):
        texto = self.txt_voz.get("1.0", "end").strip()
        if not texto:
            return
        self.txt_dig.delete("1.0", "end")
        self.txt_dig.insert("1.0", texto)
        self._falar()

    def _para_libras(self):
        texto = self.txt_dig.get("1.0", "end").strip()
        if not texto:
            return
        self.entry_lib.delete(0, "end")
        self.entry_lib.insert(0, texto[:80])
        self._mostrar_libras()
        for w in self.winfo_children():
            if isinstance(w, ttk.Notebook):
                w.select(2)
                break

    def _mostrar_libras(self):
        if not PIL_OK:
            messagebox.showwarning("Aviso",
                "Pillow não instalado.\npip install pillow")
            return
        texto = self.entry_lib.get().upper().strip()

        for w in self.frm_sin.winfo_children():
            w.destroy()
        self._fotos.clear()

        if not texto:
            tk.Label(self.frm_sin, text="Digite uma palavra acima ☝️",
                     bg=C["painel"], fg=C["sub"],
                     font=("Segoe UI", 13)).grid(row=0, column=0,
                                                  padx=20, pady=30)
            return

        col = 0
        for ch in texto:
            if ch == " ":
                tk.Label(self.frm_sin, text=" ", bg=C["painel"],
                         width=2).grid(row=0, column=col)
                col += 1
                continue

            path = os.path.join(SINAIS_DIR, f"{ch}.png")
            if os.path.exists(path):
                img = Image.open(path).resize((90, 90), Image.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                self._fotos.append(photo)
                card = tk.Frame(self.frm_sin, bg=C["card"], padx=4, pady=4)
                card.grid(row=0, column=col, padx=4, pady=6)
                tk.Label(card, image=photo, bg=C["card"]).pack()
                tk.Label(card, text=ch, bg=C["card"], fg=C["acento"],
                         font=("Segoe UI", 11, "bold")).pack()
            else:
                tk.Label(self.frm_sin, text=ch, bg=C["card"],
                         fg=C["aviso"], width=4, height=5,
                         font=("Segoe UI", 18, "bold")).grid(
                    row=0, column=col, padx=3, pady=6)
            col += 1

    # ── HELPERS ───────────────────────────────────────────────────────────
    def _btn(self, parent, txt, cmd, cor):
        return tk.Button(parent, text=txt, command=cmd,
                         bg=cor, fg=C["white"],
                         font=("Segoe UI", 11, "bold"),
                         relief="flat", cursor="hand2",
                         padx=14, pady=7,
                         activebackground=C["acento2"],
                         activeforeground="#000")

    def _set(self, widget, valor):
        widget.config(state="normal")
        widget.delete("1.0", "end")
        widget.insert("1.0", valor)
        widget.config(state="disabled")

    def _status_inicial(self):
        itens = [
            f"🎤 SR {'✅' if SR_OK else '❌'}",
            f"📢 TTS {'✅' if TTS_OK else '❌'}",
            f"🖼️ PIL {'✅' if PIL_OK else '❌'}",
            f"🎧 SD {'✅' if SD_OK else '⚠️ (opcional)'}",
        ]
        self.lbl_status.config(text="  |  ".join(itens))


if __name__ == "__main__":
    app = App()
    app.mainloop()
