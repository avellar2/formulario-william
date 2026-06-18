import { z } from 'zod'

export const menorSchema = z.object({
  nome: z.string().min(2, 'Nome obrigatório'),
  sobrenome: z.string().min(2, 'Sobrenome obrigatório'),
  data_nascimento: z.string().min(1, 'Data de nascimento obrigatória'),
  cep: z.string().length(9, 'CEP inválido'),
  bairro: z.string().min(2, 'Bairro obrigatório'),
  cidade: z.string().min(2, 'Cidade obrigatória'),
})

export const responsavelSchema = z.object({
  nome: z.string().min(2, 'Nome obrigatório'),
  sobrenome: z.string().min(2, 'Sobrenome obrigatório'),
  telefone: z.string().min(14, 'Telefone obrigatório'),
  email: z.string().email('E-mail inválido'),
  data_nascimento: z.string().min(1, 'Data obrigatória'),
  cep: z.string().length(9, 'CEP inválido'),
  bairro: z.string().min(2, 'Bairro obrigatório'),
  cidade: z.string().min(2, 'Cidade obrigatória'),
})

export type MenorData = z.infer<typeof menorSchema>
export type ResponsavelData = z.infer<typeof responsavelSchema>
