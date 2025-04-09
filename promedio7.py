import serial
import matplotlib.pyplot as plt
import numpy as np
from collections import deque
import threading
import tkinter as tk
from tkinter import ttk

# === CONFIGURACIÓN SERIAL Y EMG ===
PUERTO_SERIAL = 'COM4'  # Cambiar según puerto
BAUDIOS = 9600
VENTANA_MUESTRAS = 200
TAMAÑO_PROMEDIO = 20

UMBRAL_BAJO = 308
UMBRAL_MEDIO = 310
UMBRAL_ALTO = 312

# === BUFFERS Y ESTADO ===
datos_emg = deque(maxlen=VENTANA_MUESTRAS)
promedios = deque(maxlen=VENTANA_MUESTRAS)
estado_actual = None

# Variables globales para la GUI
movimiento_detectado = None
root = None  # Necesario para actualizar GUI desde otros hilos

# === CLASIFICACIÓN BASADA EN PROMEDIO EMG Y UMBRALES ===
def clasificar_emg(valor):
    global estado_actual

    if UMBRAL_BAJO <= valor < UMBRAL_MEDIO:
        clasificacion = "Movimiento 1"
        comando = '1'
    elif UMBRAL_MEDIO <= valor < UMBRAL_ALTO:
        clasificacion = "Movimiento 2"
        comando = '2'
    elif valor >= UMBRAL_ALTO:
        clasificacion = "Movimiento 3"
        comando = '3'
    else:
        clasificacion = "Reposo"
        comando = '0'

    if comando != estado_actual:
        ser.write(comando.encode())
        estado_actual = comando

    # ✅ Actualizar la GUI de forma segura desde el hilo principal
    if movimiento_detectado is not None and root is not None:
        root.after(0, movimiento_detectado.set, f"Clasificación: {clasificacion}")

# === LECTURA SERIAL ===
def leer_serial():
    while True:
        try:
            linea = ser.readline().decode().strip()
            if linea.isdigit():
                valor = int(linea)
                datos_emg.append(valor)
                if len(datos_emg) >= TAMAÑO_PROMEDIO:
                    promedio = np.mean(list(datos_emg)[-TAMAÑO_PROMEDIO:])
                    promedios.append(promedio)
                else:
                    promedios.append(valor)
        except:
            continue

# === GRAFICADO EN TIEMPO REAL ===
def graficar():
    plt.ion()
    fig, ax = plt.subplots()
    linea_emg, = ax.plot([], [], label='EMG')
    linea_prom, = ax.plot([], [], label='Promedio', linestyle='--')

    linea_umb_bajo = ax.axhline(UMBRAL_BAJO, color='green', linestyle=':', label='Umbral Bajo')
    linea_umb_medio = ax.axhline(UMBRAL_MEDIO, color='orange', linestyle=':', label='Umbral Medio')
    linea_umb_alto = ax.axhline(UMBRAL_ALTO, color='red', linestyle=':', label='Umbral Alto')

    ax.set_ylim(300, 320)
    ax.set_xlim(0, VENTANA_MUESTRAS)
    ax.set_title("Señal EMG")
    ax.set_xlabel("Muestras")
    ax.set_ylabel("Nivel EMG")
    ax.legend()

    while True:
        if datos_emg:
            linea_emg.set_ydata(list(datos_emg))
            linea_emg.set_xdata(np.arange(len(datos_emg)))
            linea_prom.set_ydata(list(promedios))
            linea_prom.set_xdata(np.arange(len(promedios)))

            if promedios:
                clasificar_emg(promedios[-1])

            linea_umb_bajo.set_ydata([UMBRAL_BAJO] * 2)
            linea_umb_medio.set_ydata([UMBRAL_MEDIO] * 2)
            linea_umb_alto.set_ydata([UMBRAL_ALTO] * 2)

            ax.relim()
            ax.autoscale_view(True, True, True)
            plt.pause(0.05)

# === GUI DE AJUSTE DE UMBRALES ===
def crear_gui():
    def actualizar_umbrales(*args):
        global UMBRAL_BAJO, UMBRAL_MEDIO, UMBRAL_ALTO
        UMBRAL_BAJO = int(slider_bajo.get())
        UMBRAL_MEDIO = int(slider_medio.get())
        UMBRAL_ALTO = int(slider_alto.get())

    global movimiento_detectado, root
    root = tk.Tk()
    root.title("Ajuste de Umbrales EMG")

    ttk.Label(root, text="Umbral Bajo").pack()
    slider_bajo = tk.Scale(root, from_=0, to=325, orient='horizontal', command=actualizar_umbrales)
    slider_bajo.set(UMBRAL_BAJO)
    slider_bajo.pack()

    ttk.Label(root, text="Umbral Medio").pack()
    slider_medio = tk.Scale(root, from_=0, to=325, orient='horizontal', command=actualizar_umbrales)
    slider_medio.set(UMBRAL_MEDIO)
    slider_medio.pack()

    ttk.Label(root, text="Umbral Alto").pack()
    slider_alto = tk.Scale(root, from_=0, to=325, orient='horizontal', command=actualizar_umbrales)
    slider_alto.set(UMBRAL_ALTO)
    slider_alto.pack()

    movimiento_detectado = tk.StringVar()
    movimiento_detectado.set("Clasificación: Reposo")
    ttk.Label(root, textvariable=movimiento_detectado, font=("Arial", 14), foreground="blue").pack(pady=10)

    root.mainloop()

# === INICIAR SERIAL E HILOS ===
try:
    ser = serial.Serial(PUERTO_SERIAL, BAUDIOS)
    print(f"Conectado a {PUERTO_SERIAL}")
except:
    print(f"No se pudo conectar al puerto {PUERTO_SERIAL}")
    exit()

# Lanzar hilos
threading.Thread(target=leer_serial, daemon=True).start()
threading.Thread(target=crear_gui, daemon=True).start()

# Inicia la gráfica
graficar()
