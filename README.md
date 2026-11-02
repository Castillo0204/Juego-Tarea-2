# 🎲 Trivia Total

Juego de preguntas de cultura general al estilo *Preguntados*, hecho en **Python + Tkinter** como actividad de **vibecoding guiado** (la IA como copiloto de programación).

## Cómo jugar

1. Presiona **🎡 Girar**: la rueda gira con animación y se frena en una categoría al azar.
2. Responde la pregunta de 4 opciones antes de que se acaben los **15 segundos**.
3. Al responder verás si acertaste y una explicación corta para aprender algo.

| Elemento | Regla |
|---|---|
| Puntos | Fácil = 1 · Media = 2 · Difícil = 3 |
| Racha | 3 aciertos seguidos = **+1 punto extra** |
| Vidas | Empiezas con 3 ❤️; cada fallo (o quedarte sin tiempo) resta una |
| Comodín 50/50 | 2 por partida: oculta 2 opciones incorrectas |
| Fin del juego | Te quedas sin vidas o respondes las 30 preguntas |
| Título | Al terminar recibes un título según tu nivel (ver abajo) |

### Niveles y títulos

Tu nivel sube con tu puntaje y se muestra siempre arriba. Cuando termina la partida, el nivel que alcanzaste es tu **título**:

| Nivel | Título | Puntaje mínimo |
|---|---|---|
| 1 | Novato Curioso | 0 |
| 2 | Aprendiz de Trivias | 5 |
| 3 | Explorador del Saber | 10 |
| 4 | Sabelotodo | 18 |
| 5 | Maestro de la Cultura | 28 |
| 6 | Leyenda de la Trivia | 40 |

Los niveles y sus títulos están en la lista `NIVELES` de `logica.py`; se pueden cambiar sin tocar nada más.

Hay 6 categorías (Geografía, Historia, Ciencia, Arte y Literatura, Entretenimiento y Deportes) con 5 preguntas cada una. Las preguntas no se repiten dentro de una partida y el orden de las opciones se mezcla.

## Cómo ejecutarlo

Necesitas **Python 3.8 o superior**. Tkinter ya viene incluido en Windows y macOS.

```bash
python main.py
```

En Linux, si falta Tkinter: `sudo apt install python3-tk`.

## Pruebas

```bash
python -m unittest -v
```

Las pruebas cubren la carga y validación del JSON (archivo inexistente, JSON roto, opciones incompletas, respuesta fuera de rango) y las reglas del juego (puntaje, racha, vidas, comodín, preguntas sin repetir, niveles y títulos).

## Estructura del proyecto

```
preguntados-python/
├── main.py            # Interfaz gráfica (Tkinter): ventana, ruleta animada, temporizador
├── logica.py          # Reglas del juego (puntos, vidas, niveles), sin nada de interfaz
├── preguntas.json     # Banco de preguntas (se puede editar sin tocar el código)
├── test_logica.py     # Pruebas unitarias de la lógica
├── evidencia/
│   └── prompts.md     # Prompts usados con la IA, iteraciones y reflexión
└── README.md
```

La lógica está separada de la interfaz a propósito: así se puede probar sin abrir ventanas y es más fácil de entender y modificar.

## Agregar preguntas

Añade un objeto al arreglo de `preguntas.json`. El campo `correcta` es la posición (0 a 3) de la respuesta correcta dentro de `opciones`:

```json
{
  "categoria": "Ciencia",
  "dificultad": "media",
  "pregunta": "¿Cuál es el símbolo químico del oro?",
  "opciones": ["Ag", "Go", "Au", "Or"],
  "correcta": 2,
  "explicacion": "Viene del latín aurum."
}
```

Dificultades válidas: `fácil`, `media`, `difícil`. Si el archivo tiene un error, el juego muestra un mensaje indicando qué pregunta falló en lugar de cerrarse sin explicación.

## Evidencia de vibecoding

Los prompts, las mejoras pedidas a la IA, la validación y la reflexión final están en [`evidencia/prompts.md`](evidencia/prompts.md).
