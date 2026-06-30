import pandas as pd
import re
import json

def normalizar_csv():
    df = pd.read_csv("Guia_medicamentos_pediatricos_Sebas.csv", sep=";", encoding="latin-1")
    
    filas_normalizadas = []
    ambiguedades = []
    
    total_filas = len(df)
    parsed_con_exito = 0
    
    for idx, row in df.iterrows():
        med = str(row.get('Medicamento', '')).strip()
        grupo = str(row.get('Grupo', '')).strip()
        vias_orig = str(row.get('Vía', '')).strip()
        dosis_orig = str(row.get('Dosis pediátrica usual', '')).strip()
        dosis_max_orig = str(row.get('Dosis máxima / límite', '')).strip()
        dosis_neonatal = str(row.get('Dosis neonatal', '')).strip()
        
        # Replace the latin-1 dash \x96 with standard hyphen for easier regex
        dosis_orig_clean = dosis_orig.replace('\x96', '-')
        dosis_max_orig_clean = dosis_max_orig.replace('\x96', '-')
        
        dosis_min_mg_kg = None
        dosis_max_mg_kg = None
        dosis_fija_mg = None
        frecuencia_min_horas = None
        frecuencia_max_horas = None
        dosis_max_mg_kg_dia = None
        dosis_max_absoluta_mg_dia = None
        requiere_revision_manual = False
        comentario_normalizacion = []
        
        # 1. Normalizar Vía
        via_normalizada = vias_orig.upper().replace(' ', '')
        
        # 2. Es neonatal?
        es_neonatal = True if isinstance(dosis_neonatal, str) and len(dosis_neonatal) > 5 and 'no recomendado' not in dosis_neonatal.lower() and 'evitar' not in dosis_neonatal.lower() else False
        
        # 3. Parsear dosis mg/kg
        # Look for patterns like: 10-15 mg/kg, 0.5 mg/kg, 10 a 15 mg/kg
        mg_kg_match = re.search(r'([\d\.]+)\s*(?:a|-)\s*([\d\.]+)\s*mg/kg', dosis_orig_clean.lower())
        mg_kg_single = re.search(r'(?<!-)(?<!a\s)([\d\.]+)\s*mg/kg', dosis_orig_clean.lower())
        
        if mg_kg_match:
            try:
                dosis_min_mg_kg = float(mg_kg_match.group(1))
                dosis_max_mg_kg = float(mg_kg_match.group(2))
            except: pass
        elif mg_kg_single:
            try:
                dosis_min_mg_kg = float(mg_kg_single.group(1))
                dosis_max_mg_kg = float(mg_kg_single.group(1))
            except: pass
        else:
            requiere_revision_manual = True
            comentario_normalizacion.append("No se encontró patrón claro de mg/kg en dosis.")
            
        # 4. Parsear frecuencias (cada X h, cada X a Y h)
        freq_match = re.search(r'cada\s+(\d+)\s*(?:a|-)\s*(\d+)\s*h', dosis_orig_clean.lower())
        freq_single = re.search(r'cada\s+(\d+)\s*h', dosis_orig_clean.lower())
        
        if freq_match:
            frecuencia_min_horas = int(freq_match.group(1))
            frecuencia_max_horas = int(freq_match.group(2))
        elif freq_single:
            frecuencia_min_horas = int(freq_single.group(1))
            frecuencia_max_horas = int(freq_single.group(1))
        else:
            requiere_revision_manual = True
            comentario_normalizacion.append("No se encontró patrón claro de frecuencia (cada X h).")
            
        # 5. Parsear Dosis Máxima
        # max mg/kg/dia
        max_mg_kg_dia_match = re.search(r'([\d\.]+)\s*mg/kg/d[íi]a', dosis_max_orig_clean.lower())
        if max_mg_kg_dia_match:
            dosis_max_mg_kg_dia = float(max_mg_kg_dia_match.group(1))
            
        # max g/dia o mg/dia o mg/dosis
        max_g_dia_match = re.search(r'([\d\.]+)\s*g/d[íi]a', dosis_max_orig_clean.lower())
        max_mg_dia_match = re.search(r'([\d\.]+)\s*mg/d[íi]a', dosis_max_orig_clean.lower())
        max_mg_dosis_match = re.search(r'([\d\.]+)\s*mg/dosis', dosis_max_orig_clean.lower())
        
        if max_g_dia_match:
            dosis_max_absoluta_mg_dia = float(max_g_dia_match.group(1)) * 1000
        elif max_mg_dia_match:
            dosis_max_absoluta_mg_dia = float(max_mg_dia_match.group(1))
            
        if not max_mg_kg_dia_match and not max_g_dia_match and not max_mg_dia_match and not max_mg_dosis_match:
            requiere_revision_manual = True
            comentario_normalizacion.append("No se pudo extraer límite máximo numérico.")
            
        # Ambigüedades adicionales
        if ';' in dosis_orig_clean or 'según' in dosis_orig_clean.lower() or 'titul' in dosis_max_orig_clean.lower():
            requiere_revision_manual = True
            comentario_normalizacion.append("Texto condicional o múltiples esquemas detectados.")
            
        if not requiere_revision_manual:
            parsed_con_exito += 1
        else:
            ambiguedades.append({
                "Medicamento": med,
                "Texto_Dosis": dosis_orig_clean,
                "Texto_Max": dosis_max_orig_clean,
                "Comentarios": " | ".join(comentario_normalizacion)
            })
            
        filas_normalizadas.append({
            "medicamento": med,
            "grupo": grupo,
            "via_normalizada": via_normalizada,
            "dosis_min_mg_kg": dosis_min_mg_kg,
            "dosis_max_mg_kg": dosis_max_mg_kg,
            "dosis_fija_mg": dosis_fija_mg,
            "frecuencia_min_horas": frecuencia_min_horas,
            "frecuencia_max_horas": frecuencia_max_horas,
            "dosis_max_mg_kg_dia": dosis_max_mg_kg_dia,
            "dosis_max_absoluta_mg_dia": dosis_max_absoluta_mg_dia,
            "es_neonatal": es_neonatal,
            "texto_original_dosis": dosis_orig_clean,
            "texto_original_maximo": dosis_max_orig_clean,
            "requiere_revision_manual": requiere_revision_manual,
            "comentario_normalizacion": " | ".join(comentario_normalizacion)
        })

    df_out = pd.DataFrame(filas_normalizadas)
    df_out.to_csv("Guia_medicamentos_pediatricos_Estructurada.csv", index=False, sep=";", encoding="utf-8")
    
    porcentaje = (parsed_con_exito / total_filas) * 100
    
    reporte = {
        "total_filas": total_filas,
        "parsed_con_exito": parsed_con_exito,
        "porcentaje_exito": round(porcentaje, 2),
        "ambiguedades": ambiguedades
    }
    
    with open("reporte_normalizacion.json", "w", encoding="utf-8") as f:
        json.dump(reporte, f, indent=4, ensure_ascii=False)
        
    print(f"Normalizacion completada. {parsed_con_exito}/{total_filas} ({porcentaje:.2f}%) filas parseadas limpiamente sin intervencion manual.")

if __name__ == "__main__":
    normalizar_csv()
