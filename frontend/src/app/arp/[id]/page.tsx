'use client'
import { useEffect, useState } from 'react'
import { useParams } from 'next/navigation'
import Link from 'next/link'
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import {
    Home,
    Building2,
    Calendar,
    DollarSign,
    Package,
    ExternalLink,
    Download,
    FileText,
    User,
    MapPin,
    TrendingDown,
    ArrowLeft
} from "lucide-react"

interface Item {
    codigo_item: string
    descricao: string
    valor_unitario: number
    quantidade: number
    unidade: string
    marca: string | null
    modelo: string | null
    nome_fornecedor: string | null
    cnpj_fornecedor: string | null
}

interface ARPDetail {
    arp: {
        id: string
        numero_arp: string
        numero_compra: string
        ano_compra: number
        objeto: string
        valor_total: number
        quantidade_itens: number
        situacao: string
        modalidade: string
        nome_modalidade: string
        data_inicio_vigencia: string
        data_fim_vigencia: string
        data_assinatura: string
        link_ata_pncp: string | null
        link_compra_pncp: string | null
    }
    orgao: {
        uasg: string
        nome: string
        uf: string
        municipio: string | null
    }
    itens: Item[]
}

export default function ARPDetailPage() {
    const params = useParams()
    const arpId = params.id as string

    const [data, setData] = useState<ARPDetail | null>(null)
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)
    const [sortField, setSortField] = useState<'descricao' | 'valor_unitario'>('descricao')
    const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('asc')

    useEffect(() => {
        if (arpId) {
            fetchARPDetails()
        }
    }, [arpId])

    const fetchARPDetails = async () => {
        try {
            setLoading(true)
            const res = await fetch(`http://localhost:8000/arp/${arpId}`)
            if (res.ok) {
                const responseData = await res.json()
                setData(responseData)
            } else {
                setError('ARP não encontrada')
            }
        } catch (err) {
            setError('Erro de conexão com o servidor')
            console.error(err)
        } finally {
            setLoading(false)
        }
    }

    const formatCurrency = (value: number) => {
        return new Intl.NumberFormat('pt-BR', {
            style: 'currency',
            currency: 'BRL'
        }).format(value)
    }

    const formatDate = (dateString: string) => {
        return new Date(dateString).toLocaleDateString('pt-BR')
    }

    const getSortedItems = () => {
        if (!data) return []
        const items = [...data.itens]
        items.sort((a, b) => {
            const aVal = a[sortField]
            const bVal = b[sortField]
            if (typeof aVal === 'string' && typeof bVal === 'string') {
                return sortDirection === 'asc'
                    ? aVal.localeCompare(bVal)
                    : bVal.localeCompare(aVal)
            }
            if (typeof aVal === 'number' && typeof bVal === 'number') {
                return sortDirection === 'asc' ? aVal - bVal : bVal - aVal
            }
            return 0
        })
        return items
    }

    const toggleSort = (field: 'descricao' | 'valor_unitario') => {
        if (sortField === field) {
            setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc')
        } else {
            setSortField(field)
            setSortDirection('asc')
        }
    }

    const isExpired = data ? new Date(data.arp.data_fim_vigencia) < new Date() : false

    return (
        <div className="min-h-screen bg-gradient-to-br from-purple-50 via-white to-blue-50">
            {/* Header */}
            <header className="bg-white/80 backdrop-blur-md border-b sticky top-0 z-40">
                <div className="container mx-auto px-6 h-16 flex items-center justify-between">
                    <Link href="/" className="font-bold text-2xl flex items-center gap-2">
                        <Home size={24} className="text-purple-600" />
                        <span className="gradient-text">AtaHub</span>
                    </Link>
                    <nav className="flex gap-4">
                        <Link href="/busca">
                            <Button variant="ghost">Buscar ARPs</Button>
                        </Link>
                        <Link href="/dashboard">
                            <Button variant="ghost">Dashboard</Button>
                        </Link>
                    </nav>
                </div>
            </header>

            <div className="container mx-auto p-6 max-w-7xl">
                {/* Breadcrumb */}
                <div className="mb-6">
                    <Link href="/busca" className="text-purple-600 hover:underline flex items-center gap-2">
                        <ArrowLeft size={16} />
                        Voltar para Busca
                    </Link>
                </div>

                {loading && (
                    <div className="space-y-6">
                        <Card className="animate-pulse">
                            <CardHeader>
                                <div className="h-6 bg-gray-200 rounded w-1/3"></div>
                            </CardHeader>
                            <CardContent>
                                <div className="space-y-3">
                                    <div className="h-4 bg-gray-200 rounded w-full"></div>
                                    <div className="h-4 bg-gray-200 rounded w-5/6"></div>
                                </div>
                            </CardContent>
                        </Card>
                    </div>
                )}

                {error && (
                    <Card className="p-8 text-center border-red-200 bg-red-50">
                        <p className="text-red-600 font-medium mb-4">{error}</p>
                        <Link href="/busca">
                            <Button variant="outline">Voltar para Busca</Button>
                        </Link>
                    </Card>
                )}

                {data && (
                    <div className="space-y-6">
                        {/* ARP Header */}
                        <Card className="hover-lift border-l-4 border-l-purple-500">
                            <CardHeader>
                                <div className="flex justify-between items-start">
                                    <div>
                                        <CardTitle className="text-2xl mb-2">{data.arp.numero_arp}</CardTitle>
                                        <div className="flex gap-2 flex-wrap">
                                            <Badge variant={isExpired ? "destructive" : "default"}>
                                                {isExpired ? 'Vencida' : data.arp.situacao}
                                            </Badge>
                                            <Badge variant="outline">{data.orgao.uf}</Badge>
                                            <Badge variant="outline">{data.arp.modalidade}</Badge>
                                        </div>
                                    </div>
                                    <div className="text-right">
                                        <div className="text-3xl font-bold text-green-600">
                                            {formatCurrency(data.arp.valor_total)}
                                        </div>
                                        <div className="text-sm text-gray-500 mt-1">
                                            {data.arp.quantidade_itens} itens
                                        </div>
                                    </div>
                                </div>
                            </CardHeader>
                            <CardContent className="space-y-4">
                                <div>
                                    <h3 className="font-semibold text-gray-700 mb-2 flex items-center gap-2">
                                        <FileText size={18} />
                                        Objeto
                                    </h3>
                                    <p className="text-gray-600">{data.arp.objeto}</p>
                                </div>

                                <div className="grid md:grid-cols-2 gap-6">
                                    <div>
                                        <h3 className="font-semibold text-gray-700 mb-3 flex items-center gap-2">
                                            <Building2 size={18} />
                                            Órgão
                                        </h3>
                                        <div className="space-y-2 text-sm">
                                            <p><span className="font-medium">Nome:</span> {data.orgao.nome}</p>
                                            <p><span className="font-medium">UASG:</span> {data.orgao.uasg}</p>
                                            <p className="flex items-center gap-2">
                                                <MapPin size={14} />
                                                {data.orgao.municipio ? `${data.orgao.municipio} - ` : ''}{data.orgao.uf}
                                            </p>
                                        </div>
                                    </div>

                                    <div>
                                        <h3 className="font-semibold text-gray-700 mb-3 flex items-center gap-2">
                                            <Calendar size={18} />
                                            Vigência
                                        </h3>
                                        <div className="space-y-2 text-sm">
                                            <p><span className="font-medium">Início:</span> {formatDate(data.arp.data_inicio_vigencia)}</p>
                                            <p><span className="font-medium">Fim:</span> {formatDate(data.arp.data_fim_vigencia)}</p>
                                            <p><span className="font-medium">Assinatura:</span> {formatDate(data.arp.data_assinatura)}</p>
                                        </div>
                                    </div>
                                </div>

                                <div className="flex gap-3 pt-4">
                                    {data.arp.link_ata_pncp && (
                                        <a href={data.arp.link_ata_pncp} target="_blank" rel="noopener noreferrer">
                                            <Button variant="outline" size="sm" className="gap-2">
                                                <ExternalLink size={16} />
                                                Ver Ata no PNCP
                                            </Button>
                                        </a>
                                    )}
                                    {data.arp.link_compra_pncp && (
                                        <a href={data.arp.link_compra_pncp} target="_blank" rel="noopener noreferrer">
                                            <Button variant="outline" size="sm" className="gap-2">
                                                <ExternalLink size={16} />
                                                Ver Compra no PNCP
                                            </Button>
                                        </a>
                                    )}
                                </div>
                            </CardContent>
                        </Card>

                        {/* Items Table */}
                        <Card className="hover-lift">
                            <CardHeader>
                                <div className="flex justify-between items-center">
                                    <CardTitle className="flex items-center gap-2">
                                        <Package size={20} />
                                        Itens da ARP ({data.itens.length})
                                    </CardTitle>
                                    <Button variant="outline" size="sm" className="gap-2">
                                        <Download size={16} />
                                        Exportar
                                    </Button>
                                </div>
                            </CardHeader>
                            <CardContent>
                                <div className="overflow-x-auto">
                                    <table className="w-full">
                                        <thead>
                                            <tr className="border-b">
                                                <th className="text-left p-3 font-semibold text-gray-700">
                                                    <button
                                                        onClick={() => toggleSort('descricao')}
                                                        className="flex items-center gap-1 hover:text-purple-600"
                                                    >
                                                        Descrição
                                                        {sortField === 'descricao' && (
                                                            <span>{sortDirection === 'asc' ? '↑' : '↓'}</span>
                                                        )}
                                                    </button>
                                                </th>
                                                <th className="text-left p-3 font-semibold text-gray-700">Marca/Modelo</th>
                                                <th className="text-left p-3 font-semibold text-gray-700">Fornecedor</th>
                                                <th className="text-right p-3 font-semibold text-gray-700">Quantidade</th>
                                                <th className="text-right p-3 font-semibold text-gray-700">
                                                    <button
                                                        onClick={() => toggleSort('valor_unitario')}
                                                        className="flex items-center gap-1 hover:text-purple-600 ml-auto"
                                                    >
                                                        Valor Unit.
                                                        {sortField === 'valor_unitario' && (
                                                            <span>{sortDirection === 'asc' ? '↑' : '↓'}</span>
                                                        )}
                                                    </button>
                                                </th>
                                                <th className="text-right p-3 font-semibold text-gray-700">Valor Total</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {getSortedItems().map((item, idx) => (
                                                <tr key={idx} className="border-b hover:bg-purple-50 transition">
                                                    <td className="p-3">
                                                        <div className="font-medium text-gray-900">{item.descricao}</div>
                                                        {item.codigo_item && (
                                                            <div className="text-xs text-gray-500">Cód: {item.codigo_item}</div>
                                                        )}
                                                    </td>
                                                    <td className="p-3 text-sm text-gray-600">
                                                        {item.marca && <div>{item.marca}</div>}
                                                        {item.modelo && <div className="text-xs">{item.modelo}</div>}
                                                    </td>
                                                    <td className="p-3 text-sm text-gray-600">
                                                        {item.nome_fornecedor && <div>{item.nome_fornecedor}</div>}
                                                        {item.cnpj_fornecedor && (
                                                            <div className="text-xs">{item.cnpj_fornecedor}</div>
                                                        )}
                                                    </td>
                                                    <td className="p-3 text-right text-sm">
                                                        {item.quantidade} {item.unidade}
                                                    </td>
                                                    <td className="p-3 text-right font-semibold text-green-600">
                                                        {formatCurrency(item.valor_unitario)}
                                                    </td>
                                                    <td className="p-3 text-right font-bold text-gray-900">
                                                        {formatCurrency(item.valor_unitario * item.quantidade)}
                                                    </td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </div>
                            </CardContent>
                        </Card>

                        {/* Additional Actions */}
                        <div className="flex gap-4 justify-center">
                            <Link href={`/comparar?q=${encodeURIComponent(data.itens[0]?.descricao || '')}`}>
                                <Button className="gap-2 bg-gradient-primary text-white">
                                    <TrendingDown size={18} />
                                    Comparar Preços
                                </Button>
                            </Link>
                            <Link href="/busca">
                                <Button variant="outline" className="gap-2">
                                    Buscar Outras ARPs
                                </Button>
                            </Link>
                        </div>
                    </div>
                )}
            </div>
        </div>
    )
}
