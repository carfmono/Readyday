"""
Descarga device definitions de Garmin usando credenciales de desarrollador.
Corre en GitHub Actions donde api.gcs.garmin.com no está bloqueado.
"""
import os
import sys
import json
import zipfile
import requests
from pathlib import Path
from garminconnect import Garmin

GARMIN_EMAIL = os.environ["GARMIN_EMAIL"]
GARMIN_PASSWORD = os.environ["GARMIN_PASSWORD"]
DEVICES_DIR = Path("/opt/ciq-sdk/devices")
SDK_BIN = Path("/opt/ciq-sdk/bin")

# Dispositivos que necesita ReadyDay (de manifest.xml)
TARGET_DEVICES = [
    "venu3", "venu3s", "venu2", "venu2s", "venu2plus", "venu",
    "venusq", "venusq2", "fr245", "fr245m", "fr255", "fr255m",
    "fr255s", "fr265", "fr265s", "fr955", "fr965",
    "fenix7", "fenix7s", "fenix7x", "fenix7pro", "fenix8",
    "vivoactive4", "vivoactive4s", "vivoactive5",
    "instinct2", "instinct2s", "instinct2x", "instinct3",
]

def get_garmin_token():
    print("Autenticando con Garmin...")
    client = Garmin(GARMIN_EMAIL, GARMIN_PASSWORD)
    client.login()
    # Extraer el token OAuth de la sesión
    session = client.garmin_connect_base_url
    return client

def download_devices_via_gcs(session_cookies: dict):
    """Descarga device packages desde api.gcs.garmin.com"""
    DEVICES_DIR.mkdir(parents=True, exist_ok=True)

    base_url = "https://api.gcs.garmin.com/ciq"
    headers = {"Accept": "application/json"}

    # Obtener lista de devices disponibles
    r = requests.get(f"{base_url}/devices", cookies=session_cookies, headers=headers)
    if r.status_code != 200:
        print(f"Error listando devices: {r.status_code} — {r.text[:200]}")
        return False

    available = {d["id"]: d for d in r.json()}
    print(f"Devices disponibles en Garmin: {len(available)}")

    downloaded = []
    for device_id in TARGET_DEVICES:
        if device_id not in available:
            print(f"  skip: {device_id} (no disponible)")
            continue

        device_dir = DEVICES_DIR / device_id
        if device_dir.exists():
            print(f"  cache: {device_id}")
            downloaded.append(device_id)
            continue

        url = f"{base_url}/devices/{device_id}"
        r = requests.get(url, cookies=session_cookies)
        if r.status_code == 200:
            device_dir.mkdir(parents=True, exist_ok=True)
            pkg_path = DEVICES_DIR / f"{device_id}.zip"
            pkg_path.write_bytes(r.content)
            with zipfile.ZipFile(pkg_path) as z:
                z.extractall(device_dir)
            pkg_path.unlink()
            print(f"  ok: {device_id}")
            downloaded.append(device_id)
        else:
            print(f"  error: {device_id} → {r.status_code}")

    print(f"Devices descargados: {len(downloaded)}/{len(TARGET_DEVICES)}")
    return len(downloaded) > 0

def build_devices_xml():
    """Genera devices.xml combinado para todos los devices descargados."""
    lines = ['<?xml version="1.0" encoding="UTF-8"?>', "<devices>"]

    for device_dir in sorted(DEVICES_DIR.iterdir()):
        if not device_dir.is_dir():
            continue
        device_xml = device_dir / "device.xml"
        if device_xml.exists():
            content = device_xml.read_text()
            # Extraer el contenido interno sin el header XML
            inner = content.split("<device>", 1)
            if len(inner) > 1:
                lines.append(f'  <device id="{device_dir.name}">')
                lines.append(inner[1].split("</device>")[0])
                lines.append("  </device>")

    lines.append("</devices>")
    devices_xml = DEVICES_DIR / "devices.xml"
    devices_xml.write_text("\n".join(lines))
    print(f"devices.xml generado: {devices_xml} ({len(lines)} líneas)")

def main():
    try:
        client = get_garmin_token()
        # Usar las cookies de sesión de garminconnect
        session_cookies = {}
        if hasattr(client, 'req_session') and client.req_session:
            session_cookies = dict(client.req_session.cookies)

        ok = download_devices_via_gcs(session_cookies)
        if ok:
            build_devices_xml()
        else:
            print("No se pudieron descargar devices — el build fallará")
            sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        import traceback; traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
