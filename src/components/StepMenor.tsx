import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { useState } from 'react'
import { menorSchema } from '../lib/schemas'
import type { MenorData } from '../lib/schemas'
import { fetchCep } from '../lib/viaCep'
import { FormField } from './FormField'

interface StepMenorProps {
  defaultValues?: Partial<MenorData>
  onNext: (data: MenorData) => void
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

export function StepMenor({ defaultValues, onNext }: StepMenorProps) {
  const [cepLoading, setCepLoading] = useState(false)

  const { register, handleSubmit, setValue, formState: { errors } } = useForm<MenorData>({
    resolver: zodResolver(menorSchema),
    defaultValues,
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
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <FormField
          label="Nome"
          required
          placeholder="Nome do menor"
          error={errors.nome?.message}
          {...register('nome')}
        />
        <FormField
          label="Sobrenome"
          required
          placeholder="Sobrenome do menor"
          error={errors.sobrenome?.message}
          {...register('sobrenome')}
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

      <button
        type="submit"
        className="mt-2 w-full bg-blue-600 hover:bg-blue-700 active:bg-blue-800 text-white font-semibold py-3.5 rounded-xl transition-all duration-200 shadow-md shadow-blue-200 flex items-center justify-center gap-2"
      >
        Próximo
        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
        </svg>
      </button>
    </form>
  )
}
