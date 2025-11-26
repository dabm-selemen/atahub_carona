'use client'
import { useEffect, useState } from 'react'
import Link from 'next/link'
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import {
    BarChart,
    Bar,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    Legend,
    ResponsiveContainer,
    PieChart,
    Pie,
    Cell
} from 'recharts'
import {
    TrendingUp,
    FileText,
    DollarSign,
    Package,
    Home,
    Building2,
    Calendar,
    Award
} from "lucide-react"

interface DashboardStats {
    total_arps: number
    active_arps: number
    total_items: number
    total_value: number
    arps_by_state: Array<{ uf: string; count: number }>
    recent_arps: Array<{
        id: string
        numero_arp: string
        orgao_nome: string
        uf: string
        data_inicio_vigencia: string
    }>
    top_suppliers: Array<{
        nome_fornecedor: string
        total_value: number
        contract_count: number
    }>
}

const COLORS = ['#667eea', '#764ba2', '#11998e', '#38ef7d', '#4facfe', '#00f2fe', '#fa709a', '#fee140', '#30cfd0', '#330867']

export default function DashboardPage() {
    const [stats, setStats] = useState<DashboardStats | null>(null)
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)

    useEffect(() => {
        fetchStats()
    }, [])

    const fetchStats = async () => {
        try {
            setLoading(true)
            const res = await fetch('http://localhost:8000/stats')
            if (res.ok) {
                const data = await res.json()
                setStats(data)
            } else {
                setError('Erro ao carregar estatísticas')
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

    const formatNumber = (value: number) => {
        return new Intl.NumberFormat('pt-BR', {
            notation: 'compact',
            compactDisplay: 'short'
        }).format(value)
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
                        <Link href="/fornecedores">
                            <Button variant="ghost">Fornecedores</Button>
                        </Link>
                    </nav>
                </div>
            </header>

            <div className="container mx-auto p-6 max-w-7xl">
                <div className="mb-8">
                    <h1 className="text-4xl font-bold mb-2">Dashboard Analytics</h1>
                    <p className="text-gray-600">Visão geral de ARPs e estatísticas do sistema</p>
                </div>

                {loading && (
                    <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4 mb-8">
                        {[1, 2, 3, 4].map(i => (
                            <Card key={i} className="animate-pulse">
                                <CardHeader className="pb-3">
                                    <div className="h-4 bg-gray-200 rounded w-1/2"></div>
                                </CardHeader>
                                <CardContent>
                                    <div className="h-8 bg-gray-200 rounded w-3/4"></div>
                                </CardContent>
                            </Card>
                        ))}
                    </div>
                )}

                {error && (
                    <Card className="p-8 text-center border-red-200 bg-red-50">
                        <p className="text-red-600 font-medium">{error}</p>
                        <Button onClick={fetchStats} className="mt-4" variant="outline">
                            Tentar Novamente
                        </Button>
                    </Card>
                )}

                {stats && (
                    <>
                        {/* Key Metrics Cards */}
                        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4 mb-8">
                            <Card className="hover-lift border-l-4 border-l-purple-500">
                                <CardHeader className="pb-3">
                                    <CardTitle className="text-sm font-medium text-gray-600 flex items-center gap-2">
                                        <FileText size={18} className="text-purple-600" />
                                        Total de ARPs
                                    </CardTitle>
                                </CardHeader>
                                <CardContent>
                                    <div className="text-3xl font-bold text-purple-600">
                                        {formatNumber(stats.total_arps)}
                                    </div>
                                    <p className="text-xs text-gray-500 mt-1">
                                        {formatNumber(stats.active_arps)} ativas
                                    </p>
                                </CardContent>
                            </Card>

                            <Card className="hover-lift border-l-4 border-l-green-500">
                                <CardHeader className="pb-3">
                                    <CardTitle className="text-sm font-medium text-gray-600 flex items-center gap-2">
                                        <DollarSign size={18} className="text-green-600" />
                                        Valor Total
                                    </CardTitle>
                                </CardHeader>
                                <CardContent>
                                    <div className="text-3xl font-bold text-green-600">
                                        {formatCurrency(stats.total_value)}
                                    </div>
                                    <p className="text-xs text-gray-500 mt-1">
                                        Em contratos ativos
                                    </p>
                                </CardContent>
                            </Card>

                            <Card className="hover-lift border-l-4 border-l-blue-500">
                                <CardHeader className="pb-3">
                                    <CardTitle className="text-sm font-medium text-gray-600 flex items-center gap-2">
                                        <Package size={18} className="text-blue-600" />
                                        Total de Itens
                                    </CardTitle>
                                </CardHeader>
                                <CardContent>
                                    <div className="text-3xl font-bold text-blue-600">
                                        {formatNumber(stats.total_items)}
                                    </div>
                                    <p className="text-xs text-gray-500 mt-1">
                                        Itens registrados
                                    </p>
                                </CardContent>
                            </Card>

                            <Card className="hover-lift border-l-4 border-l-orange-500">
                                <CardHeader className="pb-3">
                                    <CardTitle className="text-sm font-medium text-gray-600 flex items-center gap-2">
                                        <TrendingUp size={18} className="text-orange-600" />
                                        ARPs Ativas
                                    </CardTitle>
                                </CardHeader>
                                <CardContent>
                                    <div className="text-3xl font-bold text-orange-600">
                                        {((stats.active_arps / stats.total_arps) * 100).toFixed(1)}%
                                    </div>
                                    <p className="text-xs text-gray-500 mt-1">
                                        Taxa de ativação
                                    </p>
                                </CardContent>
                            </Card>
                        </div>

                        {/* Charts Section */}
                        <div className="grid gap-6 lg:grid-cols-2 mb-8">
                            {/* ARPs by State */}
                            <Card className="hover-lift">
                                <CardHeader>
                                    <CardTitle className="flex items-center gap-2">
                                        <Building2 size={20} />
                                        ARPs por Estado (Top 10)
                                    </CardTitle>
                                </CardHeader>
                                <CardContent>
                                    <ResponsiveContainer width="100%" height={300}>
                                        <BarChart data={stats.arps_by_state}>
                                            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                                            <XAxis dataKey="uf" stroke="#666" />
                                            <YAxis stroke="#666" />
                                            <Tooltip
                                                contentStyle={{
                                                    backgroundColor: 'rgba(255, 255, 255, 0.95)',
                                                    border: '1px solid #ddd',
                                                    borderRadius: '8px'
                                                }}
                                            />
                                            <Bar dataKey="count" fill="#667eea" radius={[8, 8, 0, 0]} />
                                        </BarChart>
                                    </ResponsiveContainer>
                                </CardContent>
                            </Card>

                            {/* Top Suppliers */}
                            <Card className="hover-lift">
                                <CardHeader>
                                    <CardTitle className="flex items-center gap-2">
                                        <Award size={20} />
                                        Top Fornecedores
                                    </CardTitle>
                                </CardHeader>
                                <CardContent>
                                    <ResponsiveContainer width="100%" height={300}>
                                        <BarChart
                                            data={stats.top_suppliers.slice(0, 5)}
                                            layout="vertical"
                                        >
                                            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                                            <XAxis type="number" stroke="#666" />
                                            <YAxis
                                                type="category"
                                                dataKey="nome_fornecedor"
                                                stroke="#666"
                                                width={150}
                                            />
                                            <Tooltip
                                                contentStyle={{
                                                    backgroundColor: 'rgba(255, 255, 255, 0.95)',
                                                    border: '1px solid #ddd',
                                                    borderRadius: '8px'
                                                }}
                                                formatter={(value: number) => formatCurrency(value)}
                                            />
                                            <Bar dataKey="total_value" fill="#11998e" radius={[0, 8, 8, 0]} />
                                        </BarChart>
                                    </ResponsiveContainer>
                                </CardContent>
                            </Card>
                        </div>

                        {/* Recent ARPs */}
                        <Card className="hover-lift">
                            <CardHeader>
                                <CardTitle className="flex items-center gap-2">
                                    <Calendar size={20} />
                                    ARPs Recentes
                                </CardTitle>
                            </CardHeader>
                            <CardContent>
                                <div className="space-y-3">
                                    {stats.recent_arps.map((arp) => (
                                        <Link
                                            key={arp.id}
                                            href={`/arp/${arp.id}`}
                                            className="block p-4 rounded-lg border hover:border-purple-300 hover:bg-purple-50 transition-all"
                                        >
                                            <div className="flex justify-between items-start">
                                                <div>
                                                    <div className="font-semibold text-gray-900 hover:text-purple-600">
                                                        {arp.numero_arp}
                                                    </div>
                                                    <div className="text-sm text-gray-600 mt-1">
                                                        {arp.orgao_nome}
                                                    </div>
                                                </div>
                                                <div className="text-right">
                                                    <div className="text-sm font-medium text-purple-600">
                                                        {arp.uf}
                                                    </div>
                                                    <div className="text-xs text-gray-500 mt-1">
                                                        {new Date(arp.data_inicio_vigencia).toLocaleDateString('pt-BR')}
                                                    </div>
                                                </div>
                                            </div>
                                        </Link>
                                    ))}
                                </div>
                            </CardContent>
                        </Card>

                        {/* Distribution Pie Chart */}
                        {stats.arps_by_state.length > 0 && (
                            <Card className="mt-6 hover-lift">
                                <CardHeader>
                                    <CardTitle>Distribuição de ARPs por Região</CardTitle>
                                </CardHeader>
                                <CardContent>
                                    <ResponsiveContainer width="100%" height={300}>
                                        <PieChart>
                                            <Pie
                                                data={stats.arps_by_state.slice(0, 10)}
                                                dataKey="count"
                                                nameKey="uf"
                                                cx="50%"
                                                cy="50%"
                                                outerRadius={100}
                                                label={(entry) => `${entry.uf}: ${entry.count}`}
                                            >
                                                {stats.arps_by_state.slice(0, 10).map((entry, index) => (
                                                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                                                ))}
                                            </Pie>
                                            <Tooltip />
                                            <Legend />
                                        </PieChart>
                                    </ResponsiveContainer>
                                </CardContent>
                            </Card>
                        )}
                    </>
                )}
            </div>
        </div>
    )
}
