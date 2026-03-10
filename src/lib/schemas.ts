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
  ausente: z.boolean(),
  nome: z.string().optional(),
  sobrenome: z.string().optional(),
  telefone: z.string().optional(),
  email: z.string().optional(),
  data_nascimento: z.string().optional(),
  cep: z.string().optional(),
  bairro: z.string().optional(),
  cidade: z.string().optional(),
}).superRefine((data, ctx) => {
  if (!data.ausente) {
    if (!data.nome || data.nome.length < 2)
      ctx.addIssue({ code: z.ZodIssueCode.custom, message: 'Nome obrigatório', path: ['nome'] })
    if (!data.sobrenome || data.sobrenome.length < 2)
      ctx.addIssue({ code: z.ZodIssueCode.custom, message: 'Sobrenome obrigatório', path: ['sobrenome'] })
    if (!data.telefone || data.telefone.length < 14)
      ctx.addIssue({ code: z.ZodIssueCode.custom, message: 'Telefone obrigatório', path: ['telefone'] })
    if (!data.email || !data.email.includes('@'))
      ctx.addIssue({ code: z.ZodIssueCode.custom, message: 'E-mail inválido', path: ['email'] })
    if (!data.data_nascimento)
      ctx.addIssue({ code: z.ZodIssueCode.custom, message: 'Data obrigatória', path: ['data_nascimento'] })
    if (!data.cep || data.cep.length < 9)
      ctx.addIssue({ code: z.ZodIssueCode.custom, message: 'CEP inválido', path: ['cep'] })
    if (!data.bairro || data.bairro.length < 2)
      ctx.addIssue({ code: z.ZodIssueCode.custom, message: 'Bairro obrigatório', path: ['bairro'] })
    if (!data.cidade || data.cidade.length < 2)
      ctx.addIssue({ code: z.ZodIssueCode.custom, message: 'Cidade obrigatória', path: ['cidade'] })
  }
})

export type MenorData = z.infer<typeof menorSchema>
export type ResponsavelData = z.infer<typeof responsavelSchema>
