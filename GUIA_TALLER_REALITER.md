# Guion práctico para REALITER · 25 minutos

**Objetivo:** demostrar cómo una estructura YAML se convierte en un diccionario digital bilingüe con búsqueda, ejemplos y audio.

## Minutos 0–4 · Consulta

Abre `http://127.0.0.1:8000` y busca `casa`. Observa `casa ↔ casă`, su definición en español y la oración bilingüe. Busca también `casa` en rumano, escribiendo `casa` sin signo diacrítico; comenta la normalización de búsquedas. Prueba `scoala` y comprueba que coincide con `școală`.

## Minutos 4–8 · Audio

Selecciona `diccionario ↔ dicționar` y reproduce las dos palabras y sus ejemplos. Explica que los audios de esta demostración son voces sintetizadas y que el sistema también acepta grabaciones nuevas. **No confundir voz sintética con documentación oral de hablantes nativos.**

## Minutos 8–13 · Lectura de YAML

En «Laboratorio YAML», identifica la estructura:

```yaml
palabras:                 # Lista general
  - id: ventana001        # Identificador único
    es: ventana            # Lema español
    ro: fereastră          # Equivalente rumano
    significado: Abertura en una pared que deja entrar luz y aire.
    audio_es: ""           # Nombre de audio español; opcional
    audio_ro: ""           # Nombre de audio rumano; opcional
    ejemplos:              # Lista anidada de ejemplos
      - es: Abro la ventana cada mañana.
        ro: Deschid fereastra în fiecare dimineață.
        audio_es: ""
        audio_ro: ""
```

**Preguntas para el público:** ¿qué marca el inicio de cada entrada? ¿Por qué importa la sangría? ¿Cómo representamos dos ejemplos para una sola palabra?

## Minutos 13–18 · Edición YAML

Elige una palabra existente y cambia únicamente su `significado`. Selecciona «Guardar cambios YAML», vuelve a la pestaña «Explorar diccionario» y verifica que la pantalla muestra la nueva información.

**Demostración de validación (opcional):** rompe deliberadamente una sangría o elimina un corchete, guarda y explica que el sistema rechaza sintaxis inválida sin sobrescribir los datos anteriores. Corrige el error.

## Minutos 18–23 · Nueva palabra

Abre «Agregar palabra» e introduce:

- **Español:** ventana
- **Rumano:** fereastră
- **Significado:** Abertura en una pared que permite la entrada de luz y aire.
- **Ejemplo ES:** Abro la ventana cada mañana.
- **Ejemplo RO:** Deschid fereastra în fiecare dimineață.

Los audios nuevos son opcionales; sin archivo se intenta utilizar la síntesis de voz del navegador. Presiona «Guardar palabra». Comprueba que `ventana ↔ fereastră` ya se puede encontrar.

## Minutos 23–25 · Nuevo ejemplo y cierre

En la ficha de `ventana`, selecciona «Agregar ejemplo»:

- **ES:** La ventana de mi habitación es grande.
- **RO:** Fereastra camerei mele este mare.

Guarda, vuelve al «Laboratorio YAML» y observa cómo la lista `ejemplos` ahora contiene dos elementos. Descarga el YAML para que los participantes lo conserven.

**Idea de cierre:** YAML facilita datos legibles y editables por personas, mientras que la web facilita búsquedas y consulta multimedia. En una aplicación de investigación más amplia habría que añadir control de versiones, revisión lingüística, roles, metadatos, protección de archivos y almacenamiento persistente.
