# paralelismo_tareas.py
#
# PARALELISMO DE TAREAS:
# - F1 ejecuta únicamente T1: palabra más frecuente.
# - F2 ejecuta únicamente T2: fecha con más mensajes.
# - F3 ejecuta únicamente T3: día de la semana con más conversación.
# - Las tres funciones reciben y analizan el 100% de los mensajes.
# - Cada tarea se ejecuta en un proceso diferente.

import re
import time
import unicodedata
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from datetime import datetime
from pathlib import Path


# Nombre exacto del archivo exportado desde WhatsApp.
ARCHIVO_CHAT = "ChatFacultad.txt"


# Palabras frecuentes sin valor informativo que no se contarán en T1.
PALABRAS_VACIAS = {
    "a", "al", "algo", "ante", "bajo", "con", "de", "del",
    "desde", "e", "el", "ella", "ellos", "en", "entre",
    "era", "es", "esa", "ese", "eso", "esta", "este", "esto", "fue",
    "ha", "han", "hasta", "hay", "la", "las", "le", "les", "lo", "los",
    "me", "mi", "mis", "muy", "no", "nos", "o", "para", "pero",
    "por", "porque", "que", "se", "si", "sin", "su", "sus", "te", "tu",
    "tus", "un", "una", "uno", "unos", "unas", "u", "y", "ya", "yo",
    "cómo", "como", "sí", "también", "tambien", "vale", "jaja",
    "jajaja", "jajaja", "jajajaja", "más", "mensaje"
}


def leer_chat(nombre_archivo):
    """
    Lee el archivo .txt exportado desde WhatsApp.

    Primero intenta codificación UTF-8 con BOM; si el archivo tiene otra
    codificación, se usa Latin-1 como respaldo.
    """
    ruta = Path(nombre_archivo)

    if not ruta.exists():
        raise FileNotFoundError(
            f"\nNo se encontró el archivo '{nombre_archivo}'.\n"
            "Ubica el archivo .txt en la misma carpeta del programa "
            "o modifica la variable ARCHIVO_CHAT."
        )

    try:
        with open(ruta, "r", encoding="utf-8-sig") as archivo:
            return archivo.readlines()

    except UnicodeDecodeError:
        with open(ruta, "r", encoding="latin-1") as archivo:
            return archivo.readlines()


def limpiar_caracteres_invisibles(texto):
    """
    Elimina marcas de dirección y espacios especiales que WhatsApp usa
    internamente en algunos nombres, números telefónicos y horas.

    Por ejemplo:
    - U+200E: marca izquierda-a-derecha.
    - U+202F: espacio estrecho no separable.
    - U+2066/U+2069: marcas de aislamiento Unicode.
    """
    texto = texto.replace("\u202f", " ")
    texto = texto.replace("\u00a0", " ")

    resultado = []

    for caracter in texto:
        categoria = unicodedata.category(caracter)

        # Cf = Formato Unicode; Cc = Control Unicode.
        if categoria not in ("Cf", "Cc"):
            resultado.append(caracter)

    return "".join(resultado)


def normalizar_hora_whatsapp(hora, periodo):
    """
    Normaliza las variantes de AM/PM usadas por WhatsApp.

    Ejemplos:
    - 4:47 + p. m.  -> 4:47 PM
    - 4:47 + p.m.   -> 4:47 PM
    - 4:47 + PM     -> 4:47 PM
    - 4:47 sin AM/PM -> 4:47
    """
    periodo = periodo.strip().lower()

    if periodo:
        periodo = re.sub(r"a\s*\.\s*m\s*\.", "AM", periodo)
        periodo = re.sub(r"p\s*\.\s*m\s*\.", "PM", periodo)
        periodo = re.sub(r"a\s*m", "AM", periodo)
        periodo = re.sub(r"p\s*m", "PM", periodo)
        periodo = periodo.upper()

        return f"{hora} {periodo}"

    return hora


def convertir_fecha(fecha_texto):
    """
    Convierte las fechas del chat a objetos datetime.

    El archivo ChatM.txt usa día/mes/año:
    13/8/2026 -> 13 de agosto de 2026
    """
    formatos = [
        "%d/%m/%Y",
        "%d/%m/%y",
        "%d-%m-%Y",
        "%d-%m-%y"
    ]

    for formato in formatos:
        try:
            return datetime.strptime(fecha_texto, formato)
        except ValueError:
            continue

    return None


def extraer_mensajes(lineas):
    """
    Convierte el chat exportado a una lista de mensajes de usuarios.

    Formato identificado en chat:
    13/8/2026, 4:54 p. m. - +57 302 4518546: ENCUESTA:
    13/8/2026, 5:02 p. m. - @dancmo: <Multimedia omitido>

    No cuenta eventos del sistema, por ejemplo:
    13/8/2026, 4:47 p. m. - Te uniste mediante el enlace...
    """
    patron_inicio = re.compile(
        r"^"
        r"(?P<fecha>\d{1,2}[/-]\d{1,2}[/-]\d{2,4})"
        r",\s*"
        r"(?P<hora>\d{1,2}:\d{2})"
        r"\s*"
        r"(?P<periodo>(?:a|p)\.?\s*m\.?|AM|PM)?"
        r"\s*-\s*"
        r"(?P<contenido>.*)$",
        re.IGNORECASE
    )

    mensajes = []
    mensaje_actual = None

    for linea in lineas:
        linea = limpiar_caracteres_invisibles(linea.rstrip("\n"))
        coincidencia = patron_inicio.match(linea)

        if coincidencia:
            fecha_texto = coincidencia.group("fecha")
            hora = coincidencia.group("hora")
            periodo = coincidencia.group("periodo") or ""
            contenido = coincidencia.group("contenido").strip()

            # Un mensaje de usuario tiene esta estructura:
            # remitente: contenido del mensaje
            if ":" in contenido:
                remitente, texto = contenido.split(":", 1)

                mensaje_actual = {
                    "fecha_texto": fecha_texto,
                    "hora": normalizar_hora_whatsapp(hora, periodo),
                    "remitente": remitente.strip(),
                    "texto": texto.strip()
                }

                mensajes.append(mensaje_actual)

            else:
                # Es un evento del sistema; no se guarda ni se cuenta.
                mensaje_actual = None

        elif mensaje_actual is not None:
            # Une el contenido de mensajes que ocupan varias líneas:
            # encuestas, mensajes extensos, etc.
            texto_continuacion = linea.strip()

            if texto_continuacion:
                mensaje_actual["texto"] += " " + texto_continuacion

    return mensajes


def es_mensaje_multimedia(texto):
    """
    Determina si el contenido corresponde a texto automático de multimedia.
    Estos mensajes no aportan palabras para T1.
    """
    texto = texto.lower().strip()

    mensajes_no_textuales = {
        "<multimedia omitido>",
        "multimedia omitido",
        "<imagen omitida>",
        "<video omitido>",
        "<audio omitido>",
        "<sticker omitido>",
        "<documento omitido>",
        "<Se editó este mensaje.>", # No cuenta la etiqueta de mensaje editado
        "Se eliminó este mensaje."
    }

    return texto in mensajes_no_textuales


def limpiar_palabras(texto):
    """
    Extrae palabras relevantes de un mensaje para T1.

    Elimina enlaces, menciones, números, signos, palabras cortas
    y palabras vacías.
    """
    if es_mensaje_multimedia(texto):
        return []

    texto = texto.lower()

    # Elimina enlaces, por ejemplo links de Microsoft Teams.
    texto = re.sub(r"https?://\S+|www\.\S+", " ", texto)

    # Elimina menciones de usuarios como @david.osp.
    texto = re.sub(r"@\S+", " ", texto)

    # Encuentra palabras en español, incluyendo tildes, ü y ñ.
    palabras = re.findall(r"[a-záéíóúüñ]+", texto)

    return [
        palabra
        for palabra in palabras
        if len(palabra) >= 3 and palabra not in PALABRAS_VACIAS
    ]


# ================================================================
# FUNCIONES PARALELAS
# Cada función recibe y procesa el 100% de los mensajes.
# ================================================================

def F1_palabra_mas_frecuente(mensajes):
    """
    T1:
    Encuentra la palabra más frecuente en el 100% de los mensajes.
    """
    contador = Counter()

    for mensaje in mensajes:
        palabras = limpiar_palabras(mensaje["texto"])
        contador.update(palabras)

    if not contador:
        return None, 0

    palabra, cantidad = contador.most_common(1)[0]
    return palabra, cantidad


def F2_fecha_mayor_conversacion(mensajes):
    """
    T2:
    Encuentra la fecha que tuvo la mayor cantidad de mensajes
    considerando el 100% del chat.
    """
    contador_fechas = Counter()

    for mensaje in mensajes:
        fecha = convertir_fecha(mensaje["fecha_texto"])

        if fecha is not None:
            fecha_normalizada = fecha.strftime("%d/%m/%Y")
            contador_fechas[fecha_normalizada] += 1

    if not contador_fechas:
        return None, 0

    fecha, cantidad = contador_fechas.most_common(1)[0]
    return fecha, cantidad


def F3_dia_semana_mas_conversacion(mensajes):
    """
    T3:
    Encuentra el día de la semana con la mayor cantidad de mensajes
    considerando el 100% del chat.
    """
    nombres_dias = [
        "Lunes",
        "Martes",
        "Miércoles",
        "Jueves",
        "Viernes",
        "Sábado",
        "Domingo"
    ]

    contador_dias = Counter()

    for mensaje in mensajes:
        fecha = convertir_fecha(mensaje["fecha_texto"])

        if fecha is not None:
            dia = nombres_dias[fecha.weekday()]
            contador_dias[dia] += 1

    if not contador_dias:
        return None, 0

    dia, cantidad = contador_dias.most_common(1)[0]
    return dia, cantidad


def main():
    print("=" * 72)
    print("ANÁLISIS DE CHAT DE WHATSAPP - PARALELISMO DE TAREAS")
    print("=" * 72)

    try:
        lineas = leer_chat(ARCHIVO_CHAT)

    except FileNotFoundError as error:
        print(error)
        return

    mensajes = extraer_mensajes(lineas)

    if not mensajes:
        print("\nNo se encontraron mensajes válidos en el archivo.")
        print("Verifica que el nombre del archivo sea correcto.")
        return

    print(f"\nArchivo analizado: {ARCHIVO_CHAT}")
    print(f"Mensajes de usuarios detectados: {len(mensajes)}")

    print("\nDistribución de tareas:")
    print("F1 ejecuta T1 sobre el 100% del chat.")
    print("F2 ejecuta T2 sobre el 100% del chat.")
    print("F3 ejecuta T3 sobre el 100% del chat.")

    # El cronómetro se inicia inmediatamente antes de crear los procesos.
    inicio = time.perf_counter()

    # Tres procesos en paralelo; cada proceso ejecuta una operación distinta.
    with ProcessPoolExecutor(max_workers=3) as executor:
        futuro_f1 = executor.submit(F1_palabra_mas_frecuente, mensajes)
        futuro_f2 = executor.submit(F2_fecha_mayor_conversacion, mensajes)
        futuro_f3 = executor.submit(F3_dia_semana_mas_conversacion, mensajes)

        palabra, cantidad_palabra = futuro_f1.result()
        fecha, cantidad_fecha = futuro_f2.result()
        dia, cantidad_dia = futuro_f3.result()

    fin = time.perf_counter()
    tiempo_total = fin - inicio

    print("\n" + "=" * 72)
    print("RESULTADOS GLOBALES DEL CHAT")
    print("=" * 72)

    if palabra:
        print(
            f"\nT1 - Palabra más frecuente: "
            f"'{palabra}' ({cantidad_palabra} veces)"
        )
    else:
        print("\nT1 - No se encontraron palabras válidas.")

    if fecha:
        print(
            f"T2 - Fecha con mayor conversación: "
            f"{fecha} ({cantidad_fecha} mensajes)"
        )
    else:
        print("T2 - No se encontraron fechas válidas.")

    if dia:
        print(
            f"T3 - Día de la semana con mayor conversación: "
            f"{dia} ({cantidad_dia} mensajes)"
        )
    else:
        print("T3 - No se encontraron días válidos.")

    print("\n" + "-" * 72)
    print(f"Tiempo total de ejecución: {tiempo_total:.6f} segundos")
    print("-" * 72)

    print("\nConclusión:")
    print(
        "F1, F2 y F3 se ejecutaron simultáneamente. Cada función tuvo "
        "acceso al 100% de los mensajes, pero realizó exclusivamente "
        "la tarea que le fue asignada."
    )


if __name__ == "__main__":
    main()