"""
Actividad 2: Suma Vectorial a Gran Escala
Versión 1: Monohilo / Secuencial

Este programa genera un arreglo de N números enteros aleatorios y calcula
la suma total recorriendo el arreglo una sola vez con un único hilo.

Nota: La actividad solicita N >= 10_000_000. Un arreglo de ese tamaño puede
usar bastante memoria y tardar algunos segundos en generarse, dependiendo
del equipo.
"""

import random
import time


MINIMO_N = 10_000_000
VALOR_MINIMO = 1
VALOR_MAXIMO = 100


def solicitar_tamano_arreglo():
    """Solicita al usuario un valor entero N y valida que sea al menos 10 millones."""
    while True:
        try:
            n = int(input(f"Ingrese N (mínimo {MINIMO_N:,}): ").replace(",", ""))

            if n < MINIMO_N:
                print(f"Error: N debe ser mayor o igual a {MINIMO_N:,}.\n")
                continue

            return n

        except ValueError:
            print("Error: ingrese un número entero válido.\n")


def generar_arreglo(n):
    """
    Genera una lista de longitud n con enteros aleatorios entre
    VALOR_MINIMO y VALOR_MAXIMO, incluidos ambos límites.

    La generación se mide aparte para que el tiempo de suma secuencial
    represente únicamente el recorrido y acumulación del arreglo.
    """
    return [random.randint(VALOR_MINIMO, VALOR_MAXIMO) for _ in range(n)]


def suma_secuencial(arreglo):
    """
    Recorre el arreglo de la posición 0 hasta la última posición y acumula
    todos los valores en una única variable. Esta función se ejecuta en
    el hilo principal, por lo que corresponde a la versión monohilo.
    """
    total = 0

    for valor in arreglo:
        total += valor

    return total


def main():
    """Controla la entrada, generación del arreglo, medición y reporte final."""
    print("=" * 66)
    print("ACTIVIDAD 2 - SUMA VECTORIAL A GRAN ESCALA")
    print("VERSIÓN 1: MONOHILO / SECUENCIAL")
    print("=" * 66)

    n = solicitar_tamano_arreglo()

    print(f"\nGenerando arreglo de {n:,} enteros aleatorios...")
    inicio_generacion = time.perf_counter()
    arreglo = generar_arreglo(n)
    fin_generacion = time.perf_counter()

    print("Arreglo generado. Iniciando suma secuencial...")

    # Se mide solo el cálculo solicitado: un recorrido secuencial del arreglo.
    inicio_suma = time.perf_counter()
    suma_total = suma_secuencial(arreglo)
    fin_suma = time.perf_counter()

    tiempo_generacion = fin_generacion - inicio_generacion
    tiempo_suma = fin_suma - inicio_suma
    tiempo_total = fin_suma - inicio_generacion

    print("\n" + "=" * 66)
    print("RESULTADOS - VERSIÓN MONOHILO / SECUENCIAL")
    print("=" * 66)
    print(f"Longitud del arreglo (N): {n:,}")
    print("Número de hilos usados: 1")
    print(f"Rango procesado: [0, {n - 1}]")
    print(f"Suma total del arreglo: {suma_total:,}")
    print(f"Tiempo de generación: {tiempo_generacion:.6f} segundos")
    print(f"Tiempo de suma secuencial: {tiempo_suma:.6f} segundos")
    print(f"Tiempo total (generación + suma): {tiempo_total:.6f} segundos")
    print("=" * 66)


if __name__ == "__main__":
    main()
