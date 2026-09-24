import random
import time
import multiprocessing


def sumar_parte(arreglo, inicio, fin, resultados, indice_proceso):
    """
    Suma los elementos del arreglo desde inicio hasta fin - 1
    y guarda el resultado parcial en la cola.
    """
    suma_parcial = 0

    for i in range(inicio, fin):
        suma_parcial += arreglo[i]

    resultados.put((indice_proceso, suma_parcial))


if __name__ == "__main__":

    # Entrada de datos
    D = int(input("Ingrese la longitud del arreglo (D): "))
    n = int(input("Ingrese la cantidad de procesos (n): "))

    # Validaciones
    if D <= 0:
        print("Error: la longitud del arreglo debe ser mayor que 0.")

    elif n <= 0:
        print("Error: la cantidad de procesos debe ser mayor que 0.")

    elif n > D:
        print("Error: la cantidad de procesos no puede ser mayor que la longitud del arreglo.")

    elif D % n != 0:
        print(f"Error: {D} no es divisible entre {n}.")
        print("Seleccione una cantidad de procesos que distribuya los datos equitativamente.")

    else:

        # Crear un arreglo de D números aleatorios entre 1 y 100
        arreglo = [random.randint(1, 100) for _ in range(D)]

        # Datos que procesará cada proceso: D / n
        datos_por_proceso = D // n

        # Cola para almacenar las sumas parciales
        resultados = multiprocessing.Queue()

        # Lista de objetos proceso
        procesos = []

        # Iniciar medición del tiempo
        # inicio_tiempo = time.perf_counter()

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

        inicio_tiempo = time.perf_counter()
        
        # Esperar a que todos los procesos terminen
        for proceso in procesos:
            proceso.join()

        # Recuperar los resultados de los procesos
        resultados_parciales = [0] * n

        for _ in range(n):
            indice, suma_parcial = resultados.get()
            resultados_parciales[indice] = suma_parcial

        # Sumar los resultados parciales
        suma_total = sum(resultados_parciales)

        # Finalizar medición del tiempo
        fin_tiempo = time.perf_counter()

        tiempo_ejecucion = fin_tiempo - inicio_tiempo

        # Resultados
        print("\n--- RESULTADOS: N PROCESOS ---")
        print("Longitud del arreglo (D):", D)
        print("Cantidad de procesos (n):", n)
        print("Datos por proceso (D / n):", datos_por_proceso)
        print("Suma parcial de cada proceso:", resultados_parciales)
        print("Suma total:", suma_total)
        print(f"Tiempo de ejecución: {tiempo_ejecucion:.10f} segundos")