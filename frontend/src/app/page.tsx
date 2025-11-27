import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import {
  Search,
  TrendingDown,
  LineChart,
  Building2,
  FileSpreadsheet,
  ShieldCheck,
  ArrowRight,
  Sparkles,
  CheckCircle2
} from "lucide-react"

export default function Home() {
  return (
    <div className="flex flex-col min-h-screen">
      {/* Header */}
      <header className="sticky top-0 z-50 px-6 h-16 flex items-center border-b bg-white/80 backdrop-blur-md">
        <div className="container mx-auto flex justify-between items-center">
          <div className="font-bold text-2xl flex items-center gap-2">
            <ShieldCheck className="text-purple-600" size={32} />
            <span className="gradient-text">AtaHub</span>
          </div>
          <nav className="flex gap-4">
            <Link href="/busca">
              <Button variant="ghost">Buscar ARPs</Button>
            </Link>
            <Link href="/dashboard">
              <Button variant="ghost">Dashboard</Button>
            </Link>
            <Link href="/busca">
              <Button className="bg-gradient-primary text-white hover:opacity-90">
                Começar <ArrowRight size={16} className="ml-2" />
              </Button>
            </Link>
          </nav>
        </div>
      </header>

      {/* Hero Section */}
      <main className="flex-1">
        <section className="relative overflow-hidden bg-gradient-to-br from-purple-50 via-white to-blue-50 py-20">
          <div className="absolute inset-0 bg-grid-pattern opacity-5"></div>

          <div className="container mx-auto px-6 relative z-10">
            <div className="text-center max-w-4xl mx-auto animate-slide-in-up">
              <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-purple-100 text-purple-700 mb-6">
                <Sparkles size={16} />
                <span className="text-sm font-medium">Powered by 2025 Government Data</span>
              </div>

              <h1 className="text-5xl md:text-7xl font-extrabold tracking-tight mb-6">
                Encontre as Melhores
                <br />
                <span className="gradient-text">Oportunidades de Carona</span>
              </h1>

              <p className="text-xl text-gray-600 max-w-3xl mx-auto mb-8 leading-relaxed">
                Plataforma inteligente para buscar, comparar e analisar Atas de Registro de Preços
                do governo brasileiro. Economize tempo e dinheiro com dados atualizados de 2025.
              </p>

              <div className="flex gap-4 justify-center mb-12">
                <Link href="/busca">
                  <Button size="lg" className="bg-gradient-primary text-white hover:opacity-90 shadow-glow px-8 py-6 text-lg">
                    <Search className="mr-2" size={20} />
                    Buscar ARPs
                  </Button>
                </Link>
                <Link href="/dashboard">
                  <Button size="lg" variant="outline" className="px-8 py-6 text-lg hover-lift">
                    <LineChart className="mr-2" size={20} />
                    Ver Dashboard
                  </Button>
                </Link>
              </div>

              {/* Quick Stats */}
              <div className="grid grid-cols-3 gap-6 max-w-2xl mx-auto">
                <div className="text-center">
                  <div className="text-3xl font-bold text-purple-600">10K+</div>
                  <div className="text-sm text-gray-600">ARPs Ativas</div>
                </div>
                <div className="text-center">
                  <div className="text-3xl font-bold text-blue-600">R$ 2B+</div>
                  <div className="text-sm text-gray-600">Valor Total</div>
                </div>
                <div className="text-center">
                  <div className="text-3xl font-bold text-green-600">500K+</div>
                  <div className="text-sm text-gray-600">Itens</div>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Features Section */}
        <section className="py-20 bg-white">
          <div className="container mx-auto px-6">
            <div className="text-center mb-16">
              <h2 className="text-4xl font-bold mb-4">Recursos Poderosos</h2>
              <p className="text-gray-600 text-lg">Tudo que você precisa para encontrar as melhores oportunidades</p>
            </div>

            <div className="grid md:grid-cols-3 gap-8">
              <Card className="hover-lift border-2 hover:border-purple-200 transition-all">
                <CardContent className="p-6">
                  <div className="w-12 h-12 bg-gradient-primary rounded-lg flex items-center justify-center mb-4">
                    <Search className="text-white" size={24} />
                  </div>
                  <h3 className="font-bold text-xl mb-2">Busca Avançada</h3>
                  <p className="text-gray-600">
                    Filtros por estado, preço, data e fornecedor. Busca textual completa em português.
                  </p>
                  <ul className="mt-4 space-y-2">
                    <li className="flex items-center gap-2 text-sm">
                      <CheckCircle2 size={16} className="text-green-500" />
                      Filtros inteligentes
                    </li>
                    <li className="flex items-center gap-2 text-sm">
                      <CheckCircle2 size={16} className="text-green-500" />
                      Ordenação flexível
                    </li>
                    <li className="flex items-center gap-2 text-sm">
                      <CheckCircle2 size={16} className="text-green-500" />
                      Resultados em tempo real
                    </li>
                  </ul>
                </CardContent>
              </Card>

              <Card className="hover-lift border-2 hover:border-green-200 transition-all">
                <CardContent className="p-6">
                  <div className="w-12 h-12 bg-gradient-success rounded-lg flex items-center justify-center mb-4">
                    <TrendingDown className="text-white" size={24} />
                  </div>
                  <h3 className="font-bold text-xl mb-2">Comparação de Preços</h3>
                  <p className="text-gray-600">
                    Compare preços entre diferentes ARPs e calcule potencial de economia.
                  </p>
                  <ul className="mt-4 space-y-2">
                    <li className="flex items-center gap-2 text-sm">
                      <CheckCircle2 size={16} className="text-green-500" />
                      Estatísticas automáticas
                    </li>
                    <li className="flex items-center gap-2 text-sm">
                      <CheckCircle2 size={16} className="text-green-500" />
                      Análise por estado
                    </li>
                    <li className="flex items-center gap-2 text-sm">
                      <CheckCircle2 size={16} className="text-green-500" />
                      Cálculo de economia
                    </li>
                  </ul>
                </CardContent>
              </Card>

              <Card className="hover-lift border-2 hover:border-blue-200 transition-all">
                <CardContent className="p-6">
                  <div className="w-12 h-12 bg-gradient-info rounded-lg flex items-center justify-center mb-4">
                    <LineChart className="text-white" size={24} />
                  </div>
                  <h3 className="font-bold text-xl mb-2">Dashboard Analytics</h3>
                  <p className="text-gray-600">
                    Visualize estatísticas e tendências com gráficos interativos.
                  </p>
                  <ul className="mt-4 space-y-2">
                    <li className="flex items-center gap-2 text-sm">
                      <CheckCircle2 size={16} className="text-green-500" />
                      Gráficos interativos
                    </li>
                    <li className="flex items-center gap-2 text-sm">
                      <CheckCircle2 size={16} className="text-green-500" />
                      Métricas em tempo real
                    </li>
                    <li className="flex items-center gap-2 text-sm">
                      <CheckCircle2 size={16} className="text-green-500" />
                      Insights automáticos
                    </li>
                  </ul>
                </CardContent>
              </Card>

              <Card className="hover-lift border-2 hover:border-orange-200 transition-all">
                <CardContent className="p-6">
                  <div className="w-12 h-12 bg-gradient-warm rounded-lg flex items-center justify-center mb-4">
                    <Building2 className="text-white" size={24} />
                  </div>
                  <h3 className="font-bold text-xl mb-2">Diretório de Fornecedores</h3>
                  <p className="text-gray-600">
                    Busque fornecedores e veja todos os contratos e estatísticas.
                  </p>
                </CardContent>
              </Card>

              <Card className="hover-lift border-2 hover:border-teal-200 transition-all">
                <CardContent className="p-6">
                  <div className="w-12 h-12 bg-gradient-cool rounded-lg flex items-center justify-center mb-4">
                    <FileSpreadsheet className="text-white" size={24} />
                  </div>
                  <h3 className="font-bold text-xl mb-2">Exportação de Dados</h3>
                  <p className="text-gray-600">
                    Exporte resultados para CSV para análise externa.
                  </p>
                </CardContent>
              </Card>

              <Card className="hover-lift border-2 hover:border-purple-200 transition-all">
                <CardContent className="p-6">
                  <div className="w-12 h-12 bg-gradient-primary rounded-lg flex items-center justify-center mb-4">
                    <ShieldCheck className="text-white" size={24} />
                  </div>
                  <h3 className="font-bold text-xl mb-2">Dados Oficiais</h3>
                  <p className="text-gray-600">
                    Integração direta com Portal Nacional de Contratações Públicas (PNCP).
                  </p>
                </CardContent>
              </Card>
            </div>
          </div>
        </section>

        {/* CTA Section */}
        <section className="py-20 bg-gradient-primary text-white">
          <div className="container mx-auto px-6 text-center">
            <h2 className="text-4xl font-bold mb-4">Pronto para Começar?</h2>
            <p className="text-xl mb-8 opacity-90">
              Acesse agora e descubra as melhores oportunidades de carona em ARPs
            </p>
            <Link href="/busca">
              <Button size="lg" variant="secondary" className="px-8 py-6 text-lg hover-lift">
                <Search className="mr-2" size={20} />
                Começar Agora
              </Button>
            </Link>
          </div>
        </section>
      </main>

      {/* Footer */}
      <footer className="bg-gray-900 text-gray-300 py-12">
        <div className="container mx-auto px-6">
          <div className="grid md:grid-cols-4 gap-8">
            <div>
              <div className="font-bold text-xl text-white mb-4 flex items-center gap-2">
                <ShieldCheck className="text-purple-400" />
                AtaHub
              </div>
              <p className="text-sm">
                Plataforma para busca e análise de Atas de Registro de Preços do governo brasileiro.
              </p>
            </div>
            <div>
              <h4 className="font-semibold text-white mb-4">Recursos</h4>
              <ul className="space-y-2 text-sm">
                <li><Link href="/busca" className="hover:text-white">Buscar ARPs</Link></li>
                <li><Link href="/dashboard" className="hover:text-white">Dashboard</Link></li>
                <li><Link href="/fornecedores" className="hover:text-white">Fornecedores</Link></li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold text-white mb-4">Dados</h4>
              <ul className="space-y-2 text-sm">
                <li>Dados de 2025</li>
                <li>Atualização contínua</li>
                <li>Fonte: PNCP</li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold text-white mb-4">Legal</h4>
              <ul className="space-y-2 text-sm">
                <li>Licença MIT</li>
                <li>Código Aberto</li>
              </ul>
            </div>
          </div>
          <div className="border-t border-gray-800 mt-8 pt-8 text-center text-sm">
            <p>© 2025 AtaHub. Todos os direitos reservados.</p>
          </div>
        </div>
      </footer>
    </div>
  )
}
