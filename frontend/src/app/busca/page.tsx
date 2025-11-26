'use client'
import { useState } from 'react'
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"

// Tipagem
interface SearchResult {
    id_arp: string;
    numero_arp: string;
    orgao_nome: string;
    uf: string;
    vigencia_fim: string;
    item: {
        descricao: string;
        valor_unitario: number;
        marca: string;
    }
}

export default function BuscaPage() {
    const [query, setQuery] = useState('')
    const [results, setResults] = useState<SearchResult[]>([])
    const [loading, setLoading] = useState(false)

    const handleSearch = async () => {
        if (!query) return;
        setLoading(true);
        try {
            const res = await fetch(`http://localhost:8000/buscar?q=${query}`);
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

    return (
        <div className="container mx-auto p-8 max-w-4xl">
            <h1 className="text-3xl font-bold mb-6">Busca de Atas (Carona)</h1>

            <div className="flex gap-4 mb-8">
                <Input
                    placeholder="Ex: Notebook i7, Cadeira Giratória..."
                    value={query}
                    onChange={e => setQuery(e.target.value)}
                />
                <Button onClick={handleSearch} disabled={loading}>
                    {loading ? "Buscando..." : "Buscar"}
                </Button>
            </div>

            <div className="grid gap-4">
                {results.map((res) => (
                    <Card key={`${res.id_arp}-${res.item.descricao}`} className="hover:shadow-md transition">
                        <CardHeader className="pb-2">
                            <div className="flex justify-between">
                                <Badge variant="outline">{res.uf}</Badge>
                                <span className="text-xs text-muted-foreground">Vence em: {res.vigencia_fim}</span>
                            </div>
                            <CardTitle className="text-lg leading-tight">{res.item.descricao}</CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div className="flex justify-between items-end mt-2">
                                <div>
                                    <p className="text-sm text-muted-foreground">{res.orgao_nome}</p>
                                    <p className="text-sm font-medium">Marca: {res.item.marca || "N/A"}</p>
                                </div>
                                <div className="text-xl font-bold text-green-700">
                                    {new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(res.item.valor_unitario)}
                                </div>
                            </div>
                        </CardContent>
                    </Card>
                ))}
            </div>
        </div>
    )
}
