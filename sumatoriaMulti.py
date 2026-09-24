import random
import time
import multiprocessing


def sumar_parte(arreglo, inicio, fin, resultados, indice_proceso):
    """
    Suma los elementos desde inicio hasta fin - 1.
    """
    suma_parcial = 0

    for i in range(inicio, fin):
        suma_parcial += arreglo[i]

    resultados.put((indice_proceso, suma_parcial))


if __name__ == "__main__":

    D = int(input("Ingrese la longitud del arreglo (D): "))
    n = int(input("Ingrese la cantidad de procesos (n): "))

    if D <= 0:
        print("Error: la longitud del arreglo debe ser mayor que 0.")

    elif n <= 0:
        print("Error: la cantidad de procesos debe ser mayor que 0.")

    elif n > D:
        print("Error: la cantidad de procesos no puede ser mayor que D.")

    elif D % n != 0:
        print(f"Error: {D} no es divisible entre {n}.")

    else:
        # Generación del arreglo fuera de la medición
        inicio_generacion = time.perf_counter()

        arreglo = [
            random.randint(1, 100)
            for _ in range(D)
        ]

        fin_generacion = time.perf_counter()

        datos_por_proceso = D // n
        resultados = multiprocessing.Queue()
        procesos = []

        # El cronómetro empieza antes de crear los procesos
        inicio_tiempo = time.perf_counter()

        # Crear e iniciar los procesos
        for i in range(n):
            inicio = i * datos_por_proceso
            fin = inicio + datos_por_proceso

            proceso = multiprocessing.Process(
                target=sumar_parte,
                args=(
                    arreglo,
                    inicio,
                    fin,
                    resultados,
                    i
                )
            )

            procesos.append(proceso)
            proceso.start()

        # Esperar a que terminen todos
        for proceso in procesos:
            proceso.join()

        # Recuperar resultados
        resultados_parciales = [0] * n

        for _ in range(n):
            indice, suma_parcial = resultados.get()
            resultados_parciales[indice] = suma_parcial

        # Sumar los resultados parciales
        suma_total = sum(resultados_parciales)

        # Finalizar el cronómetro
        fin_tiempo = time.perf_counter()

        tiempo_generacion = fin_generacion - inicio_generacion
        tiempo_ejecucion = fin_tiempo - inicio_tiempo

        print("\n--- RESULTADOS MULTIPROCESO ---")
        print("Longitud del arreglo:", D)
        print("Cantidad de procesos:", n)
        print("Datos por proceso:", datos_por_proceso)
        print("Suma parcial de cada proceso:", resultados_parciales)
        print("Suma total:", suma_total)
        print(f"Tiempo de generación: {tiempo_generacion:.6f} segundos")
        print(f"Tiempo de ejecución multiproceso: {tiempo_ejecucion:.6f} segundos")