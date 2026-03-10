import { useState } from 'react'
import { Stepper } from './components/Stepper'
import { StepMenor } from './components/StepMenor'
import { StepResponsavel } from './components/StepResponsavel'
import { supabase } from './lib/supabase'
import type { MenorData, ResponsavelData } from './lib/schemas'

const STEPS = [
  { label: 'Menor', icon: '👦' },
  { label: 'Pai', icon: '👨' },
  { label: 'Mãe', icon: '👩' },
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
  const [pai, setPai] = useState<ResponsavelData | null>(null)
  const [loading, setLoading] = useState(false)
  const [success, setSuccess] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function handleFinalSubmit(mae: ResponsavelData) {
    if (!menor || !pai) return
    setLoading(true)
    setError(null)

    const payload = {
      menor_nome: menor.nome,
      menor_sobrenome: menor.sobrenome,
      menor_data_nascimento: parseDate(menor.data_nascimento),
      menor_cep: menor.cep,
      menor_bairro: menor.bairro,
      menor_cidade: menor.cidade,
      tem_pai: !pai.ausente,
      pai_nome: pai.ausente ? null : pai.nome,
      pai_sobrenome: pai.ausente ? null : pai.sobrenome,
      pai_telefone: pai.ausente ? null : pai.telefone,
      pai_email: pai.ausente ? null : pai.email,
      pai_data_nascimento: pai.ausente ? null : parseDate(pai.data_nascimento ?? ''),
      pai_cep: pai.ausente ? null : pai.cep,
      pai_bairro: pai.ausente ? null : pai.bairro,
      pai_cidade: pai.ausente ? null : pai.cidade,
      tem_mae: !mae.ausente,
      mae_nome: mae.ausente ? null : mae.nome,
      mae_sobrenome: mae.ausente ? null : mae.sobrenome,
      mae_telefone: mae.ausente ? null : mae.telefone,
      mae_email: mae.ausente ? null : mae.email,
      mae_data_nascimento: mae.ausente ? null : parseDate(mae.data_nascimento ?? ''),
      mae_cep: mae.ausente ? null : mae.cep,
      mae_bairro: mae.ausente ? null : mae.bairro,
      mae_cidade: mae.ausente ? null : mae.cidade,
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
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
        <div className="bg-white rounded-3xl shadow-xl p-10 max-w-md w-full text-center">
          <div className="w-20 h-20 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-6">
            <svg className="w-10 h-10 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
          </div>
          <h2 className="text-2xl font-bold text-gray-800 mb-2">Cadastro realizado!</h2>
          <p className="text-gray-500 mb-8">Os dados foram salvos com sucesso.</p>
          <button
            onClick={() => { setSuccess(false); setStep(0); setMenor(null); setPai(null) }}
            className="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3.5 rounded-xl transition-all duration-200"
          >
            Novo cadastro
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
      <div className="bg-white rounded-3xl shadow-xl w-full max-w-lg overflow-hidden">
        <div className="bg-gradient-to-r from-blue-600 to-indigo-600 px-8 pt-8 pb-6">
          <Stepper steps={STEPS} current={step} />
          <h2 className="text-white text-xl font-bold text-center">
            {step === 0 && 'Dados do Menor'}
            {step === 1 && 'Dados do Pai'}
            {step === 2 && 'Dados da Mãe'}
          </h2>
          <p className="text-blue-200 text-sm text-center mt-1">
            Etapa {step + 1} de {STEPS.length}
          </p>
        </div>

        <div className="p-6 sm:p-8">
          {error && (
            <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-xl text-sm text-red-600 flex items-center gap-2">
              <svg className="w-4 h-4 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
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
              tipo="pai"
              defaultValues={pai ?? undefined}
              onBack={() => setStep(0)}
              onNext={(data) => { setPai(data); setStep(2) }}
            />
          )}

          {step === 2 && (
            <StepResponsavel
              tipo="mae"
              onBack={() => setStep(1)}
              onNext={handleFinalSubmit}
              isLast
              loading={loading}
            />
          )}
        </div>

        {step === 2 && (
          <div className="px-6 sm:px-8 pb-6 -mt-2">
            <p className="text-xs text-gray-400 text-center leading-relaxed">
              Ao salvar, você declara que leu e aceita os termos de consentimento para uso de dados conforme a{' '}
              <span className="text-blue-500 font-medium">LGPD — Lei Geral de Proteção de Dados</span>.
            </p>
          </div>
        )}
      </div>
    </div>
  )
}
