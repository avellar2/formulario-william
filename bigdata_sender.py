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
        novos_ultimos = max(0, ultimos - 9)
        novo = digits_mae[:-2] + str(novos_ultimos).zfill(2)
        print(f"    Telefone duplicado detectado! Ajustando mae: {telefone_mae} -> {novo}")
        return novo

    return telefone_mae


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
        # Tem email - preenche o campo
        preencher_campo(page, "E-mail", email)
        if not page.get_by_label("E-mail", exact=False).first.is_visible(timeout=1000):
            # Tenta variacoes do label
            for label in ["Email", "email", "e-mail", "E mail"]:
                try:
                    campo = page.get_by_label(label, exact=False).first
                    if campo.is_visible(timeout=500):
                        campo.fill(email)
                        print(f"    Email preenchido ({label})")
                        return True
                except Exception:
                    continue
            # Tenta por placeholder
            for ph in ["email", "E-mail", "Email", "e-mail"]:
                try:
                    campo = page.locator(f"input[placeholder*='{ph}' i]").first
                    if campo.is_visible(timeout=500):
                        campo.fill(email)
                        print(f"    Email preenchido (placeholder)")
                        return True
                except Exception:
                    continue
        else:
            print(f"    Email preenchido")
            return True
    else:
        # Nao tem email - marca "nao tenho email"
        print(f"    Email vazio, marcando 'nao tenho email'...")

        # Estrategia 1: Clica no label/texto "nao tenho email"
        try:
            label_nao_email = page.get_by_text(re.compile(r"n[aã]o tenho email", re.IGNORECASE)).first
            if label_nao_email.is_visible(timeout=2000):
                label_nao_email.click()
                page.wait_for_timeout(300)
                # Verifica se o checkbox associado ficou marcado
                try:
                    checkbox_nao_email = label_nao_email.locator("..").locator("input[type='checkbox']").first
                    if checkbox_nao_email.is_visible(timeout=500) and not checkbox_nao_email.is_checked():
                        checkbox_nao_email.check()
                except Exception:
                    pass
                print(f"    Checkbox 'nao tenho email' marcado via label")
                return True
        except Exception:
            pass

        # Estrategia 2: Procura o checkbox diretamente e marca
        # O checkbox "nao tenho email" costuma ser o segundo checkbox na pagina
        try:
            checkboxes = page.locator("input[type='checkbox']")
            total = checkboxes.count()
            print(f"    Encontrados {total} checkboxes na pagina")

            # Procura checkbox associado a texto "nao tenho email"
            for i in range(total):
                cb = checkboxes.nth(i)
                try:
                    # Verifica se o checkbox esta proximo do texto "nao tenho email"
                    parent = cb.locator("..")
                    parent_text = parent.text_content() or ""
                    if re.search(r"n[aã]o tenho email", parent_text, re.IGNORECASE):
                        if not cb.is_checked():
                            cb.check()
                        print(f"    Checkbox 'nao tenho email' marcado (indice {i})")
                        return True
                except Exception:
                    continue

            # Se tem pelo menos 2 checkboxes, o segundo provavelmente e "nao tenho email"
            if total >= 2:
                cb_nao_email = checkboxes.nth(1)
                if not cb_nao_email.is_checked():
                    cb_nao_email.check()
                print(f"    Segundo checkbox marcado (assumindo 'nao tenho email')")
                return True
        except Exception:
            pass

        # Estrategia 3: Clica no texto "nao tenho email" e depois marca o checkbox mais proximo
        try:
            texto = page.locator("text=Não tenho email, text=Nao tenho email, text=nao tenho email").first
            if texto.is_visible(timeout=1000):
                texto.click()
                page.wait_for_timeout(300)
                # Tenta marcar o checkbox no mesmo container
                container = texto.locator("xpath=ancestor::*[.//input[@type='checkbox']]").first
                cb = container.locator("input[type='checkbox']").first
                if not cb.is_checked():
                    cb.check()
                print(f"    Checkbox 'nao tenho email' marcado via container")
                return True
        except Exception:
            pass

        print(f"    AVISO: Nao consegui marcar 'nao tenho email' - formulario pode falhar")
        return False


def marcar_checkbox_aceito(page):
    """Marca o checkbox 'Aceito' dos termos."""
    try:
        # Tenta clicar no texto do label
        aceito = page.get_by_text(re.compile(r"aceito|li e aceito|concordo com os termos", re.IGNORECASE)).first
        if aceito.is_visible(timeout=2000):
            aceito.click()
            # Verifica se o checkbox ficou marcado
            page.wait_for_timeout(300)
            try:
                cb = aceito.locator("xpath=ancestor::*[.//input[@type='checkbox']]").locator("input[type='checkbox']").first
                if cb.is_visible(timeout=500) and not cb.is_checked():
                    cb.check()
            except Exception:
                pass
            print(f"    Checkbox 'Aceito' marcado via texto")
            return True
    except Exception:
        pass

    # Fallback: marca o primeiro checkbox (assumindo que e o de termos)
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
    tentativas = [
        ("botao Salvar/Enviar", lambda: page.get_by_role("button", name=re.compile(r"salvar|enviar|cadastrar", re.IGNORECASE)).first.click()),
        ("button[type=submit]", lambda: page.locator("button[type='submit']").first.click()),
        ("input[type=submit]", lambda: page.locator("input[type='submit']").first.click()),
        ("botao formulario", lambda: page.locator("form button").first.click()),
        ("botao .btn", lambda: page.locator(".btn, .button, .enviar, .salvar, [class*='btn'], [class*='button']").first.click()),
        ("form.submit()", lambda: page.evaluate("document.querySelector('form').submit()")),
    ]

    for nome, acao in tentativas:
        try:
            acao()
            print(f"    Formulario submetido via {nome}")
            return True
        except Exception:
            continue

    return False


def enviar_para_bigdata(dados: dict, tentativa: int = 1) -> bool:
    """Abre o browser, preenche e submete. Retorna True se sucesso."""
    max_tentativas = 3 if dados.get("tipo") == "mae" else 1
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

                # Email ou "nao tenho email"
                preencher_email(page, dados.get("email", ""))

                preencher_campo(page, "Data de Nascimento", dados["data_nascimento"])
                preencher_campo(page, "CEP", dados["cep"])

                page.wait_for_timeout(1500)

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

                try:
                    page.wait_for_load_state("networkidle", timeout=15000)
                except Exception:
                    pass

                # Verifica se apareceu alerta de "telefone ja cadastrado"
                page.wait_for_timeout(1000)
                try:
                    alerta = page.get_by_text(re.compile(r"telefone.*ja.*cadastr", re.IGNORECASE)).first
                    if alerta.is_visible():
                        msg = alerta.text_content() or "Telefone ja cadastrado"
                        print(f"    Alerta: {msg}")
                        browser.close()

                        if dados.get("tipo") == "pai":
                            print(f"    Pai ja cadastrado no BigData. Pulando.")
                            return False

                        # Se for mae, tenta de novo com telefone ajustado
                        if tentativa < max_tentativas:
                            novos_ultimos = max(0, int(telefone_atual[-2:]) - 9)
                            telefone_atual = telefone_atual[:-2] + str(novos_ultimos).zfill(2)
                            print(f"    Tentativa {tentativa + 1} com telefone ajustado: {telefone_atual}")
                            tentativa += 1
                            continue
                        else:
                            print(f"    Mae ja cadastrada apos {max_tentativas} tentativas. Pulando.")
                            return False
                except Exception:
                    pass

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
                    resultado = enviar_para_bigdata(dados)
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
                dados = extrair_dados(c, "mae")
                if dados:
                    print(f"    Enviando mae - {dados['nome']} {dados['sobrenome']}...")
                    resultado = enviar_para_bigdata(dados)
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

                page.wait_for_timeout(1500)

                marcar_checkbox_aceito(page)

                page.wait_for_timeout(500)

                input("\n  Pressione ENTER para SUBMETER, ou Ctrl+C para cancelar.")

                if not submeter_formulario(page):
                    print(f"  Falha ao submeter formulario")
                else:
                    try:
                        page.wait_for_load_state("networkidle", timeout=10000)
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