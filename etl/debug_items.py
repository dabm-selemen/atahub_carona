import requests
import json

def debug_item_fetch():
    # 1. Fetch one ARP to get valid parameters
    print("Fetching one ARP...")
    url_arp = "https://dadosabertos.compras.gov.br/modulo-arp/1_consultarARP"
    params_arp = {
        "dataVigenciaInicialMin": "2024-01-01",
        "dataVigenciaInicialMax": "2024-01-31",
        "pagina": 1,
        "tamanhoPagina": 10
    }

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept": "application/json"
    }

    try:
        resp_arp = requests.get(url_arp, params=params_arp, headers=headers, timeout=30)
        print(f"ARP Response Status: {resp_arp.status_code}")

        if resp_arp.status_code != 200:
            print(f"Error fetching ARP: {resp_arp.text}")
            return

        data_arp = resp_arp.json().get('resultado', [])
        if not data_arp:
            print("No ARPs found.")
            return

        arp = data_arp[0]
        print(f"Found ARP: {arp.get('numeroAtaRegistroPreco')}")
        print(f"  numeroCompra: {arp.get('numeroCompra')}")
        print(f"  codigoUnidadeGerenciadora: {arp.get('codigoUnidadeGerenciadora')}")
        print(f"  dataVigenciaInicial: {arp.get('dataVigenciaInicial')}")

        # 2. Try to fetch items for this ARP
        print("\nFetching items for this ARP...")
        url_items = "https://dadosabertos.compras.gov.br/modulo-arp/2_consultarARPItem"

        # Logic from ingestor.py
        data_vigencia = arp.get('dataVigenciaInicial')
        item_params = {
            "numeroCompra": arp.get('numeroCompra'),
            "codigoUnidadeGerenciadora": arp.get('codigoUnidadeGerenciadora'),
            "dataVigenciaInicialMin": data_vigencia,
            "dataVigenciaInicialMax": data_vigencia,
            "tamanhoPagina": 10
        }

        print(f"Requesting Items with params: {json.dumps(item_params, indent=2)}")

        resp_items = requests.get(url_items, params=item_params, headers=headers, timeout=30)
        print(f"Items Response Status: {resp_items.status_code}")

        if resp_items.status_code == 200:
            items = resp_items.json().get('resultado', [])
            print(f"Items found: {len(items)}")
            if items:
                print("First item JSON structure:")
                print(json.dumps(items[0], indent=2))
            else:
                print("Response body:", resp_items.text[:500])
        else:
            print(f"Error fetching items: {resp_items.text}")

    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    debug_item_fetch()
