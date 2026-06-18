"""
BigData Sender - Envia dados de pai/mae para bigdata.app.br via Playwright

Modo automatico: python bigdata_sender.py --auto
Modo manual:     python bigdata_sender.py
"""

import json
import sys
import glob
import os
import time
import re
from dotenv import load_dotenv
from supabase import create_client
from playwright.sync_api import sync_playwright

BIGDATA_URL = "https://bigdata.app.br/77/meuscadastros_add.php?codigo=MU7NWKAJ"


def init_supabase():
    """Inicializa cliente Supabase com anon key (lendo de .env.local)."""
    load_dotenv(".env.local")
    url = os.getenv("VITE_SUPABASE_URL")
    key = os.getenv("VITE_SUPABASE_ANON_KEY")
    if not url or not key:
        print("Erro: VITE_SUPABASE_URL e VITE_SUPABASE_ANON_KEY precisam estar em .env.local")
        sys.exit(1)
    return create_client(url, key)


def carregar_cadastros() -> list:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if args:
        caminho = args[0]
    else:
        arquivos = sorted(glob.glob("cadastros_*.json"), reverse=True)
        if not arquivos:
            print("\n  Nenhum arquivo cadastros_*.json encontrado.")
            print("  Exporte o JSON pelo painel admin e coloque na mesma pasta deste script.\n")
            sys.exit(1)
        caminho = arquivos[0]
        print(f"\n  Usando arquivo: {caminho}")

    with open(caminho, "r", encoding="utf-8") as f:
        return json.load(f)


def formatar_data(data_iso: str | None) -> str:
    if not data_iso:
        return ""
    partes = data_iso.split("-")
    if len(partes) != 3:
        return data_iso
    return f"{partes[2]}/{partes[1]}/{partes[0]}"


def ajustar_telefone_duplicado(telefone_pai: str, telefone_mae: str) -> str:
    """Se pai e mae tiverem o mesmo telefone, altera os 2 ultimos digitos da mae."""
    if not telefone_pai or not telefone_mae:
        return telefone_mae

    digits_pai = "".join(c for c in telefone_pai if c.isdigit())
    digits_mae = "".join(c for c in telefone_mae if c.isdigit())

    if digits_pai == digits_mae and len(digits_mae) >= 2:
        ultimos = int(digits_mae[-2:])
        substitutos = max(0, ultimos - 9)
        novo = digits_mae[:-2] + str(substitutos).zfill(2)
        print(f"    Telefone duplicado detectado! Ajustando mae: {telefone_mae} -> {novo}")
        return novo

    return telefone_mae


def telefones_sao_iguais(telefone_pai: str, telefone_mae: str) -> bool:
    """Verifica se dois telefones sao iguais (comparando apenas digitos)."""
    if not telefone_pai or not telefone_mae:
        return False
    digits_pai = "".join(c for c in telefone_pai if c.isdigit())
    digits_mae = "".join(c for c in telefone_mae if c.isdigit())
    return digits_pai == digits_mae


def extrair_dados(cadastro: dict, prefixo: str, telefone_mae_ajustado: str | None = None) -> dict | None:
    """Extrai os dados do responsavel."""
    if not cadastro.get(f"tem_{prefixo}"):
        return None

    nome_completo = cadastro.get(f"{prefixo}_nome") or ""
    partes = nome_completo.strip().split(" ", 1)
    primeiro_nome = partes[0] if partes else ""
    sobrenome_db = cadastro.get(f"{prefixo}_sobrenome") or ""
    sobrenome_final = sobrenome_db if sobrenome_db else (partes[1] if len(partes) > 1 else "")

    telefone_raw = cadastro.get(f"{prefixo}_telefone") or ""
    # Se for a mae e tiver telefone ajustado, usa o ajustado
    if prefixo == "mae" and telefone_mae_ajustado is not None:
        telefone_digits = telefone_mae_ajustado
    else:
        telefone_digits = "".join(c for c in telefone_raw if c.isdigit())

    return {
        "tipo": prefixo,
        "nome": primeiro_nome,
        "sobrenome": sobrenome_final,
        "telefone": telefone_digits,
        "email": cadastro.get(f"{prefixo}_email") or "",
        "data_nascimento": formatar_data(cadastro.get(f"{prefixo}_data_nascimento")),
        "cep": (cadastro.get(f"{prefixo}_cep") or "").replace("-", ""),
        "bairro": cadastro.get(f"{prefixo}_bairro") or "",
        "cidade": cadastro.get(f"{prefixo}_cidade") or "",
    }


def marcar_enviado(supabase, cadastro_id: str, tipo: str):
    """Marca pai/mae como enviado via funcao SECURITY DEFINER no banco."""
    try:
        supabase.rpc("marcar_enviado_bigdata", {
            "p_cadastro_id": cadastro_id,
            "p_tipo": tipo
        }).execute()
        return True
    except Exception as e:
        print(f"    Erro ao marcar {tipo} como enviado: {e}")
        return False


def preencher_campo(page, label: str, valor: str):
    """Preenche um campo de formulario buscando por label, placeholder ou name."""
    if not valor:
        return
    # Tenta por label (get_by_label)
    try:
        campo = page.get_by_label(label, exact=False).first
        if campo.is_visible(timeout=1500):
            campo.fill(valor)
            return
    except Exception:
        pass
    # Tenta por placeholder
    try:
        campo = page.locator(f"input[placeholder*='{label}']").first
        if campo.is_visible(timeout=1500):
            campo.fill(valor)
            return
    except Exception:
        pass
    # Tenta por name/id com texto similar
    try:
        label_lower = label.lower().replace("-", "").replace(" ", "")
        campo = page.locator(f"input[name*='{label_lower}'], input[id*='{label_lower}']").first
        if campo.is_visible(timeout=1500):
            campo.fill(valor)
            return
    except Exception:
        pass


def aceitar_cookies(page):
    """Tenta aceitar o banner de cookies/LGPD de diversas formas."""
    # Aguarda um pouco para o banner aparecer
    page.wait_for_timeout(500)

    seletores = [
        # Botao OK
        page.get_by_role("button", name=re.compile(r"^ok$", re.IGNORECASE)),
        page.locator("button:has-text('OK')"),
        # Botao Concordo/Aceito
        page.get_by_role("button", name=re.compile(r"concordo|aceito|aceitar", re.IGNORECASE)),
        page.get_by_text(re.compile(r"eu concordo|eu aceito", re.IGNORECASE)),
        page.locator("button:has-text('Concordo'), button:has-text('Aceito')"),
        page.locator("a:has-text('OK'), a:has-text('Concordo'), a:has-text('Aceito')"),
        # Links e botoes dentro de divs de cookie/lgpd
        page.locator("[id*='cookie'] button, [class*='cookie'] button, [id*='lgpd'] button, [class*='lgpd'] button"),
        page.locator("[id*='cookie'] a, [class*='cookie'] a, [class*='lgpd'] a"),
        page.locator("[class*='cookie'] input[type='button'], [class*='cookie'] input[type='submit']"),
        # Botao fechar (X) do banner
        page.locator("[class*='cookie'] [class*='close'], [class*='cookie'] button[aria-label*='close'], [class*='cookie'] .close"),
        page.locator("[id*='lgpd'] [class*='close'], [id*='lgpd'] button[aria-label*='close'], [id*='lgpd'] .close"),
    ]

    for seletor in seletores:
        try:
            if seletor.first.is_visible(timeout=1500):
                seletor.first.click()
                print(f"    Cookies aceitos")
                page.wait_for_timeout(500)
                return True
        except Exception:
            continue

    # Ultima tentativa: procura qualquer botao visivel dentro de div de cookie/lgpd
    try:
        cookie_div = page.locator("[id*='cookie'], [class*='cookie'], [id*='lgpd'], [class*='lgpd']").first
        if cookie_div.is_visible(timeout=1000):
            btn = cookie_div.locator("button, a, input[type='button'], input[type='submit']").first
            if btn.is_visible(timeout=1000):
                btn.click()
                print(f"    Cookies aceitos (botao generico)")
                page.wait_for_timeout(500)
                return True
    except Exception:
        pass

    print(f"    Nenhum banner de cookies encontrado (pode ja ter sido aceito)")
    return False


def preencher_email(page, email: str):
    """Preenche o campo de email ou marca 'nao tenho email'."""
    if email:
        # Tem email - tenta preencher o campo com múltiplas estratégias
        estrategias = [
            ("label E-mail", lambda: page.get_by_label("E-mail", exact=False).first),
            ("label Email", lambda: page.get_by_label("Email", exact=False).first),
            ("label e-mail", lambda: page.get_by_label("e-mail", exact=False).first),
            ("placeholder email", lambda: page.locator("input[placeholder*='email' i]").first),
            ("placeholder E-mail", lambda: page.locator("input[placeholder*='E-mail']").first),
            ("name email", lambda: page.locator("input[name*='email' i]").first),
            ("id email", lambda: page.locator("input[id*='email' i]").first),
            ("type email", lambda: page.locator("input[type='email']").first),
        ]

        for nome, get_campo in estrategias:
            try:
                campo = get_campo()
                if campo.is_visible(timeout=800):
                    campo.fill(email)
                    print(f"    Email preenchido ({nome})")
                    return True
            except Exception:
                continue

        # Última tentativa: procura qualquer input visível após o campo de telefone
        try:
            inputs = page.locator("input[type='text'], input[type='email']")
            for i in range(inputs.count()):
                inp = inputs.nth(i)
                try:
                    if inp.is_visible(timeout=500):
                        # Verifica se está perto de texto "email"
                        parent = inp.locator("xpath=ancestor::*[position() < 10]")
                        parent_text = parent.text_content() or ""
                        if "email" in parent_text.lower():
                            inp.fill(email)
                            print(f"    Email preenchido (input proximo ao texto email)")
                            return True
                except Exception:
                    continue
        except Exception:
            pass

        print(f"    AVISO: Campo de email nao encontrado - tentando continuar sem email")
        return False
    else:
        # Nao tem email - marca "nao tenho email"
        print(f"    Email vazio, marcando 'nao tenho email'...")

        # Tenta clicar no texto "nao tenho email"
        try:
            label = page.get_by_text(re.compile(r"n[aã]o tenho email", re.IGNORECASE)).first
            if label.is_visible(timeout=2000):
                label.click()
                page.wait_for_timeout(300)
                print(f"    Checkbox 'nao tenho email' marcado via label")
                return True
        except Exception:
            pass

        # Tenta encontrar e marcar o checkbox diretamente
        try:
            checkboxes = page.locator("input[type='checkbox']")
            total = checkboxes.count()

            for i in range(total):
                cb = checkboxes.nth(i)
                try:
                    parent = cb.locator("..")
                    parent_text = parent.text_content() or ""
                    if re.search(r"n[aã]o tenho email", parent_text, re.IGNORECASE):
                        if not cb.is_checked():
                            cb.check()
                        print(f"    Checkbox 'nao tenho email' marcado (indice {i})")
                        return True
                except Exception:
                    continue

            # Fallback: marca o segundo checkbox (geralmente e "nao tenho email")
            if total >= 2:
                cb = checkboxes.nth(1)
                if not cb.is_checked():
                    cb.check()
                print(f"    Segundo checkbox marcado (assumindo 'nao tenho email')")
                return True
        except Exception:
            pass

        print(f"    AVISO: Nao consegui marcar 'nao tenho email'")
        return False


def marcar_checkbox_aceito(page):
    """Marca o checkbox 'Aceito' dos termos."""
    # Tenta clicar no texto do label primeiro
    try:
        aceito = page.get_by_text(re.compile(r"aceito|li e aceito|concordo com os termos", re.IGNORECASE)).first
        if aceito.is_visible(timeout=2000):
            aceito.click()
            print(f"    Checkbox 'Aceito' marcado via texto")
            return True
    except Exception:
        pass

    # Tenta encontrar o checkbox pelo label associado
    try:
        labels = page.locator("label")
        total = labels.count()
        for i in range(total):
            label = labels.nth(i)
            try:
                text = label.text_content() or ""
                if re.search(r"aceito|li e aceito|concordo", text, re.IGNORECASE):
                    label.click()
                    print(f"    Checkbox 'Aceito' marcado via label (indice {i})")
                    return True
            except Exception:
                continue
    except Exception:
        pass

    # Fallback: marca o primeiro checkbox visível
    try:
        checkbox = page.locator("input[type='checkbox']").first
        if checkbox.is_visible(timeout=2000) and not checkbox.is_checked():
            checkbox.check()
            print(f"    Primeiro checkbox marcado (assumindo 'Aceito')")
            return True
    except Exception:
        pass

    print(f"    AVISO: Nao consegui marcar checkbox 'Aceito'")
    return False


def submeter_formulario(page) -> bool:
    """Tenta submeter o formulario de diversas formas. Retorna True se submeteu."""
    page.wait_for_timeout(3000)

    # Debug completo: lista tudo que parece clicavel
    try:
        info = page.evaluate("""() => {
            const result = { buttons: 0, submits: 0, links: 0, clickableDivs: 0, forms: 0 };
            const all = document.querySelectorAll('button, input[type="submit"], input[type="button"], a, [onclick], .btn, .button, .salvar, .enviar, [class*="submit"], [class*="btn"]');
            result.total = all.length;
            const arr = [];
            all.forEach(el => {
                const tag = el.tagName.toLowerCase();
                const text = (el.textContent || el.value || '').trim().substring(0, 50);
                const cls = el.className || '';
                const id = el.id || '';
                const type = el.getAttribute('type') || '';
                arr.push(tag + ': text="' + text + '" class="' + cls + '" id="' + id + '" type="' + type + '"');
            });
            result.items = arr.slice(0, 10);
            result.forms = document.querySelectorAll('form').length;
            return result;
        }""")
        total = info.get('total', 0)
        forms = info.get('forms', 0)
        print(f"    Encontrados {total} elementos clicaveis, {forms} forms")
        for item in info.get('items', []):
            print(f"      {item}")
    except Exception as e:
        print(f"    Debug JS falhou: {e}")

    # HTML dump do form para debug
    try:
        html_form = page.evaluate("""() => {
            const form = document.querySelector('form');
            if (form) return form.outerHTML.substring(0, 2000);
            return document.body.innerHTML.substring(0, 2000);
        }""")
        print(f"    HTML do form (primeiros 500 chars):")
        print(f"    {html_form[:500]}")
    except Exception:
        pass

    # Verifica se tem iframe
    try:
        frames = page.frames
        for frame in frames:
            if frame != page.main_frame:
                try:
                    info_frame = frame.evaluate("""() => {
                        const btn = document.querySelector('button, input[type="submit"]');
                        return btn ? btn.outerHTML : 'sem botoes';
                    }""")
                    print(f"    Frame conteudo: {info_frame}")
                except Exception:
                    pass
    except Exception:
        pass

    # Tenta submeter com JavaScript puro (mais agressivo)
    try:
        resultado_js = page.evaluate("""() => {
            // Estrategia 1: procura qualquer elemento que pareça botao de submit
            const selectors = [
                'button[type="submit"]', 'input[type="submit"]',
                'button', '[type="submit"]',
                '.btn', '.button', '.salvar', '.enviar', '.submit',
                '[class*="btn"]', '[class*="button"]', '[class*="submit"]',
                'a.btn', 'a.button',
                '[onclick]'
            ];

            for (const sel of selectors) {
                const el = document.querySelector(sel);
                if (el) {
                    const text = (el.textContent || el.value || '').toLowerCase();
                    if (text.includes('salvar') || text.includes('enviar') || text.includes('cadastrar') || text.includes('submit')) {
                        el.click();
                        return 'clicou ' + sel + ': "' + text + '"';
                    }
                }
            }

            // Estrategia 2: procura o form e dispara submit
            const form = document.querySelector('form');
            if (form) {
                // Tenta o ultimo botao do form
                const lastBtn = form.querySelector('button:last-of-type, input[type="submit"]:last-of-type, button:last-child');
                if (lastBtn) {
                    lastBtn.click();
                    return 'clicou ultimo botao do form';
                }
                // Dispara submit direto
                form.submit();
                return 'form.submit() executado';
            }

            return 'nenhum form encontrado';
        }""")
        print(f"    JS: {resultado_js}")
        if 'clicou' in str(resultado_js) or 'submit' in str(resultado_js):
            return True
        if resultado_js == 'nenhum form encontrado':
            print(f"    ERRO CRITICO: Nenhum formulario encontrado na pagina!")
    except Exception as e:
        print(f"    JS falhou: {e}")

    # Fallback: tentativas normais de Playwright
    tentativas = [
        ("button[type=submit]", lambda: page.locator("button[type='submit']").first.click()),
        ("input[type=submit]", lambda: page.locator("input[type='submit']").first.click()),
        ("botao Salvar", lambda: page.locator("button:has-text('Salvar')").first.click()),
        ("botao Enviar", lambda: page.locator("button:has-text('Enviar')").first.click()),
        ("botao Cadastrar", lambda: page.locator("button:has-text('Cadastrar')").first.click()),
        ("primeiro botao", lambda: page.locator("button").first.click()),
        ("form button", lambda: page.locator("form button").first.click()),
    ]

    for nome, acao in tentativas:
        try:
            acao()
            print(f"    Formulario submetido via {nome}")
            return True
        except Exception:
            continue

    try:
        page.screenshot(path="botao_nao_encontrado.png")
        print(f"    Print salvo em botao_nao_encontrado.png")
    except Exception:
        pass

    return False


def verificar_telefone_ja_cadastrado(page) -> bool:
    """Verifica se aparece a mensagem 'TELEFONE JA CADASTRADO' na pagina."""
    page.wait_for_timeout(800)

    # Estratégia 1: Procura texto exato
    textos_possiveis = [
        r"telefone.*ja.*cadastrado",
        r"TELEFONE.*JA.*CADASTRADO",
        r"Telefone.*já.*cadastrado",
        r"Telefone.*ja.*cadastrado",
        r"ja.*cadastrado",
        r"já.*cadastrado",
    ]

    for padrao in textos_possiveis:
        try:
            texto = page.get_by_text(re.compile(padrao, re.IGNORECASE)).first
            if texto.is_visible(timeout=800):
                print(f"    Detectado: {padrao}")
                return True
        except Exception:
            continue

    # Estratégia 2: Procura em elementos com classe de erro
    try:
        erros = page.locator("[class*='error'], [class*='erro'], [class*='invalid'], [style*='red'], [style*='vermelho']")
        for i in range(erros.count()):
            try:
                el = erros.nth(i)
                if el.is_visible(timeout=500):
                    texto = el.text_content() or ""
                    if "cadastr" in texto.lower() and "telefone" in texto.lower():
                        print(f"    Detectado em elemento de erro: {texto}")
                        return True
            except Exception:
                continue
    except Exception:
        pass

    # Estratégia 3: Procura texto próximo ao campo de telefone
    try:
        campo_tel = page.get_by_label("Telefone", exact=False).first
        if campo_tel.is_visible(timeout=500):
            # Procura elementos próximos (irmãos ou filhos do pai)
            container = campo_tel.locator("xpath=ancestor::*[position() < 5]").first
            texto_container = container.text_content() or ""
            if "cadastr" in texto_container.lower() and "telefone" in texto_container.lower():
                print(f"    Detectado no container do telefone")
                return True
    except Exception:
        pass

    return False


def enviar_para_bigdata(dados: dict, tentativa: int = 1, telefones_iguais: bool = False) -> bool:
    """Abre o browser, preenche e submete. Retorna True se sucesso.
    
    telefones_iguais: True quando pai e mae tem o mesmo telefone (permite tentar com numero ajustado)
    """
    # So tenta de novo se for mae E os telefones forem iguais ao do pai
    max_tentativas = 3 if (dados.get("tipo") == "mae" and telefones_iguais) else 1
    telefone_atual = dados["telefone"]

    while tentativa <= max_tentativas:
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=False, slow_mo=200)
                page = browser.new_page()

                page.goto(BIGDATA_URL, wait_until="networkidle")
                page.wait_for_timeout(2000)

                # Aceita banner de cookies
                aceitar_cookies(page)
                page.wait_for_timeout(1000)

                # Preenche campos basicos
                preencher_campo(page, "Quem te indicou", "William da Rocha")
                preencher_campo(page, "Nome", dados["nome"])
                preencher_campo(page, "Sobrenome", dados["sobrenome"])

                # Telefone digito a digito para respeitar mascara
                try:
                    campo_tel = page.get_by_label("Telefone", exact=False).first
                    campo_tel.click()
                    campo_tel.press_sequentially(telefone_atual, delay=40)
                except Exception:
                    preencher_campo(page, "Telefone", telefone_atual)

                # Verifica se o telefone ja esta cadastrado (antes de continuar)
                page.wait_for_timeout(1500)
                if verificar_telefone_ja_cadastrado(page):
                    print(f"    Telefone ja cadastrado detectado antes do envio!")
                    browser.close()

                    # Se for pai, sempre pula
                    if dados.get("tipo") == "pai":
                        print(f"    Pai ja cadastrado no BigData. Pulando.")
                        return False

                    # Se for mae mas telefones NAO sao iguais ao do pai, pula (ja foi cadastrado de verdade)
                    if not telefones_iguais:
                        print(f"    Mae ja cadastrada no BigData (telefones diferentes do pai). Pulando.")
                        return False

                    # Se for mae e telefones sao iguais, tenta com numero ajustado
                    if tentativa < max_tentativas:
                        ultimos_digitos = int(telefone_atual[-2:])
                        novos_digitos = max(0, ultimos_digitos - 9)
                        telefone_atual = telefone_atual[:-2] + str(novos_digitos).zfill(2)
                        print(f"    Tentativa {tentativa + 1} com telefone ajustado: {telefone_atual}")
                        tentativa += 1
                        continue
                    else:
                        print(f"    Mae ja cadastrada apos {max_tentativas} tentativas. Pulando.")
                        return False

                # Email ou "nao tenho email"
                preencher_email(page, dados.get("email", ""))

                preencher_campo(page, "Data de Nascimento", dados["data_nascimento"])
                preencher_campo(page, "CEP", dados["cep"])

                # Aguarda o preenchimento automatico de bairro e cidade via CEP
                page.wait_for_timeout(3000)

                # So preenche bairro e cidade se estiverem vazios
                try:
                    campo_bairro = page.get_by_label("Bairro", exact=False).first
                    if campo_bairro.is_visible(timeout=500):
                        valor_atual = campo_bairro.input_value()
                        if not valor_atual and dados.get("bairro"):
                            preencher_campo(page, "Bairro", dados["bairro"])
                except Exception:
                    pass

                try:
                    campo_cidade = page.get_by_label("Cidade", exact=False).first
                    if campo_cidade.is_visible(timeout=500):
                        valor_atual = campo_cidade.input_value()
                        if not valor_atual and dados.get("cidade"):
                            preencher_campo(page, "Cidade", dados["cidade"])
                except Exception:
                    pass

                page.wait_for_timeout(1000)

                # Marca checkbox "Aceito"
                marcar_checkbox_aceito(page)

                page.wait_for_timeout(500)

                # Submete
                if not submeter_formulario(page):
                    print(f"    Falha ao submeter formulario - nenhum botao encontrado")
                    try:
                        page.screenshot(path="erro_submeter.png")
                        print(f"    Print salvo em erro_submeter.png")
                    except Exception:
                        pass
                    browser.close()
                    return False

                # Aguarda redirecionamento ou carregamento
                try:
                    page.wait_for_url("**/bio-liderado/**", timeout=15000)
                    print(f"    Sucesso! Redirecionado para pagina de confirmacao")
                    browser.close()
                    return True
                except Exception:
                    pass

                try:
                    page.wait_for_load_state("networkidle", timeout=15000)
                except Exception:
                    pass

                # Verifica se houve redirecionamento para pagina de sucesso
                page.wait_for_timeout(2000)
                url_atual = page.url
                if "deputadoaureo.com.br/bio-liderado" in url_atual:
                    print(f"    Sucesso! Redirecionado para pagina de confirmacao")
                    browser.close()
                    return True

                # Verifica novamente se apareceu alerta apos submeter
                page.wait_for_timeout(1000)
                if verificar_telefone_ja_cadastrado(page):
                    print(f"    Telefone ja cadastrado detectado apos envio!")
                    browser.close()

                    if dados.get("tipo") == "pai":
                        print(f"    Pai ja cadastrado no BigData. Pulando.")
                        return False

                    if not telefones_iguais:
                        print(f"    Mae ja cadastrada no BigData (telefones diferentes do pai). Pulando.")
                        return False

                    if tentativa < max_tentativas:
                        ultimos_digitos = int(telefone_atual[-2:])
                        novos_digitos = max(0, ultimos_digitos - 9)
                        telefone_atual = telefone_atual[:-2] + str(novos_digitos).zfill(2)
                        print(f"    Tentativa {tentativa + 1} com telefone ajustado: {telefone_atual}")
                        tentativa += 1
                        continue
                    else:
                        print(f"    Mae ja cadastrada apos {max_tentativas} tentativas. Pulando.")
                        return False

                browser.close()
                return True
        except Exception as e:
            print(f"    Erro no Playwright: {e}")
            if tentativa < max_tentativas:
                tentativa += 1
                continue
            return False

    return False


def modo_auto(cadastros: list):
    """Processa todos os cadastros em sequencia."""
    supabase = init_supabase()
    total = len(cadastros)
    enviados = 0
    erros = 0
    pulados = 0
    ja_cadastrados = 0

    print(f"\n  Modo automatico: {total} cadastros para processar\n")

    for i, c in enumerate(cadastros, 1):
        menor = f"{c.get('menor_nome', '').strip()} {c.get('menor_sobrenome', '').strip()}"
        cid = c.get("id", "")

        print(f"  [{i}/{total}] {menor}")

        # Carregar status atual do banco
        try:
            status = supabase.table("cadastros").select("pai_enviado_bigdata,mae_enviado_bigdata").eq("id", cid).execute()
            if status.data:
                pai_ja_enviado = status.data[0].get("pai_enviado_bigdata", False)
                mae_ja_enviado = status.data[0].get("mae_enviado_bigdata", False)
            else:
                pai_ja_enviado = False
                mae_ja_enviado = False
        except Exception:
            pai_ja_enviado = False
            mae_ja_enviado = False

        # --- PAI ---
        if c.get("tem_pai"):
            if pai_ja_enviado:
                print(f"    Pai: ja enviado, pulando")
                pulados += 1
            else:
                dados = extrair_dados(c, "pai")
                if dados:
                    print(f"    Enviando pai - {dados['nome']} {dados['sobrenome']}...")
                    resultado = enviar_para_bigdata(dados, telefones_iguais=False)
                    if resultado:
                        marcar_enviado(supabase, cid, "pai")
                        enviados += 1
                        print(f"    Pai enviado com sucesso!")
                    else:
                        erros += 1
                        print(f"    Falha ao enviar pai")
                time.sleep(2)
        else:
            print(f"    Pai: sem dados")

        # --- MAE ---
        if c.get("tem_mae"):
            if mae_ja_enviado:
                print(f"    Mae: ja enviado, pulando")
                pulados += 1
            else:
                tel_pai = "".join(c2 for c2 in (c.get("pai_telefone") or "") if c2.isdigit())
                tel_mae = "".join(c2 for c2 in (c.get("mae_telefone") or "") if c2.isdigit())
                telefones_iguais = bool(tel_pai and tel_mae and tel_pai == tel_mae)

                # Se pai ja foi enviado e telefones sao iguais, pula a mae
                if c.get("tem_pai") and pai_ja_enviado and telefones_iguais:
                    print(f"    Mae: pai ja enviado com mesmo telefone, pulando")
                    pulados += 1
                else:
                    # Se crianca so tem mae e ela ja foi enviada, pula
                    if not c.get("tem_pai") and mae_ja_enviado:
                        print(f"    Mae: crianca so tem mae e ja foi enviada, pulando")
                        pulados += 1
                    else:
                        # Se telefones sao iguais, ajusta o da mae
                        tel_ajustado = None
                        if telefones_iguais:
                            tel_ajustado = ajustar_telefone_duplicado(
                                c.get("pai_telefone") or "",
                                c.get("mae_telefone") or ""
                            )

                        dados = extrair_dados(c, "mae", tel_ajustado)
                        if dados:
                            print(f"    Enviando mae - {dados['nome']} {dados['sobrenome']}...")
                            resultado = enviar_para_bigdata(dados, telefones_iguais=telefones_iguais)
                            if resultado:
                                marcar_enviado(supabase, cid, "mae")
                                enviados += 1
                                print(f"    Mae enviado com sucesso!")
                            else:
                                erros += 1
                                print(f"    Falha ao enviar mae")
                    time.sleep(2)
        else:
            print(f"    Mae: sem dados")

        print()

    print("="*46)
    print(f"  FINALIZADO!")
    print(f"  Enviados: {enviados} | Erros: {erros} | Pulados: {pulados}")
    print("="*46)


def exibir_menu(cadastros: list) -> dict:
    print("\n" + "="*46)
    print("  CADASTROS DISPONIVEIS")
    print("="*46)
    for i, c in enumerate(cadastros, 1):
        print(f"  {i:>3}. {c['menor_nome']} {c['menor_sobrenome']}  -  {c['menor_cidade']}")
    print("    0. Sair")
    print("="*46)

    while True:
        try:
            escolha = int(input("\nEscolha o numero do cadastro: "))
            if escolha == 0:
                sys.exit(0)
            if 1 <= escolha <= len(cadastros):
                return cadastros[escolha - 1]
        except ValueError:
            pass
        print("  Opcao invalida.")


def escolher_responsavel(cadastro: dict) -> dict | None:
    print(f"\n  Menor: {cadastro['menor_nome']} {cadastro['menor_sobrenome']}")
    print("-"*46)

    opcoes = []
    if cadastro.get("tem_pai"):
        opcoes.append(("pai", f"Pai  - {cadastro.get('pai_nome')} {cadastro.get('pai_sobrenome')}"))
    if cadastro.get("tem_mae"):
        opcoes.append(("mae", f"Mae  - {cadastro.get('mae_nome')} {cadastro.get('mae_sobrenome')}"))

    if not opcoes:
        print("  Nenhum responsavel informado neste cadastro.")
        return None

    for i, (_, label) in enumerate(opcoes, 1):
        print(f"  {i}. {label}")
    print("  0. Voltar")

    while True:
        try:
            escolha = int(input("\nEnviar qual responsavel? "))
            if escolha == 0:
                return None
            if 1 <= escolha <= len(opcoes):
                prefixo = opcoes[escolha - 1][0]
                # Verifica se precisa ajustar telefone da mae
                tel_ajustado = None
                if prefixo == "mae":
                    tel_pai = "".join(re.findall(r"\d", cadastro.get("pai_telefone") or ""))
                    tel_mae = "".join(re.findall(r"\d", cadastro.get("mae_telefone") or ""))
                    if tel_pai and tel_pai == tel_mae:
                        tel_ajustado = ajustar_telefone_duplicado(
                            cadastro.get("pai_telefone") or "",
                            cadastro.get("mae_telefone") or ""
                        )
                return extrair_dados(cadastro, prefixo, tel_ajustado)
        except ValueError:
            pass
        print("  Opcao invalida.")


def modo_manual(cadastros: list):
    """Modo interativo com navegador."""
    while True:
        cadastro = exibir_menu(cadastros)
        dados = escolher_responsavel(cadastro)

        if dados:
            print(f"\n  Abrindo browser para {dados['tipo']} - {dados['nome']}...")
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=False, slow_mo=400)
                page = browser.new_page()

                page.goto(BIGDATA_URL, wait_until="networkidle")
                page.wait_for_timeout(2000)

                # Aceita banner de cookies
                aceitar_cookies(page)
                page.wait_for_timeout(1000)

                preencher_campo(page, "Quem te indicou", "William da Rocha")
                preencher_campo(page, "Nome", dados["nome"])
                preencher_campo(page, "Sobrenome", dados["sobrenome"])

                try:
                    campo_tel = page.get_by_label("Telefone", exact=False).first
                    campo_tel.click()
                    campo_tel.press_sequentially(dados["telefone"], delay=80)
                except Exception:
                    preencher_campo(page, "Telefone", dados["telefone"])

                preencher_email(page, dados["email"])
                preencher_campo(page, "Data de Nascimento", dados["data_nascimento"])
                preencher_campo(page, "CEP", dados["cep"])

                # Aguarda o preenchimento automatico de bairro e cidade via CEP
                page.wait_for_timeout(3000)

                # So preenche bairro e cidade se estiverem vazios
                try:
                    campo_bairro = page.get_by_label("Bairro", exact=False).first
                    if campo_bairro.is_visible(timeout=500):
                        valor_atual = campo_bairro.input_value()
                        if not valor_atual and dados.get("bairro"):
                            preencher_campo(page, "Bairro", dados["bairro"])
                except Exception:
                    pass

                try:
                    campo_cidade = page.get_by_label("Cidade", exact=False).first
                    if campo_cidade.is_visible(timeout=500):
                        valor_atual = campo_cidade.input_value()
                        if not valor_atual and dados.get("cidade"):
                            preencher_campo(page, "Cidade", dados["cidade"])
                except Exception:
                    pass

                page.wait_for_timeout(1000)

                marcar_checkbox_aceito(page)

                page.wait_for_timeout(500)

                input("\n  Pressione ENTER para SUBMETER, ou Ctrl+C para cancelar.")

                if not submeter_formulario(page):
                    print(f"  Falha ao submeter formulario")
                else:
                    try:
                        page.wait_for_load_state("networkidle", timeout=10000)
                        # Verifica se houve redirecionamento para pagina de sucesso
                        url_atual = page.url
                        if "deputadoaureo.com.br/bio-liderado" in url_atual:
                            print("  Sucesso! Redirecionado para pagina de confirmacao")
                        else:
                            print("  Formulario submetido!")
                    except Exception:
                        print("  Formulario submetido (timeout ao esperar resposta)")

                input("\n  Pressione ENTER para fechar o browser.")
                browser.close()

        continuar = input("\n  Enviar outro? (s/n): ").strip().lower()
        if continuar != "s":
            break


def main():
    print("\n" + "="*46)
    print("  BIGDATA SENDER")
    print("="*46)

    # Forcar encoding UTF-8 no terminal Windows
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore

    cadastros = carregar_cadastros()
    print(f"  Total de cadastros: {len(cadastros)}")

    if "--auto" in sys.argv:
        modo_auto(cadastros)
    else:
        modo_manual(cadastros)

    print("\n  Ate logo!\n")


if __name__ == "__main__":
    main()