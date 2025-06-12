import difflib
import re
import streamlit as st
import pandas as pd
from io import BytesIO
from openpyxl import Workbook
from openpyxl.styles import PatternFill

# Configuração da página
st.set_page_config(page_title="Comparador de Arquivos", layout="wide")
st.title("📊 Comparador de Arquivos e Textos")

def get_legal_reference(text):
    """Identifica a referência legal no texto"""
    text = text.strip()
    
    # Padrões para identificar elementos jurídicos
    patterns = [
        (r'^(Art\. \d+°)', 'Artigo'),
        (r'^(§ \d+°)', 'Parágrafo'),
        (r'^(§ único)', 'Parágrafo único'),
        (r'^(INCISO [A-Z]+)', 'Inciso'),
        (r'^([a-z]\) )', 'Alínea'),
        (r'^(\d+\. )', 'Item')
    ]
    
    for pattern, ref_type in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return f"{ref_type} {match.group(1)}"
    
    return "Texto"
# Função para comparar textos
def compare_texts(text1, text2):
    text1_lines = text1.splitlines()
    text2_lines = text2.splitlines()
    
    differ = difflib.SequenceMatcher(None, text1_lines, text2_lines)
    result = []
    
    for opcode in differ.get_opcodes():
        tag, i1, i2, j1, j2 = opcode
        
        if tag == 'equal':
            for line in text1_lines[i1:i2]:
                result.append(f"<div style='margin: 5px 0;'>{line}</div>")
        
        elif tag == 'replace':
            ref1 = get_legal_reference(text1_lines[i1]) if i1 < len(text1_lines) else ""
            ref2 = get_legal_reference(text2_lines[j1]) if j1 < len(text2_lines) else ""
            ref = ref1 if ref1 else ref2
            
            result.append(f"<div style='background-color: #fffacd; margin: 10px 0; padding: 5px;'>"
                         f"<strong>{ref} foi alterado:</strong>")
            
            # Mostra diferenças entre as palavras
            if i1 < len(text1_lines) and j1 < len(text2_lines):
                words1 = text1_lines[i1].split()
                words2 = text2_lines[j1].split()
                char_diff = difflib.ndiff(words1, words2)
                
                # Reconstruir o texto com as diferenças marcadas
                line1 = []
                line2 = []
                for change in char_diff:
                    if change.startswith('- '):
                        line1.append(f"<span style='text-decoration: line-through; color: red;'>{change[2:]}</span>")
                    elif change.startswith('+ '):
                        line2.append(f"<span style='text-decoration: underline; color: green;'>{change[2:]}</span>")
                    elif change.startswith('  '):
                        line1.append(change[2:])
                        line2.append(change[2:])
                
                if i1 < len(text1_lines):
                    result.append(f"<div style='color: red;'>Versão anterior: {' '.join(line1)}</div>")
                if j1 < len(text2_lines):
                    result.append(f"<div style='color: green;'>Nova versão: {' '.join(line2)}</div>")
            
            result.append("</div>")
        
        elif tag == 'delete':
            ref = get_legal_reference(text1_lines[i1]) if i1 < len(text1_lines) else f"Linha {i1+1}"
            result.append(f"<div style='margin: 5px 0;'>"
                         f"<span style='color: red; text-decoration: line-through;'>{text1_lines[i1] if i1 < len(text1_lines) else ''}</span></div>")
        
        elif tag == 'insert':
            ref = get_legal_reference(text2_lines[j1]) if j1 < len(text2_lines) else f"Linha {j1+1}"
            result.append(f"<div style='margin: 5px 0;'>"
                         f"<span style='color: green; text-decoration: underline;'>{text2_lines[j1] if j1 < len(text2_lines) else ''}</span></div>")
    
    return "".join(result)

# Função para comparar arquivos Excel
def compare_excel(file1, file2):
    try:
        df1 = pd.read_excel(file1)
        df2 = pd.read_excel(file2)
    except Exception as e:
        st.error(f"Erro ao ler arquivos: {e}")
        return None
    
    # Criar um novo DataFrame com as diferenças
    diff_df = df1.compare(df2)
    
    # Criar um Excel com formatação
    wb = Workbook()
    ws = wb.active
    
    # Cores para destaque
    red_fill = PatternFill(start_color='FFEE1111', end_color='FFEE1111', fill_type='solid')
    green_fill = PatternFill(start_color='FF11EE11', end_color='FF11EE11', fill_type='solid')
    
    # Escrever os dados no Excel (implementação simplificada)
    for r_idx, row in enumerate(diff_df.itertuples(), 1):
        for c_idx, value in enumerate(row[1:], 1):
            ws.cell(row=r_idx, column=c_idx, value=value)
    
    # Salvar para um buffer de memória
    output = BytesIO()
    wb.save(output)
    output.seek(0)
    
    return output, diff_df

# Interface principal
tab1, tab2 = st.tabs(["Comparar Arquivos Excel/CSV", "Comparar Textos"])

with tab1:
    st.header("Comparador de Planilhas")
    col1, col2 = st.columns(2)
    
    with col1:
        arq1 = st.file_uploader("Carregar Arquivo 1", type=["xlsx", "csv"], key="file1")
    with col2:
        arq2 = st.file_uploader("Carregar Arquivo 2", type=["xlsx", "csv"], key="file2")
    
    if arq1 and arq2:
        if st.button("Comparar Arquivos"):
            with st.spinner("Processando comparação..."):
                result, diff_df = compare_excel(arq1, arq2)
                
                if result and not diff_df.empty:
                    st.success("Comparação concluída!")
                    st.dataframe(diff_df)
                    
                    st.download_button(
                        label="Baixar Excel com Diferenças",
                        data=result,
                        file_name="comparacao.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                else:
                    st.info("Os arquivos são idênticos!")

with tab2:
    st.header("Comparador de Textos")
    col1, col2 = st.columns(2)
    
    with col1:
        txt1 = st.text_area("Texto Original", height=300)
    with col2:
        txt2 = st.text_area("Texto Novo", height=300)
    
    if txt1 and txt2:
        if st.button("Comparar Textos"):
            comparison = compare_texts(txt1, txt2)
            st.markdown(comparison, unsafe_allow_html=True)