'use client'
import { useEffect, useState } from 'react'
import { useSearchParams } from 'next/navigation'
import Link from 'next/link'
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import {
    BarChart,
    Bar,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer
} from 'recharts'
import {
    Home,
    Search,
    TrendingDown,
    TrendingUp,
    DollarSign,
    Download,
    MapPin,
    Award,
    AlertCircle
} from "lucide-react"

interface ComparisonResult {
    uf: string
    count: number
    min_price: number
    max_price: number
    avg_price: number
    median_price: number
    items: Array<{
        id_arp: string
        numero_arp: string
        orgao_nome: string
        descricao: string
        valor_unitario: number
        marca: string | null
        nome_fornecedor: string | null
    }>
}

interface ComparisonData {
    query: string
    statistics: {
        min_price: number
        max_price: number
        avg_price: number
        median_price: number
        total_results: number
        savings_potential: number
    }
    results_by_state: ComparisonResult[]
}

export default function ComparacaoPage() {
    const searchParams = useSearchParams()
    const initialQuery = searchParams.get('q') || ''

    const [query, setQuery] = useState(initialQuery)
    const [data, setData] = useState<ComparisonData | null>(null)
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState<string | null>(null)

    useEffect(() => {
        if (initialQuery) {
            fetchComparison(initialQuery)
        }
    }, [initialQuery])

    const fetchComparison = async (searchQuery: string) => {
        if (!searchQuery.trim()) return

        try {
            setLoading(true)
            setError(null)
            const res = await fetch(`http://localhost:8000/comparar?q=${encodeURIComponent(searchQuery)}`)
            if (res.ok) {
                const responseData = await res.json()
                setData(responseData)
            } else {
                setError('Erro ao buscar comparação')
            }
        } catch (err) {
            setError('Erro de conexão com o servidor')
            console.error(err)
        } finally {
            setLoading(false)
        }
    }

    const handleSearch = () => {
        fetchComparison(query)
    }

    const formatCurrency = (value: number) => {
        return new Intl.NumberFormat('pt-BR', {
            style: 'currency',
            currency: 'BRL'
        }).format(value)
    }

    const getSavingsPercentage = () => {
        if (!data) return 0
        const { min_price, max_price } = data.statistics
        if (max_price === 0) return 0
        return ((max_price - min_price) / max_price * 100).toFixed(1)
    }

    const chartData = data?.results_by_state.map(state => ({
        uf: state.uf,
        'Menor Preço': state.min_price,
        'Preço Médio': state.avg_price,
        'Maior Preço': state.max_price
    })) || []

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
                        <TrendingDown className="text-purple-600" size={40} />
                        Comparação de Preços
                    </h1>
                    <p className="text-gray-600">Compare preços de itens similares entre diferentes ARPs e estados</p>
                </div>

                {/* Search Bar */}
                <Card className="mb-8 shadow-lg">
                    <CardContent className="p-6">
                        <div className="flex gap-4">
                            <div className="flex-1 relative">
                                <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={20} />
                                <Input
                                    placeholder="Digite o nome do item para comparar preços..."
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
                                {loading ? 'Comparando...' : 'Comparar'}
                            </Button>
                        </div>
                    </CardContent>
                </Card>

                {loading && (
                    <div className="grid gap-6 md:grid-cols-4 mb-8">
                        {[1, 2, 3, 4].map(i => (
                            <Card key={i} className="animate-pulse">
                                <CardHeader>
                                    <div className="h-4 bg-gray-200 rounded w-1/2"></div>
                                </CardHeader>
                                <CardContent>
                                    <div className="h-8 bg-gray-200 rounded"></div>
                                </CardContent>
                            </Card>
                        ))}
                    </div>
                )}

                {error && (
                    <Card className="p-8 text-center border-red-200 bg-red-50">
                        <AlertCircle className="mx-auto text-red-600 mb-4" size={48} />
                        <p className="text-red-600 font-medium">{error}</p>
                    </Card>
                )}

                {data && (
                    <>
                        {/* Statistics Cards */}
                        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4 mb-8">
                            <Card className="hover-lift border-l-4 border-l-green-500">
                                <CardHeader className="pb-3">
                                    <CardTitle className="text-sm font-medium text-gray-600 flex items-center gap-2">
                                        <TrendingDown size={18} className="text-green-600" />
                                        Menor Preço
                                    </CardTitle>
                                </CardHeader>
                                <CardContent>
                                    <div className="text-3xl font-bold text-green-600">
                                        {formatCurrency(data.statistics.min_price)}
                                    </div>
                                    <p className="text-xs text-gray-500 mt-1">Melhor oferta encontrada</p>
                                </CardContent>
                            </Card>

                            <Card className="hover-lift border-l-4 border-l-red-500">
                                <CardHeader className="pb-3">
                                    <CardTitle className="text-sm font-medium text-gray-600 flex items-center gap-2">
                                        <TrendingUp size={18} className="text-red-600" />
                                        Maior Preço
                                    </CardTitle>
                                </CardHeader>
                                <CardContent>
                                    <div className="text-3xl font-bold text-red-600">
                                        {formatCurrency(data.statistics.max_price)}
                                    </div>
                                    <p className="text-xs text-gray-500 mt-1">Preço mais alto</p>
                                </CardContent>
                            </Card>

                            <Card className="hover-lift border-l-4 border-l-blue-500">
                                <CardHeader className="pb-3">
                                    <CardTitle className="text-sm font-medium text-gray-600 flex items-center gap-2">
                                        <DollarSign size={18} className="text-blue-600" />
                                        Preço Médio
                                    </CardTitle>
                                </CardHeader>
                                <CardContent>
                                    <div className="text-3xl font-bold text-blue-600">
                                        {formatCurrency(data.statistics.avg_price)}
                                    </div>
                                    <p className="text-xs text-gray-500 mt-1">Média de {data.statistics.total_results} resultados</p>
                                </CardContent>
                            </Card>

                            <Card className="hover-lift border-l-4 border-l-purple-500">
                                <CardHeader className="pb-3">
                                    <CardTitle className="text-sm font-medium text-gray-600 flex items-center gap-2">
                                        <Award size={18} className="text-purple-600" />
                                        Economia Potencial
                                    </CardTitle>
                                </CardHeader>
                                <CardContent>
                                    <div className="text-3xl font-bold text-purple-600">
                                        {getSavingsPercentage()}%
                                    </div>
                                    <p className="text-xs text-gray-500 mt-1">
                                        Economize {formatCurrency(data.statistics.savings_potential)}
                                    </p>
                                </CardContent>
                            </Card>
                        </div>

                        {/* Price Distribution Chart */}
                        <Card className="mb-8 hover-lift">
                            <CardHeader>
                                <CardTitle>Distribuição de Preços por Estado</CardTitle>
                            </CardHeader>
                            <CardContent>
                                <ResponsiveContainer width="100%" height={400}>
                                    <BarChart data={chartData}>
                                        <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                                        <XAxis dataKey="uf" stroke="#666" />
                                        <YAxis stroke="#666" />
                                        <Tooltip
                                            contentStyle={{
                                                backgroundColor: 'rgba(255, 255, 255, 0.95)',
                                                border: '1px solid #ddd',
                                                borderRadius: '8px'
                                            }}
                                            formatter={(value: number) => formatCurrency(value)}
                                        />
                                        <Legend />
                                        <Bar dataKey="Menor Preço" fill="#11998e" radius={[8, 8, 0, 0]} />
                                        <Bar dataKey="Preço Médio" fill="#4facfe" radius={[8, 8, 0, 0]} />
                                        <Bar dataKey="Maior Preço" fill="#fa709a" radius={[8, 8, 0, 0]} />
                                    </BarChart>
                                </ResponsiveContainer>
                            </CardContent>
                        </Card>

                        {/* Results by State */}
                        <div className="space-y-6">
                            <div className="flex justify-between items-center">
                                <h2 className="text-2xl font-bold">Resultados por Estado ({data.results_by_state.length})</h2>
                                <Button variant="outline" size="sm" className="gap-2">
                                    <Download size={16} />
                                    Exportar Comparação
                                </Button>
                            </div>

                            {data.results_by_state.map((state) => (
                                <Card key={state.uf} className="hover-lift">
                                    <CardHeader>
                                        <div className="flex justify-between items-center">
                                            <CardTitle className="flex items-center gap-2">
                                                <MapPin size={20} className="text-purple-600" />
                                                {state.uf}
                                            </CardTitle>
                                            <div className="flex gap-4 text-sm">
                                                <div>
                                                    <span className="text-gray-600">Mín:</span>
                                                    <span className="font-semibold text-green-600 ml-1">
                                                        {formatCurrency(state.min_price)}
                                                    </span>
                                                </div>
                                                <div>
                                                    <span className="text-gray-600">Méd:</span>
                                                    <span className="font-semibold text-blue-600 ml-1">
                                                        {formatCurrency(state.avg_price)}
                                                    </span>
                                                </div>
                                                <div>
                                                    <span className="text-gray-600">Máx:</span>
                                                    <span className="font-semibold text-red-600 ml-1">
                                                        {formatCurrency(state.max_price)}
                                                    </span>
                                                </div>
                                            </div>
                                        </div>
                                    </CardHeader>
                                    <CardContent>
                                        <div className="space-y-3">
                                            {state.items.slice(0, 3).map((item, idx) => (
                                                <div
                                                    key={idx}
                                                    className="p-4 rounded-lg border hover:border-purple-300 hover:bg-purple-50 transition"
                                                >
                                                    <div className="flex justify-between items-start">
                                                        <div className="flex-1">
                                                            <Link
                                                                href={`/arp/${item.id_arp}`}
                                                                className="font-medium text-gray-900 hover:text-purple-600"
                                                            >
                                                                {item.descricao}
                                                            </Link>
                                                            <div className="text-sm text-gray-600 mt-1">
                                                                {item.orgao_nome}
                                                            </div>
                                                            {item.marca && (
                                                                <Badge variant="outline" className="mt-2">
                                                                    {item.marca}
                                                                </Badge>
                                                            )}
                                                            {item.nome_fornecedor && (
                                                                <div className="text-xs text-gray-500 mt-1">
                                                                    Fornecedor: {item.nome_fornecedor}
                                                                </div>
                                                            )}
                                                        </div>
                                                        <div className="text-right ml-4">
                                                            <div className="text-2xl font-bold text-green-600">
                                                                {formatCurrency(item.valor_unitario)}
                                                            </div>
                                                            {item.valor_unitario === state.min_price && (
                                                                <Badge className="mt-2 bg-green-500 text-white">
                                                                    Melhor Preço
                                                                </Badge>
                                                            )}
                                                        </div>
                                                    </div>
                                                </div>
                                            ))}
                                            {state.items.length > 3 && (
                                                <p className="text-sm text-gray-500 text-center">
                                                    +{state.items.length - 3} mais resultados neste estado
                                                </p>
                                            )}
                                        </div>
                                    </CardContent>
                                </Card>
                            ))}
                        </div>
                    </>
                )}

                {!loading && !data && !error && (
                    <Card className="p-12 text-center">
                        <TrendingDown className="mx-auto text-purple-600 mb-4" size={64} />
                        <h3 className="text-2xl font-bold mb-2">Compare Preços de Itens</h3>
                        <p className="text-gray-600 mb-6">
                            Digite o nome de um item para ver a comparação de preços entre diferentes estados e ARPs
                        </p>
                        <div className="flex justify-center gap-2">
                            {['Notebook', 'Cadeira', 'Impressora', 'Mesa'].map(term => (
                                <Button
                                    key={term}
                                    variant="outline"
                                    size="sm"
                                    onClick={() => {
                                        setQuery(term)
                                        fetchComparison(term)
                                    }}
                                >
                                    {term}
                                </Button>
                            ))}
                        </div>
                    </Card>
                )}
            </div>
        </div>
    )
}
