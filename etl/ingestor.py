import requests
import psycopg2
import uuid
from datetime import datetime

# Conexão DB (Hardcoded para dev, usar env vars em prod)
# Using port 5433 as configured
DB_CONN = "postgresql://postgres:password@localhost:5433/govcompras"

def run_etl():
    conn = psycopg2.connect(DB_CONN)
    cur = conn.cursor()

    # 1. Configurar Busca na API do Governo
    # Endpoints atualizados conforme Swagger UI
    url = "https://dadosabertos.compras.gov.br/modulo-arp/1_consultarARP"
    params = {
        "dataVigenciaInicialMin": "2023-01-01",
        "dataVigenciaInicialMax": "2024-12-31",
        "pagina": 1
    }

    print("Buscando dados...")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept": "application/json"
    }
    resp = requests.get(url, params=params, headers=headers, timeout=30)
    if resp.status_code != 200:
        print(f"Erro na API: {resp.status_code} - {resp.text}")

    data = resp.json().get('resultado', [])
    print(f"Encontrados {len(data)} registros.")

    for row in data:
        # Mapeamento de campos baseado na resposta da API
        # numeroAtaRegistroPreco -> numero_arp
        # numeroControlePncpAta -> codigo_arp_api
        # codigoUnidadeGerenciadora -> uasg_id (e orgao.codigo)
        # dataVigenciaInicial -> data_inicio_vigencia
        # dataVigenciaFinal -> data_fim_vigencia
        # objeto -> objeto

        # Salvar Órgão
        # A resposta da API traz dados do órgão na raiz
        codigo_orgao = row.get('codigoUnidadeGerenciadora')
        nome_orgao = row.get('nomeUnidadeGerenciadora')
        uf_orgao = '' # Não disponível na raiz, talvez ignorar ou buscar de outra forma

        if codigo_orgao:
            cur.execute("""
                INSERT INTO orgaos (uasg, nome, uf) VALUES (%s, %s, %s)
                ON CONFLICT (uasg) DO UPDATE SET nome = EXCLUDED.nome
            """, (str(codigo_orgao), nome_orgao, uf_orgao))

        # Salvar ARP
        arp_uuid_val = str(uuid.uuid4())
        codigo_arp_api = row.get('numeroControlePncpAta')

        cur.execute("""
            INSERT INTO arps (id, codigo_arp_api, numero_arp, uasg_id, data_inicio_vigencia, data_fim_vigencia, objeto, numero_compra)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (codigo_arp_api) DO UPDATE SET numero_arp = EXCLUDED.numero_arp
            RETURNING id
        """, (
            arp_uuid_val,
            str(codigo_arp_api),
            row.get('numeroAtaRegistroPreco'),
            str(codigo_orgao),
            row.get('dataVigenciaInicial'),
            row.get('dataVigenciaFinal'),
            row.get('objeto'),
            row.get('numeroCompra')
        ))

        arp_id = cur.fetchone()

        if arp_id:
            # Busca Itens (Nested Request)
            arp_uuid = arp_id[0]
            numero_arp = row.get('numeroAtaRegistroPreco')
            print(f"Processando itens da ARP {numero_arp}...")

            try:
                # Tentar buscar itens com parâmetros compostos e datas obrigatórias
                # A API exige dataVigenciaInicialMin e Max. Usaremos a data da própria ARP.
                data_vigencia = row.get('dataVigenciaInicial')

                item_params = {
                    "numeroCompra": row.get('numeroCompra'),
                    "codigoUnidadeGerenciadora": row.get('codigoUnidadeGerenciadora'),
                    "dataVigenciaInicialMin": data_vigencia,
                    "dataVigenciaInicialMax": data_vigencia,
                    "tamanhoPagina": 500
                }

                itens_resp = requests.get(
                    "https://dadosabertos.compras.gov.br/modulo-arp/2_consultarARPItem",
                    params=item_params,
                    headers=headers,
                    timeout=30
                )

                if itens_resp.status_code == 200:
                    itens = itens_resp.json().get('resultado', [])
                    print(f"  - Encontrados {len(itens)} itens.")

                    for item in itens:
                        # Mapeamento de itens (precisa verificar chaves do item também, mas assumindo padrão similar)
                        # numeroItem -> numeroItem
                        # descricao -> descricaoItem
                        # valorUnitario -> valorUnitarioHomologado
                        # quantidade -> quantidadeHomologada
                        # unidade -> unidadeMedida
                        # marca -> marca

                        item_uuid = str(uuid.uuid4())
                        cur.execute("""
                            INSERT INTO itens_arp (
                                id, arp_id, numero_item, codigo_item, descricao, tipo_item,
                                valor_unitario, valor_total, quantidade, unidade, marca, modelo,
                                classificacao_fornecedor, cnpj_fornecedor, nome_fornecedor,
                                situacao_sicaf, codigo_pdm, nome_pdm, quantidade_empenhada,
                                percentual_maior_desconto, maximo_adesao, item_excluido
                            )
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """, (
                            item_uuid,
                            arp_uuid,
                            item.get('numeroItem'),
                            str(item.get('codigoItem')) if item.get('codigoItem') else None,
                            item.get('descricaoItem'),
                            item.get('tipoItem'),
                            item.get('valorUnitario'),
                            item.get('valorTotal'),
                            item.get('quantidadeHomologadaItem'),
                            None,  # unidade - not in API response
                            None,  # marca - not in API response
                            None,  # modelo - not in API response
                            item.get('classificacaoFornecedor'),
                            item.get('niFornecedor'),
                            item.get('nomeRazaoSocialFornecedor'),
                            item.get('situacaoSicaf'),
                            item.get('codigoPdm'),
                            item.get('nomePdm'),
                            item.get('quantidadeEmpenhada'),
                            item.get('percentualMaiorDesconto'),
                            item.get('maximoAdesao'),
                            item.get('itemExcluido', False)
                        ))
                else:
                    print(f"  - Erro ao buscar itens: {itens_resp.status_code} - {itens_resp.text}")

            except Exception as e:
                print(f"Erro nos itens: {e}")

        conn.commit()

    conn.close()
    print("ETL Finalizado.")

if __name__ == "__main__":
    run_etl()
