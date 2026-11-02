"""Lógica de Trivia Total (juego estilo Preguntados).

Este archivo NO sabe nada de ventanas ni botones: solo maneja las reglas
(preguntas, puntaje, racha, vidas, comodines). Así se puede probar solo
con test_logica.py y la interfaz (main.py) queda más simple.
"""

import json
import random
from dataclasses import dataclass
from pathlib import Path

# ---------- Reglas del juego (si quieres cambiar algo, empieza aquí) ----------
PUNTOS_POR_DIFICULTAD = {"fácil": 1, "media": 2, "difícil": 3}
VIDAS_INICIALES = 3
COMODINES_INICIALES = 2
RACHA_PARA_BONUS = 3        # cada 3 aciertos seguidos ganas +1 punto extra
TIEMPO_POR_PREGUNTA = 15    # segundos

CAMPOS_OBLIGATORIOS = ("categoria", "dificultad", "pregunta", "opciones", "correcta", "explicacion")


@dataclass(frozen=True)
class Nivel:
    numero: int
    titulo: str
    puntos_minimos: int    # puntaje que se necesita para alcanzar este nivel


# Del más bajo al más alto. Para cambiar títulos o dificultad del juego, edita esta lista.
NIVELES = [
    Nivel(1, "Novato Curioso", 0),
    Nivel(2, "Aprendiz de Trivias", 5),
    Nivel(3, "Explorador del Saber", 10),
    Nivel(4, "Sabelotodo", 18),
    Nivel(5, "Maestro de la Cultura", 28),
    Nivel(6, "Leyenda de la Trivia", 40),
]


def nivel_para(puntaje):
    """Devuelve el nivel más alto cuyo puntaje mínimo ya alcanzaste."""
    actual = NIVELES[0]
    for nivel in NIVELES:
        if puntaje >= nivel.puntos_minimos:
            actual = nivel
    return actual


class ErrorPreguntas(Exception):
    """Se lanza cuando preguntas.json no existe o tiene datos inválidos."""


@dataclass
class Pregunta:
    categoria: str
    dificultad: str
    texto: str
    opciones: list
    correcta: int          # posición (0 a 3) de la respuesta correcta en `opciones`
    explicacion: str


@dataclass
class Resultado:
    acierto: bool
    puntos: int = 0        # puntos por la dificultad
    bonus: int = 0         # puntos extra por racha
    subio_nivel: bool = False   # True si con esta respuesta alcanzaste un nivel nuevo


# ---------- Carga y validación del archivo de preguntas ----------
def cargar_preguntas(ruta):
    """Lee el JSON y devuelve una lista de Pregunta. Valida todo antes de jugar."""
    try:
        with open(ruta, encoding="utf-8") as archivo:
            datos = json.load(archivo)
    except FileNotFoundError:
        raise ErrorPreguntas(f"No se encontró el archivo de preguntas: {ruta}")
    except json.JSONDecodeError as error:
        raise ErrorPreguntas(f"El JSON tiene un error de formato: {error}")

    if not isinstance(datos, list) or not datos:
        raise ErrorPreguntas("El JSON debe ser una lista con al menos una pregunta.")

    return [_validar_pregunta(item, numero) for numero, item in enumerate(datos, start=1)]


def _validar_pregunta(item, numero):
    """Revisa una pregunta del JSON y la convierte en un objeto Pregunta."""
    if not isinstance(item, dict):
        raise ErrorPreguntas(f"Pregunta #{numero}: debe ser un objeto JSON.")

    faltantes = [campo for campo in CAMPOS_OBLIGATORIOS if campo not in item]
    if faltantes:
        raise ErrorPreguntas(f"Pregunta #{numero}: faltan los campos {', '.join(faltantes)}.")

    opciones = item["opciones"]
    if not isinstance(opciones, list) or len(opciones) != 4 or len(set(opciones)) != 4:
        raise ErrorPreguntas(f"Pregunta #{numero}: necesita exactamente 4 opciones distintas.")

    correcta = item["correcta"]
    if not isinstance(correcta, int) or isinstance(correcta, bool) or not 0 <= correcta <= 3:
        raise ErrorPreguntas(f"Pregunta #{numero}: 'correcta' debe ser un número de 0 a 3.")

    if item["dificultad"] not in PUNTOS_POR_DIFICULTAD:
        validas = ", ".join(PUNTOS_POR_DIFICULTAD)
        raise ErrorPreguntas(f"Pregunta #{numero}: dificultad inválida (usa: {validas}).")

    return Pregunta(
        categoria=item["categoria"],
        dificultad=item["dificultad"],
        texto=item["pregunta"],
        opciones=list(opciones),
        correcta=correcta,
        explicacion=item["explicacion"],
    )


# ---------- Estado de una partida ----------
class Juego:
    def __init__(self, preguntas, azar=None):
        # `azar` se puede pasar para que los tests sean repetibles
        self.azar = azar or random.Random()

        self.pendientes = {}   # categoría -> preguntas que aún no han salido
        for pregunta in preguntas:
            self.pendientes.setdefault(pregunta.categoria, []).append(pregunta)
        for lista in self.pendientes.values():
            self.azar.shuffle(lista)
        self.categorias = list(self.pendientes)   # todas, en el orden del JSON

        self.puntaje = 0
        self.racha = 0
        self.vidas = VIDAS_INICIALES
        self.comodines = COMODINES_INICIALES
        self.respondidas = 0
        self.aciertos = 0

    def categorias_disponibles(self):
        """Categorías que todavía tienen preguntas sin usar."""
        return [c for c, lista in self.pendientes.items() if lista]

    @property
    def terminado(self):
        return self.vidas <= 0 or not self.categorias_disponibles()

    @property
    def nivel(self):
        """Nivel actual según el puntaje. Al perder, este nivel es tu título."""
        return nivel_para(self.puntaje)

    def siguiente_nivel(self):
        """El próximo nivel por alcanzar, o None si ya estás en el más alto."""
        for nivel in NIVELES:
            if nivel.puntos_minimos > self.puntaje:
                return nivel
        return None

    def elegir_categoria(self):
        """La 'ruleta': elige al azar entre las categorías con preguntas."""
        disponibles = self.categorias_disponibles()
        if not disponibles:
            raise ValueError("Ya no quedan preguntas.")
        return self.azar.choice(disponibles)

    def siguiente_pregunta(self, categoria):
        """Saca una pregunta de la categoría (nunca se repite) y mezcla sus opciones."""
        lista = self.pendientes.get(categoria)
        if not lista:
            raise ValueError(f"No quedan preguntas en la categoría {categoria}.")
        base = lista.pop()

        texto_correcto = base.opciones[base.correcta]
        opciones = base.opciones[:]
        self.azar.shuffle(opciones)
        return Pregunta(
            categoria=base.categoria,
            dificultad=base.dificultad,
            texto=base.texto,
            opciones=opciones,
            correcta=opciones.index(texto_correcto),   # la posición cambió al mezclar
            explicacion=base.explicacion,
        )

    def responder(self, pregunta, indice):
        """Evalúa la respuesta elegida y actualiza puntaje, racha y vidas."""
        self.respondidas += 1
        if indice != pregunta.correcta:
            return self._fallar()

        self.aciertos += 1
        self.racha += 1
        puntos = PUNTOS_POR_DIFICULTAD[pregunta.dificultad]
        bonus = 0
        if self.racha >= RACHA_PARA_BONUS:
            bonus = 1
            self.racha = 0

        nivel_anterior = self.nivel
        self.puntaje += puntos + bonus
        subio_nivel = self.nivel.numero > nivel_anterior.numero
        return Resultado(True, puntos, bonus, subio_nivel)

    def tiempo_agotado(self):
        """Quedarse sin tiempo cuenta como fallar."""
        self.respondidas += 1
        return self._fallar()

    def usar_comodin(self, pregunta):
        """50/50: devuelve las posiciones de 2 opciones incorrectas para ocultarlas."""
        if self.comodines <= 0:
            return []
        self.comodines -= 1
        incorrectas = [i for i in range(4) if i != pregunta.correcta]
        return self.azar.sample(incorrectas, 2)

    def _fallar(self):
        self.vidas -= 1
        self.racha = 0
        return Resultado(False)


def ruta_preguntas_por_defecto():
    return Path(__file__).with_name("preguntas.json")
