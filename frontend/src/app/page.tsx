import Link from "next/link"
import { Button } from "@/components/ui/button"
import { ArrowRight, ShieldCheck } from "lucide-react"

export default function Home() {
  return (
    <div className="flex flex-col min-h-screen">
      <header className="px-6 h-16 flex items-center border-b justify-between">
        <div className="font-bold text-xl flex items-center gap-2">
          <ShieldCheck className="text-blue-600" />
          GovCompras.ai
        </div>
        <nav>
          <Link href="/busca">
            <Button variant="ghost">Ir para Busca</Button>
          </Link>
        </nav>
      </header>

      <main className="flex-1 flex flex-col items-center justify-center text-center p-8 bg-slate-50">
        <h1 className="text-4xl md:text-6xl font-extrabold tracking-tight mb-6">
          Encontre Oportunidades de <br />
          <span className="text-blue-600">Carona em Atas</span>
        </h1>
        <p className="text-lg text-slate-600 max-w-2xl mb-8">
          Monitore Diários Oficiais, compare preços e encontre Atas de Registro de Preços
          vigentes para vender mais ou comprar melhor.
        </p>

        <div className="flex gap-4">
          <Link href="/busca">
            <Button size="lg" className="gap-2">
              Acessar Painel <ArrowRight size={16} />
            </Button>
          </Link>
        </div>
      </main>
    </div>
  )
}
