import pandas as pd
import numpy as np

def clean_numeric_series(series: pd.Series) -> pd.Series:
    """Limpia una serie de caracteres monetarios y devuelve una serie numérica."""
    return pd.to_numeric(
        series.astype(str).str.replace('$', '', regex=False).str.replace('€', '', regex=False)
        .str.replace('£', '', regex=False).str.replace(',', '', regex=False)
        .str.replace('(', '-', regex=False).str.replace(')', '', regex=False).str.strip(),
        errors='coerce'
    ).fillna(0.0)

def infer_columns_by_mathematical_weights(df: pd.DataFrame) -> tuple[str, str, str, float]:
    """Infiere las columnas de Cuenta, Descripción y Saldo basado en heurísticas."""
    cols = list(df.columns)
    if len(cols) < 2:
        return cols[0], cols[0], cols[0], 100.0
    
    sample = df.head(min(len(df), 120))
    scores_cta, scores_desc, scores_saldo = {}, {}, {}
    total_cols = max(1, len(cols) - 1)
    
    for i, col in enumerate(cols):
        s = sample[col].astype(str).str.strip()
        ordinal = i / total_cols
        clean_num = clean_numeric_series(s)
        num_ratio = float((~clean_num.isna()).mean())
        has_neg = 1.0 if (clean_num < 0).any() else 0.0
        code_ratio = float((s.str.match(r'^[0-9A-Za-z\.\-_/]+$') & (~s.str.contains(' ', regex=False))).mean()) if len(s) > 0 else 0.0
        spaces_ratio = float(s.str.contains(r'\s+', regex=True).mean()) if len(s) > 0 else 0.0
        avg_char_len, uniq_ratio = float(s.str.len().mean()) if len(s) > 0 else 0.0, float(s.nunique() / max(1, len(s)))
        
        scores_saldo[col] = (0.50 * num_ratio) + (0.20 * has_neg) + (0.15 * (1.0 - code_ratio)) + (0.15 * ordinal)
        scores_cta[col] = (0.40 * code_ratio) + (0.30 * uniq_ratio) + (0.20 * (1.0 - spaces_ratio)) + (0.10 * (1.0 - ordinal))
        scores_desc[col] = (0.50 * spaces_ratio) + (0.30 * (1.0 - num_ratio)) + (0.20 * min(1.0, avg_char_len / 15.0))
        
    best_score, best_assignment = -1.0, (cols[0], cols[min(1, len(cols)-1)], cols[-1])
    for c_i in cols:
        for d_j in cols:
            if d_j == c_i and len(cols) >= 3: continue
            for s_k in cols:
                if (s_k == c_i or s_k == d_j) and len(cols) >= 3: continue
                total = scores_cta[c_i] + scores_desc[d_j] + scores_saldo[s_k]
                if total > best_score:
                    best_score, best_assignment = total, (c_i, d_j, s_k)
                    
    conf_pct = min(100.0, max(10.0, (best_score / 3.0) * 100.0))
    return best_assignment[0], best_assignment[1], best_assignment[2], conf_pct

def read_excel_smart_header(excel_file, sheet_name) -> pd.DataFrame:
    """Lee un excel identificando de forma inteligente la fila de cabecera."""
    df_preview = pd.read_excel(excel_file, sheet_name=sheet_name, header=None, nrows=15)
    best_row, max_non_na = 0, 0
    for r in range(len(df_preview)):
        non_na = df_preview.iloc[r].dropna().count()
        if non_na > max_non_na and non_na >= 2:
            max_non_na, best_row = non_na, r
    df_full = pd.read_excel(excel_file, sheet_name=sheet_name, header=best_row)
    return df_full.dropna(how='all', axis=1).dropna(how='all', axis=0)
