"""
BigData Sender - Envia dados de pai/mãe para bigdata.app.br via Playwright

Requisitos (instalar uma vez):
  pip install playwright
  playwright install chromium

Como usar:
  1. No painel admin, clique em "Exportar JSON" para baixar o arquivo
  2. Coloque o arquivo JSON na mesma pasta deste script
  3. Execute: python bigdata_sender.py
     Ou informe o caminho: python bigdata_sender.py meu_arquivo.json
"""

import json
import sys
import glob
import os
from playwright.sync_api import sync_playwright

BIGDATA_URL = "https://bigdata.app.br/77/meuscadastros_add.php?codigo=MU7NWK"


def formatar_data(data_iso: str | None) -> str:
    if not data_iso:
        return ""
    partes = data_iso.split("-")
    if len(partes) != 3:
        return data_iso
    return f"{partes[2]}/{partes[1]}/{partes[0]}"


def carregar_cadastros() -> list:
    # Argumento passado na linha de comando
    if len(sys.argv) > 1:
        caminho = sys.argv[1]
    else:
        # Procura pelo JSON mais recente na pasta atual
        arquivos = sorted(glob.glob("cadastros_*.json"), reverse=True)
        if not arquivos:
            print("\n  ✗ Nenhum arquivo cadastros_*.json encontrado.")
            print("  Exporte o JSON pelo painel admin e coloque na mesma pasta deste script.\n")
            sys.exit(1)
        caminho = arquivos[0]
        print(f"\n  Usando arquivo: {caminho}")

    with open(caminho, "r", encoding="utf-8") as f:
        return json.load(f)


def exibir_menu(cadastros: list) -> dict:
    print("\n══════════════════════════════════════")
    print("  CADASTROS DISPONÍVEIS")
    print("══════════════════════════════════════")
    for i, c in enumerate(cadastros, 1):
        print(f"  {i:>3}. {c['menor_nome']} {c['menor_sobrenome']}  —  {c['menor_cidade']}")
    print("    0. Sair")
    print("══════════════════════════════════════")

    while True:
        try:
            escolha = int(input("\nEscolha o número do cadastro: "))
            if escolha == 0:
                sys.exit(0)
            if 1 <= escolha <= len(cadastros):
                return cadastros[escolha - 1]
        except ValueError:
            pass
        print("  Opção inválida, tente novamente.")


def escolher_responsavel(cadastro: dict) -> dict | None:
    print(f"\n  Menor: {cadastro['menor_nome']} {cadastro['menor_sobrenome']}")
    print("──────────────────────────────────────")

    opcoes = []
    if cadastro.get("tem_pai"):
        opcoes.append(("pai", f"Pai  — {cadastro.get('pai_nome')} {cadastro.get('pai_sobrenome')}"))
    if cadastro.get("tem_mae"):
        opcoes.append(("mae", f"Mãe  — {cadastro.get('mae_nome')} {cadastro.get('mae_sobrenome')}"))

    if not opcoes:
        print("  Nenhum responsável informado neste cadastro.")
        return None

    for i, (_, label) in enumerate(opcoes, 1):
        print(f"  {i}. {label}")
    print("  0. Voltar")

    while True:
        try:
            escolha = int(input("\nEnviar qual responsável? "))
            if escolha == 0:
                return None
            if 1 <= escolha <= len(opcoes):
                prefixo = opcoes[escolha - 1][0]
                nome_completo = cadastro.get(f"{prefixo}_nome") or ""
                partes = nome_completo.strip().split(" ", 1)
                primeiro_nome = partes[0]
                sobrenome_db  = cadastro.get(f"{prefixo}_sobrenome") or ""
                # Se o sobrenome do banco estiver vazio, usa o resto do nome completo
                sobrenome_final = sobrenome_db if sobrenome_db else (partes[1] if len(partes) > 1 else "")

                telefone_raw = cadastro.get(f"{prefixo}_telefone") or ""
                telefone_digits = "".join(c for c in telefone_raw if c.isdigit())

                return {
                    "nome":             primeiro_nome,
                    "sobrenome":        sobrenome_final,
                    "telefone":         telefone_digits,
                    "email":            cadastro.get(f"{prefixo}_email") or "",
                    "data_nascimento":  formatar_data(cadastro.get(f"{prefixo}_data_nascimento")),
                    "cep":              (cadastro.get(f"{prefixo}_cep") or "").replace("-", ""),
                    "bairro":           cadastro.get(f"{prefixo}_bairro") or "",
                    "cidade":           cadastro.get(f"{prefixo}_cidade") or "",
                }
        except ValueError:
            pass
        print("  Opção inválida.")


def preencher_campo(page, label: str, valor: str):
    if not valor:
        return
    try:
        page.get_by_label(label, exact=False).first.fill(valor)
        return
    except Exception:
        pass
    try:
        page.locator(f"input[placeholder*='{label}']").first.fill(valor)
    except Exception:
        pass


def enviar_para_bigdata(dados: dict):
    print("\n  Abrindo browser...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=400)
        page = browser.new_page()

        print(f"  Navegando para BigData...")
        page.goto(BIGDATA_URL, wait_until="networkidle")

        print("  Preenchendo campos...")
        preencher_campo(page, "Quem te indicou", "William da Rocha")
        preencher_campo(page, "Nome", dados["nome"])
        preencher_campo(page, "Sobrenome", dados["sobrenome"])

        # Telefone: digita dígito a dígito para respeitar a máscara do site
        try:
            campo_tel = page.get_by_label("Telefone", exact=False).first
            campo_tel.click()
            campo_tel.press_sequentially(dados["telefone"], delay=80)
        except Exception:
            preencher_campo(page, "Telefone", dados["telefone"])

        preencher_campo(page, "E-mail", dados["email"])
        preencher_campo(page, "Data de Nascimento", dados["data_nascimento"])
        preencher_campo(page, "CEP", dados["cep"])

        # Aguarda ViaCEP preencher bairro/cidade automaticamente
        page.wait_for_timeout(1500)

        # Marca o checkbox de aceite LGPD
        try:
            checkbox = page.locator("input[type='checkbox']").first
            if not checkbox.is_checked():
                checkbox.check()
        except Exception:
            pass

        print("\n  ✓ Campos preenchidos!")
        print("  Revise os dados no browser.")
        print("  Pressione ENTER aqui para SUBMETER, ou Ctrl+C para cancelar.")
        input()

        try:
            page.locator("button[type='submit'], input[type='submit'], button:has-text('Salvar')").first.click()
            page.wait_for_load_state("networkidle", timeout=10000)
            print("  ✓ Formulário submetido!")
        except Exception as e:
            print(f"  ✗ Erro ao submeter: {e}")

        input("\n  Pressione ENTER para fechar o browser.")
        browser.close()


def main():
    print("\n══════════════════════════════════════")
    print("  BIGDATA SENDER")
    print("══════════════════════════════════════")

    cadastros = carregar_cadastros()

    while True:
        cadastro   = exibir_menu(cadastros)
        dados      = escolher_responsavel(cadastro)

        if dados:
            enviar_para_bigdata(dados)

        continuar = input("\n  Enviar outro? (s/n): ").strip().lower()
        if continuar != "s":
            break

    print("\n  Até logo!\n")


if __name__ == "__main__":
    main()
