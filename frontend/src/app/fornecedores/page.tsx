'use client'
import { useState } from 'react'
import Link from 'next/link'
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import {
    Home,
    Search,
    Building2,
    FileText,
    DollarSign,
    TrendingUp,
    ExternalLink
} from "lucide-react"

interface Supplier {
    nome_fornecedor: string
    cnpj_fornecedor: string | null
    contract_count: number
    total_value: number
    avg_value: number
}

export default function FornecedoresPage() {
    const [query, setQuery] = useState('')
    const [suppliers, setSuppliers] = useState<Supplier[]>([])
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState<string | null>(null)
    const [searched, setSearched] = useState(false)

    const handleSearch = async () => {
        if (!query.trim()) return

        try {
            setLoading(true)
            setError(null)
            setSearched(true)
            const res = await fetch(
                `http://localhost:8000/fornecedores?q=${encodeURIComponent(query)}&limit=50`
            )
            if (res.ok) {
                const data = await res.json()
                setSuppliers(data)
            } else {
                setError('Erro ao buscar fornecedores')
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
            currency: 'BRL',
            notation: 'compact',
            compactDisplay: 'short'
        }).format(value)
    }

    const formatCNPJ = (cnpj: string) => {
        // Format CNPJ: 00.000.000/0000-00
        const cleaned = cnpj.replace(/\D/g, '')
        if (cleaned.length !== 14) return cnpj
        return cleaned.replace(/(\d{2})(\d{3})(\d{3})(\d{4})(\d{2})/, '$1.$2.$3/$4-$5')
    }

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
                <div className="mb-8">
                    <h1 className="text-4xl font-bold mb-2 flex items-center gap-3">
                        <Building2 className="text-purple-600" size={40} />
                        Diretório de Fornecedores
                    </h1>
                    <p className="text-gray-600">Busque fornecedores e veja suas estatísticas de contratos</p>
                </div>

                {/* Search Bar */}
                <Card className="mb-8 shadow-lg">
                    <CardContent className="p-6">
                        <div className="flex gap-4">
                            <div className="flex-1 relative">
                                <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={20} />
                                <Input
                                    placeholder="Buscar por nome do fornecedor ou CNPJ..."
                                    value={query}
                                    onChange={(e) => setQuery(e.target.value)}
                                    onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
                                    className="pl-10 h-12 text-lg"
                                />
                            </div>
                            <Button
                                onClick={handleSearch}
                                disabled={loading || !query.trim()}
                                size="lg"
                                className="bg-gradient-primary text-white px-8"
                            >
                                {loading ? 'Buscando...' : 'Buscar'}
                            </Button>
                        </div>
                    </CardContent>
                </Card>

                {/* Loading State */}
                {loading && (
                    <div className="grid gap-4 md:grid-cols-2">
                        {[1, 2, 3, 4].map(i => (
                            <Card key={i} className="animate-pulse">
                                <CardHeader>
                                    <div className="h-5 bg-gray-200 rounded w-2/3"></div>
                                </CardHeader>
                                <CardContent>
                                    <div className="space-y-2">
                                        <div className="h-4 bg-gray-200 rounded w-1/2"></div>
                                        <div className="h-4 bg-gray-200 rounded w-1/3"></div>
                                    </div>
                                </CardContent>
                            </Card>
                        ))}
                    </div>
                )}

                {/* Error State */}
                {error && (
                    <Card className="p-8 text-center border-red-200 bg-red-50">
                        <p className="text-red-600 font-medium">{error}</p>
                    </Card>
                )}

                {/* Results */}
                {suppliers.length > 0 && (
                    <>
                        <div className="mb-6">
                            <p className="text-gray-600">
                                <span className="font-semibold text-purple-600">{suppliers.length}</span> fornecedores encontrados
                            </p>
                        </div>

                        <div className="grid gap-4 md:grid-cols-2">
                            {suppliers.map((supplier, idx) => (
                                <Card key={idx} className="hover-lift border-l-4 border-l-purple-500">
                                    <CardHeader>
                                        <CardTitle className="text-lg">
                                            {supplier.nome_fornecedor}
                                        </CardTitle>
                                        {supplier.cnpj_fornecedor && (
                                            <p className="text-sm text-gray-500 font-mono">
                                                CNPJ: {formatCNPJ(supplier.cnpj_fornecedor)}
                                            </p>
                                        )}
                                    </CardHeader>
                                    <CardContent>
                                        <div className="grid grid-cols-3 gap-4 mb-4">
                                            <div className="text-center p-3 bg-purple-50 rounded-lg">
                                                <div className="flex items-center justify-center gap-1 text-purple-600 mb-1">
                                                    <FileText size={16} />
                                                </div>
                                                <div className="text-2xl font-bold text-purple-600">
                                                    {supplier.contract_count}
                                                </div>
                                                <div className="text-xs text-gray-600">Contratos</div>
                                            </div>

                                            <div className="text-center p-3 bg-green-50 rounded-lg">
                                                <div className="flex items-center justify-center gap-1 text-green-600 mb-1">
                                                    <DollarSign size={16} />
                                                </div>
                                                <div className="text-lg font-bold text-green-600">
                                                    {formatCurrency(supplier.total_value)}
                                                </div>
                                                <div className="text-xs text-gray-600">Total</div>
                                            </div>

                                            <div className="text-center p-3 bg-blue-50 rounded-lg">
                                                <div className="flex items-center justify-center gap-1 text-blue-600 mb-1">
                                                    <TrendingUp size={16} />
                                                </div>
                                                <div className="text-lg font-bold text-blue-600">
                                                    {formatCurrency(supplier.avg_value)}
                                                </div>
                                                <div className="text-xs text-gray-600">Média</div>
                                            </div>
                                        </div>

                                        <Link href={`/busca?fornecedor=${encodeURIComponent(supplier.nome_fornecedor)}`}>
                                            <Button variant="outline" size="sm" className="w-full gap-2">
                                                <ExternalLink size={14} />
                                                Ver ARPs deste Fornecedor
                                            </Button>
                                        </Link>
                                    </CardContent>
                                </Card>
                            ))}
                        </div>
                    </>
                )}

                {/* Empty State */}
                {searched && !loading && suppliers.length === 0 && !error && (
                    <Card className="p-12 text-center">
                        <Building2 className="mx-auto text-gray-300 mb-4" size={64} />
                        <h3 className="text-2xl font-bold mb-2">Nenhum fornecedor encontrado</h3>
                        <p className="text-gray-600 mb-6">
                            Tente buscar com um nome diferente ou CNPJ completo
                        </p>
                    </Card>
                )}

                {/* Initial State */}
                {!searched && !loading && (
                    <Card className="p-12 text-center">
                        <Building2 className="mx-auto text-purple-600 mb-4" size={64} />
                        <h3 className="text-2xl font-bold mb-2">Buscar Fornecedores</h3>
                        <p className="text-gray-600 mb-6">
                            Digite o nome ou CNPJ de um fornecedor para ver suas estatísticas e contratos
                        </p>
                        <div className="flex flex-col gap-3 max-w-md mx-auto">
                            <div className="flex items-start gap-3 text-left p-3 bg-purple-50 rounded-lg">
                                <Badge className="bg-purple-600">Dica</Badge>
                                <p className="text-sm text-gray-700">
                                    Você pode buscar por parte do nome. Ex: "Tecnologia", "Comércio", "Serviços"
                                </p>
                            </div>
                            <div className="flex items-start gap-3 text-left p-3 bg-blue-50 rounded-lg">
                                <Badge className="bg-blue-600">Info</Badge>
                                <p className="text-sm text-gray-700">
                                    Para CNPJ, digite apenas os números (com ou sem formatação)
                                </p>
                            </div>
                        </div>
                    </Card>
                )}

                {/* Popular Searches */}
                {!searched && !loading && (
                    <Card className="mt-8">
                        <CardHeader>
                            <CardTitle className="text-lg">Sugestões de Busca</CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div className="flex flex-wrap gap-2">
                                {[
                                    'Tecnologia',
                                    'Comércio',
                                    'Serviços',
                                    'Distribuidora',
                                    'Indústria',
                                    'Informática',
                                    'Material',
                                    'Equipamentos'
                                ].map(term => (
                                    <Button
                                        key={term}
                                        variant="outline"
                                        size="sm"
                                        onClick={() => {
                                            setQuery(term)
                                            setTimeout(() => handleSearch(), 100)
                                        }}
                                    >
                                        {term}
                                    </Button>
                                ))}
                            </div>
                        </CardContent>
                    </Card>
                )}
            </div>
        </div>
    )
}
