"""Interfaz gráfica (Tkinter) de Trivia Total, un juego estilo Preguntados.

Aquí solo hay código de pantalla: botones, colores, ruleta y temporizador.
Las reglas del juego (puntos, vidas, niveles) viven en logica.py.

Ejecutar:  python main.py
"""

import math
import random
import time
import tkinter as tk
from tkinter import messagebox, ttk

from logica import (
    COMODINES_INICIALES,
    NIVELES,
    PUNTOS_POR_DIFICULTAD,
    RACHA_PARA_BONUS,
    TIEMPO_POR_PREGUNTA,
    ErrorPreguntas,
    Juego,
    cargar_preguntas,
    ruta_preguntas_por_defecto,
)

# ---------- Colores ----------
FONDO = "#1e1e2e"
TEXTO = "#cdd6f4"
OPCION = "#313244"
OPCION_HOVER = "#45475a"
OPCION_APAGADA = "#252536"
VERDE = "#40a02b"
ROJO = "#d20f39"
AMARILLO = "#f9e2af"
MORADO = "#8839ef"
GRIS_AGOTADA = "#585b70"
PALETA_CATEGORIAS = ["#1e66f5", "#df8e1d", "#40a02b", "#8839ef", "#ea76cb", "#fe640b"]

# ---------- Medidas de la ruleta ----------
RULETA_ANCHO = 380
RULETA_ALTO = 380
RULETA_CX = 190          # centro de la rueda
RULETA_CY = 205
RULETA_RADIO = 160
DURACION_GIRO_MS = 3600  # cuánto dura el giro
FRAME_MS = 20            # una "foto" de la animación cada 20 ms (~50 por segundo)
PAUSA_TRAS_GIRO_MS = 900 # tiempo para ver la categoría antes de mostrar la pregunta


class Ruleta(tk.Canvas):
    """Rueda de categorías dibujada con arcos. Gira con animación y se frena en la elegida.

    La rueda guarda `rotacion`: cuántos grados ha girado en sentido horario.
    Arriba hay un puntero fijo; la categoría que queda bajo el puntero es la elegida.
    """

    def __init__(self, master):
        super().__init__(master, width=RULETA_ANCHO, height=RULETA_ALTO, bg=FONDO, highlightthickness=0)
        self.categorias = []
        self.colores = {}
        self.arcos = []
        self.textos = []
        self.rotacion = 0.0
        self.girando = False
        self._inicio_giro = 0.0
        self._ultima_categoria = None

    def configurar(self, categorias, colores):
        """Dibuja la rueda desde cero con las categorías y colores dados."""
        self.delete("all")
        self.categorias = list(categorias)
        self.colores = colores
        self.arcos = []
        self.textos = []
        self.rotacion = 0.0

        caja = (
            RULETA_CX - RULETA_RADIO, RULETA_CY - RULETA_RADIO,
            RULETA_CX + RULETA_RADIO, RULETA_CY + RULETA_RADIO,
        )
        for categoria in self.categorias:
            self.arcos.append(self.create_arc(
                *caja, start=0, extent=1, fill=colores[categoria],
                outline=FONDO, width=3, style="pieslice",
            ))
            self.textos.append(self.create_text(
                RULETA_CX, RULETA_CY, text=categoria, fill="white", font=("Helvetica", 10, "bold"),
            ))

        # Estas dos piezas no giran: el botón central y el puntero de arriba
        self.create_oval(
            RULETA_CX - 26, RULETA_CY - 26, RULETA_CX + 26, RULETA_CY + 26,
            fill=FONDO, outline=TEXTO, width=3,
        )
        self.create_polygon(
            RULETA_CX - 15, 6, RULETA_CX + 15, 6, RULETA_CX, 50,
            fill=AMARILLO, outline="white", width=2,
        )
        self._dibujar()

    def marcar_agotadas(self, disponibles):
        """Pinta de gris las categorías a las que ya no les quedan preguntas."""
        for categoria, arco in zip(self.categorias, self.arcos):
            color = self.colores[categoria] if categoria in disponibles else GRIS_AGOTADA
            self.itemconfigure(arco, fill=color)

    def categoria_en_puntero(self):
        """Categoría que está justo bajo el puntero en este momento."""
        n = len(self.categorias)
        paso = 360 / n
        return self.categorias[int(((-self.rotacion) % 360) / paso) % n]

    def girar(self, objetivo, al_terminar, al_cambiar=None):
        """Gira varias vueltas y frena con el puntero sobre `objetivo`.

        al_cambiar(categoria): se llama cada vez que otra categoría pasa bajo el puntero.
        al_terminar(categoria): se llama una sola vez, cuando la rueda se detiene.
        """
        if self.girando or objetivo not in self.categorias:
            return
        paso = 360 / len(self.categorias)
        k = self.categorias.index(objetivo)

        # Ángulo (0 a 360) que debe tener la rueda al final para que `objetivo` quede
        # bajo el puntero. El desvío evita frenar siempre exactamente en el centro.
        desvio = random.uniform(-0.35, 0.35) * paso
        angulo_final = (-(k + 0.5) * paso + desvio) % 360

        vueltas = random.randint(4, 5)
        inicio = self.rotacion
        fin = inicio + vueltas * 360 + ((angulo_final - inicio) % 360)

        self.girando = True
        self._ultima_categoria = None
        self._inicio_giro = time.monotonic()
        self._animar(inicio, fin, al_terminar, al_cambiar)

    def _animar(self, inicio, fin, al_terminar, al_cambiar):
        """Un cuadro de la animación. Se llama a sí misma cada FRAME_MS hasta terminar."""
        transcurrido_ms = (time.monotonic() - self._inicio_giro) * 1000
        t = min(transcurrido_ms / DURACION_GIRO_MS, 1.0)   # progreso: 0 al inicio, 1 al final
        suave = 1 - (1 - t) ** 3                           # arranca rápido y frena poco a poco
        self.rotacion = inicio + (fin - inicio) * suave
        self._dibujar()

        categoria = self.categoria_en_puntero()
        if al_cambiar and categoria != self._ultima_categoria:
            al_cambiar(categoria)
        self._ultima_categoria = categoria

        if t >= 1:
            self.girando = False
            al_terminar(categoria)
        else:
            self.after(FRAME_MS, lambda: self._animar(inicio, fin, al_terminar, al_cambiar))

    def _dibujar(self):
        """Coloca cada porción y su texto según la rotación actual."""
        n = len(self.categorias)
        if n == 0:
            return
        paso = 360 / n
        for i in range(n):
            # Ángulo del centro de la porción i (Tk mide en sentido antihorario desde las 3 en punto)
            centro = 90 - (i + 0.5) * paso - self.rotacion
            self.itemconfigure(self.arcos[i], start=centro - paso / 2, extent=paso)

            radianes = math.radians(centro)
            x = RULETA_CX + RULETA_RADIO * 0.62 * math.cos(radianes)
            y = RULETA_CY - RULETA_RADIO * 0.62 * math.sin(radianes)
            self.coords(self.textos[i], x, y)

            # El texto sigue el radio; en la mitad izquierda se voltea para no quedar de cabeza
            angulo_texto = centro if math.cos(radianes) >= 0 else centro + 180
            try:
                self.itemconfigure(self.textos[i], angle=angulo_texto)
            except tk.TclError:
                pass   # Tk viejo sin texto rotado: se queda horizontal


class Opcion(tk.Label):
    """Botón de respuesta.

    Usamos Label y no Button porque tk.Button ignora los colores en macOS.
    """

    def __init__(self, master, comando):
        super().__init__(
            master, text="", font=("Helvetica", 13), fg=TEXTO, bg=OPCION_APAGADA,
            wraplength=620, justify="left", anchor="w", padx=14, pady=7,
        )
        self.comando = comando
        self.activa = False
        self.bind("<Button-1>", self._click)
        self.bind("<Enter>", lambda _e: self.activa and self.config(bg=OPCION_HOVER))
        self.bind("<Leave>", lambda _e: self.activa and self.config(bg=OPCION))

    def mostrar(self, texto, activa=True):
        self.activa = activa
        self.config(text=texto, bg=OPCION if activa else OPCION_APAGADA)

    def desactivar(self):
        self.activa = False

    def pintar(self, color):
        self.config(bg=color)

    def _click(self, _evento):
        if self.activa:
            self.comando()


class AppTrivia(tk.Tk):
    def __init__(self, preguntas):
        super().__init__()
        self.title("Trivia Total")
        self.geometry("720x720")
        self.configure(bg=FONDO)
        self.resizable(False, False)

        self.preguntas = preguntas
        self.juego = None
        self.pregunta_actual = None
        self.respondida = False
        self.timer_id = None
        self.tiempo_restante = 0
        self.colores = {}

        self._construir_interfaz()
        self.nueva_partida()

    # ---------- Construcción de la pantalla ----------
    def _construir_interfaz(self):
        self.lbl_marcador = tk.Label(self, bg=FONDO, fg=TEXTO, font=("Helvetica", 15, "bold"))
        self.lbl_marcador.pack(pady=(15, 8))

        self.lbl_categoria = tk.Label(self, font=("Helvetica", 18, "bold"), fg="white", pady=12)
        self.lbl_categoria.pack(fill="x", padx=30)

        # Zona central de tamaño fijo: muestra la ruleta O la pregunta (nunca las dos)
        self.centro = tk.Frame(self, bg=FONDO, width=720, height=440)
        self.centro.pack(pady=5)
        self.centro.pack_propagate(False)

        self.vista_ruleta = tk.Frame(self.centro, bg=FONDO)
        self.ruleta = Ruleta(self.vista_ruleta)
        self.ruleta.pack(pady=5)

        self.vista_pregunta = tk.Frame(self.centro, bg=FONDO)
        self.lbl_tiempo = tk.Label(self.vista_pregunta, bg=FONDO, fg=AMARILLO, font=("Helvetica", 14, "bold"))
        self.lbl_tiempo.pack(pady=(10, 0))

        self.lbl_pregunta = tk.Label(
            self.vista_pregunta, bg=FONDO, fg=TEXTO, font=("Helvetica", 16, "bold"),
            wraplength=640, height=2,
        )
        self.lbl_pregunta.pack(padx=30, pady=(5, 10))

        self.opciones = [Opcion(self.vista_pregunta, lambda i=i: self.responder(i)) for i in range(4)]
        for opcion in self.opciones:
            opcion.pack(fill="x", padx=40, pady=4)

        self.lbl_explicacion = tk.Label(
            self.vista_pregunta, bg=FONDO, fg=TEXTO, font=("Helvetica", 12), wraplength=640, height=4,
        )
        self.lbl_explicacion.pack(padx=30, pady=8)

        # Vista del final de la partida: aquí se muestra el título obtenido
        self.vista_final = tk.Frame(self.centro, bg=FONDO)
        self.lbl_motivo_final = tk.Label(self.vista_final, bg=FONDO, fg=TEXTO, font=("Helvetica", 16))
        self.lbl_motivo_final.pack(pady=(35, 25))
        tk.Label(
            self.vista_final, text="TU TÍTULO", bg=FONDO, fg=AMARILLO, font=("Helvetica", 14, "bold"),
        ).pack()
        self.lbl_titulo_final = tk.Label(
            self.vista_final, bg=FONDO, fg="white", font=("Helvetica", 32, "bold"), wraplength=640,
        )
        self.lbl_titulo_final.pack(pady=(5, 5))
        self.lbl_nivel_final = tk.Label(self.vista_final, bg=FONDO, fg=AMARILLO, font=("Helvetica", 16, "bold"))
        self.lbl_nivel_final.pack(pady=(0, 25))
        self.lbl_resumen_final = tk.Label(
            self.vista_final, bg=FONDO, fg=TEXTO, font=("Helvetica", 14), wraplength=640, justify="center",
        )
        self.lbl_resumen_final.pack()

        botones = tk.Frame(self, bg=FONDO)
        botones.pack(pady=5)
        self.btn_girar = ttk.Button(botones, text="🎡 Girar", command=self.girar)
        self.btn_comodin = ttk.Button(botones, text="🃏 50/50", command=self.usar_comodin)
        self.btn_continuar = ttk.Button(botones, text="Continuar ➜", command=self.continuar)
        for boton in (self.btn_girar, self.btn_comodin, self.btn_continuar):
            boton.pack(side="left", padx=8)

    def _ver(self, vista):
        """Muestra una sola vista en la zona central: ruleta, pregunta o final."""
        for otra in (self.vista_ruleta, self.vista_pregunta, self.vista_final):
            otra.pack_forget()
        vista.pack(fill="both", expand=True)

    # ---------- Flujo de la partida ----------
    def nueva_partida(self):
        self._detener_tiempo()
        self.juego = Juego(self.preguntas)
        self.colores = {
            categoria: PALETA_CATEGORIAS[i % len(PALETA_CATEGORIAS)]
            for i, categoria in enumerate(self.juego.categorias)
        }
        self.ruleta.configurar(self.juego.categorias, self.colores)
        self.btn_girar.config(text="🎡 Girar", command=self.girar)
        self._mostrar_inicio()

    def _mostrar_inicio(self):
        """Pantalla con la ruleta, lista para girar."""
        self.pregunta_actual = None
        self.respondida = False
        self.lbl_categoria.config(text="¿Qué categoría te tocará?", bg=OPCION)
        self.lbl_tiempo.config(text="")
        self.lbl_pregunta.config(text="")
        self.lbl_explicacion.config(text="")
        for opcion in self.opciones:
            opcion.mostrar("", activa=False)
        self.ruleta.marcar_agotadas(self.juego.categorias_disponibles())
        self._ver(self.vista_ruleta)
        self.btn_girar.config(state="normal")
        self.btn_comodin.config(state="disabled")
        self.btn_continuar.config(state="disabled")
        self._actualizar_marcador()

    def girar(self):
        self.btn_girar.config(state="disabled")
        categoria = self.juego.elegir_categoria()   # la lógica decide al azar; la rueda lo "actúa"
        self.ruleta.girar(categoria, al_terminar=self._ruleta_termino, al_cambiar=self._mostrar_categoria)

    def _ruleta_termino(self, categoria):
        self._mostrar_categoria(categoria)
        self.after(PAUSA_TRAS_GIRO_MS, lambda: self.mostrar_pregunta(categoria))

    def _mostrar_categoria(self, nombre):
        self.lbl_categoria.config(text=nombre, bg=self.colores[nombre])

    def mostrar_pregunta(self, categoria):
        pregunta = self.juego.siguiente_pregunta(categoria)
        self.pregunta_actual = pregunta
        self.respondida = False

        puntos = PUNTOS_POR_DIFICULTAD[pregunta.dificultad]
        plural = "s" if puntos > 1 else ""
        self.lbl_categoria.config(
            text=f"{pregunta.categoria} · {pregunta.dificultad} ({puntos} pt{plural})",
            bg=self.colores[pregunta.categoria],
        )
        self.lbl_pregunta.config(text=pregunta.texto)
        self.lbl_explicacion.config(text="")
        for letra, opcion, texto in zip("ABCD", self.opciones, pregunta.opciones):
            opcion.mostrar(f"{letra}) {texto}", activa=True)
        self._ver(self.vista_pregunta)

        puede_comodin = self.juego.comodines > 0
        self.btn_comodin.config(state="normal" if puede_comodin else "disabled")

        self.tiempo_restante = TIEMPO_POR_PREGUNTA
        self._tick()

    # ---------- Temporizador ----------
    def _tick(self):
        """Se llama cada segundo mientras hay una pregunta sin responder."""
        color = ROJO if self.tiempo_restante <= 5 else AMARILLO
        self.lbl_tiempo.config(text=f"⏱ {self.tiempo_restante} s", fg=color)
        if self.tiempo_restante == 0:
            self.timer_id = None
            self._tiempo_agotado()
            return
        self.tiempo_restante -= 1
        self.timer_id = self.after(1000, self._tick)

    def _detener_tiempo(self):
        if self.timer_id is not None:
            self.after_cancel(self.timer_id)
            self.timer_id = None

    def _tiempo_agotado(self):
        if self.respondida:
            return
        resultado = self.juego.tiempo_agotado()
        self._revelar(None, resultado, "⏰ ¡Se acabó el tiempo!")

    # ---------- Respuestas ----------
    def responder(self, indice):
        if self.pregunta_actual is None or self.respondida:
            return
        self._detener_tiempo()
        resultado = self.juego.responder(self.pregunta_actual, indice)
        self._revelar(indice, resultado)

    def usar_comodin(self):
        if self.pregunta_actual is None or self.respondida:
            return
        for indice in self.juego.usar_comodin(self.pregunta_actual):
            self.opciones[indice].mostrar("—", activa=False)
        self.btn_comodin.config(state="disabled")
        self._actualizar_marcador()

    def _revelar(self, elegida, resultado, mensaje=None):
        """Pinta verde la correcta, roja la elegida (si falló) y muestra la explicación."""
        self.respondida = True
        pregunta = self.pregunta_actual
        for i, opcion in enumerate(self.opciones):
            opcion.desactivar()
            if i == pregunta.correcta:
                opcion.pintar(VERDE)
            elif i == elegida:
                opcion.pintar(ROJO)

        lineas = []
        if resultado.acierto:
            titulo = f"✅ ¡Correcto! +{resultado.puntos} pts"
            if resultado.bonus:
                titulo += f"  y +{resultado.bonus} por racha 🔥"
            lineas.append(titulo)
            if resultado.subio_nivel:
                nivel = self.juego.nivel
                lineas.append(f"🎉 ¡Subiste al nivel {nivel.numero}: {nivel.titulo}!")
        else:
            lineas.append(mensaje or "❌ Incorrecto")
        lineas.append(f"💡 {pregunta.explicacion}")
        self.lbl_explicacion.config(text="\n".join(lineas))

        self.btn_comodin.config(state="disabled")
        etiqueta = "Ver mi título ➜" if self.juego.terminado else "Continuar ➜"
        self.btn_continuar.config(text=etiqueta, state="normal")
        self._actualizar_marcador()

    def continuar(self):
        if self.juego.terminado:
            self._mostrar_final()
        else:
            self._mostrar_inicio()

    def _mostrar_final(self):
        """Pantalla de fin de partida: aquí se entrega el título según el nivel alcanzado."""
        juego = self.juego
        nivel = juego.nivel
        if juego.vidas <= 0:
            motivo = "Te quedaste sin vidas 💔"
        else:
            motivo = "¡Respondiste todas las preguntas! 🏆"

        siguiente = juego.siguiente_nivel()
        if siguiente is None:
            progreso = "¡Alcanzaste el nivel máximo!"
        else:
            faltan = siguiente.puntos_minimos - juego.puntaje
            progreso = f"Te faltaron {faltan} pts para ser «{siguiente.titulo}»"

        self.lbl_categoria.config(text="Fin del juego", bg=MORADO)
        self.lbl_motivo_final.config(text=motivo)
        self.lbl_titulo_final.config(text=nivel.titulo)
        self.lbl_nivel_final.config(text=f"🏅 Nivel {nivel.numero} de {len(NIVELES)}")
        self.lbl_resumen_final.config(
            text=f"Puntaje final: {juego.puntaje}\nAciertos: {juego.aciertos} de {juego.respondidas} preguntas\n{progreso}"
        )
        self._ver(self.vista_final)
        self.btn_girar.config(text="🔄 Jugar de nuevo", command=self.nueva_partida, state="normal")
        self.btn_continuar.config(state="disabled")

    def _actualizar_marcador(self):
        juego = self.juego
        nivel = juego.nivel
        self.lbl_marcador.config(
            text=(
                f"⭐ {juego.puntaje}    🔥 {juego.racha}/{RACHA_PARA_BONUS}"
                f"    ❤️ {juego.vidas}    🃏 {juego.comodines}/{COMODINES_INICIALES}\n"
                f"🏅 Nivel {nivel.numero} · {nivel.titulo}"
            )
        )


def main():
    try:
        preguntas = cargar_preguntas(ruta_preguntas_por_defecto())
    except ErrorPreguntas as error:
        # Sin ventana principal: solo mostramos el error y salimos
        raiz = tk.Tk()
        raiz.withdraw()
        messagebox.showerror("No se pudieron cargar las preguntas", str(error))
        return
    AppTrivia(preguntas).mainloop()


if __name__ == "__main__":
    main()
