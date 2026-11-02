# Evidencia de vibecoding

> IA usada: Claude (Anthropic).

---

## 1. Prompts utilizados

### Prompt 1: contenido del juego (banco de preguntas)

**Qué pedí a la IA:** que actuara como diseñador de trivias y creara 6 categorías con 5 preguntas cada una (4 opciones, una correcta, dificultad variada y explicación breve), más unas reglas para jugar en grupo.

**Prompt completo:**
```
Eres un diseñador de juegos de mesa y creador de trivias con experiencia en preguntas y respuestas de cultura general al estilo del programa "Preguntados". Necesito que crees un juego completo de preguntas y respuestas listo para jugarse.

Estructura el juego en seis categorías de preguntas, con cinco preguntas por categoría: Geografía, Historia, Ciencia, Arte y Literatura, Entretenimiento y Deportes. Cada pregunta debe tener cuatro opciones de respuesta, con una sola correcta, y las opciones incorrectas deben ser plausibles pero claramente distinguibles para alguien que sepa la respuesta. Varía la dificultad entre fácil, media y difícil, y distribúyela de forma equilibrada en cada categoría.

Para cada pregunta, indica la respuesta correcta y una breve explicación de una o dos frases que sirva para aprender algo al jugar. Asegúrate de que todos los datos sean verificables y estén actualizados, y evita preguntas ambiguas o con más de una respuesta válida.

Como el juego está pensado para jugarse en grupo, incluye también una sección de reglas breve: número de jugadores, cómo se elige la categoría, cómo se puntúa (por ejemplo, más puntos por respuestas difíciles) y cómo se determina el ganador. Mantén el tono amigable y dinámico, con un lenguaje claro para todas las edades.

Entrega el resultado con títulos claros por categoría y numeración de preguntas, de modo que pueda imprimirse o usarse directamente en una partida.```

**Por qué lo planteé así / qué ajusté: Necesitaba un juego de preguntas de cultura general. Ajusté cosas como un sistema de niveles y animaciones para que el juego fuera mas dinámico. 

### Prompt 2: código del juego

**Qué pedí a la IA:** un juego completo con su código, listo para subir a GitHub, a partir de ese banco de preguntas.

**Prompt completo:**
```
Necesito el código, para poder subirlo a un repositorio en GitHub.
```

**Qué salió y qué le faltó: La IA presentó un juego de preguntas y respuestas sin ningún tipo de animación.

**Por qué refiné el siguiente prompt: El primer prompt me dio una serie de preguntas y respuestas que iban a ser el contenido del juego. El Prompt me dio el código de dicho juego 

### Prompt 3: (tu primera mejora real)

**Qué pedí a la IA:** 


Quiero que agregues al juego un sistema de "Niveles" en el que a la hora de perder te de un "titulo", además me gastaría una animación de la rueda girando


**Por qué lo refiné:** Quería un sistema de niveles que se le regresa al jugador al finalizar la sesión de juegos y además una animación giratoria de la ruleta. 

---

## 2. Iteración y mejora

La versión base ya tenía temporizador de 15 s, vidas, racha y comodín 50/50, con un botón "Girar" que solo cambiaba el nombre de la categoría. Después pedí una mejora:

| Cambio pedido | Prompt usado | Resultado |
|---|---|---|
| Sistema de niveles con título al perder, y animación de la rueda | "Quiero que agregues al juego un sistema de "Niveles" en el que a la hora de perder te de un "titulo", ademas me gustaria una animacion de la rueda girando" | Se agregó la tabla `NIVELES` en `logica.py` (el nivel se muestra siempre y al terminar recibes un título) y una rueda dibujada en un `Canvas` que gira y frena en la categoría elegida. |

**Por qué lo pedí / qué le faltó al primer resultado:** ✏️ (por ejemplo: el juego funcionaba pero se sentía plano, sin progresión ni efecto visual).

**Ajustes que hizo falta pedir después de ver el resultado:** ✏️ (si pides más cambios, anótalos aquí como nuevas filas de la tabla).

---

## 3. Validación del resultado

**Cómo probé el código:**

- Pruebas automáticas: `python -m unittest -v` (20 pruebas sobre carga del JSON, reglas del juego y niveles).
- Pruebas manuales jugando. ✏️ Anota qué probaste tú, por ejemplo:
  - Dejar que se acabe el tiempo en una pregunta.
  - Usar el comodín 50/50 y confirmar que nunca oculta la correcta.
  - Perder las 3 vidas y ver la pantalla final.
  - Jugar hasta agotar una categoría.
  - Romper a propósito `preguntas.json` (borrar una coma) y ver el mensaje de error.

**Error, limitación o ajuste que encontré:** La computadora no me reconocía python al inicio. 
---

## 4. Reflexión final

**Qué aprendí usando IA para programar:** Lo exacto que hay que ser en los prompts ya que al pedir el juego sin ocupar la palabra "código" la IA no me dio lo que yo necesitaba.

**Ventajas y límites que identifiqué del vibecoding: 
Velocidad, no hay bloqueas al empezar. La IA tiende a hacer un programa con una interfaz simple. 

**Qué partes del código comprendo y cuáles necesito reforzar:** Considero que comprendo gran parte del código pero necesito reforzar la idea de hacer animaciones en las aplicaciones. 