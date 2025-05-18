import requests
import csv
import time
from datetime import datetime
import schedule

# 🔧 Configuración inicial
API_KEY = 'AIzaSyCl-DeJQFZscq_nRuRFHFnQUv5NTyZ4u3Y'
URLS = [
    'https://empresa.corona.co/sostenibilidad/',
    'https://empresa.corona.co/quienes-somos/'
]
CSV_FILE = 'metrics.csv'
RETRY_LIMIT = 5

# 🎯 Métricas a capturar
METRICS = {
    'lcp': 'largest-contentful-paint',
    'page_weight': 'totalBytes',
    'tbt': 'total-blocking-time',
    'speed_index': 'speed-index',
    'fcp': 'first-contentful-paint',
    'tti': 'interactive',
    'http_requests': 'totalRequestCount',
    'ttfb': 'server-response-time',
    'page_load_time': 'loadTime',
    'cls': 'cumulative-layout-shift'
}

# 🧠 Función para obtener datos de una URL
def get_pagespeed_metrics(URLS):
    for attempt in range(1, RETRY_LIMIT + 1):
        try:
            response = requests.get(
                'https://www.googleapis.com/pagespeedonline/v5/runPagespeed',
                params={
                    'url': URLS,
                    'key': API_KEY,
                    'strategy': 'desktop'
                },
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"[{datetime.now()}] Fallo al intentar {attempt} con {url}: {e}")
            time.sleep(5)  # Pequeña pausa antes del siguiente intento
    return None

# 📦 Función para parsear el JSON de respuesta
def parse_metrics(data):
    try:
        lighthouse = data['lighthouseResult']['audits']
        loading_exp = data['loadingExperience']['metrics']

        return {
            'lcp': lighthouse[METRICS['lcp']]['numericValue'] / 1000,
            'page_weight': sum(item.get('transferSize', 0) for item in lighthouse['resource-summary']['details']['items']) / 1024,
            'tbt': lighthouse[METRICS['tbt']]['numericValue'],
            'speed_index': lighthouse[METRICS['speed_index']]['numericValue'],
            'fcp': lighthouse[METRICS['fcp']]['numericValue'],
            'tti': lighthouse[METRICS['tti']]['numericValue'],
            'http_requests': data['lighthouseResult']['audits']['resource-summary']['details']['items'][0]['requestCount'],
            'ttfb': lighthouse[METRICS['ttfb']]['numericValue'],
            'page_load_time': lighthouse['metrics']['details']['items'][0]['observedLoad'],
            'cls': lighthouse[METRICS['cls']]['numericValue'],
        }
    except Exception as e:
        print(f"[{datetime.now()}] Error al parsear métricas: {e}")
        return None

# 📝 Función para guardar resultados en CSV
def save_to_csv(row):
    file_exists = False
    try:
        with open(CSV_FILE, 'r'):
            file_exists = True
    except FileNotFoundError:
        pass

    with open(CSV_FILE, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=row.keys())
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)

# 🔄 Proceso general
def process_all_urls():
    for url in URLS:
        print(f"[{datetime.now()}] Escaneando {url}...")
        data = get_pagespeed_metrics(url)
        if not data:
            print(f"[{datetime.now()}] No se pudo obtener datos para {url}")
            continue
        metrics = parse_metrics(data)
        if not metrics:
            print(f"[{datetime.now()}] No se pudieron extraer métricas de {url}")
            continue

        row = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'url': url,
            **metrics
        }
        save_to_csv(row)
        print(f"[{datetime.now()}] Datos guardados para {url}")

# 🕒 Programación cada 30 minutos
schedule.every(30).minutes.do(process_all_urls)

if __name__ == '__main__':
    print("⏳ Iniciando monitoreo de PageSpeed...")
    process_all_urls()  # Ejecuta una vez al iniciar
    while True:
        schedule.run_pending()
        time.sleep(1)
