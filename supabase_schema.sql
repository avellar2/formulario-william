-- Execute no SQL Editor do Supabase
CREATE TABLE cadastros (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  created_at TIMESTAMPTZ DEFAULT NOW(),

  -- Menor
  menor_nome TEXT NOT NULL,
  menor_sobrenome TEXT NOT NULL,
  menor_data_nascimento DATE NOT NULL,
  menor_cep TEXT NOT NULL,
  menor_bairro TEXT NOT NULL,
  menor_cidade TEXT NOT NULL,

  -- Pai
  tem_pai BOOLEAN NOT NULL DEFAULT TRUE,
  pai_nome TEXT,
  pai_sobrenome TEXT,
  pai_telefone TEXT,
  pai_email TEXT,
  pai_data_nascimento DATE,
  pai_cep TEXT,
  pai_bairro TEXT,
  pai_cidade TEXT,

  -- Mãe
  tem_mae BOOLEAN NOT NULL DEFAULT TRUE,
  mae_nome TEXT,
  mae_sobrenome TEXT,
  mae_telefone TEXT,
  mae_email TEXT,
  mae_data_nascimento DATE,
  mae_cep TEXT,
  mae_bairro TEXT,
  mae_cidade TEXT
);

-- Permitir inserção pública (anon)
ALTER TABLE cadastros ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Allow public insert" ON cadastros
  FOR INSERT TO anon WITH CHECK (true);

-- Somente usuário autenticado pode ver os cadastros
CREATE POLICY "Allow authenticated select" ON cadastros
  FOR SELECT TO authenticated USING (true);
