import customtkinter as ctk
from PIL import Image
import requests
import io
import threading
import sys
from pathlib import Path
import ctypes
import re
import winreg
from datetime import date, timedelta


# Reinicia sem janela de console se estiver rodando com python.exe comum
if sys.platform == "win32" and "pythonw" not in sys.executable.lower():
    import subprocess
    args = [sys.executable.replace("python.exe", "pythonw.exe")] + sys.argv
    try:
        subprocess.Popen(args)
        sys.exit(0)
    except FileNotFoundError:
        pass  # pythonw não encontrado, continua normalmente


API_BASE  = "https://api.nasa.gov/planetary/apod?api_key=DEMO_KEY&thumbs=True"
YT_THUMB  = "https://i.ytimg.com/vi/{id}/{q}.jpg"
APOD_DIR  = Path.home() / "Pictures" / "APOD"
SAVE_PATH = APOD_DIR / "apod.jpg"

PREVIEW_W, PREVIEW_H = 500, 281   # prévia 16:9 exibida na tela

# Chave do registro para iniciar com o Windows
STARTUP_KEY  = r"Software\Microsoft\Windows\CurrentVersion\Run"
STARTUP_NAME = "NASA_APOD_Wallpaper"


IDIOMAS = {
    "pt-BR": {
        "codigo_traducao":       "pt",
        "titulo_app":            "NASA Wallpaper",
        "subtitulo_boas_vindas": "Como posso te chamar?",
        "placeholder_nome":      "Seu nome",
        "botao_entrar":          "Entrar",
        "aviso_nome":            "Digite seu nome para continuar.",
        "saudacao":              "Olá, {nome}.",
        "subtitulo_foto":        "Foto astronômica do dia",
        "data_foto":             "Data: {data}",
        "btn_atualizar":         "Atualizar agora",
        "btn_agendar":           "Iniciar com o Windows",
        "btn_parar":             "Parar de iniciar com o Windows",
        "conectando":            "Buscando informações da NASA...",
        "baixando_previa":       "Baixando prévia...",
        "aplicando":             "Aplicando fundo de tela...",
        "atualizado":            "Fundo de tela atualizado com sucesso.",
        "agendando":             "Salvando configuração...",
        "agendado":              "Pronto! O app iniciará com o Windows e atualizará o fundo automaticamente.",
        "parado":                "Removido da inicialização do Windows.",
        "erro_carregar":         "Erro ao carregar.",
        "tentar_novamente":      "Tentar novamente",
        "erro_agendar":          "Erro ao configurar: {exc}",
        "erro_8dias":            "A NASA não publicou nenhuma imagem nos últimos 8 dias.",
        "clique_atualizar":      "Clique em Atualizar agora para definir o fundo de tela.",
    },
    "en": {
        "codigo_traducao":       "en",
        "titulo_app":            "NASA Wallpaper",
        "subtitulo_boas_vindas": "What's your name?",
        "placeholder_nome":      "Your name",
        "botao_entrar":          "Enter",
        "aviso_nome":            "Please enter your name to continue.",
        "saudacao":              "Hello, {nome}.",
        "subtitulo_foto":        "Astronomy Picture of the Day",
        "data_foto":             "Date: {data}",
        "btn_atualizar":         "Update now",
        "btn_agendar":           "Start with Windows",
        "btn_parar":             "Stop starting with Windows",
        "conectando":            "Fetching NASA info...",
        "baixando_previa":       "Downloading preview...",
        "aplicando":             "Applying wallpaper...",
        "atualizado":            "Wallpaper updated successfully.",
        "agendando":             "Saving setting...",
        "agendado":              "Done! The app will start with Windows and update the wallpaper automatically.",
        "parado":                "Removed from Windows startup.",
        "erro_carregar":         "Failed to load.",
        "tentar_novamente":      "Try again",
        "erro_agendar":          "Configuration error: {exc}",
        "erro_8dias":            "NASA has not published any image in the last 8 days.",
        "clique_atualizar":      "Click Update now to set the wallpaper.",
    },
    "es": {
        "codigo_traducao":       "es",
        "titulo_app":            "NASA Wallpaper",
        "subtitulo_boas_vindas": "Como te llamas?",
        "placeholder_nome":      "Tu nombre",
        "botao_entrar":          "Entrar",
        "aviso_nome":            "Por favor, escribe tu nombre para continuar.",
        "saudacao":              "Hola, {nome}.",
        "subtitulo_foto":        "Foto astronomica del dia",
        "data_foto":             "Fecha: {data}",
        "btn_atualizar":         "Actualizar ahora",
        "btn_agendar":           "Iniciar con Windows",
        "btn_parar":             "Dejar de iniciar con Windows",
        "conectando":            "Obteniendo informacion de la NASA...",
        "baixando_previa":       "Descargando vista previa...",
        "aplicando":             "Aplicando fondo de pantalla...",
        "atualizado":            "Fondo de pantalla actualizado con exito.",
        "agendando":             "Guardando configuracion...",
        "agendado":              "Listo. La app iniciara con Windows y actualizara el fondo automaticamente.",
        "parado":                "Eliminado del inicio de Windows.",
        "erro_carregar":         "Error al cargar.",
        "tentar_novamente":      "Intentar de nuevo",
        "erro_agendar":          "Error al configurar: {exc}",
        "erro_8dias":            "La NASA no ha publicado ninguna imagen en los ultimos 8 dias.",
        "clique_atualizar":      "Haz clic en Actualizar ahora para establecer el fondo.",
    },
}

idioma_atual = "pt-BR"

def t(chave, **kwargs):
    texto = IDIOMAS[idioma_atual].get(chave, chave)
    return texto.format(**kwargs) if kwargs else texto

def codigo_traducao():
    return IDIOMAS[idioma_atual]["codigo_traducao"]

# Registro do Windows: iniciar com o Windows

def startup_esta_ativo() -> bool:
    """Retorna True se a entrada de autostart existe no registro."""
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, STARTUP_KEY) as chave:
            winreg.QueryValueEx(chave, STARTUP_NAME)
            return True
    except FileNotFoundError:
        return False
    except OSError:
        return False


def ativar_startup():
    """Adiciona o app à inicialização do Windows via registro (sem UAC)."""
    script = Path(__file__).resolve()
    # Usa pythonw para não abrir janela de console
    exe = sys.executable
    if exe.lower().endswith("python.exe"):
        pythonw = exe[:-10] + "pythonw.exe"
        if Path(pythonw).exists():
            exe = pythonw
    valor = f'"{exe}" "{script}" --executar'
    with winreg.OpenKey(
        winreg.HKEY_CURRENT_USER, STARTUP_KEY,
        0, winreg.KEY_SET_VALUE
    ) as chave:
        winreg.SetValueEx(chave, STARTUP_NAME, 0, winreg.REG_SZ, valor)


def desativar_startup():
    """Remove a entrada de autostart do registro."""
    try:
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, STARTUP_KEY,
            0, winreg.KEY_SET_VALUE
        ) as chave:
            winreg.DeleteValue(chave, STARTUP_NAME)
    except FileNotFoundError:
        pass  # já não existia

# Helpers de texto

def corrigir_pontuacao(texto: str) -> str:
    texto = texto.strip()
    if not texto:
        return texto
    if texto[-1] not in ".!?":
        texto += "."
    return texto[0].upper() + texto[1:]

def capitalizar_titulo(texto: str) -> str:
    texto = texto.strip()
    if not texto:
        return texto
    palavras = texto.split()
    resultado = []
    for i, p in enumerate(palavras):
        if i == 0 or (len(p) > 1 and not p.isupper()):
            resultado.append(p[0].upper() + p[1:] if p else p)
        else:
            resultado.append(p)
    return " ".join(resultado)


# Imagem / NASA

def extrair_id_youtube(url):
    m = re.search(r"(?:v=|youtu\.be/|embed/)([A-Za-z0-9_-]{11})", url or "")
    return m.group(1) if m else None


def miniatura_youtube(id_video):
    for qualidade in ("maxresdefault", "sddefault", "hqdefault"):
        try:
            r = requests.get(YT_THUMB.format(id=id_video, q=qualidade), timeout=15)
            if r.status_code == 200 and len(r.content) > 5_000:
                return r.content
        except requests.RequestException:
            pass
    return None


def obter_bytes_imagem(dados):
    if dados.get("media_type") == "image":
        url = dados.get("hdurl") or dados.get("url")
        if url:
            return requests.get(url, timeout=60).content
    if dados.get("thumbnail_url"):
        return requests.get(dados["thumbnail_url"], timeout=30).content
    id_yt = extrair_id_youtube(dados.get("url", ""))
    if id_yt:
        return miniatura_youtube(id_yt)
    return None


def consultar_nasa(dias_atras=0):
    data = date.today() - timedelta(days=dias_atras)
    dados = requests.get(API_BASE + f"&date={data}", timeout=15).json()
    return dados, data


def traduzir(texto):
    lang = codigo_traducao()
    if lang == "en":
        return texto
    try:
        r = requests.get(
            "https://translate.googleapis.com/translate_a/single",
            params={"client": "gtx", "sl": "en", "tl": lang, "dt": "t", "q": texto},
            timeout=15,
        )
        return "".join(parte[0] for parte in r.json()[0])
    except Exception:
        return texto


def redimensionar_capa(img: Image.Image, largura: int, altura: int) -> Image.Image:
    """
    Redimensiona a imagem para cobrir exatamente (largura x altura) sem distorcer,
    cortando as bordas excedentes (equivalente a CSS background-size: cover).
    """
    orig_w, orig_h = img.size
    escala = max(largura / orig_w, altura / orig_h)
    novo_w = round(orig_w * escala)
    novo_h = round(orig_h * escala)
    img = img.resize((novo_w, novo_h), Image.LANCZOS)
    # Corta ao centro
    esq = (novo_w - largura) // 2
    top  = (novo_h - altura) // 2
    img  = img.crop((esq, top, esq + largura, top + altura))
    return img


def resolucao_tela() -> tuple[int, int]:
    """Retorna a resolução real do monitor principal (sem escala DPI)."""
    user32 = ctypes.windll.user32
    user32.SetProcessDPIAware()
    return user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)


def atualizar_fundo_de_tela():
    for tentativa in range(8):
        try:
            data = date.today() - timedelta(days=tentativa)
            dados = requests.get(API_BASE + f"&date={data}", timeout=15).json()
            imagem = obter_bytes_imagem(dados)
            if not imagem:
                raise ValueError("sem imagem")
            break
        except Exception:
            continue
    else:
        raise RuntimeError(t("erro_8dias"))

    # Redimensiona para cobrir a tela sem distorcer
    larg, alt = resolucao_tela()
    img = Image.open(io.BytesIO(imagem))
    img = redimensionar_capa(img, larg, alt)

    APOD_DIR.mkdir(parents=True, exist_ok=True)
    img.save(str(SAVE_PATH), format="JPEG", quality=95)

    ctypes.windll.user32.SystemParametersInfoW(20, 0, str(SAVE_PATH), 3)
    return dados, imagem          # retorna bytes originais para a prévia


# UI

class SeletorIdioma(ctk.CTkFrame):
    OPCOES = [("PT", "pt-BR"), ("EN", "en"), ("ES", "es")]

    def __init__(self, master, ao_trocar):
        super().__init__(master, fg_color="transparent")
        self.ao_trocar = ao_trocar
        self._botoes = {}
        for label, codigo in self.OPCOES:
            b = ctk.CTkButton(
                self, text=label, width=52, height=30,
                font=ctk.CTkFont(size=12, weight="bold"),
                command=lambda c=codigo: self._selecionar(c),
            )
            b.pack(side="left", padx=4)
            self._botoes[codigo] = b
        self._realcar(idioma_atual)

    def _selecionar(self, codigo):
        global idioma_atual
        idioma_atual = codigo
        self._realcar(codigo)
        self.ao_trocar()

    def _realcar(self, codigo):
        for c, b in self._botoes.items():
            b.configure(fg_color=("#1f538d", "#1f6aa5") if c == codigo else ("gray75", "gray25"))


class TelaBemVindo(ctk.CTkFrame):
    def __init__(self, master, ao_confirmar):
        super().__init__(master, fg_color="transparent")
        self.ao_confirmar = ao_confirmar
        self._construir()

    def _construir(self):
        for w in self.winfo_children():
            w.destroy()

        outer = ctk.CTkFrame(self, fg_color="transparent")
        outer.place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(outer, text=t("titulo_app"),
                     font=ctk.CTkFont(size=30, weight="bold")).pack(pady=(0, 6))

        SeletorIdioma(outer, self._construir).pack(pady=(0, 20))

        ctk.CTkLabel(outer, text=t("subtitulo_boas_vindas"),
                     font=ctk.CTkFont(size=15)).pack(pady=(0, 12))

        self.entrada = ctk.CTkEntry(
            outer, placeholder_text=t("placeholder_nome"),
            width=240, height=40, justify="center",
            font=ctk.CTkFont(size=13),
        )
        self.entrada.pack(pady=(0, 16))
        self.entrada.bind("<Return>", lambda e: self._confirmar())

        ctk.CTkButton(
            outer, text=t("botao_entrar"),
            width=240, height=40,
            font=ctk.CTkFont(size=13),
            command=self._confirmar,
        ).pack()

        self.aviso = ctk.CTkLabel(outer, text="", text_color="red",
                                  font=ctk.CTkFont(size=12))
        self.aviso.pack(pady=(10, 0))

    def _confirmar(self):
        nome = self.entrada.get().strip()
        if not nome:
            self.aviso.configure(text=t("aviso_nome"))
            return
        self.ao_confirmar(nome)


class TelaPrincipal(ctk.CTkFrame):
    def __init__(self, master, nome):
        super().__init__(master, fg_color="transparent")
        self.nome     = nome
        self._ctk_img = None

        inner = ctk.CTkFrame(self, fg_color="transparent")
        inner.place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(inner, text=t("saudacao", nome=nome),
                     font=ctk.CTkFont(size=20, weight="bold")).pack(pady=(0, 2))
        ctk.CTkLabel(inner, text=t("subtitulo_foto"),
                     font=ctk.CTkFont(size=12), text_color="gray").pack()

        # Prévia grande da imagem
        self.label_imagem = ctk.CTkLabel(inner, text="", width=PREVIEW_W, height=PREVIEW_H)
        self.label_imagem.pack(pady=(14, 6))

        self.label_data = ctk.CTkLabel(
            inner, text="",
            font=ctk.CTkFont(size=11), text_color="gray",
        )
        self.label_data.pack(pady=(0, 4))

        self.label_titulo = ctk.CTkLabel(
            inner, text="",
            font=ctk.CTkFont(size=15, weight="bold"),
            wraplength=500, justify="center",
        )
        self.label_titulo.pack(pady=(0, 6))

        self.label_desc = ctk.CTkLabel(
            inner, text=t("clique_atualizar"),
            font=ctk.CTkFont(size=11),
            wraplength=500, justify="center", text_color="gray",
        )
        self.label_desc.pack(pady=(0, 16))

        self.botao = ctk.CTkButton(
            inner, text=t("btn_atualizar"),
            width=230, height=40,
            font=ctk.CTkFont(size=13),
            command=self._atualizar,
        )
        self.botao.pack(pady=(0, 6))

        # Botão de startup — texto muda conforme estado atual
        self.botao_startup = ctk.CTkButton(
            inner,
            text=t("btn_parar") if startup_esta_ativo() else t("btn_agendar"),
            width=230, height=40,
            font=ctk.CTkFont(size=13),
            command=self._toggle_startup,
        )
        self.botao_startup.pack(pady=(0, 10))

        self.label_status = ctk.CTkLabel(
            inner, text="",
            font=ctk.CTkFont(size=11),
            text_color="gray", wraplength=500, justify="center",
        )
        self.label_status.pack()

        # Ao abrir: busca metadados + prévia, sem alterar wallpaper
        self._buscar_info()

    # Busca informações (sem mudar wallpaper)

    def _buscar_info(self):
        self.botao.configure(state="disabled")
        self.label_status.configure(text=t("conectando"), text_color="gray")
        threading.Thread(target=self._tarefa_info, daemon=True).start()

    def _tarefa_info(self):
        try:
            dados = None
            data_pub = None
            for tentativa in range(8):
                try:
                    dados, data_pub = consultar_nasa(tentativa)
                    if dados.get("title"):
                        break
                except Exception:
                    continue
            if not dados:
                raise RuntimeError(t("erro_8dias"))

            titulo    = capitalizar_titulo(traduzir(dados.get("title", "")))
            descricao = corrigir_pontuacao(traduzir(dados.get("explanation", "")))
            data_str  = t("data_foto", data=str(data_pub))

            self.after(0, self._aplicar_texto, titulo, descricao, data_str)
            self.after(0, lambda: self.label_status.configure(text=t("baixando_previa"), text_color="gray"))

            img_bytes = obter_bytes_imagem(dados)
            if img_bytes:
                img = Image.open(io.BytesIO(img_bytes))
                img = redimensionar_capa(img, PREVIEW_W, PREVIEW_H)
                ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(PREVIEW_W, PREVIEW_H))
                self.after(0, self._aplicar_previa, ctk_img)
            else:
                self.after(0, lambda: self.label_status.configure(text="", text_color="gray"))

        except Exception as exc:
            self.after(0, self._erro, str(exc))

    def _aplicar_texto(self, titulo, descricao, data_str):
        self.label_data.configure(text=data_str)
        self.label_titulo.configure(text=titulo)
        self.label_desc.configure(text=descricao)
        self.botao.configure(state="normal", text=t("btn_atualizar"))

    def _aplicar_previa(self, ctk_img):
        self._ctk_img = ctk_img
        self.label_imagem.configure(image=ctk_img)
        self.label_status.configure(text="", text_color="gray")

    # Atualizar wallpaper agora

    def _atualizar(self):
        self.botao.configure(state="disabled", text=t("aplicando"))
        self.botao_startup.configure(state="disabled")
        self.label_status.configure(text=t("aplicando"), text_color="gray")
        threading.Thread(target=self._tarefa_atualizar, daemon=True).start()

    def _tarefa_atualizar(self):
        try:
            dados, imagem = atualizar_fundo_de_tela()
            # Usa bytes originais para a prévia (sem distorção na UI)
            img = Image.open(io.BytesIO(imagem))
            img = redimensionar_capa(img, PREVIEW_W, PREVIEW_H)
            ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(PREVIEW_W, PREVIEW_H))
            titulo    = capitalizar_titulo(traduzir(dados.get("title", "")))
            descricao = corrigir_pontuacao(traduzir(dados.get("explanation", "")))
            self.after(0, self._aplicar_atualizar, ctk_img, titulo, descricao)
        except Exception as exc:
            self.after(0, self._erro, str(exc))

    def _aplicar_atualizar(self, ctk_img, titulo, descricao):
        self._ctk_img = ctk_img
        self.label_imagem.configure(image=ctk_img)
        self.label_titulo.configure(text=titulo)
        self.label_desc.configure(text=descricao)
        self.botao.configure(state="normal", text=t("btn_atualizar"))
        self.botao_startup.configure(state="normal")
        self.label_status.configure(text=t("atualizado"), text_color="gray")

    # Toggle: Iniciar com Windows / Parar de iniciar com Windows

    def _toggle_startup(self):
        self.botao_startup.configure(state="disabled")
        self.label_status.configure(text=t("agendando"), text_color="gray")
        threading.Thread(target=self._tarefa_toggle_startup, daemon=True).start()

    def _tarefa_toggle_startup(self):
        try:
            if startup_esta_ativo():
                desativar_startup()
                novo_texto = t("btn_agendar")
                status_msg = t("parado")
            else:
                ativar_startup()
                novo_texto = t("btn_parar")
                status_msg = t("agendado")
            self.after(0, lambda: self.botao_startup.configure(
                state="normal", text=novo_texto
            ))
            self.after(0, lambda: self.label_status.configure(
                text=status_msg, text_color="gray"
            ))
        except Exception as exc:
            self.after(0, lambda: self.label_status.configure(
                text=t("erro_agendar", exc=exc), text_color="red"
            ))
            self.after(0, lambda: self.botao_startup.configure(state="normal"))

    # Erro genérico

    def _erro(self, msg):
        self.label_status.configure(text=msg, text_color="red")
        self.botao.configure(state="normal", text=t("tentar_novamente"))
        self.botao_startup.configure(state="normal")


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("NASA Wallpaper")
        self.geometry("560x900")
        self.resizable(False, False)
        ctk.set_appearance_mode("dark")
        self._tela_atual = None
        self._mostrar_boas_vindas()

    def _mostrar_boas_vindas(self):
        self._trocar_tela(TelaBemVindo(self, self._mostrar_principal))

    def _mostrar_principal(self, nome):
        self._trocar_tela(TelaPrincipal(self, nome))

    def _trocar_tela(self, nova_tela):
        if self._tela_atual:
            self._tela_atual.destroy()
        self._tela_atual = nova_tela
        self._tela_atual.place(x=0, y=0, relwidth=1, relheight=1)

# Entry points


if __name__ == "__main__":
    argumentos = sys.argv[1:]

    if "--executar" in argumentos:
        # Chamado automaticamente na inicialização do Windows:
        # atualiza o wallpaper silenciosamente e fecha.
        try:
            atualizar_fundo_de_tela()
        except Exception as exc:
            print(f"Erro: {exc}")

    else:
        app = App()
        app.mainloop()