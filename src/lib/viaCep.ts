export interface ViaCepResponse {
  logradouro: string
  bairro: string
  localidade: string
  uf: string
  erro?: boolean
}

export async function fetchCep(cep: string): Promise<ViaCepResponse | null> {
  const clean = cep.replace(/\D/g, '')
  if (clean.length !== 8) return null
  try {
    const res = await fetch(`https://viacep.com.br/ws/${clean}/json/`)
    const data: ViaCepResponse = await res.json()
    if (data.erro) return null
    return data
  } catch {
    return null
  }
}
