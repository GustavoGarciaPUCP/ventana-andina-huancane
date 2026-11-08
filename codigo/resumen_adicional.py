"""Descriptivos de salidas congeladas; no ajusta modelos, pesos ni umbrales."""
from pathlib import Path
import json
import pandas as pd


def resumir(out):
    out = Path(out)
    avisos = pd.read_csv(out / 'predicciones_prueba_m3.csv')
    episodios = pd.read_csv(out / 'episodios_prueba.csv')
    episodios = episodios.loc[episodios.thermal == -3]
    validos = avisos['valido'].astype(bool)
    a = avisos.loc[validos, 'aviso_beta0.5_logistica']
    b = avisos.loc[validos, 'aviso_beta0.5_arbol']
    resultado = {
        'alcance': 'Descripcion posterior de salidas, sin nuevas decisiones de ajuste',
        'thermal': -3,
        'beta': 0.5,
        'n': int(validos.sum()),
        'desacuerdo_avisos_logistica_arbol': int((a != b).sum()),
        'fraccion_desacuerdo': float((a != b).mean()),
        'episodios_prueba': len(episodios),
        'episodios_por_ano': {str(int(k)): int(v) for k, v in episodios.groupby('year').size().items()},
        'subventanas_en_episodios': int(episodios.subventanas_tres_dias.sum()),
        'positivos_prueba': int(avisos.loc[validos, 'y'].sum()),
        'episodios_tocan_borde': int(episodios.toca_borde_temporada.sum()),
    }
    (out / 'resumen_descriptivo.json').write_text(
        json.dumps(resultado, indent=2, ensure_ascii=False), encoding='utf-8'
    )
    return resultado


if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('--out-dir', type=Path, default=Path('resultados'))
    print(json.dumps(resumir(p.parse_args().out_dir), indent=2))
