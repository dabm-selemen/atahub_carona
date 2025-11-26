import psycopg2
import uuid
from datetime import datetime, timedelta
import random

# Conexão DB (usando a mesma configuração do ingestor)
DB_CONN = "postgresql://postgres:password@localhost:5433/govcompras"

# Dados de exemplo realistas
ORGAOS_SAMPLE = [
    {"uasg": "153173", "nome": "Ministério da Saúde", "uf": "DF"},
    {"uasg": "160010", "nome": "Ministério da Educação", "uf": "DF"},
    {"uasg": "110100", "nome": "Comando do Exército", "uf": "DF"},
    {"uasg": "114102", "nome": "Marinha do Brasil", "uf": "RJ"},
    {"uasg": "120001", "nome": "Polícia Federal", "uf": "DF"},
    {"uasg": "153001", "nome": "Hospital das Forças Armadas", "uf": "DF"},
    {"uasg": "158154", "nome": "Universidade Federal de São Paulo", "uf": "SP"},
    {"uasg": "153025", "nome": "Fundação Oswaldo Cruz", "uf": "RJ"},
    {"uasg": "170500", "nome": "Instituto Nacional de Pesquisas Espaciais", "uf": "SP"},
    {"uasg": "154040", "nome": "Agência Nacional de Vigilância Sanitária", "uf": "DF"},
]

# Templates de ARPs com objetos realistas
ARP_TEMPLATES = [
    {
        "objeto": "Registro de preços para aquisição de equipamentos de informática e periféricos",
        "itens": [
            {"descricao": "Notebook Dell Latitude 5420, Intel Core i5, 8GB RAM, 256GB SSD", "valor_min": 3500, "valor_max": 4500, "unidade": "UN", "marca": "Dell"},
            {"descricao": "Monitor LED 24 polegadas Full HD, HDMI, VGA", "valor_min": 600, "valor_max": 900, "unidade": "UN", "marca": "LG"},
            {"descricao": "Mouse óptico USB com fio", "valor_min": 15, "valor_max": 35, "unidade": "UN", "marca": "Logitech"},
            {"descricao": "Teclado USB ABNT2 com fio", "valor_min": 40, "valor_max": 80, "unidade": "UN", "marca": "Microsoft"},
            {"descricao": "Webcam Full HD 1080p com microfone integrado", "valor_min": 200, "valor_max": 350, "unidade": "UN", "marca": "Logitech"},
        ]
    },
    {
        "objeto": "Registro de preços para aquisição de materiais de escritório e expediente",
        "itens": [
            {"descricao": "Papel A4 75g/m² resma com 500 folhas", "valor_min": 18, "valor_max": 25, "unidade": "RESMA", "marca": "Chamex"},
            {"descricao": "Caneta esferográfica azul ponta média", "valor_min": 0.80, "valor_max": 1.50, "unidade": "UN", "marca": "BIC"},
            {"descricao": "Grampeador de mesa capacidade 25 folhas", "valor_min": 15, "valor_max": 30, "unidade": "UN", "marca": "Jocar"},
            {"descricao": "Pasta suspensa marmorizada", "valor_min": 2.50, "valor_max": 4.00, "unidade": "UN", "marca": "Dello"},
            {"descricao": "Caderno universitário 200 folhas capa dura", "valor_min": 12, "valor_max": 20, "unidade": "UN", "marca": "Tilibra"},
        ]
    },
    {
        "objeto": "Registro de preços para aquisição de medicamentos e insumos hospitalares",
        "itens": [
            {"descricao": "Dipirona Sódica 500mg comprimido", "valor_min": 0.05, "valor_max": 0.15, "unidade": "COMP", "marca": "EMS"},
            {"descricao": "Paracetamol 750mg comprimido", "valor_min": 0.08, "valor_max": 0.20, "unidade": "COMP", "marca": "Medley"},
            {"descricao": "Luva de procedimento não estéril tamanho M", "valor_min": 0.25, "valor_max": 0.45, "unidade": "UN", "marca": "Supermax"},
            {"descricao": "Seringa descartável 10ml com agulha", "valor_min": 0.40, "valor_max": 0.70, "unidade": "UN", "marca": "BD"},
            {"descricao": "Álcool em gel 70% antisséptico 500ml", "valor_min": 8, "valor_max": 15, "unidade": "FRASCO", "marca": "Rioquímica"},
        ]
    },
    {
        "objeto": "Registro de preços para aquisição de mobiliário para escritório",
        "itens": [
            {"descricao": "Mesa para escritório em L 150x150cm com gavetas", "valor_min": 800, "valor_max": 1200, "unidade": "UN", "marca": "Dalla Costa"},
            {"descricao": "Cadeira giratória presidente com braços reguláveis", "valor_min": 600, "valor_max": 900, "unidade": "UN", "marca": "Cavaletti"},
            {"descricao": "Armário alto 2 portas 180x80x40cm", "valor_min": 700, "valor_max": 1000, "unidade": "UN", "marca": "Pandin"},
            {"descricao": "Estante de aço 5 prateleiras 200x100x40cm", "valor_min": 400, "valor_max": 650, "unidade": "UN", "marca": "Lar Aço"},
            {"descricao": "Gaveteiro volante 3 gavetas com rodízios", "valor_min": 350, "valor_max": 550, "unidade": "UN", "marca": "Dalla Costa"},
        ]
    },
    {
        "objeto": "Registro de preços para aquisição de equipamentos de segurança e proteção individual",
        "itens": [
            {"descricao": "Capacete de segurança classe B com jugular", "valor_min": 25, "valor_max": 45, "unidade": "UN", "marca": "MSA"},
            {"descricao": "Óculos de proteção incolor antiembaçante", "valor_min": 8, "valor_max": 15, "unidade": "UN", "marca": "3M"},
            {"descricao": "Luva de raspa cano longo", "valor_min": 12, "valor_max": 20, "unidade": "PAR", "marca": "Volk"},
            {"descricao": "Bota de segurança PVC cano médio", "valor_min": 40, "valor_max": 70, "unidade": "PAR", "marca": "Marluvas"},
            {"descricao": "Colete refletivo laranja com faixas", "valor_min": 15, "valor_max": 25, "unidade": "UN", "marca": "Plastcor"},
        ]
    },
    {
        "objeto": "Registro de preços para aquisição de material de limpeza e higiene",
        "itens": [
            {"descricao": "Detergente líquido neutro 500ml", "valor_min": 2, "valor_max": 4, "unidade": "FRASCO", "marca": "Ypê"},
            {"descricao": "Desinfetante líquido lavanda 2 litros", "valor_min": 6, "valor_max": 10, "unidade": "FRASCO", "marca": "Pinho Sol"},
            {"descricao": "Papel higiênico folha dupla rolo 30m", "valor_min": 1.50, "valor_max": 2.50, "unidade": "ROLO", "marca": "Personal"},
            {"descricao": "Sabonete líquido perolado 800ml", "valor_min": 8, "valor_max": 12, "unidade": "REFIL", "marca": "Protex"},
            {"descricao": "Saco de lixo 100 litros preto reforçado", "valor_min": 0.80, "valor_max": 1.50, "unidade": "UN", "marca": "Emballe"},
        ]
    },
    {
        "objeto": "Registro de preços para aquisição de veículos automotores",
        "itens": [
            {"descricao": "Veículo sedan 1.6 flex 4 portas ar condicionado", "valor_min": 75000, "valor_max": 95000, "unidade": "UN", "marca": "Chevrolet"},
            {"descricao": "Veículo utilitário pickup cabine dupla 4x4 diesel", "valor_min": 180000, "valor_max": 220000, "unidade": "UN", "marca": "Toyota"},
            {"descricao": "Veículo SUV 2.0 flex automático 7 lugares", "valor_min": 150000, "valor_max": 180000, "unidade": "UN", "marca": "Hyundai"},
            {"descricao": "Ambulância tipo A simples remoção", "valor_min": 120000, "valor_max": 150000, "unidade": "UN", "marca": "Fiat"},
        ]
    },
    {
        "objeto": "Registro de preços para aquisição de equipamentos de ar condicionado",
        "itens": [
            {"descricao": "Ar condicionado split 12000 BTUs inverter", "valor_min": 1800, "valor_max": 2500, "unidade": "UN", "marca": "Samsung"},
            {"descricao": "Ar condicionado split 18000 BTUs inverter", "valor_min": 2500, "valor_max": 3500, "unidade": "UN", "marca": "LG"},
            {"descricao": "Ar condicionado split 24000 BTUs inverter", "valor_min": 3200, "valor_max": 4500, "unidade": "UN", "marca": "Midea"},
            {"descricao": "Ar condicionado janela 10000 BTUs", "valor_min": 1200, "valor_max": 1800, "unidade": "UN", "marca": "Consul"},
        ]
    },
]

def populate_database():
    """Popula o banco de dados com dados de exemplo realistas"""
    conn = psycopg2.connect(DB_CONN)
    cur = conn.cursor()

    print("🚀 Iniciando população do banco de dados...")

    # 1. Inserir Órgãos
    print("\n📋 Inserindo órgãos...")
    for orgao in ORGAOS_SAMPLE:
        cur.execute("""
            INSERT INTO orgaos (uasg, nome, uf)
            VALUES (%s, %s, %s)
            ON CONFLICT (uasg) DO UPDATE
            SET nome = EXCLUDED.nome, uf = EXCLUDED.uf
        """, (orgao["uasg"], orgao["nome"], orgao["uf"]))
    print(f"   ✅ {len(ORGAOS_SAMPLE)} órgãos inseridos")

    # 2. Inserir ARPs e Itens
    print("\n📝 Inserindo ARPs e itens...")
    total_arps = 0
    total_itens = 0

    # Criar múltiplas ARPs para cada órgão usando os templates
    for orgao in ORGAOS_SAMPLE:
        # Cada órgão terá de 2 a 4 ARPs
        num_arps = random.randint(2, 4)
        templates_selecionados = random.sample(ARP_TEMPLATES, min(num_arps, len(ARP_TEMPLATES)))

        for idx, template in enumerate(templates_selecionados):
            # Gerar datas de vigência
            # ARPs vigentes: data início entre 6 meses atrás e hoje
            # data fim entre 6 meses e 2 anos no futuro
            dias_inicio = random.randint(-180, 0)
            dias_duracao = random.randint(180, 730)

            data_inicio = datetime.now().date() + timedelta(days=dias_inicio)
            data_fim = data_inicio + timedelta(days=dias_duracao)

            # Gerar número da ARP (formato: ano/número sequencial)
            ano = data_inicio.year
            numero_sequencial = random.randint(1, 999)
            numero_arp = f"{ano:04d}/{numero_sequencial:04d}"

            # Gerar código único da API
            codigo_arp_api = f"ARP-{orgao['uasg']}-{ano}-{numero_sequencial:04d}"

            # Inserir ARP
            arp_uuid = str(uuid.uuid4())
            cur.execute("""
                INSERT INTO arps (id, codigo_arp_api, numero_arp, uasg_id, data_inicio_vigencia, data_fim_vigencia, objeto)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (codigo_arp_api) DO NOTHING
                RETURNING id
            """, (
                arp_uuid,
                codigo_arp_api,
                numero_arp,
                orgao["uasg"],
                data_inicio,
                data_fim,
                template["objeto"]
            ))

            result = cur.fetchone()
            if result:
                arp_id = result[0]
                total_arps += 1

                # Inserir itens da ARP
                for item_idx, item_template in enumerate(template["itens"], 1):
                    # Gerar valor aleatório dentro da faixa
                    valor_unitario = round(random.uniform(
                        item_template["valor_min"],
                        item_template["valor_max"]
                    ), 2)

                    # Gerar quantidade aleatória baseada no tipo de item
                    if valor_unitario > 50000:  # Veículos
                        quantidade = random.randint(1, 5)
                    elif valor_unitario > 1000:  # Equipamentos caros
                        quantidade = random.randint(5, 50)
                    elif valor_unitario > 100:  # Equipamentos médios
                        quantidade = random.randint(10, 200)
                    else:  # Materiais de consumo
                        quantidade = random.randint(100, 5000)

                    item_uuid = str(uuid.uuid4())
                    cur.execute("""
                        INSERT INTO itens_arp (
                            id, arp_id, numero_item, descricao, valor_unitario,
                            quantidade, unidade, marca, search_vector
                        )
                        VALUES (
                            %s, %s, %s, %s, %s, %s, %s, %s,
                            setweight(to_tsvector('portuguese', %s), 'A') ||
                            setweight(to_tsvector('portuguese', %s), 'B')
                        )
                    """, (
                        item_uuid,
                        arp_id,
                        item_idx,
                        item_template["descricao"],
                        valor_unitario,
                        quantidade,
                        item_template["unidade"],
                        item_template["marca"],
                        item_template["descricao"],
                        item_template["marca"]
                    ))
                    total_itens += 1

    conn.commit()
    print(f"   ✅ {total_arps} ARPs inseridas")
    print(f"   ✅ {total_itens} itens inseridos")

    # 3. Verificar dados inseridos
    print("\n📊 Verificando dados inseridos...")
    cur.execute("SELECT COUNT(*) FROM orgaos")
    count_orgaos = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM arps")
    count_arps = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM itens_arp")
    count_itens = cur.fetchone()[0]

    print(f"   📌 Total de órgãos: {count_orgaos}")
    print(f"   📌 Total de ARPs: {count_arps}")
    print(f"   📌 Total de itens: {count_itens}")

    # 4. Testar busca full-text
    print("\n🔍 Testando busca full-text...")
    test_queries = ["notebook", "medicamento", "cadeira", "veículo", "ar condicionado"]

    for query in test_queries:
        cur.execute("""
            SELECT COUNT(*) FROM itens_arp
            WHERE search_vector @@ plainto_tsquery('portuguese', %s)
        """, (query,))
        count = cur.fetchone()[0]
        print(f"   🔎 '{query}': {count} resultados")

    conn.close()
    print("\n✨ População do banco de dados concluída com sucesso!")
    print("\n💡 Dica: Execute o backend e teste a API em http://localhost:8000/buscar?q=notebook")

if __name__ == "__main__":
    populate_database()
