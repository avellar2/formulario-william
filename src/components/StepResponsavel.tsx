import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { useState } from 'react'
import { responsavelSchema } from '../lib/schemas'
import type { ResponsavelData } from '../lib/schemas'
import { fetchCep } from '../lib/viaCep'
import { FormField } from './FormField'

interface StepResponsavelProps {
  tipo: 'pai' | 'mae'
  defaultValues?: Partial<ResponsavelData>
  onNext: (data: ResponsavelData) => void
  onBack: () => void
  isLast?: boolean
  loading?: boolean
}

function maskPhone(value: string): string {
  return value
    .replace(/\D/g, '')
    .replace(/(\d{2})(\d)/, '($1) $2')
    .replace(/(\d{5})(\d)/, '$1-$2')
    .slice(0, 15)
}

function maskDate(value: string): string {
  return value
    .replace(/\D/g, '')
    .replace(/(\d{2})(\d)/, '$1/$2')
    .replace(/(\d{2})\/(\d{2})(\d)/, '$1/$2/$3')
    .slice(0, 10)
}

function maskCep(value: string): string {
  return value.replace(/\D/g, '').replace(/(\d{5})(\d)/, '$1-$2').slice(0, 9)
}

export function StepResponsavel({ tipo, defaultValues, onNext, onBack, isLast, loading }: StepResponsavelProps) {
  const [cepLoading, setCepLoading] = useState(false)

  const label = tipo === 'pai' ? 'Pai' : 'Mãe'
  const ausenteLabel = tipo === 'pai' ? 'Pai não está presente / não informado' : 'Mãe não está presente / não informada'

  const { register, handleSubmit, setValue, watch, formState: { errors } } = useForm<ResponsavelData>({
    resolver: zodResolver(responsavelSchema),
    defaultValues: { ausente: false, nome: '', sobrenome: '', telefone: '', email: '', data_nascimento: '', cep: '', bairro: '', cidade: '', ...defaultValues },
  })

  const ausente = watch('ausente')

  async function handleCepBlur(cep: string) {
    if (cep.replace(/\D/g, '').length !== 8) return
    setCepLoading(true)
    const data = await fetchCep(cep)
    if (data) {
      setValue('bairro', data.bairro, { shouldValidate: true })
      setValue('cidade', `${data.localidade} - ${data.uf}`, { shouldValidate: true })
    }
    setCepLoading(false)
  }

  return (
    <form onSubmit={handleSubmit(onNext)} className="flex flex-col gap-5">
      {/* Toggle ausente */}
      <label className="flex items-center gap-3 p-4 bg-amber-50 border border-amber-200 rounded-xl cursor-pointer select-none group">
        <div className="relative">
          <input
            type="checkbox"
            className="sr-only peer"
            {...register('ausente')}
          />
          <div className="w-11 h-6 bg-gray-300 peer-checked:bg-amber-500 rounded-full transition-colors duration-200" />
          <div className="absolute top-0.5 left-0.5 w-5 h-5 bg-white rounded-full shadow transition-transform duration-200 peer-checked:translate-x-5" />
        </div>
        <span className="text-sm font-medium text-amber-800">{ausenteLabel}</span>
      </label>

      {!ausente && (
        <>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <FormField
              label={`Nome do ${label}`}
              required
              placeholder={`Nome`}
              error={errors.nome?.message}
              {...register('nome')}
            />
            <FormField
              label={`Sobrenome do ${label}`}
              required
              placeholder={`Sobrenome`}
              error={errors.sobrenome?.message}
              {...register('sobrenome')}
            />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <FormField
              label="Telefone"
              required
              placeholder="(00) 00000-0000"
              error={errors.telefone?.message}
              {...register('telefone')}
              onChange={(e) => {
                e.target.value = maskPhone(e.target.value)
                register('telefone').onChange(e)
              }}
            />
            <FormField
              label="E-mail"
              required
              type="email"
              placeholder="email@exemplo.com"
              error={errors.email?.message}
              {...register('email')}
            />
          </div>

          <FormField
            label="Data de Nascimento"
            required
            placeholder="DD/MM/AAAA"
            error={errors.data_nascimento?.message}
            {...register('data_nascimento')}
            onChange={(e) => {
              e.target.value = maskDate(e.target.value)
              register('data_nascimento').onChange(e)
            }}
          />

          <FormField
            label="CEP"
            required
            placeholder="00000-000"
            loading={cepLoading}
            error={errors.cep?.message}
            {...register('cep')}
            onChange={(e) => {
              e.target.value = maskCep(e.target.value)
              register('cep').onChange(e)
            }}
            onBlur={(e) => handleCepBlur(e.target.value)}
          />

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <FormField
              label="Bairro"
              required
              placeholder="Preenchido automaticamente"
              error={errors.bairro?.message}
              {...register('bairro')}
            />
            <FormField
              label="Cidade"
              required
              placeholder="Preenchido automaticamente"
              error={errors.cidade?.message}
              {...register('cidade')}
            />
          </div>
        </>
      )}

      <div className="flex gap-3 mt-2">
        <button
          type="button"
          onClick={onBack}
          className="flex-1 bg-white hover:bg-gray-50 text-gray-600 font-semibold py-3.5 rounded-xl border border-gray-200 transition-all duration-200 flex items-center justify-center gap-2"
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
          Voltar
        </button>

        <button
          type="submit"
          disabled={loading}
          className="flex-1 bg-blue-600 hover:bg-blue-700 active:bg-blue-800 disabled:opacity-60 text-white font-semibold py-3.5 rounded-xl transition-all duration-200 shadow-md shadow-blue-200 flex items-center justify-center gap-2"
        >
          {loading ? (
            <>
              <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
              Salvando...
            </>
          ) : isLast ? (
            <>
              Salvar
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            </>
          ) : (
            <>
              Próximo
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
            </>
          )}
        </button>
      </div>
    </form>
  )
}
