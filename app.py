"""Diccionario español–rumano para un taller de YAML (servidor educativo)."""
from __future__ import annotations

import base64
import binascii
import hmac
import json
import mimetypes
import os
import re
import shutil
import tempfile
import threading
import unicodedata
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

import yaml

ROOT = Path(__file__).resolve().parent
STORAGE = Path(os.environ.get("STORAGE_DIR", ROOT / "storage")).resolve()
DB = STORAGE / "diccionario.yaml"
AUDIO = STORAGE / "audio"
SEED = ROOT / "seed"
STATIC = ROOT / "static"
EDIT_PASSWORD = os.environ.get("EDIT_PASSWORD", "")
LOCK = threading.RLock()
MAX_BODY = 15 * 1024 * 1024
MAX_AUDIO = 2 * 1024 * 1024
AUDIO_EXTS = {".wav", ".mp3", ".ogg", ".m4a", ".webm"}
FILE_PATTERN = re.compile(r"^[0-9a-f]{32}\.(?:wav|mp3|ogg|m4a|webm)$")
ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]{1,64}$")


class DataError(ValueError):
    pass


def text_field(value, label, limit, required=False):
    if not isinstance(value, str):
        raise DataError(f"'{label}' debe contener texto.")
    value = value.strip()
    if required and not value:
        raise DataError(f"El campo '{label}' es obligatorio.")
    if len(value) > limit:
        raise DataError(f"El campo '{label}' excede {limit} caracteres.")
    return value


def normalize_audio(value):
    if value in (None, ""):
        return ""
    if not isinstance(value, str) or not FILE_PATTERN.fullmatch(value):
        raise DataError("Nombre de audio no válido. Usa la interfaz para subir archivos.")
    return value


def validate_store(raw):
    if not isinstance(raw, dict) or not isinstance(raw.get("palabras"), list):
        raise DataError("El YAML debe contener 'palabras:' con una lista de entradas.")
    if len(raw["palabras"]) > 1000:
        raise DataError("La demostración admite como máximo 1000 entradas.")
    cleaned, used_ids = [], set()
    for i, word in enumerate(raw["palabras"], 1):
        if not isinstance(word, dict):
            raise DataError(f"La entrada {i} debe ser un mapa YAML.")
        uid = word.get("id") or uuid.uuid4().hex
        if not isinstance(uid, str) or not ID_PATTERN.fullmatch(uid) or uid in used_ids:
            raise DataError(f"ID inválido o duplicado en la entrada {i}.")
        used_ids.add(uid)
        examples = word.get("ejemplos", [])
        if not isinstance(examples, list) or len(examples) > 30:
            raise DataError(f"'ejemplos' en la entrada {i} debe ser una lista (máximo 30).")
        fixed_examples = []
        for j, ex in enumerate(examples, 1):
            if not isinstance(ex, dict):
                raise DataError(f"El ejemplo {j} de la entrada {i} no es válido.")
            fixed_examples.append({
                "es": text_field(ex.get("es", ""), "ejemplo.es", 500, True),
                "ro": text_field(ex.get("ro", ""), "ejemplo.ro", 500, True),
                "audio_es": normalize_audio(ex.get("audio_es")),
                "audio_ro": normalize_audio(ex.get("audio_ro")),
            })
        cleaned.append({
            "id": uid,
            "es": text_field(word.get("es", ""), "es", 100, True),
            "ro": text_field(word.get("ro", ""), "ro", 100, True),
            "significado": text_field(word.get("significado", ""), "significado", 700, True),
            "audio_es": normalize_audio(word.get("audio_es")),
            "audio_ro": normalize_audio(word.get("audio_ro")),
            "ejemplos": fixed_examples,
        })
    return {"palabras": cleaned}


def bootstrap():
    STORAGE.mkdir(parents=True, exist_ok=True)
    AUDIO.mkdir(parents=True, exist_ok=True)
    if not DB.exists():
        shutil.copyfile(SEED / "diccionario.yaml", DB)
    for src in (SEED / "audio").glob("*.wav"):
        target = AUDIO / src.name
        if not target.exists():
            shutil.copyfile(src, target)
    load_store()


def load_store():
    with LOCK:
        return validate_store(yaml.safe_load(DB.read_text(encoding="utf-8")))


def yaml_text(data):
    return yaml.safe_dump(data, allow_unicode=True, sort_keys=False, width=90)


def save_store(data):
    clean = validate_store(data)
    STORAGE.mkdir(parents=True, exist_ok=True)
    with LOCK:
        fd, name = tempfile.mkstemp(suffix=".tmp", prefix="diccionario_", dir=STORAGE)
        try:
            with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
                f.write("# Diccionario español–rumano · taller REALITER\n")
                f.write("# Edita las palabras y los ejemplos conservando la sangría.\n")
                f.write(yaml_text(clean))
            os.replace(name, DB)
        finally:
            if os.path.exists(name):
                os.unlink(name)
    return clean


def fold(value):
    value = unicodedata.normalize("NFKD", value.casefold())
    return "".join(c for c in value if not unicodedata.combining(c))


def check_audio_magic(blob, ext):
    return {
        ".wav": lambda b: len(b) >= 12 and b[:4] == b"RIFF" and b[8:12] == b"WAVE",
        ".mp3": lambda b: b[:3] == b"ID3" or (len(b) > 2 and b[0] == 255 and (b[1] & 224) == 224),
        ".ogg": lambda b: b[:4] == b"OggS",
        ".m4a": lambda b: len(b) >= 12 and b[4:8] == b"ftyp",
        ".webm": lambda b: b[:4] == b"\x1aE\xdf\xa3",
    }[ext](blob)


def save_audio(field):
    if not field:
        return ""
    if not isinstance(field, dict):
        raise DataError("Formato de audio no válido.")
    ext = Path(str(field.get("filename", ""))).suffix.lower()
    if ext not in AUDIO_EXTS:
        raise DataError("Formato admitido: WAV, MP3, OGG, M4A o WEBM.")
    encoded = field.get("content")
    if not isinstance(encoded, str) or len(encoded) > (MAX_AUDIO * 4 // 3 + 10):
        raise DataError("Audio demasiado grande (máximo 2 MB por archivo).")
    try:
        blob = base64.b64decode(encoded, validate=True)
    except (ValueError, binascii.Error) as e:
        raise DataError("El audio no está codificado correctamente.") from e
    if not blob or len(blob) > MAX_AUDIO or not check_audio_magic(blob, ext):
        raise DataError("Audio vacío, demasiado grande o con formato incorrecto.")
    filename = uuid.uuid4().hex + ext
    (AUDIO / filename).write_bytes(blob)
    return filename


def media_fields(src):
    return {"audio_es": save_audio(src.get("audio_es")), "audio_ro": save_audio(src.get("audio_ro"))}


def add_word(payload):
    if not isinstance(payload, dict):
        raise DataError("Debes proporcionar los datos de una palabra.")
    with LOCK:
        db = load_store()
        es = text_field(payload.get("es", ""), "es", 100, True)
        ro = text_field(payload.get("ro", ""), "ro", 100, True)
        if any(fold(x["es"]) == fold(es) and fold(x["ro"]) == fold(ro) for x in db["palabras"]):
            raise DataError("Esta combinación de palabra y traducción ya existe.")
        significado = text_field(payload.get("significado", ""), "significado", 700, True)
        ex_es = text_field(payload.get("ejemplo_es", ""), "ejemplo_es", 500, True)
        ex_ro = text_field(payload.get("ejemplo_ro", ""), "ejemplo_ro", 500, True)
        audios = media_fields(payload)
        ex_audios = media_fields({"audio_es": payload.get("ejemplo_audio_es"), "audio_ro": payload.get("ejemplo_audio_ro")})
        entry = {"id": uuid.uuid4().hex, "es": es, "ro": ro, "significado": significado,
                 **audios, "ejemplos": [{"es": ex_es, "ro": ex_ro, **ex_audios}]}
        db["palabras"].append(entry)
        save_store(db)
        return entry


def add_example(uid, payload):
    if not isinstance(payload, dict):
        raise DataError("Datos del ejemplo no válidos.")
    with LOCK:
        db = load_store()
        word = next((w for w in db["palabras"] if w["id"] == uid), None)
        if word is None:
            raise DataError("La palabra no existe.")
        if len(word["ejemplos"]) >= 30:
            raise DataError("Límite de 30 ejemplos por palabra.")
        ex = {"es": text_field(payload.get("es", ""), "ejemplo.es", 500, True),
              "ro": text_field(payload.get("ro", ""), "ejemplo.ro", 500, True), **media_fields(payload)}
        word["ejemplos"].append(ex)
        save_store(db)
        return word


class Handler(BaseHTTPRequestHandler):
    server_version = "RealiterYAML/1.0"

    def send_bytes(self, status, data, content_type="application/json; charset=utf-8", extra=None):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Referrer-Policy", "same-origin")
        if extra:
            for name, value in extra.items():
                self.send_header(name, value)
        self.end_headers()
        try:
            self.wfile.write(data)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def send_json(self, status, obj):
        self.send_bytes(status, json.dumps(obj, ensure_ascii=False).encode("utf-8"))

    def fail(self, status, msg):
        self.send_json(status, {"error": msg})

    def editable(self):
        if EDIT_PASSWORD:
            given = self.headers.get("X-Edit-Key", "")
            return hmac.compare_digest(given.encode("utf-8"), EDIT_PASSWORD.encode("utf-8"))
        return self.client_address[0] in {"127.0.0.1", "::1"}

    def get_path(self):
        parsed = urlsplit(self.path)
        return parsed.path, parse_qs(parsed.query)

    def do_GET(self):
        path, params = self.get_path()
        try:
            if path in {"/", "/index.html"}:
                return self.static_file(STATIC / "index.html")
            if path in {"/static/app.js", "/static/style.css"}:
                return self.static_file(ROOT / path.lstrip("/"))
            if path == "/api/status":
                return self.send_json(200, {"local_edit": self.editable(), "password_needed": bool(EDIT_PASSWORD)})
            if path == "/api/entries":
                db = load_store()
                query = fold(params.get("q", [""])[0][:150].strip())
                if query:
                    matches = [w for w in db["palabras"] if any(query in fold(x) for x in
                        (w["es"], w["ro"], w["significado"], *(y for e in w["ejemplos"] for y in (e["es"], e["ro"]))))]
                else:
                    matches = db["palabras"]
                return self.send_json(200, {"palabras": matches, "total": len(db["palabras"])})
            if path == "/api/yaml":
                return self.send_bytes(200, DB.read_bytes(), "text/yaml; charset=utf-8")
            if path == "/api/export":
                return self.send_bytes(200, DB.read_bytes(), "application/x-yaml; charset=utf-8",
                                       {"Content-Disposition": 'attachment; filename="diccionario_es_ro.yaml"'})
            if path.startswith("/media/"):
                filename = path[len("/media/"):]
                if not FILE_PATTERN.fullmatch(filename):
                    return self.fail(404, "Audio no encontrado.")
                audio = AUDIO / filename
                if not audio.exists():
                    return self.fail(404, "Audio no encontrado.")
                return self.send_bytes(200, audio.read_bytes(), mimetypes.guess_type(filename)[0] or "application/octet-stream")
            return self.fail(404, "Ruta no encontrada.")
        except (DataError, yaml.YAMLError) as e:
            self.fail(422, str(e))
        except OSError:
            self.fail(500, "No se pudo acceder al almacenamiento.")

    def static_file(self, path):
        if not path.exists():
            return self.fail(404, "Archivo no encontrado.")
        content_type = mimetypes.guess_type(str(path))[0] or "text/plain"
        return self.send_bytes(200, path.read_bytes(), content_type + "; charset=utf-8")

    def do_POST(self):
        self.write_request()

    def do_PUT(self):
        self.write_request()

    def write_request(self):
        path, _ = self.get_path()
        if not self.editable():
            return self.fail(403, "Edición restringida. Introduce la contraseña o utiliza localhost.")
        if self.headers.get("Content-Type", "").split(";")[0].strip().lower() != "application/json":
            return self.fail(415, "Envía los datos como application/json.")
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            return self.fail(400, "Longitud de petición inválida.")
        if not 0 < length <= MAX_BODY:
            return self.fail(413, "La petición debe tener menos de 15 MB.")
        try:
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
            if path == "/api/words" and self.command == "POST":
                return self.send_json(201, {"palabra": add_word(payload)})
            if path.startswith("/api/words/") and path.endswith("/examples") and self.command == "POST":
                uid = path[len("/api/words/"):-len("/examples")]
                if not ID_PATTERN.fullmatch(uid):
                    return self.fail(400, "Identificador inválido.")
                return self.send_json(201, {"palabra": add_example(uid, payload)})
            if path == "/api/yaml" and self.command == "PUT":
                raw_text = payload.get("yaml") if isinstance(payload, dict) else None
                if not isinstance(raw_text, str) or len(raw_text) > 600000:
                    raise DataError("El texto YAML es inválido o demasiado largo.")
                data = validate_store(yaml.safe_load(raw_text))
                saved = save_store(data)
                return self.send_json(200, {"ok": True, "total": len(saved["palabras"])})
            return self.fail(404, "Operación no encontrada.")
        except (DataError, yaml.YAMLError, UnicodeError, ValueError, json.JSONDecodeError) as e:
            self.fail(422, str(e))
        except OSError:
            self.fail(500, "No se pudieron guardar los archivos.")


def main():
    bootstrap()
    port = int(os.environ.get("PORT", "8000"))
    host = os.environ.get("HOST", "0.0.0.0" if os.environ.get("PORT") else "127.0.0.1")
    print(f"Diccionario REALITER: http://127.0.0.1:{port}", flush=True)
    if host != "127.0.0.1" and not EDIT_PASSWORD:
        print("AVISO: edición bloqueada para clientes remotos; establece EDIT_PASSWORD.", flush=True)
    ThreadingHTTPServer((host, port), Handler).serve_forever()


if __name__ == "__main__":
    main()
