import streamlit as st
import pandas as pd
from io import BytesIO
import os
# Comparar Textos
from difflib import Differ, SequenceMatcher 
# Comparar Documentos
from PyPDF2 import PdfReader, PdfWriter 
import docx
import chardet 
#Comparar Excel
from openpyxl import Workbook 
from openpyxl.styles import PatternFill

def main():
# Configuração da página
    st.set_page_config(page_title="Comparador GNCP", page_icon="Brasão.png", layout="wide")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.image("Logomarca SEAD 2.png", width=800)
        
# CSS customizado para forçar o tema
    st.markdown(
        """
        <style>
            img {
                margin-top: -3rem !important;
                margin-bottom: -1.2rem !important;
                align: center !important;
            }
            h1 {
                font-size: 2.12rem !important;
                margin-bottom: 1rem !important;
                margin-left: 1.6rem !important;
            }
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
        """,unsafe_allow_html=True)
    st.markdown("<h1 style='text-align: center;'>Comparador de Arquivos e Textos da GNCP</h1>", unsafe_allow_html=True)

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
                border: 1px solid #ddd;
                border-radius: 6px;
                overflow: hidden;
                max-height: 80vh; 
                overflow-y: auto;
                overflow-x: auto;
            }
            .diff-column {
                width: 50%;
                min-width: 0;
                max-width: 50%;
                padding: 10px;
                margin: 0;
                border-right: 1px solid #eee;
                background: #fff;
                box-sizing: border-box;
                display: flex;
                flex-direction: column;
            }
            .diff-column:last-child {
                border-right: none;
            }
            .diff-line {
                white-space: pre-wrap;
                margin: 2px 0;
                padding: 2px;
                border-left: 4px solid transparent;
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
                border-left: 4px solid #ff6f6f;
            }
            .added {
                background-color: #ddffdd;
                text-decoration: underline;
                border-left: 4px solid #4fe87b;
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
                margin-right: 5px;
                user-select: none;
                width: 20px;
                display: inline-block;
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
                result.append(f'<div class="diff-line empty"><span class="line-number">{i+1}</span>&nbsp;</div>')
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
                result.append(f'<div class="diff-line empty"><span class="line-number">{i+1}</span>&nbsp;</div>')
            else:
                result.append(f'<div class="diff-line {line_class}"><span class="line-number">{i+1}</span>{line}</div>')
        
        result.append("""
            </div>
        </div>
        """)
        
        return ''.join(result)

# Funções para comparar arquivos 
    def extract_text(file):
        """Extrai e padroniza texto de diferentes formatos de arquivo"""
        if not file:
            return None
            
        file_extension = file.name.split('.')[-1].lower()
        if file_extension not in ['pdf', 'docx', 'doc', 'txt', 'csv']:
            st.error(f"Formato não suportado: {file_extension}")
            return None
        
        try:
            # Padroniza o tratamento de encoding para todos os formatos
            def decode_text(raw_data):
                """Função auxiliar para decodificar texto com detecção de encoding"""
                if not raw_data:
                    return ""
                    
                # Detecta encoding com confiança mínima de 70%
                detected = chardet.detect(raw_data)
                encoding = detected['encoding'] if detected['confidence'] > 0.7 else 'utf-8'
                
                try:
                    return raw_data.decode(encoding)
                except (UnicodeDecodeError, LookupError):
                    # Tenta utf-8 com fallback para substituição de caracteres inválidos
                    return raw_data.decode('utf-8', errors='replace')
            
            # PDF - Mantém estrutura original
            if file_extension == 'pdf':
                try:
                    reader = PdfReader(file)
                    num_paginas = len(reader.pages)
                    texto_completo = []
                    for i in range(num_paginas):
                        pagina = reader.pages[i]
                        texto_pagina = pagina.extract_text()
                        texto_completo.append(texto_pagina)
                    texto_final = '\n'.join(texto_completo) if texto_completo else None
                    if texto_final:
                        texto_final = texto_final.replace('\r\n', '\n').replace('\r', '\n')
                        linhas = texto_final.split('\n')
                        paragrafos = []
                        paragrafo_atual = []
                        for linha in linhas:
                            # Remove numeração do início da linha (ex: "1. ", "2. ", "10. ")
                            linha_sem_num = linha.lstrip()
                            import re
                            linha_sem_num = re.sub(r'^\d+\.\s*', '', linha_sem_num)
                            if linha_sem_num.strip() == "":
                                if paragrafo_atual:
                                    paragrafos.append(' '.join(paragrafo_atual).strip())
                                    paragrafo_atual = []
                            else:
                                paragrafo_atual.append(linha_sem_num.strip())
                        if paragrafo_atual:
                            paragrafos.append(' '.join(paragrafo_atual).strip())
                        texto_final = '\n\n'.join(paragrafos)
                    return texto_final if texto_final else None
                except Exception as e:
                    print(f"Erro ao ler o PDF: {e}")
                    return None
                
            # DOCX - Padroniza espaçamento entre parágrafos
            elif file_extension in ['docx', 'doc']:
                try:
                    doc = docx.Document(file)
                    text_lines = []
                    
                    for para in doc.paragraphs:
                        if para.text.strip():
                            text_lines.append(para.text.strip())
                        else:
                            text_lines.append('')
                    
                    text = '\n'.join(text_lines)
                    return text.strip() if text.strip() else None
                except Exception as e:
                    st.error(f"Erro ao ler arquivo Word: {str(e)}")
                    return None

            # TXT/CSV - Padroniza tratamento de quebras de linha
            elif file_extension in ['txt', 'csv']:
                file.seek(0)
                raw_data = file.read()
                text = decode_text(raw_data)
                
                if not text:
                    st.warning("O arquivo está vazio.")
                    return None
                    
                # Padroniza quebras de linha para \n
                text = text.replace('\r\n', '\n').replace('\r', '\n')
                # Remove numeração do início de cada linha
                import re
                linhas = text.split('\n')
                linhas_sem_enum = [
                                re.sub(
                                    r'^\s*((\d+(\.\d+)*[.)]?)|[.\-•])[\s\t\u00A0]*',  # cobre . espaço, .\t, . , 1.2.3. etc
                                    '',
                                    linha
                                ).strip()
                                for linha in linhas
                            ]            
                texto_final = '\n'.join(linhas_sem_enum)

                # Para CSV, trata como texto puro (não tenta parsear)
                return texto_final.strip() if texto_final.strip() else None

            else:
                st.error(f"Formato não suportado: {file_extension}")
                return None
                
        except Exception as e:
            st.error(f"Erro ao processar arquivo: {str(e)}")
            return None

    def compare_docs(doc1, doc2):
        """Compara dois documentos com visualização lado a lado"""
        text1 = extract_text(doc1) or ""
        text2 = extract_text(doc2) or ""

        if not text1 and not text2:
            return None, None, True
        
        if text1.strip() == text2.strip():
            return None, None, True
        
        # Divide os textos em linhas mantendo as quebras originais
        text1_lines = text1.splitlines()
        text2_lines = text2.splitlines()
        
        # Remove linhas vazias do início e fim, mas mantém as do meio
        text1_lines = [line.rstrip() for line in text1_lines]
        text2_lines = [line.rstrip() for line in text2_lines]
        
        # Usa SequenceMatcher para alinhar as linhas
        matcher = SequenceMatcher(None, text1_lines, text2_lines)
        
        # Prepara o resultado em HTML (mesmo estilo anterior)
        result = []
        result.append("""
        <style>
            .diff-container {
                display: flex;
                width: 100%;
                font-family: Arial, sans-serif;
                border: 1px solid #ddd;
                border-radius: 5px;
                overflow: hidden;
                max-height: 80vh; 
                overflow-y: auto;
                overflow-x: auto;
            }
            .diff-column {
                width: 50%;
                min-width: 0;
                max-width: 50%;
                padding: 10px;
                margin: 0;
                border-right: 1px solid #eee;
                background: #fff;
                box-sizing: border-box;
                display: flex;
                flex-direction: column;
            }
            .diff-column:last-child {
                border-right: none;
            }
            .diff-line {
                white-space: pre-wrap;
                margin: 2px 0;
                padding: 2px;
                border-left: 4px solid transparent;
            }
            .unchanged {
                background-color: #f8f8f8;
            }
            .deleted {
                background-color: #ffdddd;
                text-decoration: line-through;
                border-left: 4px solid #ff6f6f;
            }
            .added {
                background-color: #ddffdd;
                text-decoration: underline;
                border-left: 4px solid #4fe87b;
            }
            .changed-old {
                background-color: #ff6f6f;
                text-decoration: line-through;
            }
            .changed-new {
                background-color: #4fe87b;
                text-decoration: underline;
            }
            .line-number {
                color: #999;
                margin-right: 5px;
                user-select: none;
                width: 20px;
                display: inline-block;
            }
            .diff-header {
                background: #f5f5f5;
                padding: 10px;
                font-weight: bold;
                border-bottom: 1px solid #ddd;
                margin: -10px -10px 10px -10px;
            }
            .empty-line {
                height: 5px;
                margin: 2px 0;
                background: repeating-linear-gradient(
                    45deg,
                    #f0f0f0,
                    #f0f0f0 2px,
                    white 2px,
                    white 4px
                );
            }
        </style>
        <div class="diff-container">
            <div class="diff-column">
                <div class="diff-header">Documento Original</div>
        """)
        
        left_lines = []
        right_lines = []
        changes_report = []
        line_counter = 1
        
        # Processa cada bloco de diferenças
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == 'equal':
                for line in text1_lines[i1:i2]:
                    if line.strip() == "":
                        left_lines.append(('empty-line', '', line_counter))
                        right_lines.append(('empty-line', '', line_counter))
                    else:
                        left_lines.append(('unchanged', line, line_counter))
                        right_lines.append(('unchanged', line, line_counter))
                    line_counter += 1

            elif tag == 'delete':
                for line in text1_lines[i1:i2]:
                    if line.strip() == "":
                        left_lines.append(('empty-line', '', line_counter))
                        right_lines.append(('empty-line', '', line_counter))
                    else:
                        left_lines.append(('deleted', line, line_counter))
                        right_lines.append(('empty', '', line_counter))
                        changes_report.append({
                            'Tipo': 'Removido',
                            'Conteúdo': line,
                            'Localização': f'Linha {line_counter}'
                        })
                    line_counter += 1

            elif tag == 'insert':
                for line in text2_lines[j1:j2]:
                    if line.strip() == "":
                        left_lines.append(('empty-line', '', line_counter))
                        right_lines.append(('empty-line', '', line_counter))
                    else:
                        if left_lines and left_lines[-1][0] == 'empty':
                            right_lines[-1] = ('added', line, right_lines[-1][2])
                        else:
                            left_lines.append(('empty', '', line_counter))
                            right_lines.append(('added', line, line_counter))
                        changes_report.append({
                            'Tipo': 'Adicionado',
                            'Conteúdo': line,
                            'Localização': f'Linha {line_counter}'
                        })
                    line_counter += 1

            elif tag == 'replace':
                # Processa substituições mantendo a estrutura de linhas
                max_lines = max((i2-i1), (j2-j1))
                for n in range(max_lines):
                    old_line = text1_lines[i1 + n] if n < (i2-i1) else ""
                    new_line = text2_lines[j1 + n] if n < (j2-j1) else ""
                    
                    if old_line.strip() == "" and new_line.strip() == "":
                        left_lines.append(('empty-line', '', line_counter))
                        right_lines.append(('empty-line', '', line_counter))
                    elif old_line.strip() == "":
                        left_lines.append(('empty', '', line_counter))
                        right_lines.append(('added', new_line, line_counter))
                        changes_report.append({
                            'Tipo': 'Adicionado',
                            'Conteúdo': new_line,
                            'Localização': f'Linha {line_counter}'
                        })
                    elif new_line.strip() == "":
                        left_lines.append(('deleted', old_line, line_counter))
                        right_lines.append(('empty', '', line_counter))
                        changes_report.append({
                            'Tipo': 'Removido',
                            'Conteúdo': old_line,
                            'Localização': f'Linha {line_counter}'
                        })
                    else:
                        # Comparação detalhada dentro da linha
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
                        
                        left_lines.append(('changed', ' '.join(old_text), line_counter))
                        right_lines.append(('changed', ' '.join(new_text), line_counter))
                        
                        changes_report.append({
                            'Tipo': 'Alterado',
                            'Original': old_line,
                            'Modificado': new_line,
                            'Localização': f'Linha {line_counter}'
                        })
                    
                    line_counter += 1

        # Adiciona as linhas do lado esquerdo (original)
        for line_class, line, line_num in left_lines:
            if line_class == 'empty-line':
                result.append(f'<div class="empty-line" title="Linha {line_num}"></div>')
            elif line_class == 'empty':
                result.append(f'<div class="diff-line empty"><span class="line-number">{line_num}</span>&nbsp;</div>')
            else:
                result.append(f'<div class="diff-line {line_class}"><span class="line-number">{line_num}</span>{line}</div>')

        result.append("""
            </div>
            <div class="diff-column">
                <div class="diff-header">Documento Modificado</div>
        """)
        
        # Adiciona as linhas do lado direito (modificado)
        for line_class, line, line_num in right_lines:
            if line_class == 'empty-line':
                result.append(f'<div class="empty-line" title="Linha {line_num}"></div>')
            elif line_class == 'empty':
                result.append(f'<div class="diff-line empty"><span class="line-number">{line_num}</span>&nbsp;</div>')
            else:
                result.append(f'<div class="diff-line {line_class}"><span class="line-number">{line_num}</span>{line}</div>')
        
        result.append("""
            </div>
        </div>
        """)
        
        # Gerar relatório de alterações
        diff_df = pd.DataFrame(changes_report) if changes_report else None
        
        return ''.join(result), diff_df, False

# Funções para comparar planilhas Excel
    def compare_excel(file1, file2, selected_sheet=None):
        try:
            xls1 = pd.ExcelFile(file1)
            xls2 = pd.ExcelFile(file2)
        except Exception as e:
            st.error(f"Erro ao ler arquivos: {e}")
            return None

        # Determinar quais abas comparar
        all_sheets = sorted(set(xls1.sheet_names) | set(xls2.sheet_names))
        
        if selected_sheet:
            if selected_sheet not in all_sheets:
                st.warning(f"A aba '{selected_sheet}' não foi encontrada em ambos arquivos.")
                return None
            sheets_to_compare = [selected_sheet]
        else:
            sheets_to_compare = all_sheets

        results = {}
        
        for sheet in sheets_to_compare:
            # Carregar dados
            df1 = xls1.parse(sheet) if sheet in xls1.sheet_names else pd.DataFrame()
            df2 = xls2.parse(sheet) if sheet in xls2.sheet_names else pd.DataFrame()

            # Garantir alinhamento
            df1 = df1.reset_index(drop=True)
            df2 = df2.reset_index(drop=True)
            max_rows = max(len(df1), len(df2))
            all_cols = df1.columns.union(df2.columns)
            df1 = df1.reindex(index=range(max_rows), columns=all_cols)
            df2 = df2.reindex(index=range(max_rows), columns=all_cols)

            # Função de estilização
            def highlight_diff(val1, val2):
                if pd.isna(val1) and pd.isna(val2):
                    return ""
                if pd.isna(val1):
                    return "background-color: #FFCCCC"  # Adicionado (verde claro)
                if pd.isna(val2):
                    return "background-color: #CCFFCC"  # Removido (vermelho claro)
                if val1 != val2:
                    return "background-color: #FFFF99"  # Alterado (amarelo)
                return ""

            # Aplicar estilização
            style1 = df1.copy()
            style2 = df2.copy()
            for col in all_cols:
                for i in range(max_rows):
                    v1 = df1.at[i, col]
                    v2 = df2.at[i, col]
                    style1.at[i, col] = highlight_diff(v2, v1)
                    style2.at[i, col] = highlight_diff(v2, v1)

            # Criar DataFrames estilizados
            styled_df1 = df1.style.apply(
                lambda col: style1[col.name] if col.name in style1.columns else [""]*len(df1), 
                axis=0
            )
            styled_df2 = df2.style.apply(
                lambda col: style2[col.name] if col.name in style2.columns else [""]*len(df2), 
                axis=0
            )
            
            results[sheet] = (styled_df1, styled_df2)
        
        return results if not selected_sheet else results.get(selected_sheet)

    def excel_equal(file1, file2):
        import pandas as pd

        try:
            xls1 = pd.ExcelFile(file1)
            xls2 = pd.ExcelFile(file2)
        except Exception as e:
            return False

        sheets1 = set(xls1.sheet_names)
        sheets2 = set(xls2.sheet_names)
        if sheets1 != sheets2:
            return False

        for sheet in sheets1:
            df1 = xls1.parse(sheet)
            df2 = xls2.parse(sheet)
            # Converte nomes das colunas para string antes de ordenar
            df1.columns = df1.columns.map(str)
            df2.columns = df2.columns.map(str)
            df1 = df1.sort_index(axis=1).sort_index()
            df2 = df2.sort_index(axis=1).sort_index()
            if not df1.equals(df2):
                return False
        return True

# Interface principal
    tab1, tab2, tab3 = st.tabs([ "Comparar Textos", "Comparar Documentos", "Comparar Planilhas Excel"])

    with tab1:
        col1, col2 = st.columns(2)

        if "txt1" not in st.session_state:
            st.session_state.txt1 = ""
        if "txt2" not in st.session_state:
            st.session_state.txt2 = ""
        
        with col1:
            st.session_state.txt1 = st.text_area("Texto Original", value=st.session_state.txt1, key="txt1_input",  height=300)
        with col2:
            st.session_state.txt2 = st.text_area("Texto Modificado", value=st.session_state.txt2, key="txt2_input", height=300)
        
        if  st.session_state.txt1 and  st.session_state.txt2:
            btn_col1, btn_col2 = st.columns([1, 1])
            with btn_col1:
                comparar = st.button("Comparar Textos")
            with btn_col2:
                apagar = st.button("Limpar Textos")
                
            if comparar:
                comparison = compare_texts( st.session_state.txt1,  st.session_state.txt2)
                st.markdown(comparison, unsafe_allow_html=True)
                
                st.download_button(
                label="Baixar Comparação",
                data=comparison.encode("utf-8"),
                file_name="Textos Comparados.html",
                mime="text/html"
            )
                
            if apagar:
                st.session_state.txt1 = ""
                st.session_state.txt2 = ""
                st.rerun()

    with tab2:
        col1, col2 = st.columns(2)

        # Adicione um contador de reset no session_state
        if "arq_reset" not in st.session_state:
            st.session_state.arq_reset = 0

        with col1:
            st.session_state.arq1 = st.file_uploader(
                "Carregar Documento 1",
                type=["doc", "docx", "pdf", "txt", "csv"],
                accept_multiple_files=False,
                key=f"file1_input_{st.session_state.arq_reset}"
            )
        with col2:
            st.session_state.arq2 = st.file_uploader(
                "Carregar Documento 2",
                type=["doc", "docx", "pdf", "txt", "csv"],
                accept_multiple_files=False,
                key=f"file2_input_{st.session_state.arq_reset}"
            )

        if st.session_state.arq1 and st.session_state.arq2:
            btn_col1, btn_col2 = st.columns([1, 1])
            with btn_col1:
                comparar = st.button("Comparar Documentos", key="comparar_docs")
            with btn_col2:
                limpar = st.button("Limpar Uploads", key="limpar_docs")

            text1 = st.session_state.arq1.name.split('.')[-1].lower()
            text2 = st.session_state.arq2.name.split('.')[-1].lower()

            if comparar:
                with st.spinner("Fazendo comparações..."):
                    if text1 != text2:
                        st.error("Só é possível comparar arquivos do mesmo tipo/extensão!")
                    else:
                        result_doc, diff_doc, iguais = compare_docs(st.session_state.arq1, st.session_state.arq2)
                        if iguais:
                            st.info("Os arquivos são idênticos!")
                        elif result_doc and (diff_doc is None or not diff_doc.empty):
                            st.markdown(result_doc, unsafe_allow_html=True)
                            st.download_button(
                                label="Baixar Comparação",
                                data=result_doc.encode("utf-8"),
                                file_name="Arquivos Comparados.html",
                                mime="text/html"
                            )
                        else:
                            st.error("Não foi possível comparar os documentos. Verifique os formatos.")

            elif limpar:
                st.session_state.arq1 = None
                st.session_state.arq2 = None
                st.session_state.arq_reset += 1  # incrementa para forçar reset dos file_uploaders
                st.rerun()

    with tab3:
        st.title("EM DESENVOLVIMENTO")
        # col1, col2 = st.columns(2)

        # if "file_reset" not in st.session_state:
        #     st.session_state.file_reset = 0
        
        # with col1:
        #     st.session_state.file1 = st.file_uploader(
        #         "Carregar Arquivo 1", 
        #         type=["xlsx"],
        #         accept_multiple_files=False, 
        #         key=f"wb1_{st.session_state.file_reset}"
                        
        #         )
        # with col2:
        #     st.session_state.file2 = st.file_uploader(
        #         "Carregar Arquivo 2", 
        #         type=["xlsx"],
        #         accept_multiple_files=False, 
        #         key=f"wb2_{st.session_state.file_reset}"
        #         )
            
        # if st.session_state.file1 and st.session_state.file2:
        #     btn_col1, btn_col2 = st.columns([1, 1])
        #     with btn_col1:
        #         comparar = st.button("Comparar Planilhas", key="comparar_excel")
        #     with btn_col2:
        #         limpar = st.button("Limpar Uploads", key="limpar_excel")

        #     # Verificar se os arquivos são os mesmos
        #     if st.session_state.file1.name == st.session_state.file2.name:
        #         st.warning("Você carregou o mesmo arquivo duas vezes!")
        #     # Verificar se os arquivos são idênticos   
        #     elif excel_equal(st.session_state.file1, st.session_state.file2):
        #         st.warning("Os arquivos são idênticos!")

        #     else:
        #         try:
        #             xls1 = pd.ExcelFile(st.session_state.file1)
        #             xls2 = pd.ExcelFile(st.session_state.file2)
        #             all_sheets = sorted(set(xls1.sheet_names) | set(xls2.sheet_names))
        #             if len(all_sheets) > 1:
        #                 selected_sheet = st.selectbox(
        #                     "Selecione a aba para comparar:",
        #                     options= all_sheets,
        #                     index=0
        #                 )
        #                 compare_all = (selected_sheet == "Todas as abas")
        #             else:
        #                 compare_all = False
        #                 selected_sheet = all_sheets[0] if all_sheets else None
                        
        #             if comparar:
        #                 with st.spinner("Comparando arquivos..."):
        #                     result = compare_excel(st.session_state.file1, st.session_state.file2, selected_sheet)
        #                     if result:
        #                         styled1, styled2 = result
        #                         st.markdown(f"**Arquivo 1: `{selected_sheet}`**")
        #                         st.dataframe(styled1, use_container_width=True, height=600)

        #                         st.divider()

        #                         st.markdown(f"**Arquivo 2: `{selected_sheet}`**")
        #                         st.dataframe(styled2, use_container_width=True, height=600)
        #             elif limpar:
        #                 st.session_state.file1 = None
        #                 st.session_state.file2 = None
        #                 st.session_state.file_reset += 1  # incrementa para forçar reset dos file_uploaders
        #                 st.rerun()

        #         except Exception as e:
        #             st.error(f"Erro ao processar arquivos: {e}")

if __name__ == "__main__":
    main()