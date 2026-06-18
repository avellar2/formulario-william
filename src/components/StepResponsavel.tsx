import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { useState } from 'react'
import { responsavelSchema } from '../lib/schemas'
import type { ResponsavelData } from '../lib/schemas'
import { fetchCep } from '../lib/viaCep'
import { FormField } from './FormField'

interface StepResponsavelProps {
  titulo: string
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

export function StepResponsavel({ titulo, defaultValues, onNext, onBack, isLast, loading }: StepResponsavelProps) {
  const [cepLoading, setCepLoading] = useState(false)

  const { register, handleSubmit, setValue, formState: { errors } } = useForm<ResponsavelData>({
    resolver: zodResolver(responsavelSchema),
    defaultValues: { nome: '', sobrenome: '', telefone: '', email: '', data_nascimento: '', cep: '', bairro: '', cidade: '', ...defaultValues },
  })

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
      <div className="mb-2">
        <h3 className="text-lg font-semibold text-gray-900">{titulo}</h3>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
        <FormField
          label="Nome"
          required
          placeholder="Primeiro nome"
          error={errors.nome?.message}
          {...register('nome')}
        />
        <FormField
          label="Sobrenome"
          required
          placeholder="Sobrenome"
          error={errors.sobrenome?.message}
          {...register('sobrenome')}
        />
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
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

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
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

      <div className="flex gap-3 mt-4">
        <button
          type="button"
          onClick={onBack}
          className="flex-1 bg-white hover:bg-gray-50 text-gray-700 font-medium py-3.5 rounded-lg border border-gray-200 transition-all duration-200"
        >
          Voltar
        </button>

        <button
          type="submit"
          disabled={loading}
          className="flex-1 bg-gradient-to-r from-orange-500 to-amber-500 hover:from-orange-600 hover:to-amber-600 disabled:opacity-50 text-white font-medium py-3.5 rounded-lg transition-all duration-200 hover:shadow-lg hover:shadow-orange-100"
        >
          {loading ? (
            <span className="flex items-center justify-center gap-2">
              <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
              Salvando...
            </span>
          ) : isLast ? (
            'Confirmar Inscrição'
          ) : (
            'Continuar'
          )}
        </button>
      </div>
    </form>
  )
}
