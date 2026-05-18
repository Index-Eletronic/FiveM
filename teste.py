import time
import csv
import math
import threading
from datetime import datetime

import psutil

LIMITE_ALERTA = 75
LIMITE_CRITICO = 85
INTERVALO = 2
ARQUIVO_LOG = "log_watercooler.csv"
ATIVAR_STRESS_TEST = False  # Troque para True se quiser testar com carga pesada


def salvar_log(data_hora, temperatura, status):
    arquivo_existe = False

    try:
        with open(ARQUIVO_LOG, "r", encoding="utf-8"):
            arquivo_existe = True
    except FileNotFoundError:
        pass

    with open(ARQUIVO_LOG, "a", newline="", encoding="utf-8") as arquivo:
        writer = csv.writer(arquivo, delimiter=";")

        if not arquivo_existe:
            writer.writerow(["data_hora", "temperatura_cpu", "status"])

        writer.writerow([data_hora, temperatura, status])


def classificar_temperatura(temp):
    if temp >= LIMITE_CRITICO:
        return "CRITICO - verificar bomba/fans/pasta termica"
    elif temp >= LIMITE_ALERTA:
        return "ALERTA - temperatura alta"
    return "OK"


def stress_cpu():
    while True:
        try:
            math.factorial(50000)
        except Exception:
            pass


def iniciar_stress():
    total_threads = psutil.cpu_count(logical=True) or 4

    print(f"Iniciando stress test com {total_threads} threads...")

    for _ in range(total_threads):
        t = threading.Thread(target=stress_cpu, daemon=True)
        t.start()


def obter_temperatura_cpu():
    try:
        sensores = psutil.sensors_temperatures()
    except Exception:
        sensores = {}

    if not sensores:
        return None, []

    leituras_encontradas = []

    palavras_cpu = [
        "cpu",
        "core",
        "package",
        "tdie",
        "tctl",
        "k10temp",
        "zenpower",
    ]

    for nome_sensor, entradas in sensores.items():
        for entrada in entradas:
            label = entrada.label or ""
            atual = entrada.current

            texto_busca = f"{nome_sensor} {label}".lower()

            if any(palavra in texto_busca for palavra in palavras_cpu):
                leituras_encontradas.append({
                    "sensor": nome_sensor,
                    "label": label,
                    "temperatura": atual
                })

    if not leituras_encontradas:
        for nome_sensor, entradas in sensores.items():
            for entrada in entradas:
                leituras_encontradas.append({
                    "sensor": nome_sensor,
                    "label": entrada.label or "",
                    "temperatura": entrada.current
                })

    temperatura_maxima = max(item["temperatura"] for item in leituras_encontradas)

    return temperatura_maxima, leituras_encontradas


def mostrar_sensores_detectados():
    try:
        sensores = psutil.sensors_temperatures()
    except Exception:
        sensores = {}

    print("\nSensores detectados pelo psutil:")

    if not sensores:
        print("Nenhum sensor detectado pelo psutil no Windows.")
        print("Recomendado: verificar temperatura pela BIOS ou instalar HWiNFO.")
        return

    for nome_sensor, entradas in sensores.items():
        print(f"\nSensor: {nome_sensor}")
        for entrada in entradas:
            print(f"  {entrada.label or 'Sem label'}: {entrada.current} °C")


def main():
    print("=" * 60)
    print(" Monitor de Water Cooler / Temperatura CPU")
    print("=" * 60)
    print("Pressione CTRL + C para parar.\n")

    mostrar_sensores_detectados()

    if ATIVAR_STRESS_TEST:
        iniciar_stress()
    else:
        print("\nStress test desativado.")
        print("Para ativar, altere ATIVAR_STRESS_TEST = True\n")

    temperatura_anterior = None

    try:
        while True:
            data_hora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            temperatura, leituras = obter_temperatura_cpu()

            if temperatura is None:
                print(f"[{data_hora}] Sensor de temperatura não encontrado.")
                print("No Windows, o psutil geralmente não lê temperatura da CPU.")
                print("Use BIOS, HWiNFO ou LibreHardwareMonitor com WMI ativo.")
                time.sleep(INTERVALO)
                continue

            status = classificar_temperatura(temperatura)

            print(f"[{data_hora}] CPU Máx: {temperatura:.1f} °C | {status}")

            if temperatura_anterior is not None:
                subida = temperatura - temperatura_anterior

                if subida >= 8:
                    print("ALERTA: subida rápida de temperatura.")
                    print("Verifique bomba, fans, encaixe do bloco e pasta térmica.")

            if temperatura >= LIMITE_CRITICO:
                print("CRÍTICO: temperatura muito alta.")
                print("Recomendo desligar o PC e revisar a instalação do water cooler.")

            salvar_log(data_hora, temperatura, status)

            temperatura_anterior = temperatura
            time.sleep(INTERVALO)

    except KeyboardInterrupt:
        print("\nMonitoramento finalizado.")
        print(f"Log salvo em: {ARQUIVO_LOG}")


if __name__ == "__main__":
    main()