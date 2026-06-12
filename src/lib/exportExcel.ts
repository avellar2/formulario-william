import ExcelJS from 'exceljs'

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

function fmt(date: string | null): string {
  if (!date) return '—'
  const [y, m, d] = date.split('-')
  return `${d}/${m}/${y}`
}

function fmtDateTime(date: string): string {
  return new Date(date).toLocaleString('pt-BR', {
    day: '2-digit', month: '2-digit', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
  })
}

export async function exportToExcel(cadastros: Cadastro[]) {
  const wb = new ExcelJS.Workbook()
  wb.creator = 'Cadastro App'
  wb.created = new Date()

  // ── Cores ──────────────────────────────────────────
  const AZUL_HEADER  = '1E40AF'   // azul escuro
  const AZUL_LIGHT   = 'DBEAFE'   // azul claro (linha par)
  const BRANCO       = 'FFFFFF'
  const VERDE_HEADER = '065F46'
  const VERDE_LIGHT  = 'D1FAE5'
  const ROSA_HEADER  = '9D174D'
  const ROSA_LIGHT   = 'FCE7F3'

  // ── Helpers ────────────────────────────────────────
  function headerStyle(bgHex: string): Partial<ExcelJS.Style> {
    return {
      font:      { bold: true, color: { argb: 'FFFFFFFF' }, size: 11 },
      fill:      { type: 'pattern', pattern: 'solid', fgColor: { argb: `FF${bgHex}` } },
      alignment: { horizontal: 'center', vertical: 'middle', wrapText: true },
      border: {
        top:    { style: 'thin', color: { argb: 'FFCBD5E1' } },
        left:   { style: 'thin', color: { argb: 'FFCBD5E1' } },
        bottom: { style: 'thin', color: { argb: 'FFCBD5E1' } },
        right:  { style: 'thin', color: { argb: 'FFCBD5E1' } },
      },
    }
  }

  function cellStyle(bgHex: string): Partial<ExcelJS.Style> {
    return {
      font:      { size: 10, color: { argb: 'FF1E293B' } },
      fill:      { type: 'pattern', pattern: 'solid', fgColor: { argb: `FF${bgHex}` } },
      alignment: { horizontal: 'left', vertical: 'middle', wrapText: false },
      border: {
        top:    { style: 'hair', color: { argb: 'FFE2E8F0' } },
        left:   { style: 'hair', color: { argb: 'FFE2E8F0' } },
        bottom: { style: 'hair', color: { argb: 'FFE2E8F0' } },
        right:  { style: 'hair', color: { argb: 'FFE2E8F0' } },
      },
    }
  }

  // ══════════════════════════════════════════════════
  // ABA 1 — Todos os dados
  // ══════════════════════════════════════════════════
  const ws = wb.addWorksheet('Cadastros', {
    views: [{ state: 'frozen', ySplit: 2 }],
  })

  // Título mesclado
  ws.mergeCells('A1:X1')
  const titleCell = ws.getCell('A1')
  titleCell.value = `CADASTROS — exportado em ${new Date().toLocaleDateString('pt-BR')}`
  titleCell.style = {
    font:      { bold: true, size: 14, color: { argb: 'FFFFFFFF' } },
    fill:      { type: 'pattern', pattern: 'solid', fgColor: { argb: `FF${AZUL_HEADER}` } },
    alignment: { horizontal: 'center', vertical: 'middle' },
  }
  ws.getRow(1).height = 32

  // Cabeçalhos
  const headers = [
    'Data Cadastro',
    // Menor
    'Menor — Nome', 'Menor — Sobrenome', 'Menor — Nascimento',
    'Menor — CEP', 'Menor — Bairro', 'Menor — Cidade',
    // Pai
    'Pai — Nome', 'Pai — Sobrenome', 'Pai — Telefone', 'Pai — E-mail',
    'Pai — Nascimento', 'Pai — CEP', 'Pai — Bairro', 'Pai — Cidade',
    // Mãe
    'Mãe — Nome', 'Mãe — Sobrenome', 'Mãe — Telefone', 'Mãe — E-mail',
    'Mãe — Nascimento', 'Mãe — CEP', 'Mãe — Bairro', 'Mãe — Cidade',
  ]

  const headerRow = ws.getRow(2)
  headerRow.height = 36
  headers.forEach((h, i) => {
    const col = i + 1
    const cell = headerRow.getCell(col)
    cell.value = h

    // Cor por grupo
    if (i === 0)             cell.style = headerStyle(AZUL_HEADER)
    else if (i >= 1 && i <= 6)  cell.style = headerStyle('1D4ED8')   // menor
    else if (i >= 7 && i <= 14) cell.style = headerStyle(VERDE_HEADER) // pai
    else                         cell.style = headerStyle(ROSA_HEADER)  // mãe
  })

  // Larguras das colunas
  const widths = [18, 14,16,14, 12,16,22, 14,16,16,26, 14,12,16,22, 14,16,16,26, 14,12,16,22]
  widths.forEach((w, i) => { ws.getColumn(i + 1).width = w })

  // Dados
  cadastros.forEach((c, idx) => {
    const isEven = idx % 2 === 0
    const bgMenor = isEven ? AZUL_LIGHT  : BRANCO
    const bgPai   = isEven ? VERDE_LIGHT : BRANCO
    const bgMae   = isEven ? ROSA_LIGHT  : BRANCO
    const bgBase  = isEven ? 'F1F5F9'    : BRANCO

    const values = [
      fmtDateTime(c.created_at),
      c.menor_nome, c.menor_sobrenome, fmt(c.menor_data_nascimento),
      c.menor_cep, c.menor_bairro, c.menor_cidade,
      c.tem_pai ? (c.pai_nome ?? '—') : 'NÃO INFORMADO',
      c.tem_pai ? (c.pai_sobrenome ?? '—') : '',
      c.tem_pai ? (c.pai_telefone ?? '—') : '',
      c.tem_pai ? (c.pai_email ?? '—') : '',
      c.tem_pai ? fmt(c.pai_data_nascimento) : '',
      c.tem_pai ? (c.pai_cep ?? '—') : '',
      c.tem_pai ? (c.pai_bairro ?? '—') : '',
      c.tem_pai ? (c.pai_cidade ?? '—') : '',
      c.tem_mae ? (c.mae_nome ?? '—') : 'NÃO INFORMADA',
      c.tem_mae ? (c.mae_sobrenome ?? '—') : '',
      c.tem_mae ? (c.mae_telefone ?? '—') : '',
      c.tem_mae ? (c.mae_email ?? '—') : '',
      c.tem_mae ? fmt(c.mae_data_nascimento) : '',
      c.tem_mae ? (c.mae_cep ?? '—') : '',
      c.tem_mae ? (c.mae_bairro ?? '—') : '',
      c.tem_mae ? (c.mae_cidade ?? '—') : '',
    ]

    const row = ws.addRow(values)
    row.height = 22
    values.forEach((_, i) => {
      const cell = row.getCell(i + 1)
      if (i === 0)              cell.style = cellStyle(bgBase)
      else if (i >= 1 && i <= 6)  cell.style = cellStyle(bgMenor)
      else if (i >= 7 && i <= 14) cell.style = cellStyle(bgPai)
      else                         cell.style = cellStyle(bgMae)
    })
  })

  // ── Download ───────────────────────────────────────
  const buffer = await wb.xlsx.writeBuffer()
  const blob   = new Blob([buffer], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' })
  const url    = URL.createObjectURL(blob)
  const a      = document.createElement('a')
  a.href       = url
  a.download   = `cadastros_${new Date().toISOString().slice(0, 10)}.xlsx`
  a.click()
  URL.revokeObjectURL(url)
}
