# paralelismo_datos.py
#
# PARALELISMO DE DATOS:
# - El chat se divide en 3 segmentos.
# - F1 realiza T1 en los tres segmentos.
# - F2 realiza T2 en los tres segmentos.
# - F3 realiza T3 en los tres segmentos.
# - Se combinan los resultados parciales para obtener resultados globales.

import re
import time
import unicodedata
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from datetime import datetime
from pathlib import Path


# Nombre del archivo exportado desde WhatsApp.
ARCHIVO_CHAT = "ChatFacultad.txt"

# Número de segmentos de datos.
NUMERO_SEGMENTOS = 3

# Palabras que se excluyen para obtener una palabra más significativa.
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
    Lee el archivo de texto exportado desde WhatsApp.
    Primero intenta UTF-8 y, si falla, prueba Latin-1.
    """
    ruta = Path(nombre_archivo)

    if not ruta.exists():
        raise FileNotFoundError(
            f"\nNo se encontró el archivo: {nombre_archivo}\n"
            "Verifica que el .txt esté en la misma carpeta del programa."
        )

    try:
        with open(ruta, "r", encoding="utf-8-sig") as archivo:
            return archivo.readlines()

    except UnicodeDecodeError:
        with open(ruta, "r", encoding="latin-1") as archivo:
            return archivo.readlines()


def limpiar_caracteres_invisibles(texto):
    """
    WhatsApp puede exportar espacios especiales e indicadores Unicode invisibles:
    U+200E, U+200F, U+202A, U+202C, U+2066, U+2069, etc.

    Esta función los elimina y reemplaza espacios especiales por espacios comunes.
    """
    texto = texto.replace("\u202f", " ")
    texto = texto.replace("\u00a0", " ")

    caracteres_limpios = []

    for caracter in texto:
        categoria = unicodedata.category(caracter)

        # Se eliminan caracteres Unicode de control y de formato.
        if categoria not in ("Cf", "Cc"):
            caracteres_limpios.append(caracter)

    return "".join(caracteres_limpios)


def normalizar_hora_whatsapp(texto):
    """
    Convierte las variantes de hora de WhatsApp al formato AM o PM.

    Ejemplos:
    '4:47 p. m.' -> '4:47 PM'
    '4:47 p.m.'  -> '4:47 PM'
    '4:47 PM'    -> '4:47 PM'
    """
    texto = texto.strip().lower()

    texto = re.sub(r"a\s*\.\s*m\s*\.", "AM", texto)
    texto = re.sub(r"p\s*\.\s*m\s*\.", "PM", texto)
    texto = re.sub(r"a\s*m", "AM", texto)
    texto = re.sub(r"p\s*m", "PM", texto)

    texto = texto.upper()
    texto = re.sub(r"\s+", " ", texto).strip()

    return texto


def convertir_fecha(fecha_texto):
    """
    Convierte fechas del formato colombiano de WhatsApp.

    Ejemplos válidos:
    13/8/2026
    01/01/2026
    13-8-2026

    Se asume día/mes/año, como corresponde a tu archivo ChatM.txt.
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


def es_inicio_mensaje(linea):
    """
    Identifica si una línea inicia un mensaje o evento de WhatsApp.

    Ejemplo detectado:
    13/8/2026, 4:54 p. m. - +57 302 4518546: Hola
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

    return patron_inicio.match(linea)


def extraer_mensajes(lineas):
    """
    Extrae los mensajes reales enviados por participantes.

    Ignora:
    - Mensajes de sistema.
    - Entradas sin el formato 'Remitente: contenido'.
    - Eventos como creación del grupo, participantes que se unen,
      cambios de configuración o cifrado.

    Conserva y une mensajes de varias líneas.
    """
    mensajes = []
    mensaje_actual = None

    for linea in lineas:
        linea = limpiar_caracteres_invisibles(linea.rstrip("\n"))
        coincidencia = es_inicio_mensaje(linea)

        if coincidencia:
            fecha_texto = coincidencia.group("fecha")
            hora_texto = coincidencia.group("hora")
            periodo = coincidencia.group("periodo") or ""
            contenido = coincidencia.group("contenido").strip()

            hora_normalizada = normalizar_hora_whatsapp(
                f"{hora_texto} {periodo}"
            )

            # Un mensaje de usuario tiene un separador ":"
            # Ejemplo: "+57 302 4518546: Hola".
            if ":" in contenido:
                remitente, texto = contenido.split(":", 1)

                remitente = remitente.strip()
                texto = texto.strip()

                mensaje_actual = {
                    "fecha_texto": fecha_texto,
                    "hora": hora_normalizada,
                    "remitente": remitente,
                    "texto": texto
                }

                mensajes.append(mensaje_actual)

            else:
                # Es un evento del sistema: no se cuenta como mensaje de usuario.
                mensaje_actual = None

        elif mensaje_actual is not None:
            # Si la línea no comienza con fecha, es continuación del último mensaje.
            texto_continuacion = linea.strip()

            if texto_continuacion:
                mensaje_actual["texto"] += " " + texto_continuacion

    return mensajes


def es_mensaje_multimedia(texto):
    """
    Identifica textos automáticos de WhatsApp asociados a contenido no incluido.
    """
    texto = texto.lower().strip()

    valores_no_textuales = {
        "<multimedia omitido>",
        "multimedia omitido",
        "<imagen omitida>",
        "<video omitido>",
        "<audio omitido>",
        "<sticker omitido>",
        "<documento omitido>",
        "<Se editó este mensaje.>", # No cuenta la etiqueta de mensaje editado
        "Se eliminó este mensaje." # Indicacion de mensaje eliminado
    }

    return texto in valores_no_textuales


def limpiar_palabras(texto):
    """
    Convierte un texto en una lista de palabras útiles para T1.

    Se excluyen:
    - Enlaces.
    - Números.
    - Etiquetas de usuarios.
    - Palabras de menos de tres letras.
    - Palabras vacías.
    - Mensajes multimedia omitidos.
    """
    if es_mensaje_multimedia(texto):
        return []

    texto = texto.lower()

    # Elimina enlaces como https://teams.microsoft.com/...
    texto = re.sub(r"https?://\S+|www\.\S+", " ", texto)

    # Elimina menciones que empiezan por @.
    texto = re.sub(r"@\S+", " ", texto)

    # Conserva palabras en español, incluidos acentos y ñ.
    palabras = re.findall(r"[a-záéíóúüñ]+", texto)

    return [
        palabra
        for palabra in palabras
        if len(palabra) >= 3 and palabra not in PALABRAS_VACIAS
    ]


def dividir_segmentos(datos, cantidad_segmentos=3):
    """
    Divide los datos en segmentos de tamaño equilibrado.

    Si hay 100 mensajes:
    - Segmento 1: 34 mensajes
    - Segmento 2: 33 mensajes
    - Segmento 3: 33 mensajes
    """
    segmentos = []
    total = len(datos)
    tamanio_base = total // cantidad_segmentos
    residuo = total % cantidad_segmentos

    inicio = 0

    for indice in range(cantidad_segmentos):
        tamanio = tamanio_base + (1 if indice < residuo else 0)
        fin = inicio + tamanio

        segmentos.append(datos[inicio:fin])
        inicio = fin

    return segmentos


# -------------------------------------------------------------------
# F1, F2 y F3:
# Cada función aplica UNA tarea a TODOS los segmentos.
# -------------------------------------------------------------------

def F1_palabra_mas_frecuente(segmentos):
    """
    T1: Busca la palabra más frecuente.

    Esta función analiza los tres segmentos, genera un contador por segmento
    y combina los contadores para obtener la palabra más frecuente global.
    """
    contador_global = Counter()
    resultados_por_segmento = []

    for numero, segmento in enumerate(segmentos, start=1):
        contador_segmento = Counter()

        for mensaje in segmento:
            contador_segmento.update(limpiar_palabras(mensaje["texto"]))

        contador_global.update(contador_segmento)

        if contador_segmento:
            palabra, cantidad = contador_segmento.most_common(1)[0]

            resultados_por_segmento.append({
                "segmento": numero,
                "palabra": palabra,
                "cantidad": cantidad
            })
        else:
            resultados_por_segmento.append({
                "segmento": numero,
                "palabra": None,
                "cantidad": 0
            })

    if not contador_global:
        return {
            "palabra_global": None,
            "cantidad_global": 0,
            "por_segmento": resultados_por_segmento
        }

    palabra_global, cantidad_global = contador_global.most_common(1)[0]

    return {
        "palabra_global": palabra_global,
        "cantidad_global": cantidad_global,
        "por_segmento": resultados_por_segmento
    }


def F2_fecha_mayor_conversacion(segmentos):
    """
    T2: Busca la fecha con más mensajes.

    Analiza los tres segmentos, cuenta las fechas en cada segmento,
    combina los conteos y obtiene la fecha con mayor conversación global.
    """
    contador_global = Counter()
    resultados_por_segmento = []

    for numero, segmento in enumerate(segmentos, start=1):
        contador_segmento = Counter()

        for mensaje in segmento:
            fecha = convertir_fecha(mensaje["fecha_texto"])

            if fecha is not None:
                fecha_normalizada = fecha.strftime("%d/%m/%Y")
                contador_segmento[fecha_normalizada] += 1

        contador_global.update(contador_segmento)

        if contador_segmento:
            fecha, cantidad = contador_segmento.most_common(1)[0]

            resultados_por_segmento.append({
                "segmento": numero,
                "fecha": fecha,
                "cantidad": cantidad
            })
        else:
            resultados_por_segmento.append({
                "segmento": numero,
                "fecha": None,
                "cantidad": 0
            })

    if not contador_global:
        return {
            "fecha_global": None,
            "cantidad_global": 0,
            "por_segmento": resultados_por_segmento
        }

    fecha_global, cantidad_global = contador_global.most_common(1)[0]

    return {
        "fecha_global": fecha_global,
        "cantidad_global": cantidad_global,
        "por_segmento": resultados_por_segmento
    }


def F3_dia_semana_mas_conversacion(segmentos):
    """
    T3: Busca el día de la semana con más mensajes.

    Analiza los tres segmentos, cuenta los días de la semana en cada uno,
    combina los resultados y obtiene el día más conversado globalmente.
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

    contador_global = Counter()
    resultados_por_segmento = []

    for numero, segmento in enumerate(segmentos, start=1):
        contador_segmento = Counter()

        for mensaje in segmento:
            fecha = convertir_fecha(mensaje["fecha_texto"])

            if fecha is not None:
                dia = nombres_dias[fecha.weekday()]
                contador_segmento[dia] += 1

        contador_global.update(contador_segmento)

        if contador_segmento:
            dia, cantidad = contador_segmento.most_common(1)[0]

            resultados_por_segmento.append({
                "segmento": numero,
                "dia": dia,
                "cantidad": cantidad
            })
        else:
            resultados_por_segmento.append({
                "segmento": numero,
                "dia": None,
                "cantidad": 0
            })

    if not contador_global:
        return {
            "dia_global": None,
            "cantidad_global": 0,
            "por_segmento": resultados_por_segmento
        }

    dia_global, cantidad_global = contador_global.most_common(1)[0]

    return {
        "dia_global": dia_global,
        "cantidad_global": cantidad_global,
        "por_segmento": resultados_por_segmento
    }


def mostrar_resultados_segmentos(resultado_f1, resultado_f2, resultado_f3):
    """
    Muestra los resultados parciales de cada segmento.
    Esto demuestra que F1, F2 y F3 recorrieron los tres segmentos.
    """
    print("\n" + "=" * 72)
    print("RESULTADOS PARCIALES POR SEGMENTO")
    print("=" * 72)

    for indice in range(NUMERO_SEGMENTOS):
        dato_f1 = resultado_f1["por_segmento"][indice]
        dato_f2 = resultado_f2["por_segmento"][indice]
        dato_f3 = resultado_f3["por_segmento"][indice]

        print(f"\nSEGMENTO {indice + 1}")

        if dato_f1["palabra"]:
            print(
                f"  F1 / T1 - Palabra más frecuente: "
                f"'{dato_f1['palabra']}' ({dato_f1['cantidad']} veces)"
            )
        else:
            print("  F1 / T1 - Sin palabras válidas.")

        if dato_f2["fecha"]:
            print(
                f"  F2 / T2 - Fecha con más mensajes: "
                f"{dato_f2['fecha']} ({dato_f2['cantidad']} mensajes)"
            )
        else:
            print("  F2 / T2 - Sin fechas válidas.")

        if dato_f3["dia"]:
            print(
                f"  F3 / T3 - Día con más conversación: "
                f"{dato_f3['dia']} ({dato_f3['cantidad']} mensajes)"
            )
        else:
            print("  F3 / T3 - Sin días válidos.")


def main():
    print("=" * 72)
    print("ANÁLISIS DE CHAT DE WHATSAPP - PARALELISMO DE DATOS")
    print("=" * 72)

    try:
        lineas = leer_chat(ARCHIVO_CHAT)

    except FileNotFoundError as error:
        print(error)
        return

    mensajes = extraer_mensajes(lineas)

    if not mensajes:
        print("\nNo se encontraron mensajes de usuarios con formato válido.")
        print("Verifica el nombre del archivo y el formato del chat.")
        return

    segmentos = dividir_segmentos(mensajes, NUMERO_SEGMENTOS)

    print(f"\nArchivo analizado: {ARCHIVO_CHAT}")
    print(f"Mensajes de usuarios encontrados: {len(mensajes)}")
    print(f"Cantidad de segmentos: {NUMERO_SEGMENTOS}")

    for posicion, segmento in enumerate(segmentos, start=1):
        print(f"Segmento {posicion}: {len(segmento)} mensajes")

    print("\nDistribución del trabajo:")
    print("F1 ejecuta T1 en los segmentos 1, 2 y 3.")
    print("F2 ejecuta T2 en los segmentos 1, 2 y 3.")
    print("F3 ejecuta T3 en los segmentos 1, 2 y 3.")

    inicio = time.perf_counter()

    # Se crean tres procesos:
    # Proceso 1: F1 ejecuta T1 sobre TODOS los segmentos.
    # Proceso 2: F2 ejecuta T2 sobre TODOS los segmentos.
    # Proceso 3: F3 ejecuta T3 sobre TODOS los segmentos.
    with ProcessPoolExecutor(max_workers=3) as executor:
        futuro_f1 = executor.submit(F1_palabra_mas_frecuente, segmentos)
        futuro_f2 = executor.submit(F2_fecha_mayor_conversacion, segmentos)
        futuro_f3 = executor.submit(F3_dia_semana_mas_conversacion, segmentos)

        resultado_f1 = futuro_f1.result()
        resultado_f2 = futuro_f2.result()
        resultado_f3 = futuro_f3.result()

    fin = time.perf_counter()
    tiempo_total = fin - inicio

    mostrar_resultados_segmentos(resultado_f1, resultado_f2, resultado_f3)

    print("\n" + "=" * 72)
    print("RESULTADOS GLOBALES DEL CHAT")
    print("=" * 72)

    if resultado_f1["palabra_global"]:
        print(
            f"\nT1 - Palabra más frecuente: "
            f"'{resultado_f1['palabra_global']}' "
            f"({resultado_f1['cantidad_global']} veces)"
        )
    else:
        print("\nT1 - No se encontraron palabras válidas.")

    if resultado_f2["fecha_global"]:
        print(
            f"T2 - Fecha con mayor conversación: "
            f"{resultado_f2['fecha_global']} "
            f"({resultado_f2['cantidad_global']} mensajes)"
        )
    else:
        print("T2 - No se encontraron fechas válidas.")

    if resultado_f3["dia_global"]:
        print(
            f"T3 - Día de la semana con mayor conversación: "
            f"{resultado_f3['dia_global']} "
            f"({resultado_f3['cantidad_global']} mensajes)"
        )
    else:
        print("T3 - No se encontraron días válidos.")

    print("\n" + "-" * 72)
    print(f"Tiempo total de ejecución: {tiempo_total:.6f} segundos")
    print("-" * 72)

    print("\nConclusión:")
    print(
        "Los datos se dividen en tres segmentos. Cada función procesa "
        "los tres segmentos para su tarea asignada y, posteriormente, "
        "se combinan los resultados parciales para calcular el resultado global."
    )


if __name__ == "__main__":
    main()