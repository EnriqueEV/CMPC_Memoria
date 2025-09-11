"""
STEP 3: ANÁLISIS COMPREHENSIVE DE RESULTADOS BASE
================================================
- Analizar resultados con split_roles.csv + resumen_2025.csv base (sin filtros temporales)
- Identificar patrones y estadísticas clave
- Preparar datos para implementar clasificador ML
"""

import pandas as pd
import numpy as np
from ast import literal_eval
import sys
import os
from datetime import datetime
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

def comprehensive_base_analysis():
    """
    Análisis comprehensivo de resultados base
    """
    
    print("="*60)
    print("   ANÁLISIS COMPREHENSIVE - RESULTADOS BASE")
    print("   (Sin filtros temporales, datos completos)")
    print("="*60)
    
    # 1. CARGA DE DATOS BASE
    print("\n1. CARGANDO DATOS BASE...")
    
    try:
        split_df = pd.read_csv('data/processed/split_roles.csv')
        split_df['Rol'] = split_df['Rol'].apply(literal_eval)
        split_df['Location'] = split_df['Location'].apply(literal_eval)
        print(f"   ✓ Split roles: {len(split_df)} usuarios cargados")
        
        resumen_df = pd.read_csv('data/processed/resumen_2025.csv')
        resumen_df['Fecha'] = pd.to_datetime(resumen_df['Fecha'])
        print(f"   ✓ Resumen 2025: {len(resumen_df)} asignaciones cargadas")
        
        # Estadísticas básicas
        print(f"   ✓ Período resumen: {resumen_df['Fecha'].min().date()} a {resumen_df['Fecha'].max().date()}")
        print(f"   ✓ Usuarios únicos en resumen: {resumen_df['Usuario'].nunique()}")
        print(f"   ✓ Roles únicos en resumen: {resumen_df['Rol'].nunique()}")
        
    except Exception as e:
        print(f"   Error cargando datos: {e}")
        return
    
    # 2. ANÁLISIS DE DISTRIBUCIÓN DE ROLES
    print("\n2. ANÁLISIS DE DISTRIBUCIÓN DE ROLES...")
    
    # Roles por usuario en split_df
    roles_por_usuario = split_df['Rol'].apply(len)
    print(f"   • Promedio roles por usuario: {roles_por_usuario.mean():.1f}")
    print(f"   • Mediana roles por usuario: {roles_por_usuario.median():.1f}")
    print(f"   • Mín-Máx roles por usuario: {roles_por_usuario.min()}-{roles_por_usuario.max()}")
    print(f"   • Usuarios sin roles: {(roles_por_usuario == 0).sum()}")
    
    # Top roles más comunes
    all_roles = []
    for roles_list in split_df['Rol']:
        all_roles.extend(roles_list)
    
    roles_series = pd.Series(all_roles)
    top_roles = roles_series.value_counts().head(10)
    print(f"\n   Top 10 roles más comunes:")
    for i, (rol, count) in enumerate(top_roles.items(), 1):
        print(f"     {i:2d}. {rol}: {count} usuarios")
    
    # 3. ANÁLISIS TEMPORAL DE ASIGNACIONES
    print("\n3. ANÁLISIS TEMPORAL DE ASIGNACIONES...")
    
    # Asignaciones por mes
    resumen_df['Mes'] = resumen_df['Fecha'].dt.to_period('M')
    asignaciones_mes = resumen_df.groupby('Mes').size()
    print(f"   • Asignaciones por mes:")
    for mes, count in asignaciones_mes.items():
        print(f"     {mes}: {count:,} asignaciones")
    
    # Usuarios activos por mes  
    usuarios_mes = resumen_df.groupby('Mes')['Usuario'].nunique()
    print(f"\n   • Usuarios únicos con asignaciones por mes:")
    for mes, count in usuarios_mes.items():
        print(f"     {mes}: {count} usuarios")
    
    # 4. ANÁLISIS DE DEPARTAMENTOS Y FUNCIONES
    print("\n4. ANÁLISIS ORGANIZACIONAL...")
    
    print(f"   • Total departamentos: {split_df['Departamento'].nunique()}")
    print(f"   • Total funciones: {split_df['Función'].nunique()}")
    
    # Top departamentos
    top_depts = split_df['Departamento'].value_counts().head(5)
    print(f"\n   Top 5 departamentos:")
    for i, (dept, count) in enumerate(top_depts.items(), 1):
        print(f"     {i}. {dept}: {count} usuarios")
    
    # Top funciones
    top_funcs = split_df['Función'].value_counts().head(5)
    print(f"\n   Top 5 funciones:")
    for i, (func, count) in enumerate(top_funcs.items(), 1):
        print(f"     {i}. {func}: {count} usuarios")
    
    # 5. ANÁLISIS DE UBICACIONES (SUCURSALES)
    print("\n5. ANÁLISIS DE UBICACIONES...")
    
    all_locations = []
    for locs_list in split_df['Location']:
        all_locations.extend(locs_list)
    
    locations_series = pd.Series(all_locations)
    top_locations = locations_series.value_counts()
    print(f"   • Total ubicaciones únicas: {len(top_locations)}")
    print(f"   Top ubicaciones:")
    for i, (loc, count) in enumerate(top_locations.head(10).items(), 1):
        print(f"     {i:2d}. {loc}: {count} asignaciones")
    
    # 6. ANÁLISIS DE ROLES EN RESUMEN vs SPLIT
    print("\n6. ANÁLISIS DE COHERENCIA ROLES...")
    
    # Extraer roles base del resumen (sin sufijos)
    resumen_df['RolBase'] = resumen_df['Rol'].str.split('-').str[0]
    roles_resumen = set(resumen_df['RolBase'].unique())
    
    # Roles en split_df
    roles_split = set(all_roles)
    
    print(f"   • Roles únicos en split: {len(roles_split)}")
    print(f"   • Roles únicos en resumen: {len(roles_resumen)}")
    print(f"   • Roles en común: {len(roles_split & roles_resumen)}")
    print(f"   • Solo en split: {len(roles_split - roles_resumen)}")
    print(f"   • Solo en resumen: {len(roles_resumen - roles_split)}")
    
    # 7. PREPARACIÓN PARA ANÁLISIS DE SIMILITUD
    print("\n7. PREPARANDO ANÁLISIS DE SIMILITUD...")
    
    # Verificar si existe la matriz de similitud
    if os.path.exists('data/processed/user_similarity.csv'):
        print("   ✓ Matriz de similitud encontrada")
        sim_df = pd.read_csv('data/processed/user_similarity.csv', index_col=0)
        print(f"   ✓ Matriz cargada: {sim_df.shape}")
        
        # Estadísticas de similitud
        # Excluir diagonal (similitud consigo mismo = 1.0)
        np.fill_diagonal(sim_df.values, np.nan)
        sim_values = sim_df.values.flatten()
        sim_values = sim_values[~np.isnan(sim_values)]
        
        print(f"   • Similitud promedio: {np.mean(sim_values):.4f}")
        print(f"   • Similitud mediana: {np.median(sim_values):.4f}")
        print(f"   • Similitud mín-máx: {np.min(sim_values):.4f} - {np.max(sim_values):.4f}")
        print(f"   • Pares con similitud >0.8: {(sim_values > 0.8).sum():,}")
        print(f"   • Pares con similitud >0.9: {(sim_values > 0.9).sum():,}")
        
    else:
        print("   Matriz de similitud no encontrada - ejecutar pair_similarity.py")
    
    # 8. RECOMENDACIONES PARA SIGUIENTE ANÁLISIS
    print("\n8. RECOMENDACIONES PARA PRÓXIMOS PASOS...")
    
    print("   Análisis completado. Para continuar:")
    print("   1. Ejecutar simple_run.py con datos base para obtener scores actuales")
    print("   2. Analizar usuarios con mejor/peor performance individual")
    print("   3. Implementar clasificador ML para filtrar recomendaciones")
    print("   4. Considerar clustering avanzado (Louvain, Node2Vec)")
    
    # 9. GUARDAR RESUMEN ESTADÍSTICO
    print("\n9. GUARDANDO RESUMEN...")
    
    summary_stats = {
        'timestamp': datetime.now().isoformat(),
        'total_usuarios': len(split_df),
        'total_asignaciones_2025': len(resumen_df),
        'promedio_roles_usuario': roles_por_usuario.mean(),
        'total_departamentos': split_df['Departamento'].nunique(),
        'total_funciones': split_df['Función'].nunique(),
        'total_roles_unicos_split': len(roles_split),
        'total_roles_unicos_resumen': len(roles_resumen),
        'roles_en_common': len(roles_split & roles_resumen),
        'periodo_inicio': resumen_df['Fecha'].min().isoformat(),
        'periodo_fin': resumen_df['Fecha'].max().isoformat()
    }
    
    summary_df = pd.DataFrame([summary_stats])
    summary_df.to_csv('data/processed/comprehensive_base_summary.csv', index=False)
    print("   ✓ Resumen guardado en: data/processed/comprehensive_base_summary.csv")
    
    print("\n" + "="*60)
    print("   ANÁLISIS BASE COMPLETADO")
    print("   Datos listos para implementar clasificador ML")  
    print("="*60)

if __name__ == "__main__":
    comprehensive_base_analysis()