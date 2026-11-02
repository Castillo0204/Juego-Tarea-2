"""Pruebas de la lógica del juego.

Ejecutar:  python -m unittest -v
"""

import json
import random
import tempfile
import unittest
from pathlib import Path

from logica import (
    NIVELES,
    VIDAS_INICIALES,
    ErrorPreguntas,
    Juego,
    Pregunta,
    cargar_preguntas,
    nivel_para,
)

RUTA_JSON = Path(__file__).with_name("preguntas.json")


def pregunta_de_prueba(numero, categoria="Ciencia", dificultad="fácil"):
    """Pregunta falsa cuya respuesta correcta es siempre la opción 'a' (posición 0)."""
    return Pregunta(categoria, dificultad, f"Pregunta {numero}", ["a", "b", "c", "d"], 0, "Explicación")


def pregunta_json(**cambios):
    datos = {
        "categoria": "Ciencia", "dificultad": "fácil", "pregunta": "¿Prueba?",
        "opciones": ["a", "b", "c", "d"], "correcta": 0, "explicacion": "Porque sí.",
    }
    datos.update(cambios)
    return datos


class TestCargaDePreguntas(unittest.TestCase):
    def _cargar_texto(self, texto):
        with tempfile.TemporaryDirectory() as carpeta:
            ruta = Path(carpeta) / "preguntas.json"
            ruta.write_text(texto, encoding="utf-8")
            return cargar_preguntas(ruta)

    def test_archivo_real_tiene_6_categorias_de_5_preguntas(self):
        preguntas = cargar_preguntas(RUTA_JSON)
        self.assertEqual(len(preguntas), 30)
        categorias = {p.categoria for p in preguntas}
        self.assertEqual(len(categorias), 6)
        for categoria in categorias:
            self.assertEqual(sum(p.categoria == categoria for p in preguntas), 5)

    def test_json_mal_formado(self):
        with self.assertRaises(ErrorPreguntas):
            self._cargar_texto("[{ esto no es json")

    def test_archivo_inexistente(self):
        with self.assertRaises(ErrorPreguntas):
            cargar_preguntas(Path("no_existe.json"))

    def test_correcta_fuera_de_rango(self):
        with self.assertRaises(ErrorPreguntas):
            self._cargar_texto(json.dumps([pregunta_json(correcta=7)]))

    def test_menos_de_4_opciones(self):
        with self.assertRaises(ErrorPreguntas):
            self._cargar_texto(json.dumps([pregunta_json(opciones=["a", "b", "c"])]))

    def test_campo_faltante(self):
        datos = pregunta_json()
        del datos["explicacion"]
        with self.assertRaises(ErrorPreguntas):
            self._cargar_texto(json.dumps([datos]))

    def test_dificultad_invalida(self):
        with self.assertRaises(ErrorPreguntas):
            self._cargar_texto(json.dumps([pregunta_json(dificultad="imposible")]))


class TestJuego(unittest.TestCase):
    def setUp(self):
        self.preguntas = [pregunta_de_prueba(i) for i in range(5)]
        self.juego = Juego(self.preguntas, azar=random.Random(1))

    def test_las_preguntas_no_se_repiten_y_la_categoria_se_agota(self):
        vistas = set()
        while "Ciencia" in self.juego.categorias_disponibles():
            vistas.add(self.juego.siguiente_pregunta("Ciencia").texto)
        self.assertEqual(len(vistas), 5)
        self.assertTrue(self.juego.terminado)
        with self.assertRaises(ValueError):
            self.juego.siguiente_pregunta("Ciencia")

    def test_al_mezclar_opciones_la_correcta_sigue_siendo_correcta(self):
        for _ in range(5):
            pregunta = self.juego.siguiente_pregunta("Ciencia")
            self.assertEqual(pregunta.opciones[pregunta.correcta], "a")

    def test_puntos_segun_dificultad(self):
        juego = Juego([pregunta_de_prueba(1, dificultad="difícil")])
        pregunta = juego.siguiente_pregunta("Ciencia")
        juego.responder(pregunta, pregunta.correcta)
        self.assertEqual(juego.puntaje, 3)

    def test_tres_aciertos_seguidos_dan_bonus_y_reinician_la_racha(self):
        for _ in range(3):
            pregunta = self.juego.siguiente_pregunta("Ciencia")
            self.juego.responder(pregunta, pregunta.correcta)
        self.assertEqual(self.juego.puntaje, 3 + 1)   # 3 fáciles + 1 de bonus
        self.assertEqual(self.juego.racha, 0)

    def test_fallar_resta_vida_y_reinicia_racha(self):
        pregunta = self.juego.siguiente_pregunta("Ciencia")
        self.juego.responder(pregunta, pregunta.correcta)
        self.assertEqual(self.juego.racha, 1)

        pregunta = self.juego.siguiente_pregunta("Ciencia")
        incorrecta = (pregunta.correcta + 1) % 4
        resultado = self.juego.responder(pregunta, incorrecta)
        self.assertFalse(resultado.acierto)
        self.assertEqual(self.juego.vidas, VIDAS_INICIALES - 1)
        self.assertEqual(self.juego.racha, 0)

    def test_sin_vidas_el_juego_termina(self):
        for _ in range(VIDAS_INICIALES):
            pregunta = self.juego.siguiente_pregunta("Ciencia")
            self.juego.responder(pregunta, (pregunta.correcta + 1) % 4)
        self.assertEqual(self.juego.vidas, 0)
        self.assertTrue(self.juego.terminado)

    def test_quedarse_sin_tiempo_cuenta_como_fallo(self):
        self.juego.tiempo_agotado()
        self.assertEqual(self.juego.vidas, VIDAS_INICIALES - 1)
        self.assertEqual(self.juego.respondidas, 1)

    def test_comodin_oculta_2_incorrectas_y_nunca_la_correcta(self):
        pregunta = self.juego.siguiente_pregunta("Ciencia")
        ocultas = self.juego.usar_comodin(pregunta)
        self.assertEqual(len(set(ocultas)), 2)
        self.assertNotIn(pregunta.correcta, ocultas)

    def test_comodines_se_acaban(self):
        pregunta = self.juego.siguiente_pregunta("Ciencia")
        while self.juego.comodines > 0:
            self.juego.usar_comodin(pregunta)
        self.assertEqual(self.juego.usar_comodin(pregunta), [])


class TestNiveles(unittest.TestCase):
    def test_tabla_de_niveles_es_coherente(self):
        self.assertEqual(NIVELES[0].puntos_minimos, 0)   # todos empiezan en el nivel 1
        minimos = [n.puntos_minimos for n in NIVELES]
        self.assertEqual(minimos, sorted(set(minimos)))  # ordenados y sin repetir
        self.assertEqual([n.numero for n in NIVELES], list(range(1, len(NIVELES) + 1)))

    def test_nivel_segun_puntaje_en_los_limites(self):
        self.assertEqual(nivel_para(0).numero, 1)
        self.assertEqual(nivel_para(4).numero, 1)
        self.assertEqual(nivel_para(5).numero, 2)
        self.assertEqual(nivel_para(39).numero, 5)
        self.assertEqual(nivel_para(40).numero, 6)
        self.assertEqual(nivel_para(500).numero, 6)

    def test_responder_avisa_cuando_subes_de_nivel(self):
        juego = Juego([pregunta_de_prueba(i) for i in range(5)], azar=random.Random(1))
        avisos = []
        for _ in range(4):
            pregunta = juego.siguiente_pregunta("Ciencia")
            avisos.append(juego.responder(pregunta, pregunta.correcta).subio_nivel)
        # puntaje tras cada acierto: 1, 2, 4 (con bonus), 5 -> el nivel 2 empieza en 5
        self.assertEqual(avisos, [False, False, False, True])
        self.assertEqual(juego.nivel.numero, 2)

    def test_siguiente_nivel_y_nivel_maximo(self):
        juego = Juego([pregunta_de_prueba(1)])
        self.assertEqual(juego.siguiente_nivel().numero, 2)
        juego.puntaje = 7
        self.assertEqual(juego.siguiente_nivel().puntos_minimos, 10)
        juego.puntaje = 100
        self.assertIsNone(juego.siguiente_nivel())


if __name__ == "__main__":
    unittest.main()
