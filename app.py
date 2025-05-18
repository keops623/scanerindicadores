import requests
import csv
import time
from datetime import datetime
import schedule

# —————— CONFIGURACIÓN ——————
API_KEY    = 'AIzaSyDiQAJkJYFbhf6KMk4Sp3y2QpTIkICP6pA'
URLS       = [
    'https://corona.co/ambientes-banos/bano-privado',
    'https://corona.co/productos/servicios/asesorias/c/servicio-asesorias'
]
CSV_FILE   = 'metrics.csv'
# ——————————————————————————


def fetch_metrics(URLS: str) -> dict:
    """
    Llama a la API PageSpeed Insights y extrae los 10 indicadores solicitados.
    Lanza excepción si la petición falla (HTTP error, timeout…).
    """
    params = {
        'url': URLS,
        'key': API_KEY,
        'strategy': 'desktop'    # o 'mobile'
    }
    resp = requests.get(
        'https://www.googleapis.com/pagespeedonline/v5/runPagespeed',
        params=params,
        timeout=30
    )
    resp.raise_for_status()
    data   = resp.json()
    audits = data['lighthouseResult']['audits']
    # El audit "metrics" agrupa varios de los tiempos clave
    m      = audits['metrics']['details']['items'][0]
    
    return {
        'lcp'            : m.get('largestContentfulPaint'),
        'fcp'            : m.get('firstContentfulPaint'),
        'speed_index'    : m.get('speedIndex'),
        'tbt'            : m.get('totalBlockingTime'),
        'tti'            : m.get('interactive'),
        'page_load_time' : m.get('observedLoad'),
        'cls'            : audits['cumulative-layout-shift'].get('numericValue'),
        'ttfb'           : audits['server-response-time'].get('numericValue'),
        'http_requests'  : len(audits['network-requests']['details']['items']),
        'page_weight'    : sum(
            item.get('transferSize', 0)
            for item in audits['resource-summary']['details']['items']
        )
    }


def init_csv():
    """
    Crea el CSV con cabecera si no existe.
    """
    header = [
        'timestamp',
        'url',
        'LCP',
        'Page Weight',
        'TBT',
        'Speed Index',
        'FCP',
        'TTI',
        'HTTP Requests',
        'TTFB',
        'Page Load Time',
        'CLS'
    ]
    try:
        with open(CSV_FILE, 'x', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(header)
    except FileExistsError:
        pass


def scan_and_save():
    """
    Recorre cada URL, obtiene métricas y las guarda en el CSV.
    """
    now = datetime.now().isoformat()
    with open(CSV_FILE, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        for url in URLS:
            try:
                met = fetch_metrics(url)
                writer.writerow([
                    now,
                    url,
                    met['lcp'],
                    met['page_weight'],
                    met['tbt'],
                    met['speed_index'],
                    met['fcp'],
                    met['tti'],
                    met['http_requests'],
                    met['ttfb'],
                    met['page_load_time'],
                    met['cls']
                ])
                print(f"[{now}] ✔ Métricas guardadas para {url}")
            except Exception as e:
                print(f"[{now}] ⚠ Error en {url}: {e}")


if __name__ == '__main__':
    init_csv()
    scan_and_save()
    # Programa la tarea cada 30 minutos
    schedule.every(30).minutes.do(scan_and_save)

    print("⏱ Iniciada tarea; presiona CTRL+C para detener.")
    while True:
        schedule.run_pending()
        time.sleep(1)
