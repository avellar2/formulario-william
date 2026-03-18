import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { supabase } from '../lib/supabase'
import { signOut } from '../lib/auth'

interface Cadastro {
  id: string
  created_at: string
  menor_nome: string
  menor_sobrenome: string
  menor_data_nascimento: string
  menor_cep: string
  menor_bairro: string
  menor_cidade: string
  tem_pai: boolean
  pai_nome: string | null
  pai_sobrenome: string | null
  pai_telefone: string | null
  pai_email: string | null
  pai_data_nascimento: string | null
  pai_cep: string | null
  pai_bairro: string | null
  pai_cidade: string | null
  tem_mae: boolean
  mae_nome: string | null
  mae_sobrenome: string | null
  mae_telefone: string | null
  mae_email: string | null
  mae_data_nascimento: string | null
  mae_cep: string | null
  mae_bairro: string | null
  mae_cidade: string | null
}

function formatDate(date: string | null): string {
  if (!date) return '—'
  const [y, m, d] = date.split('-')
  return `${d}/${m}/${y}`
}

function formatDateTime(date: string): string {
  const d = new Date(date)
  return d.toLocaleString('pt-BR', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' })
}

function Badge({ present, label }: { present: boolean; label: string }) {
  return (
    <span className={`inline-flex items-center gap-1 text-xs font-medium px-2 py-0.5 rounded-full ${present ? 'bg-green-100 text-green-700' : 'bg-amber-100 text-amber-700'}`}>
      <span className={`w-1.5 h-1.5 rounded-full ${present ? 'bg-green-500' : 'bg-amber-500'}`} />
      {label}
    </span>
  )
}

const BIGDATA_URL = 'https://bigdata.app.br/77/meuscadastros_add.php?codigo=MU7NWK'

function submitToBigdata(fields: Record<string, string | null>) {
  const form = document.createElement('form')
  form.method = 'POST'
  form.action = BIGDATA_URL
  form.target = '_blank'

  Object.entries(fields).forEach(([name, value]) => {
    const input = document.createElement('input')
    input.type = 'hidden'
    input.name = name
    input.value = value ?? ''
    form.appendChild(input)
  })

  document.body.appendChild(form)
  form.submit()
  document.body.removeChild(form)
}


function ExpandedRow({ c }: { c: Cadastro }) {
  function sendPai() {
    submitToBigdata({
      nome: c.pai_nome,
      sobrenome: c.pai_sobrenome,
      telefone: c.pai_telefone,
      email: c.pai_email,
      data_nascimento: c.pai_data_nascimento,
      cep: c.pai_cep,
      bairro: c.pai_bairro,
      cidade: c.pai_cidade,
      aceito: '1',
    })
  }

  function sendMae() {
    submitToBigdata({
      nome: c.mae_nome,
      sobrenome: c.mae_sobrenome,
      telefone: c.mae_telefone,
      email: c.mae_email,
      data_nascimento: c.mae_data_nascimento,
      cep: c.mae_cep,
      bairro: c.mae_bairro,
      cidade: c.mae_cidade,
      aceito: '1',
    })
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 p-4 bg-blue-50/50 border-t border-blue-100">
      {/* Menor */}
      <div className="bg-white rounded-xl p-4 border border-gray-100">
        <p className="text-xs font-semibold text-blue-600 uppercase tracking-wide mb-3">👦 Menor</p>
        <div className="flex flex-col gap-2 text-sm">
          <Row label="Nome" value={`${c.menor_nome} ${c.menor_sobrenome}`} />
          <Row label="Nascimento" value={formatDate(c.menor_data_nascimento)} />
          <Row label="CEP" value={c.menor_cep} />
          <Row label="Bairro" value={c.menor_bairro} />
          <Row label="Cidade" value={c.menor_cidade} />
        </div>
      </div>

      {/* Pai */}
      <div className="bg-white rounded-xl p-4 border border-gray-100">
        <p className="text-xs font-semibold text-blue-600 uppercase tracking-wide mb-3">👨 Pai</p>
        {!c.tem_pai ? (
          <p className="text-sm text-amber-600 font-medium">Pai não informado</p>
        ) : (
          <>
            <div className="flex flex-col gap-2 text-sm">
              <Row label="Nome" value={`${c.pai_nome} ${c.pai_sobrenome}`} />
              <Row label="Nascimento" value={formatDate(c.pai_data_nascimento)} />
              <Row label="Telefone" value={c.pai_telefone} />
              <Row label="E-mail" value={c.pai_email} />
              <Row label="Bairro" value={c.pai_bairro} />
              <Row label="Cidade" value={c.pai_cidade} />
            </div>
            <button
              onClick={sendPai}
              className="mt-3 flex items-center justify-center gap-2 w-full py-2 px-3 bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold rounded-lg transition-colors"
            >
              <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
              </svg>
              Enviar Pai para BigData
            </button>
          </>
        )}
      </div>

      {/* Mãe */}
      <div className="bg-white rounded-xl p-4 border border-gray-100">
        <p className="text-xs font-semibold text-blue-600 uppercase tracking-wide mb-3">👩 Mãe</p>
        {!c.tem_mae ? (
          <p className="text-sm text-amber-600 font-medium">Mãe não informada</p>
        ) : (
          <>
            <div className="flex flex-col gap-2 text-sm">
              <Row label="Nome" value={`${c.mae_nome} ${c.mae_sobrenome}`} />
              <Row label="Nascimento" value={formatDate(c.mae_data_nascimento)} />
              <Row label="Telefone" value={c.mae_telefone} />
              <Row label="E-mail" value={c.mae_email} />
              <Row label="Bairro" value={c.mae_bairro} />
              <Row label="Cidade" value={c.mae_cidade} />
            </div>
            <button
              onClick={sendMae}
              className="mt-3 flex items-center justify-center gap-2 w-full py-2 px-3 bg-pink-600 hover:bg-pink-700 text-white text-xs font-semibold rounded-lg transition-colors"
            >
              <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
              </svg>
              Enviar Mãe para BigData
            </button>
          </>
        )}
      </div>
    </div>
  )
}

function Row({ label, value }: { label: string; value: string | null }) {
  return (
    <div className="flex flex-col">
      <span className="text-xs text-gray-400">{label}</span>
      <span className="text-gray-700 font-medium">{value || '—'}</span>
    </div>
  )
}

export default function Admin() {
  const navigate = useNavigate()
  const [cadastros, setCadastros] = useState<Cadastro[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [expanded, setExpanded] = useState<string | null>(null)

  async function fetchCadastros() {
    setLoading(true)
    const { data, error } = await supabase
      .from('cadastros')
      .select('*')
      .order('created_at', { ascending: false })
    if (error) console.error('Supabase error:', error)
    console.log('Cadastros retornados:', data)
    setCadastros(data ?? [])
    setLoading(false)
  }

  useEffect(() => {
    supabase.auth.getSession().then(({ data }) => {
      if (!data.session) {
        navigate('/admin/login')
      } else {
        fetchCadastros()
      }
    })
  }, [navigate])

  async function handleSignOut() {
    await signOut()
    navigate('/admin/login')
  }

  function handleExportJson() {
    const blob = new Blob([JSON.stringify(cadastros, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `cadastros_${new Date().toISOString().slice(0, 10)}.json`
    a.click()
    URL.revokeObjectURL(url)
  }

  const filtered = cadastros.filter((c) =>
    `${c.menor_nome} ${c.menor_sobrenome}`.toLowerCase().includes(search.toLowerCase())
  )

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
              <svg className="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
            </div>
            <div>
              <h1 className="text-base font-bold text-gray-800">Cadastros</h1>
              <p className="text-xs text-gray-400">{cadastros.length} registro{cadastros.length !== 1 ? 's' : ''}</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={handleExportJson}
              className="flex items-center gap-2 text-sm text-gray-500 hover:text-blue-600 transition-colors font-medium"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
              </svg>
              Exportar JSON
            </button>
          <button
            onClick={handleSignOut}
            className="flex items-center gap-2 text-sm text-gray-500 hover:text-red-500 transition-colors font-medium"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
            </svg>
            Sair
          </button>
          </div>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-4 sm:px-6 py-6">
        {/* Busca */}
        <div className="mb-4 relative max-w-sm">
          <svg className="w-4 h-4 text-gray-400 absolute left-3 top-1/2 -translate-y-1/2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
          <input
            type="text"
            placeholder="Buscar por nome do menor..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-9 pr-4 py-2.5 rounded-xl border border-gray-200 bg-white text-sm text-gray-700 focus:border-blue-500 focus:ring-2 focus:ring-blue-100 outline-none transition-all"
          />
        </div>

        {/* Tabela */}
        <div className="bg-white rounded-2xl border border-gray-200 overflow-hidden shadow-sm">
          {loading ? (
            <div className="flex items-center justify-center py-20">
              <div className="w-8 h-8 border-3 border-blue-500 border-t-transparent rounded-full animate-spin" />
            </div>
          ) : filtered.length === 0 ? (
            <div className="text-center py-20 text-gray-400">
              <svg className="w-12 h-12 mx-auto mb-3 opacity-30" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
              </svg>
              <p className="text-sm">Nenhum cadastro encontrado</p>
            </div>
          ) : (
            <div>
              {/* Header da tabela */}
              <div className="hidden md:grid grid-cols-[1fr_1fr_auto_auto_auto] gap-4 px-5 py-3 bg-gray-50 border-b border-gray-200 text-xs font-semibold text-gray-500 uppercase tracking-wide">
                <span>Menor</span>
                <span>Cidade</span>
                <span>Pai</span>
                <span>Mãe</span>
                <span>Data</span>
              </div>

              {filtered.map((c) => (
                <div key={c.id}>
                  <button
                    onClick={() => setExpanded(expanded === c.id ? null : c.id)}
                    className="w-full text-left px-5 py-4 border-b border-gray-100 hover:bg-gray-50 transition-colors"
                  >
                    <div className="hidden md:grid grid-cols-[1fr_1fr_auto_auto_auto] gap-4 items-center">
                      <span className="font-semibold text-gray-800 text-sm">
                        {c.menor_nome} {c.menor_sobrenome}
                      </span>
                      <span className="text-sm text-gray-500">{c.menor_cidade}</span>
                      <Badge present={c.tem_pai} label={c.tem_pai ? 'Com pai' : 'Sem pai'} />
                      <Badge present={c.tem_mae} label={c.tem_mae ? 'Com mãe' : 'Sem mãe'} />
                      <span className="text-xs text-gray-400 whitespace-nowrap">{formatDateTime(c.created_at)}</span>
                    </div>

                    {/* Mobile */}
                    <div className="md:hidden flex items-center justify-between">
                      <div>
                        <p className="font-semibold text-gray-800 text-sm">{c.menor_nome} {c.menor_sobrenome}</p>
                        <p className="text-xs text-gray-400 mt-0.5">{c.menor_cidade} · {formatDateTime(c.created_at)}</p>
                        <div className="flex gap-1.5 mt-2">
                          <Badge present={c.tem_pai} label={c.tem_pai ? 'Com pai' : 'Sem pai'} />
                          <Badge present={c.tem_mae} label={c.tem_mae ? 'Com mãe' : 'Sem mãe'} />
                        </div>
                      </div>
                      <svg
                        className={`w-4 h-4 text-gray-400 transition-transform duration-200 flex-shrink-0 ml-3 ${expanded === c.id ? 'rotate-180' : ''}`}
                        fill="none" viewBox="0 0 24 24" stroke="currentColor"
                      >
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                      </svg>
                    </div>

                    {/* Chevron desktop */}
                    <div className="hidden md:flex absolute right-4 top-1/2 -translate-y-1/2">
                    </div>
                  </button>

                  {expanded === c.id && <ExpandedRow c={c} />}
                </div>
              ))}
            </div>
          )}
        </div>
      </main>
    </div>
  )
}
