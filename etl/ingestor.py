import requests
import psycopg2
from datetime import datetime

# Conexão DB (Hardcoded para dev, usar env vars em prod)
# Using port 5433 as configured
DB_CONN = "postgresql://postgres:password@localhost:5433/govcompras"

def run_etl():
    conn = psycopg2.connect(DB_CONN)
    cur = conn.cursor()

    # 1. Configurar Busca na API do Governo
    url = "https://dadosabertos.compras.gov.br/modulo-arp/11_consultar_arp"
    params = {
        "data_inicio_vigencia": "2024-01-01",
        "data_fim_vigencia": "2024-12-31",
        "pagina": 1
    }

    print("Buscando dados...")
    resp = requests.get(url, params=params)
    data = resp.json().get('resultado', [])

    for row in data:
        # Salvar Órgão
        orgao = row.get('orgaoGerenciador', {})
        cur.execute("""
            INSERT INTO orgaos (uasg, nome, uf) VALUES (%s, %s, %s)
            ON CONFLICT (uasg) DO UPDATE SET nome = EXCLUDED.nome
        """, (str(orgao.get('codigo')), orgao.get('nome'), orgao.get('siglaUf')))

        # Salvar ARP
        cur.execute("""
            INSERT INTO arps (codigo_arp_api, numero_arp, uasg_id, data_inicio_vigencia, data_fim_vigencia, objeto)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (codigo_arp_api) DO NOTHING
            RETURNING id
        """, (
            str(row.get('codigoArp')), row.get('numeroArp'), str(orgao.get('codigo')),
            row.get('dataInicioVigencia'), row.get('dataFimVigencia'), row.get('objeto')
        ))

        arp_id = cur.fetchone()

        # Se arp_id é None, a ARP já existia e não retornou ID.
        # Em produção, faríamos um SELECT para pegar o ID.
        if arp_id:
            # Busca Itens (Nested Request)
            arp_uuid = arp_id[0]
            print(f"Processando itens da ARP {row.get('numeroArp')}...")

            try:
                itens_resp = requests.get(
                    "https://dadosabertos.compras.gov.br/modulo-arp/11_consultar_itens_arp",
                    params={"codigo_arp": row.get('codigoArp')}
                )
                itens = itens_resp.json().get('resultado', [])

                for item in itens:
                    # Preparar vetor de busca (descrição + marca)
                    # Nota: O Postgres preenche o TSVECTOR via Trigger ou Update,
                    # mas aqui inserimos os dados brutos.
                    cur.execute("""
                        INSERT INTO itens_arp (arp_id, numero_item, descricao, valor_unitario, quantidade, unidade, marca, search_vector)
                        VALUES (%s, %s, %s, %s, %s, %s, %s,
                        setweight(to_tsvector('portuguese', %s), 'A') || setweight(to_tsvector('portuguese', %s), 'B'))
                    """, (
                        arp_uuid, item.get('numeroItem'), item.get('descricaoItem'),
                        item.get('valorUnitarioHomologado'), item.get('quantidadeHomologada'),
                        item.get('unidadeMedida'), item.get('marca'),
                        item.get('descricaoItem'), item.get('marca') or ''
                    ))
            except Exception as e:
                print(f"Erro nos itens: {e}")

        conn.commit()

    conn.close()
    print("ETL Finalizado.")

if __name__ == "__main__":
    run_etl()
