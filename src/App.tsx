import { useState } from 'react'
import { Stepper } from './components/Stepper'
import { StepMenor } from './components/StepMenor'
import { StepResponsavel } from './components/StepResponsavel'
import { supabase } from './lib/supabase'
import type { MenorData, ResponsavelData } from './lib/schemas'

const STEPS = [
  { label: 'Criança' },
  { label: 'Responsável 1' },
  { label: 'Responsável 2' },
]

function parseDate(value: string): string | null {
  if (!value) return null
  const parts = value.split('/')
  if (parts.length !== 3) return null
  return `${parts[2]}-${parts[1]}-${parts[0]}`
}

export default function App() {
  const [step, setStep] = useState(0)
  const [menor, setMenor] = useState<MenorData | null>(null)
  const [resp1, setResp1] = useState<ResponsavelData | null>(null)
  const [loading, setLoading] = useState(false)
  const [success, setSuccess] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function handleFinalSubmit(resp2: ResponsavelData) {
    if (!menor || !resp1) return
    setLoading(true)
    setError(null)

    const payload = {
      menor_nome: menor.nome,
      menor_sobrenome: menor.sobrenome,
      menor_data_nascimento: parseDate(menor.data_nascimento),
      menor_cep: menor.cep,
      menor_bairro: menor.bairro,
      menor_cidade: menor.cidade,
      tem_pai: true,
      pai_nome: resp1.nome,
      pai_sobrenome: resp1.sobrenome,
      pai_telefone: resp1.telefone,
      pai_email: resp1.email,
      pai_data_nascimento: parseDate(resp1.data_nascimento ?? ''),
      pai_cep: resp1.cep,
      pai_bairro: resp1.bairro,
      pai_cidade: resp1.cidade,
      tem_mae: true,
      mae_nome: resp2.nome,
      mae_sobrenome: resp2.sobrenome,
      mae_telefone: resp2.telefone,
      mae_email: resp2.email,
      mae_data_nascimento: parseDate(resp2.data_nascimento ?? ''),
      mae_cep: resp2.cep,
      mae_bairro: resp2.bairro,
      mae_cidade: resp2.cidade,
    }

    const { error: sbError } = await supabase.from('cadastros').insert(payload)

    setLoading(false)

    if (sbError) {
      console.error('Erro Supabase:', JSON.stringify(sbError))
      setError(`Erro: ${sbError.message} (${sbError.code})`)
      return
    }

    setSuccess(true)
  }

  if (success) {
    return (
      <div className="min-h-screen flex items-center justify-center p-6">
        <div className="bg-white rounded-2xl shadow-xl p-12 max-w-md w-full text-center animate-fade-in">
          <div className="w-16 h-16 bg-green-50 rounded-full flex items-center justify-center mx-auto mb-6">
            <svg className="w-8 h-8 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
          </div>
          <h2 className="font-display text-2xl font-semibold text-gray-900 mb-2">Inscrição Confirmada</h2>
          <p className="text-gray-600 mb-8">Os dados foram salvos com sucesso.</p>
          <button
            onClick={() => { setSuccess(false); setStep(0); setMenor(null); setResp1(null) }}
            className="w-full bg-gray-900 hover:bg-gray-800 text-white font-medium py-3 rounded-lg transition-colors"
          >
            Nova inscrição
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen flex items-center justify-center p-6">
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-2xl overflow-hidden animate-fade-in">
        {/* Barra de accent laranja */}
        <div className="h-1 bg-gradient-to-r from-orange-500 to-amber-500" />
        
        {/* Header */}
        <div className="px-10 pt-10 pb-8">
          <div className="text-center mb-8">
            <h1 className="font-display text-3xl font-semibold text-gray-900 mb-2">
              Passeio Cultural
            </h1>
            <p className="text-gray-500 text-sm">
              Formulário de inscrição
            </p>
          </div>

          <Stepper steps={STEPS} current={step} />
        </div>

        {/* Content */}
        <div className="px-10 pb-10">
          {error && (
            <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700 flex items-center gap-3">
              <svg className="w-5 h-5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
              </svg>
              {error}
            </div>
          )}

          {step === 0 && (
            <StepMenor
              defaultValues={menor ?? undefined}
              onNext={(data) => { setMenor(data); setStep(1) }}
            />
          )}

          {step === 1 && (
            <StepResponsavel
              titulo="Responsável Masculino"
              defaultValues={resp1 ?? undefined}
              onBack={() => setStep(0)}
              onNext={(data) => { setResp1(data); setStep(2) }}
            />
          )}

          {step === 2 && (
            <StepResponsavel
              titulo="Responsável Feminino"
              onBack={() => setStep(1)}
              onNext={handleFinalSubmit}
              isLast
              loading={loading}
            />
          )}

          {step === 2 && (
            <p className="text-xs text-gray-400 text-center mt-6 leading-relaxed">
              Ao salvar, você declara que leu e aceita os termos de consentimento para uso de dados conforme a{' '}
              <span className="text-gray-600 font-medium">LGPD — Lei Geral de Proteção de Dados</span>.
            </p>
          )}
        </div>
      </div>
    </div>
  )
}
