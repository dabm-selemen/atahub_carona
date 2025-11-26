"""
Data Transformers

Transform API responses to database-ready format.
Maps API fields to database schema fields with validation and type conversion.
"""

from typing import Dict, Any, Optional
from datetime import date, datetime
from decimal import Decimal
import uuid
import structlog

from utils.date_utils import parse_api_date, parse_api_datetime

logger = structlog.get_logger(__name__)


def safe_get(data: Dict[str, Any], key: str, default=None):
    """Safely get value from dict, returning default if None or missing"""
    value = data.get(key)
    return value if value is not None else default


def safe_int(value: Any) -> Optional[int]:
    """Safely convert to int"""
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (ValueError, TypeError):
        return None


def safe_decimal(value: Any, precision: int = 2) -> Optional[Decimal]:
    """Safely convert to Decimal"""
    if value is None or value == "":
        return None
    try:
        return Decimal(str(value)).quantize(Decimal(10) ** -precision)
    except (ValueError, TypeError):
        return None


def safe_bool(value: Any) -> bool:
    """Safely convert to bool"""
    if value is None:
        return False
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in ("true", "1", "yes", "sim")
    return bool(value)


def safe_date(value: Any) -> Optional[date]:
    """Safely parse date"""
    if not value:
        return None
    try:
        if isinstance(value, date):
            return value
        return parse_api_date(str(value))
    except ValueError:
        logger.warning("date_parse_failed", value=value)
        return None


def safe_datetime(value: Any) -> Optional[datetime]:
    """Safely parse datetime"""
    if not value:
        return None
    try:
        if isinstance(value, datetime):
            return value
        return parse_api_datetime(str(value))
    except ValueError:
        logger.warning("datetime_parse_failed", value=value)
        return None


# ============================================================================
# ORGAO TRANSFORMER
# ============================================================================

def transform_orgao_from_api(api_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transform orgao/agency data from API to database format

    Args:
        api_data: Raw API response for an ARP (contains orgao data)

    Returns:
        Dictionary ready for database insertion

    API Fields:
        - codigoUnidadeGerenciadora → uasg
        - nomeUnidadeGerenciadora → nome
        - (uf not provided in API, default to empty)
    """
    return {
        "uasg": str(safe_get(api_data, "codigoUnidadeGerenciadora", "")),
        "nome": safe_get(api_data, "nomeUnidadeGerenciadora"),
        "uf": safe_get(api_data, "uf", ""),  # Usually not in ARP API response
    }


# ============================================================================
# ARP TRANSFORMER
# ============================================================================

def transform_arp_from_api(api_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transform ARP data from API to database format

    Args:
        api_data: Raw API response for an ARP

    Returns:
        Dictionary ready for database insertion

    API Fields Mapping:
        numeroControlePncpAta → codigo_arp_api (UNIQUE KEY)
        numeroAtaRegistroPreco → numero_arp
        numeroCompra → numero_compra (CRITICAL!)
        anoCompra → ano_compra
        codigoUnidadeGerenciadora → uasg_id
        dataVigenciaInicial → data_inicio_vigencia
        dataVigenciaFinal → data_fim_vigencia
        dataAssinatura → data_assinatura
        dataHoraAtualizacao → data_atualizacao_pncp
        objeto → objeto
        valorTotal → valor_total
        quantidadeItens → quantidade_itens
        statusAta → situacao
        codigoModalidadeCompra → modalidade
        nomeModalidadeCompra → nome_modalidade
        numeroControlePncpCompra → numero_controle_pncp_compra
        numeroControlePncpAta → numero_controle_pncp_ata
        linkAtaPNCP → link_ata_pncp
        linkCompraPNCP → link_compra_pncp
        idCompra → id_compra
        codigoOrgao → codigo_orgao
        nomeOrgao → nome_orgao
        ataExcluido → ata_excluido
    """
    return {
        # Primary identification
        "id": str(uuid.uuid4()),
        "codigo_arp_api": str(safe_get(api_data, "numeroControlePncpAta", "")),
        "numero_arp": safe_get(api_data, "numeroAtaRegistroPreco"),
        "numero_compra": safe_get(api_data, "numeroCompra"),  # CRITICAL!
        "ano_compra": safe_int(safe_get(api_data, "anoCompra")),

        # Organization
        "uasg_id": str(safe_get(api_data, "codigoUnidadeGerenciadora", "")),

        # Dates
        "data_inicio_vigencia": safe_date(safe_get(api_data, "dataVigenciaInicial")),
        "data_fim_vigencia": safe_date(safe_get(api_data, "dataVigenciaFinal")),
        "data_assinatura": safe_date(safe_get(api_data, "dataAssinatura")),
        "data_atualizacao_pncp": safe_datetime(safe_get(api_data, "dataHoraAtualizacao")),

        # Content
        "objeto": safe_get(api_data, "objeto"),

        # Financial
        "valor_total": safe_decimal(safe_get(api_data, "valorTotal"), precision=2),
        "quantidade_itens": safe_int(safe_get(api_data, "quantidadeItens")),

        # Status and classification
        "situacao": safe_get(api_data, "statusAta"),
        "modalidade": safe_get(api_data, "codigoModalidadeCompra"),
        "nome_modalidade": safe_get(api_data, "nomeModalidadeCompra"),

        # PNCP identifiers
        "numero_controle_pncp_compra": safe_get(api_data, "numeroControlePncpCompra"),
        "numero_controle_pncp_ata": safe_get(api_data, "numeroControlePncpAta"),
        "link_ata_pncp": safe_get(api_data, "linkAtaPNCP"),
        "link_compra_pncp": safe_get(api_data, "linkCompraPNCP"),
        "id_compra": safe_get(api_data, "idCompra"),

        # Additional metadata
        "codigo_orgao": str(safe_get(api_data, "codigoOrgao", "")) if safe_get(api_data, "codigoOrgao") else None,
        "nome_orgao": safe_get(api_data, "nomeOrgao") or safe_get(api_data, "nomeUnidadeGerenciadora"),

        # Soft delete
        "ata_excluido": safe_bool(safe_get(api_data, "ataExcluido", False)),
    }


# ============================================================================
# ITEM TRANSFORMER
# ============================================================================

def transform_item_from_api(
    api_data: Dict[str, Any],
    arp_id: str
) -> Dict[str, Any]:
    """
    Transform ARP item data from API to database format

    Args:
        api_data: Raw API response for an item
        arp_id: UUID of parent ARP

    Returns:
        Dictionary ready for database insertion

    API Fields Mapping:
        numeroItem → numero_item
        codigoItem → codigo_item
        descricaoItem → descricao
        tipoItem → tipo_item
        valorUnitario → valor_unitario
        valorTotal → valor_total
        quantidadeHomologada → quantidade
        unidadeMedida → unidade
        marca → marca
        modelo → modelo
        classificacaoFornecedor → classificacao_fornecedor
        niFornecedor → cnpj_fornecedor
        nomeRazaoSocialFornecedor → nome_fornecedor
        situacaoSicaf → situacao_sicaf
        codigoPdm → codigo_pdm
        nomePdm → nome_pdm
        quantidadeEmpenhada → quantidade_empenhada
        percentualMaiorDesconto → percentual_maior_desconto
        maximoAdesao → maximo_adesao
        itemExcluido → item_excluido
    """
    return {
        # Primary identification
        "id": str(uuid.uuid4()),
        "arp_id": arp_id,
        "numero_item": safe_int(safe_get(api_data, "numeroItem")),
        "codigo_item": safe_get(api_data, "codigoItem"),

        # Description
        "descricao": safe_get(api_data, "descricaoItem"),
        "tipo_item": safe_get(api_data, "tipoItem"),

        # Pricing and quantity
        "valor_unitario": safe_decimal(safe_get(api_data, "valorUnitario"), precision=4),
        "valor_total": safe_decimal(safe_get(api_data, "valorTotal"), precision=2),
        "quantidade": safe_decimal(safe_get(api_data, "quantidadeHomologadaVencedor") or safe_get(api_data, "quantidadeHomologada"), precision=4),
        "unidade": safe_get(api_data, "unidadeMedida"),

        # Product details
        "marca": safe_get(api_data, "marca"),
        "modelo": safe_get(api_data, "modelo"),

        # Supplier information
        "classificacao_fornecedor": safe_get(api_data, "classificacaoFornecedor"),
        "cnpj_fornecedor": safe_get(api_data, "niFornecedor"),
        "nome_fornecedor": safe_get(api_data, "nomeRazaoSocialFornecedor"),
        "situacao_sicaf": safe_get(api_data, "situacaoSicaf"),

        # Classification
        "codigo_pdm": safe_int(safe_get(api_data, "codigoPdm")),
        "nome_pdm": safe_get(api_data, "nomePdm"),

        # Additional metrics
        "quantidade_empenhada": safe_decimal(safe_get(api_data, "quantidadeEmpenhada"), precision=4),
        "percentual_maior_desconto": safe_decimal(safe_get(api_data, "percentualMaiorDesconto"), precision=2),
        "maximo_adesao": safe_decimal(safe_get(api_data, "maximoAdesao"), precision=2),

        # Soft delete
        "item_excluido": safe_bool(safe_get(api_data, "itemExcluido", False)),
    }


# ============================================================================
# BATCH TRANSFORMERS
# ============================================================================

def transform_arps_batch(api_arps: list) -> tuple[list, list]:
    """
    Transform a batch of ARPs and extract orgaos

    Args:
        api_arps: List of ARP dictionaries from API

    Returns:
        Tuple of (transformed_arps, unique_orgaos)
    """
    transformed_arps = []
    orgaos_dict = {}  # Use dict to deduplicate by UASG

    for api_arp in api_arps:
        try:
            # Transform ARP
            arp = transform_arp_from_api(api_arp)
            transformed_arps.append(arp)

            # Extract orgao
            orgao = transform_orgao_from_api(api_arp)
            orgaos_dict[orgao["uasg"]] = orgao

        except Exception as e:
            logger.error(
                "transform_arp_failed",
                error=str(e),
                arp=api_arp.get("numeroControlePncpAta")
            )
            continue

    unique_orgaos = list(orgaos_dict.values())

    logger.info(
        "batch_transform_complete",
        arps_count=len(transformed_arps),
        orgaos_count=len(unique_orgaos)
    )

    return transformed_arps, unique_orgaos


def transform_items_batch(api_items: list, arp_id: str) -> list:
    """
    Transform a batch of items for a specific ARP

    Args:
        api_items: List of item dictionaries from API
        arp_id: UUID of parent ARP

    Returns:
        List of transformed items
    """
    transformed_items = []

    for api_item in api_items:
        try:
            item = transform_item_from_api(api_item, arp_id)
            transformed_items.append(item)
        except Exception as e:
            logger.error(
                "transform_item_failed",
                error=str(e),
                item=api_item.get("numeroItem")
            )
            continue

    logger.debug(
        "items_batch_transform_complete",
        arp_id=arp_id,
        items_count=len(transformed_items)
    )

    return transformed_items


# ============================================================================
# VALIDATION
# ============================================================================

def validate_arp(arp_data: Dict[str, Any]) -> tuple[bool, list[str]]:
    """
    Validate transformed ARP data

    Args:
        arp_data: Transformed ARP dictionary

    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []

    # Required fields
    if not arp_data.get("codigo_arp_api"):
        errors.append("Missing codigo_arp_api")

    if not arp_data.get("numero_compra"):
        errors.append("Missing numero_compra (CRITICAL)")

    if not arp_data.get("uasg_id"):
        errors.append("Missing uasg_id")

    # Date validation
    if arp_data.get("data_inicio_vigencia") and arp_data.get("data_fim_vigencia"):
        if arp_data["data_inicio_vigencia"] > arp_data["data_fim_vigencia"]:
            errors.append("data_inicio_vigencia > data_fim_vigencia")

    is_valid = len(errors) == 0

    if not is_valid:
        logger.warning(
            "arp_validation_failed",
            arp=arp_data.get("numero_arp"),
            errors=errors
        )

    return is_valid, errors


def validate_item(item_data: Dict[str, Any]) -> tuple[bool, list[str]]:
    """
    Validate transformed item data

    Args:
        item_data: Transformed item dictionary

    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []

    # Required fields
    if not item_data.get("arp_id"):
        errors.append("Missing arp_id")

    if item_data.get("numero_item") is None:
        errors.append("Missing numero_item")

    is_valid = len(errors) == 0

    if not is_valid:
        logger.warning(
            "item_validation_failed",
            item=item_data.get("numero_item"),
            errors=errors
        )

    return is_valid, errors


# ============================================================================
# TESTING
# ============================================================================

if __name__ == "__main__":
    # Test transformers with sample data
    print("=== Transformer Tests ===\n")

    # Sample API data (from user's example)
    sample_arp = {
        "numeroAtaRegistroPreco": "00421/2023",
        "codigoUnidadeGerenciadora": "155008",
        "nomeUnidadeGerenciadora": "HOSPITAL UNIVERSITARIO DO PIAUI",
        "codigoOrgao": "26443",
        "nomeOrgao": "EMPRESA BRASILEIRA DE SERVICOS HOSPITALARES",
        "linkAtaPNCP": "https://pncp.gov.br/app/atas/15126437000143/2023/723/1",
        "linkCompraPNCP": "https://pncp.gov.br/app/editais/15126437000143/2023/000723",
        "numeroCompra": "00057",
        "anoCompra": "2023",
        "codigoModalidadeCompra": "05",
        "nomeModalidadeCompra": "Pregão",
        "dataAssinatura": "2023-07-25T00:00:00",
        "dataVigenciaInicial": "2023-07-26",
        "dataVigenciaFinal": "2024-07-25",
        "valorTotal": 63120,
        "statusAta": "Ata de Registro de Preços",
        "objeto": "Registro de preços para a eventual aquisição...",
        "quantidadeItens": 6,
        "dataHoraAtualizacao": "2023-07-27T10:11:58",
        "ataExcluido": False,
        "numeroControlePncpAta": "15126437000143-1-000723/2023-000001",
        "numeroControlePncpCompra": "15126437000143-1-000723/2023",
        "idCompra": "15500805000572023"
    }

    # Test ARP transformation
    print("1. Transform ARP:")
    arp = transform_arp_from_api(sample_arp)
    print(f"   ✅ numero_arp: {arp['numero_arp']}")
    print(f"   ✅ numero_compra: {arp['numero_compra']}")
    print(f"   ✅ uasg_id: {arp['uasg_id']}")

    # Test validation
    print("\n2. Validate ARP:")
    is_valid, errors = validate_arp(arp)
    print(f"   {'✅' if is_valid else '❌'} Valid: {is_valid}")
    if errors:
        print(f"   Errors: {errors}")

    print("\n✅ Transformer tests completed")
