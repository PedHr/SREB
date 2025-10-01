import ollama
import pdfplumber
import json

def classificar_descricao_com_ia(descricao: str, categorias_possiveis: list) -> str:
    
    categorias_str = ", ".join(categorias_possiveis)

    prompt = f"""
    Você é um assistente de finanças pessoais. Sua tarefa é classificar a descrição de uma transação de cartão de crédito em UMA das seguintes categorias: {categorias_str}.

    Descrição da Transação: "{descricao}"

    Responda APENAS com o nome exato da categoria escolhida, e nada mais.
    """

    try:
        response = ollama.chat(
            model='phi3:mini',
            messages=[{'role': 'user', 'content': prompt}]
        )
        categoria_sugerida = response['message']['content'].strip()
        
        if categoria_sugerida in categorias_possiveis:
            return categoria_sugerida
        else:
            return "Outros"

    except Exception as e:
        print(f"Erro ao classificar '{descricao}': {e}")
        return "Erro na Classificação"
    
def limpar_pdf(arquivo):
    arquivo_pdf = arquivo

    tabela_completa = []

    try:
        with pdfplumber.open(arquivo_pdf) as pdf:

            pagina2 = pdf.pages[1]
            tabela_pagina2 = pagina2.extract_table()
            if tabela_pagina2:
                tabela_completa.extend(tabela_pagina2)
                print(f"Foi encontrado {len(tabela_pagina2)} linhas na tabela 2.")


            pagina3 = pdf.pages[2]
            tabela_pagina3 = pagina3.extract_table()
            if tabela_pagina3:
                tabela_completa.extend(tabela_pagina3[1:])
                print(f"Foi encontrado {len(tabela_pagina2)} linhas na tabela 3.")


            pagina4 = pdf.pages[3]
            tabela_pagina4 = pagina4.extract_table()
            if tabela_pagina4:
                tabela_completa.extend(tabela_pagina4[1:])
                print(f"Foi encontrado {len(tabela_pagina2)} linhas na tabela 4.")

    except Exception as e:
        print(f"Erro: {e}")

    transacoes_limpas = []
    categoria_atual = "Não Categorizado"

    for linha in tabela_completa: 

        if len(linha) < 5 or all(item is None for item in linha):
            continue


        data = linha[1]
        descricao = linha[2]
        valor = linha[4]

        if (data is None or data == "") and (descricao is not None and descricao != "") and (valor is None or valor == ""):
            categoria_atual = descricao.strip()
            print(f"🔄 Categoria alterada para: {categoria_atual}")
            continue 

        if (data is not None and data != "") and (valor is not None and "R$" in valor):
            try:
                valor_str_limpo = valor.replace('R$', '').strip().replace('.', '').replace(',', '.')
                valor_float = float(valor_str_limpo)
            except (ValueError, TypeError):
                continue

            transacao = {
                "data": data.strip(),
                "descricao": descricao.strip(),
                "valor": valor_float,
                "categoria": categoria_atual
            }
            
            transacoes_limpas.append(transacao)
    return transacoes_limpas

CATEGORIAS = [
    "Alimentação",
    "Supermercado",
    "Transporte",
    "Moradia",
    "Saúde",
    "Lazer",
    "Educação",
    "Vestuário",
    "Assinaturas e Serviços",
    "Investimentos",
    "Cuidados Pessoais",
    "Outros"
]

arquivo_pdf = 'fatura.pdf'
transacoes_limpas = limpar_pdf(arquivo_pdf)

print("Iniciando classificação de ia")

cache_de_classificação = {}

for transacao in transacoes_limpas:
    descricao = transacao['descricao']

    if descricao in cache_de_classificação:
        nova_categoria = cache_de_classificação[descricao]
    else:
        nova_categoria = classificar_descricao_com_ia(descricao, CATEGORIAS)
        cache_de_classificação[descricao] = nova_categoria

    transacao['categoria_id'] = nova_categoria

print("\n--- ✅ Classificação Finalizada! ---")
print("\n--- ✨ Transações com Novas Categorias da IA ---")
print(json.dumps(transacoes_limpas, indent=2, ensure_ascii=False))