'use client'
import { useState } from 'react'
import Link from 'next/link'
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import {
    Search,
    Filter,
    Download,
    TrendingDown,
    Home,
    Building2,
    Calendar,
    DollarSign,
    MapPin,
    Package
} from "lucide-react"

// Tipagem
interface SearchResult {
    id_arp: string;
    numero_arp: string;
    orgao_nome: string;
    uf: string;
    vigencia_fim: string;
    vigencia_inicio: string;
    item: {
        descricao: string;
        valor_unitario: number;
        marca: string;
        quantidade: number;
        modelo?: string;
        unidade?: string;
        fornecedor?: string;
    }
}

export default function BuscaPage() {
    const [query, setQuery] = useState('')
    const [results, setResults] = useState<SearchResult[]>([])
    const [loading, setLoading] = useState(false)

    // Filters
    const [selectedUFs, setSelectedUFs] = useState<string[]>([])
    const [minPrice, setMinPrice] = useState('')
    const [maxPrice, setMaxPrice] = useState('')
    const [sortBy, setSortBy] = useState('relevance')
    const [showFilters, setShowFilters] = useState(true)

    const estados = ['AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA', 'MT', 'MS', 'MG', 'PA', 'PB', 'PR', 'PE', 'PI', 'RJ', 'RN', 'RS', 'RO', 'RR', 'SC', 'SP', 'SE', 'TO']

    const handleSearch = async () => {
        if (!query && selectedUFs.length === 0) return;
        setLoading(true);
        try {
            // Build query params
            const params = new URLSearchParams();
            if (query) params.append('q', query);
            if (selectedUFs.length > 0) params.append('ufs', selectedUFs.join(','));
            if (minPrice) params.append('min_price', minPrice);
            if (maxPrice) params.append('max_price', maxPrice);
            params.append('sort_by', sortBy);

            const res = await fetch(`http://localhost:8000/buscar?${params.toString()}`);
            if (res.ok) {
                const data = await res.json();
                setResults(data);
            }
        } catch (err) {
            console.error(err);
        } finally {
            setLoading(false);
        }
    }

    const handleExport = async () => {
        const params = new URLSearchParams();
        if (query) params.append('q', query);
        if (selectedUFs.length > 0) params.append('ufs', selectedUFs.join(','));
        if (minPrice) params.append('min_price', minPrice);
        if (maxPrice) params.append('max_price', maxPrice);

        window.open(`http://localhost:8000/exportar?${params.toString()}`, '_blank');
    }

    const toggleUF = (uf: string) => {
        setSelectedUFs(prev =>
            prev.includes(uf) ? prev.filter(u => u !== uf) : [...prev, uf]
        )
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
                        <Link href="/dashboard">
                            <Button variant="ghost">Dashboard</Button>
                        </Link>
                        <Link href="/fornecedores">
                            <Button variant="ghost">Fornecedores</Button>
                        </Link>
                    </nav>
                </div>
            </header>

            <div className="container mx-auto p-6 max-w-7xl">
                <div className="mb-8">
                    <h1 className="text-4xl font-bold mb-2">Buscar Atas de Registro de Preços</h1>
                    <p className="text-gray-600">Encontre as melhores oportunidades de carona com filtros avançados</p>
                </div>

                <div className="grid lg:grid-cols-[280px_1fr] gap-6">
                    {/* Filters Sidebar */}
                    <div className="space-y-4">
                        <Card className="sticky top-20">
                            <CardHeader className="pb-3">
                                <div className="flex items-center justify-between">
                                    <CardTitle className="text-lg flex items-center gap-2">
                                        <Filter size={18} />
                                        Filtros
                                    </CardTitle>
                                    <Button
                                        variant="ghost"
                                        size="sm"
                                        onClick={() => setShowFilters(!showFilters)}
                                    >
                                        {showFilters ? 'Ocultar' : 'Mostrar'}
                                    </Button>
                                </div>
                            </CardHeader>
                            {showFilters && (
                                <CardContent className="space-y-6">
                                    {/* States Filter */}
                                    <div>
                                        <label className="font-medium text-sm mb-2 block flex items-center gap-2">
                                            <MapPin size={16} />
                                            Estados
                                        </label>
                                        <div className="grid grid-cols-3 gap-2 max-h-64 overflow-y-auto p-2 border rounded-lg">
                                            {estados.map(uf => (
                                                <button
                                                    key={uf}
                                                    onClick={() => toggleUF(uf)}
                                                    className={`px-2 py-1 text-xs rounded transition ${selectedUFs.includes(uf)
                                                            ? 'bg-purple-600 text-white'
                                                            : 'bg-gray-100 hover:bg-gray-200'
                                                        }`}
                                                >
                                                    {uf}
                                                </button>
                                            ))}
                                        </div>
                                        {selectedUFs.length > 0 && (
                                            <button
                                                onClick={() => setSelectedUFs([])}
                                                className="text-xs text-purple-600 mt-2 hover:underline"
                                            >
                                                Limpar ({selectedUFs.length})
                                            </button>
                                        )}
                                    </div>

                                    {/* Price Range Filter */}
                                    <div>
                                        <label className="font-medium text-sm mb-2 block flex items-center gap-2">
                                            <DollarSign size={16} />
                                            Faixa de Preço
                                        </label>
                                        <div className="space-y-2">
                                            <Input
                                                type="number"
                                                placeholder="Mínimo (R$)"
                                                value={minPrice}
                                                onChange={(e) => setMinPrice(e.target.value)}
                                                className="text-sm"
                                            />
                                            <Input
                                                type="number"
                                                placeholder="Máximo (R$)"
                                                value={maxPrice}
                                                onChange={(e) => setMaxPrice(e.target.value)}
                                                className="text-sm"
                                            />
                                        </div>
                                    </div>

                                    {/* Sort */}
                                    <div>
                                        <label className="font-medium text-sm mb-2 block">Ordenar Por</label>
                                        <select
                                            value={sortBy}
                                            onChange={(e) => setSortBy(e.target.value)}
                                            className="w-full p-2 border rounded-lg text-sm"
                                        >
                                            <option value="relevance">Relevância</option>
                                            <option value="price_asc">Menor Preço</option>
                                            <option value="price_desc">Maior Preço</option>
                                            <option value="date_asc">Vencimento (mais cedo)</option>
                                            <option value="date_desc">Vencimento (mais tarde)</option>
                                        </select>
                                    </div>

                                    {/* Apply Filters */}
                                    <Button
                                        onClick={handleSearch}
                                        className="w-full bg-gradient-primary text-white"
                                        disabled={loading}
                                    >
                                        {loading ? 'Buscando...' : 'Aplicar Filtros'}
                                    </Button>
                                </CardContent>
                            )}
                        </Card>
                    </div>

                    {/* Main Content */}
                    <div className="space-y-6">
                        {/* Search Bar */}
                        <Card className="shadow-lg">
                            <CardContent className="p-6">
                                <div className="flex gap-4">
                                    <div className="flex-1 relative">
                                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={20} />
                                        <Input
                                            placeholder="Ex: Notebook i7, Cadeira Giratória, Material de Escritório..."
                                            value={query}
                                            onChange={(e) => setQuery(e.target.value)}
                                            onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
                                            className="pl-10 h-12 text-lg"
                                        />
                                    </div>
                                    <Button
                                        onClick={handleSearch}
                                        disabled={loading}
                                        size="lg"
                                        className="bg-gradient-primary text-white px-8"
                                    >
                                        {loading ? 'Buscando...' : 'Buscar'}
                                    </Button>
                                </div>
                            </CardContent>
                        </Card>

                        {/* Results Header */}
                        {results.length > 0 && (
                            <div className="flex justify-between items-center">
                                <p className="text-gray-600">
                                    <span className="font-semibold text-purple-600">{results.length}</span> resultados encontrados
                                </p>
                                <div className="flex gap-2">
                                    <Button
                                        variant="outline"
                                        size="sm"
                                        onClick={handleExport}
                                        className="gap-2"
                                    >
                                        <Download size={16} />
                                        Exportar CSV
                                    </Button>
                                    {query && (
                                        <Link href={`/comparar?q=${encodeURIComponent(query)}`}>
                                            <Button
                                                variant="outline"
                                                size="sm"
                                                className="gap-2"
                                            >
                                                <TrendingDown size={16} />
                                                Comparar Preços
                                            </Button>
                                        </Link>
                                    )}
                                </div>
                            </div>
                        )}

                        {/* Results Grid */}
                        <div className="grid gap-4">
                            {results.map((res, idx) => (
                                <Card
                                    key={`${res.id_arp}-${idx}`}
                                    className="hover-lift hover:shadow-lg transition-all duration-300 border-l-4 border-l-purple-500"
                                >
                                    <CardHeader className="pb-3">
                                        <div className="flex justify-between items-start mb-2">
                                            <div className="flex gap-2">
                                                <Badge variant="outline" className="bg-purple-50">
                                                    <MapPin size={12} className="mr-1" />
                                                    {res.uf}
                                                </Badge>
                                                <Badge variant="outline" className="bg-blue-50">
                                                    <Calendar size={12} className="mr-1" />
                                                    Vence: {new Date(res.vigencia_fim).toLocaleDateString('pt-BR')}
                                                </Badge>
                                            </div>
                                        </div>
                                        <CardTitle className="text-lg leading-tight hover:text-purple-600 transition">
                                            <Link href={`/arp/${res.id_arp}`}>
                                                {res.item.descricao}
                                            </Link>
                                        </CardTitle>
                                    </CardHeader>
                                    <CardContent>
                                        <div className="grid md:grid-cols-2 gap-4">
                                            <div className="space-y-2">
                                                <div className="flex items-center gap-2 text-sm text-gray-600">
                                                    <Building2 size={16} />
                                                    <span>{res.orgao_nome}</span>
                                                </div>
                                                {res.item.marca && (
                                                    <div className="flex items-center gap-2 text-sm">
                                                        <Package size={16} className="text-gray-500" />
                                                        <span className="font-medium">Marca:</span> {res.item.marca}
                                                    </div>
                                                )}
                                                {res.item.fornecedor && (
                                                    <div className="text-sm text-gray-600">
                                                        <span className="font-medium">Fornecedor:</span> {res.item.fornecedor}
                                                    </div>
                                                )}
                                            </div>
                                            <div className="flex flex-col items-end justify-between">
                                                <div className="text-right">
                                                    <div className="text-3xl font-bold text-green-600">
                                                        {new Intl.NumberFormat('pt-BR', {
                                                            style: 'currency',
                                                            currency: 'BRL'
                                                        }).format(res.item.valor_unitario)}
                                                    </div>
                                                    <div className="text-sm text-gray-500">
                                                        {res.item.quantidade} {res.item.unidade || 'unidade(s)'}
                                                    </div>
                                                </div>
                                                <Link href={`/arp/${res.id_arp}`}>
                                                    <Button variant="outline" size="sm" className="mt-2">
                                                        Ver Detalhes
                                                    </Button>
                                                </Link>
                                            </div>
                                        </div>
                                    </CardContent>
                                </Card>
                            ))}
                        </div>

                        {/* Empty State */}
                        {results.length === 0 && !loading && (
                            <Card className="p-12 text-center">
                                <div className="max-w-md mx-auto space-y-4">
                                    <div className="w-20 h-20 bg-purple-100 rounded-full flex items-center justify-center mx-auto">
                                        <Search size={40} className="text-purple-600" />
                                    </div>
                                    <h3 className="text-2xl font-bold">Nenhum resultado encontrado</h3>
                                    <p className="text-gray-600">
                                        Tente buscar por termos diferentes ou ajuste os filtros para encontrar mais resultados.
                                    </p>
                                    <div className="pt-4">
                                        <p className="text-sm text-gray-500 mb-2">Exemplos de buscas:</p>
                                        <div className="flex flex-wrap gap-2 justify-center">
                                            {['Notebook', 'Cadeira', 'Impressora', 'Material de Escritório'].map(term => (
                                                <Button
                                                    key={term}
                                                    variant="outline"
                                                    size="sm"
                                                    onClick={() => {
                                                        setQuery(term);
                                                        setTimeout(() => handleSearch(), 100);
                                                    }}
                                                >
                                                    {term}
                                                </Button>
                                            ))}
                                        </div>
                                    </div>
                                </div>
                            </Card>
                        )}

                        {/* Loading State */}
                        {loading && (
                            <div className="grid gap-4">
                                {[1, 2, 3].map(i => (
                                    <Card key={i} className="animate-pulse">
                                        <CardHeader>
                                            <div className="h-4 bg-gray-200 rounded w-3/4"></div>
                                        </CardHeader>
                                        <CardContent>
                                            <div className="space-y-2">
                                                <div className="h-3 bg-gray-200 rounded w-1/2"></div>
                                                <div className="h-3 bg-gray-200 rounded w-2/3"></div>
                                            </div>
                                        </CardContent>
                                    </Card>
                                ))}
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    )
}
