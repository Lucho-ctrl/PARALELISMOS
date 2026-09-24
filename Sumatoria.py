import random
import time
import threading

def sumar_parte(arreglo, inicio, fin, resultados, indice_hilo):
    """
    Suma los elementos del arreglo desde inicio hasta fin - 1
    y guarda el resultado parcial en resultados[indice_hilo].
    """
    suma_parcial = 0

    for i in range(inicio, fin):
        suma_parcial += arreglo[i]

    resultados[indice_hilo] = suma_parcial


# Entrada de datos
D = int(input("Ingrese la longitud del arreglo (D): "))
n = int(input("Ingrese la cantidad de hilos (n): "))

# Validaciones
if D <= 0:
    print("Error: la longitud del arreglo debe ser mayor que 0.")

elif n <= 0:
    print("Error: la cantidad de hilos debe ser mayor que 0.")

elif n > D:
    print("Error: la cantidad de hilos no puede ser mayor que la longitud del arreglo.")

elif D % n != 0:
    print(f"Error: {D} no es divisible entre {n}.")
    print("Seleccione una cantidad de hilos que distribuya los datos equitativamente.")

else:
    # Crear un arreglo de D números aleatorios entre 1 y 100
    arreglo = [random.randint(1, 100) for _ in range(D)]

    # Datos que procesará cada hilo: D / n
    datos_por_hilo = D // n

    # Lista para almacenar la suma parcial de cada hilo
    resultados_parciales = [0] * n

    # Lista de objetos hilo
    hilos = []

    # Iniciar medición del tiempo
    inicio_tiempo = time.perf_counter()

    # Crear e iniciar los hilos
    for i in range(n):
        inicio = i * datos_por_hilo
        fin = inicio + datos_por_hilo

        hilo = threading.Thread(
            target=sumar_parte,
            args=(arreglo, inicio, fin, resultados_parciales, i)
        )

        hilos.append(hilo)
        hilo.start()

    # Esperar a que todos los hilos terminen
    for hilo in hilos:
        hilo.join()

    # Sumar los resultados parciales producidos por cada hilo
    suma_total = sum(resultados_parciales)

    # Finalizar medición del tiempo
    fin_tiempo = time.perf_counter()

    tiempo_ejecucion = fin_tiempo - inicio_tiempo

    # Resultados
    print("RESULTADOS: N HILOS ---")
    print("Longitud del arreglo (D):", D)
    print("Cantidad de hilos (n):", n)
    print("Datos por hilo (D / n):", datos_por_hilo)
    print("Suma parcial de cada hilo:", resultados_parciales)
    print("Suma total:", suma_total)
    print(f"Tiempo de ejecución: {tiempo_ejecucion:.10f} segundos")