from difflib import Differ, SequenceMatcher
import os
import streamlit as st
import pandas as pd
from io import BytesIO
from openpyxl import Workbook
from openpyxl.styles import PatternFill

# Verifica se o arquivo de tema existe
if not os.path.exists(".streamlit/config.toml"):
    st.error("Arquivo de tema não encontrado! Crie em: .streamlit/config.toml")
else:
    
    # Configuração da página
    st.set_page_config(page_title="Comparador GNCP", layout="wide")
    st.title("📊 Comparador de Arquivos e Textos da GNCP")
    
    # CSS customizado para forçar o tema
    st.markdown(
        """
        <style>
            :root {
                --primary-color: #1bb50b !important;  /* Verde */
                --background-color: #FFFFFF !important;  /* Branco */
                --secondary-background-color: #FFFFFF !important;  /* Branco */
                --text-color: #000000 !important;  /* Preto */
            }

            /* Aplica cinza SOMENTE nos inputs */
            .stTextInput>div>div>input,
            .stNumberInput>div>div>input,
            .stTextArea>div>div>textarea,
            .stSelectbox>div>div>select,
            .stDateInput>div>div>input {
                background-color: #F3F3F3 !important;  /* Cinza claro */
                border-radius: 8px !important;
            }

            /* Mantém fundo branco em outros containers */
            .stApp, .stSidebar, .stAlert, .stMarkdown {
                background-color: #FFFFFF !important;
            }
        </style>
        """,
        unsafe_allow_html=True
    )

# Função para comparar textos
def compare_texts(text1, text2):
    # Divide os textos em linhas
    text1_lines = [line.strip() for line in text1.splitlines() if line.strip()]
    text2_lines = [line.strip() for line in text2.splitlines() if line.strip()]
    
    # Usa SequenceMatcher para alinhar as linhas
    matcher = SequenceMatcher(None, text1_lines, text2_lines)
    
    # Prepara o resultado em HTML
    result = []
    result.append("""
    <style>
        .diff-container {
            display: flex;
            width: 100%;
            font-family: monospace;
        }
        .diff-column {
            flex: 1;
            padding: 10px;
        }
        .diff-line {
            white-space: pre-wrap;
            margin: 2px 0;
            padding: 2px;
        }
        .diff-cell {
            flex: 1;
            padding: 2px 10px;
            white-space: pre-wrap;
        }
        .unchanged {
            background-color: #f8f8f8;
        }
        .deleted {
            background-color: #ffdddd;
            text-decoration: line-through;
        }
        .added {
            background-color: #ddffdd;
            text-decoration: underline;
        }
        .changed-old {
            background-color: #ff758f;
            text-decoration: line-through;
        }
        .changed-new {
            background-color: #abff4f;
            text-decoration: underline;
        }
        .line-number {
            color: #999;
            margin-right: 10px;
            user-select: none;
        }
    </style>
    <div class="diff-container">
        <div class="diff-column">
            <h3>Texto Original</h3>
    """)
    
    left_lines = []
    right_lines = []
    
    # Processa cada bloco de diferenças
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():

        if tag == 'equal':
            for line in text1_lines[i1:i2]:
                left_lines.append(('unchanged', line))
                right_lines.append(('unchanged', line))

        elif tag == 'delete':
            for line in text1_lines[i1:i2]:
                left_lines.append(('deleted', line))
                right_lines.append(('empty', ''))

        elif tag == 'insert':
            for line in text2_lines[j1:j2]:
                if left_lines and left_lines[-1][0] == 'empty':
                    right_lines[-1] = ('added', line)
                else:
                    left_lines.append(('empty',''))
                    right_lines.append(('added',line))

        elif tag == 'replace':
            matched_pairs = []
            used_new = set()
            used_old = set()
            # Pareamento linha a linha
            for i, old_line in enumerate(text1_lines[i1:i2]):
                best_match = None
                best_ratio = 0.8
                for j, new_line in enumerate(text2_lines[j1:j2]):
                    if j in used_new:
                        continue
                    ratio = SequenceMatcher(None, old_line, new_line).ratio()
                    if ratio > best_ratio:
                        best_ratio = ratio
                        best_match = j
                if best_match is not None:
                    matched_pairs.append((i, best_match))
                    used_new.add(best_match)
                    used_old.add(i)

            # Agora percorre ambos os blocos na ordem original
            old_idx, new_idx = 0, 0
            len_old = i2 - i1
            len_new = j2 - j1
            while old_idx < len_old or new_idx < len_new:
                # Se ambos são pareados
                pair = next(((oi, nj) for oi, nj in matched_pairs if oi == old_idx and nj == new_idx), None)
                if pair:
                    old_line = text1_lines[i1 + old_idx]
                    new_line = text2_lines[j1 + new_idx]
                    d = Differ()
                    diff = list(d.compare(old_line.split(), new_line.split()))
                    old_text = []
                    new_text = []
                    for word in diff:
                        if word.startswith('- '):
                            old_text.append(f'<span class="changed-old">{word[2:]}</span>')
                        elif word.startswith('+ '):
                            new_text.append(f'<span class="changed-new">{word[2:]}</span>')
                        elif word.startswith('  '):
                            old_text.append(word[2:])
                            new_text.append(word[2:])
                    left_lines.append(('changed', ' '.join(old_text)))
                    right_lines.append(('changed', ' '.join(new_text)))
                    old_idx += 1
                    new_idx += 1
                elif old_idx < len_old and old_idx not in used_old:
                    left_lines.append(('deleted', text1_lines[i1 + old_idx]))
                    right_lines.append(('empty', ''))
                    old_idx += 1
                elif new_idx < len_new and new_idx not in used_new:
                    left_lines.append(('empty', ''))
                    right_lines.append(('added', text2_lines[j1 + new_idx]))
                    new_idx += 1
                else:
                    old_idx += 1
                    new_idx += 1

    # Adiciona as linhas do lado esquerdo (original)
    for i, (line_class, line) in enumerate(left_lines):
        if line_class == 'empty':
            result.append(f'<div class="diff-line">&nbsp;</div>')
        else:
            result.append(f'<div class="diff-line {line_class}"><span class="line-number">{i+1}</span>{line}</div>')
    
    result.append("""
        </div>
        <div class="diff-column">
            <h3>Texto Modificado</h3>
    """)
    
    # Adiciona as linhas do lado direito (modificado)
    for i, (line_class, line) in enumerate(right_lines):
        if line_class == 'empty':
            result.append(f'<div class="diff-line">&nbsp;</div>')
        else:
            result.append(f'<div class="diff-line {line_class}"><span class="line-number">{i+1}</span>{line}</div>')
    
    result.append("""
        </div>
    </div>
    """)
    
    return ''.join(result)

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
tab1, tab2, tab3 = st.tabs([ "Comparar Textos", "Comparar Documentos", "Comparar Planilhas Excel"])

with tab1:
    st.header("Comparar Textos")
    col1, col2 = st.columns(2)
    
    with col1:
        txt1 = st.text_area("Texto Original", height=300)
    with col2:
        txt2 = st.text_area("Texto Modificado", height=300)
    
    if txt1 and txt2:
        if st.button("Comparar Textos"):
            comparison = compare_texts(txt1, txt2)
            st.markdown(comparison, unsafe_allow_html=True)

with tab2:
    
    st.header("Comparar Documentos")
    st.markdown(" EM DESENVOLVIMENTO")

    # col1, col2 = st.columns(2)
    # with col1:
    #     arq1 = st.file_uploader("Carregar Documento 1", type=["doc", "pdf", "txt", "csv"], key="file1")
    # with col2:
    #     arq2 = st.file_uploader("Carregar Documento 2", type=["doc", "pdf", "txt", "csv"], key="file2")
    
with tab3:
    st.header("Comparar Planihas")
    st.markdown(" EM DESENVOLVIMENTO")

    # col1, col2 = st.columns(2)
    # with col1:
    #     sheet1 = st.file_uploader("Carregar Arquivo 1", type=["xlsx"], key="wb1")
    # with col2:
    #     sheet2 = st.file_uploader("Carregar Arquivo 2", type=["xlsx"], key="wb2")
        
    # if sheet1 and sheet2:
    #     if st.button("Comparar Arquivos"):
    #         with st.spinner("Processando comparação..."):
    #             result, diff_df = compare_excel(sheet1, sheet2)
                
    #             if result and not diff_df.empty:
    #                 st.success("Comparação concluída!")
    #                 st.dataframe(diff_df)
                    
    #                 st.download_button(
    #                     label="Baixar Excel com Diferenças",
    #                     data=result,
    #                     file_name="comparacao.xlsx",
    #                     mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    #                 )
    #             else:
    #                 st.info("Os arquivos são idênticos!")