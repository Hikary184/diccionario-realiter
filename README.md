# REALITER · Diccionario parlante español–rumano con YAML

Prototipo académico para demostrar un diccionario bilingüe que **lee y escribe entradas en YAML**, busca palabras y reproduce grabaciones. Contiene **12 palabras y 48 archivos WAV sintetizados** (palabra y ejemplo en español y rumano).

## 1 · Requisitos

- Computadora con Python **3.10 o superior** (Windows, macOS o Linux).
- Conexión a internet solamente para instalar PyYAML la primera vez.
- Navegador actualizado (Chrome, Edge o Firefox).

## 2 · Cómo iniciarlo (Windows, Visual Studio Code)

1. Descomprime el archivo ZIP y abre la carpeta `realiter_diccionario_yaml` en Visual Studio Code.
2. Abre **Terminal > Nuevo terminal**.
3. Instala el único paquete:

   ```powershell
   py -m pip install -r requirements.txt
   ```

4. Inicia el programa:

   ```powershell
   py app.py
   ```

5. Abre en tu navegador: **http://127.0.0.1:8000**.

También puedes hacer doble clic en `iniciar_windows.bat` si tienes instalado Python y PyYAML.

**macOS/Linux**: `python3 -m pip install -r requirements.txt` y `python3 app.py`.

## 3 · Taller en 6 momentos

| Momento | Práctica | Aprendizaje |
|---|---|---|
| 1 | Buscar `casa` o `casă` | Consultar el mismo recurso desde ambos idiomas |
| 2 | Escuchar palabras y oraciones | Vincular una entrada lexicográfica con audio |
| 3 | Abrir «Laboratorio YAML» | Comprender mapas, listas, claves y valores |
| 4 | Cambiar una definición desde YAML | Relación entre archivo de datos y pantalla |
| 5 | Agregar `ventana ↔ fereastră` | Generación de una nueva entrada estructurada |
| 6 | Añadir otro ejemplo a una palabra | Modelar relaciones uno-a-muchos con listas YAML |

## 4 · Ejemplo de entrada YAML

```yaml
palabras:
  - id: ventana001
    es: ventana
    ro: fereastră
    significado: Abertura en una pared que permite la entrada de luz y aire.
    audio_es: ""
    audio_ro: ""
    ejemplos:
      - es: Abro la ventana cada mañana.
        ro: Deschid fereastra în fiecare dimineață.
        audio_es: ""
        audio_ro: ""
```

- `palabras:` es una **lista**.
- `-` inicia una nueva entrada o ejemplo.
- `es`, `ro`, `significado` son **claves** y sus correspondientes textos son **valores**.
- `ejemplos:` es otra lista, anidada dentro de una entrada.
- `audio_es` y `audio_ro` guardan el nombre del archivo dentro de `storage/audio/`.
- El campo `id` identifica una entrada y debe ser único.

## 5 · Dónde se guardan los cambios

Al primer arranque se crea la carpeta `storage/`:

```text
realiter_diccionario_yaml/
├── app.py
├── requirements.txt
├── seed/
│   ├── diccionario.yaml     # 12 entradas iniciales
│   └── audio/               # 48 WAV de muestra
├── static/
│   ├── index.html
│   ├── style.css
│   └── app.js
└── storage/                 # Se crea al iniciar
    ├── diccionario.yaml     # Archivo editable REAL
    └── audio/               # Audios iniciales y subidos
```

`seed/` es solamente la plantilla original. **No debes modificarla para registrar nuevas palabras**: todos los cambios se almacenan en `storage/diccionario.yaml`. Para restaurar la demostración, detén el programa y elimina o renombra `storage/`, y vuelve a iniciar. Para conservar tus avances, haz copia de seguridad de `storage/`.

## 6 · Grabaciones

Las 48 grabaciones que vienen con el proyecto se crearon con un sintetizador de voz: son **demostrativas y no grabaciones humanas**. En las entradas nuevas puedes subir grabaciones propias desde los formularios. Para cambiar el audio de una palabra ya registrada, agrega el archivo a `storage/audio/` con un nombre hexadecimal de 32 caracteres seguido de su extensión compatible, y modifica la referencia correspondiente en `storage/diccionario.yaml`. Los audios que faltan se intentan reproducir mediante la síntesis de voz del navegador; el rumano puede no estar disponible en todos los equipos. Los formatos aceptados para archivos nuevos son WAV, MP3, OGG, M4A y WEBM (hasta 2 MB por archivo).

## 7 · Publicación en internet (opcional)

Este servidor es una **herramienta didáctica**, no un sistema endurecido para producción. Para exhibirlo en línea:

1. Crea un repositorio de GitHub con estos archivos, **sin subir la carpeta `storage/`** (excluida en `.gitignore`).
2. En [Render](https://render.com/), crea un *Web Service* desde el repositorio.
3. Comando de instalación: `pip install -r requirements.txt`.
4. Comando de inicio: `python app.py`.
5. Establece `EDIT_PASSWORD` como una clave fuerte y secreta en las variables de entorno del servicio. Nunca la incluyas en GitHub. Render proporciona el puerto mediante `PORT`; el programa lo utilizará automáticamente.
6. **Importante:** Render utiliza almacenamiento efímero en servicios gratuitos. Los cambios en YAML y los audios nuevos pueden perderse al reiniciar, suspender o republicar el servicio. Si necesitas conservar las entradas online, configura un disco persistente en un plan compatible (por ejemplo, monta `/opt/render/project/src/storage`) y establece `STORAGE_DIR=/opt/render/project/src/storage`, o migra a almacenamiento externo. No anuncies el modo gratuito como almacenamiento duradero.

El prototipo usa un solo proceso y un archivo YAML, por lo que está orientado a **grupos pequeños y demostraciones**, no a edición concurrente masiva. Las contraseñas se envían únicamente cuando se guarda y la plataforma pública debe usar HTTPS.

## 8 · Archivos y opciones

| Archivo o variable | Función |
|---|---|
| `app.py` | Servidor Python y lógica para buscar, validar y guardar |
| `seed/diccionario.yaml` | Datos de muestra originales |
| `storage/diccionario.yaml` | Datos vivos después del primer arranque |
| `static/` | Interfaz web completa |
| `EDIT_PASSWORD` | Contraseña para permitir edición remota |
| `STORAGE_DIR` | Carpeta de almacenamiento persistente opcional |
| `PORT` | Puerto del servidor; por defecto 8000 |

**Nota:** las equivalencias y definiciones son demostrativas, no proceden de una revisión terminológica oficial. Deben validarse lingüísticamente antes de incorporarlas a un recurso académico definitivo.
