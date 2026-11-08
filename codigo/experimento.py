"""Experimento reproducible: ventanas frias en una celda PISCOt de Huancane.

Fases separadas: prepare selecciona TODO sin evaluar 2016--2020 y escribe
freeze.json; test exige ese archivo y modelos ya ajustados. No se reentrena
con validacion. --data-dir contiene los dos NetCDF diarios originales.
"""
from __future__ import annotations
import argparse
import hashlib
import importlib.metadata
import json
import platform
import time
import warnings
from pathlib import Path

import joblib
import netCDF4
import numpy as np
import pandas as pd
import sklearn
from sklearn.exceptions import ConvergenceWarning
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeClassifier

SEED = 2026
THERMALS = [-3., -2., -4.]
MODELS = ['logistica', 'arbol', 'knn', 'mezcla', 'frecuencia_mensual', 'persistencia']
CLASSIFIERS = MODELS[:4]
FEATURES = [f'{v}_lag_{lag}' for v in ['tmin', 'tmax'] for lag in range(6, -1, -1)] + ['sin_dia', 'cos_dia']
FOLDS = [(1981, 1995, 1996, 2000), (1981, 2000, 2001, 2005), (1981, 2005, 2006, 2010)]
GRIDS = {
    'logistica': [{'C': c} for c in [.1, 1., 10.]],
    'arbol': [{'max_depth': d, 'min_samples_leaf': leaf} for d in [3, 5, 8] for leaf in [30, 10]],
    'knn': [{'n_neighbors': k} for k in [31, 15, 5]],
}


def clean_json(obj):
    if isinstance(obj, dict):
        return {str(k): clean_json(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [clean_json(v) for v in obj]
    if isinstance(obj, np.ndarray):
        return clean_json(obj.tolist())
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.bool_,)):
        return bool(obj)
    if isinstance(obj, (np.floating, float)):
        return float(obj) if np.isfinite(obj) else None
    return obj


def write_json(path, obj):
    Path(path).write_text(json.dumps(clean_json(obj), ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False), encoding='utf-8')


def sha(path):
    with open(path, 'rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def save_csv(df, path):
    df.to_csv(path, index=False, encoding='utf-8-sig', float_format='%.12g', date_format='%Y-%m-%d')


def extract_cell(data_dir, out):
    """Lee solo una celda de cada NetCDF; no interpreta metricas del test."""
    out.mkdir(parents=True, exist_ok=True)
    frames, manifest, geometry = {}, {}, {}
    for variable in ['tmin', 'tmax']:
        path = data_dir / f'{variable}_daily_1981_2020_010.nc'
        manifest[variable] = {'filename': path.name, 'bytes': path.stat().st_size, 'sha256': sha(path)}
        with netCDF4.Dataset(path) as ds:
            lat, lon = np.asarray(ds['latitude'][:]), np.asarray(ds['longitude'][:])
            i, j = int(np.argmin(abs(lat + 15.225))), int(np.argmin(abs(lon + 69.755)))
            assert np.isclose(lat[i], -15.225) and np.isclose(lon[j], -69.755), 'Celda inesperada'
            dates = netCDF4.num2date(ds['time'][:], ds['time'].units, calendar=ds['time'].calendar)
            dates = pd.DatetimeIndex([d.strftime('%Y-%m-%d') for d in dates])
            vals = np.ma.filled(ds[variable][:, i, j], np.nan).astype(float)
            frames[variable] = pd.Series(vals, index=dates)
            geometry[variable] = {'latitude': float(lat[i]), 'longitude': float(lon[j]), 'latitude_index': i, 'longitude_index': j, 'variable_dimensions': list(ds[variable].dimensions), 'shape': list(ds[variable].shape), 'calendar': str(ds['time'].calendar), 'global_attributes': {a: str(ds.getncattr(a)) for a in ds.ncattrs()}}
    a, b = frames['tmin'], frames['tmax']
    assert a.index.equals(b.index), 'Fechas Tmin y Tmax distintas'
    duplicates = int(a.index.duplicated().sum())
    audit = {'duplicate_dates': duplicates, 'dates_sorted': bool(a.index.is_monotonic_increasing), 'first_date': str(a.index.min().date()), 'last_date': str(a.index.max().date()), 'rows_original': len(a), 'geometry': geometry}
    write_json(out / 'manifest_fuentes.json', manifest)
    if duplicates or not a.index.is_monotonic_increasing:
        write_json(out / 'auditoria_datos.json', audit)
        raise ValueError('Fechas duplicadas/desordenadas: no resolver silenciosamente')
    full = pd.date_range('1981-01-01', '2020-12-31', freq='D')
    assert a.index.min() >= full.min() and a.index.max() <= full.max()
    df = pd.DataFrame({'tmin': a, 'tmax': b}).reindex(full)
    df.index.name = 'fecha'
    finite = np.isfinite(df.tmin) & np.isfinite(df.tmax)
    consistent = df.tmin <= df.tmax
    df['valido_dia'] = finite & consistent
    audit.update({'rows_full_calendar': len(df), 'missing_calendar_dates': len(full.difference(a.index)), 'missing_or_nonfinite_tmin': int((~np.isfinite(df.tmin)).sum()), 'missing_or_nonfinite_tmax': int((~np.isfinite(df.tmax)).sum()), 'tmin_exceeds_tmax': int((finite & ~consistent).sum()), 'invalid_days': int((~df.valido_dia).sum()), 'imputation': 'Ninguna; las ventanas que tocan dias invalidos se excluyen.', 'extraction_precision': 'float64 a partir de valores originales NetCDF, sin redondear para entrenar.'})
    write_json(out / 'auditoria_datos.json', audit)
    # 17 cifras significativas garantizan round-trip de float64 en el cache.
    df.reset_index().to_csv(out / 'celda_diaria.csv', index=False, float_format='%.17g', date_format='%Y-%m-%d', encoding='utf-8')
    return df, manifest, audit


def make_examples(daily, thermal, min_year=1981, max_year=2020):
    """t-6..t son atributos; t+1..t+3 son objetivo. QC en diez dias."""
    x = pd.DataFrame(index=daily.index)
    for v in ['tmin', 'tmax']:
        for lag in range(6, -1, -1):
            x[f'{v}_lag_{lag}'] = daily[v].shift(lag)
    denominator = np.where(daily.index.is_leap_year, 366., 365.)
    angle = 2 * np.pi * daily.index.dayofyear.to_numpy() / denominator
    x['sin_dia'], x['cos_dia'] = np.sin(angle), np.cos(angle)
    history_valid = pd.concat([daily.valido_dia.shift(k) for k in range(7)], axis=1).eq(True).all(axis=1)
    target_valid = pd.concat([daily.valido_dia.shift(-k) for k in range(1, 4)], axis=1).eq(True).all(axis=1)
    future = pd.concat([daily.tmin.shift(-k) for k in range(1, 4)], axis=1)
    past3 = pd.concat([daily.tmin.shift(k) for k in range(3)], axis=1)
    x['valido_historia'], x['valido_objetivo'] = history_valid, target_valid
    x['valido'] = history_valid & target_valid
    x['y'] = future.le(thermal).all(axis=1).astype(float).where(x.valido)
    x['persistencia'] = past3.le(thermal).all(axis=1).astype(float).where(x.valido)
    x['objetivo_inicio'] = x.index + pd.Timedelta(days=1)
    x['objetivo_fin'] = x.index + pd.Timedelta(days=3)
    x['year'], x['month'] = x.index.year, x.index.month
    mmdd = x.index.strftime('%m-%d')
    x = x.loc[(mmdd >= '04-01') & (mmdd <= '09-27') & (x.year >= min_year) & (x.year <= max_year)].copy()
    x.index.name = 'fecha'
    assert len(x) == 180 * (max_year - min_year + 1)
    assert x.objetivo_fin.dt.month.le(9).all()
    assert (x.objetivo_inicio > x.index).all()
    assert np.isfinite(x.loc[x.valido, FEATURES].to_numpy()).all()
    return x


def score(y, p, pred, beta=.5):
    y, p, pred = np.asarray(y, dtype=int), np.asarray(p, dtype=float), np.asarray(pred, dtype=bool)
    n = len(y)
    tp = int(((y == 1) & pred).sum()); fp = int(((y == 0) & pred).sum())
    fn = int(((y == 1) & ~pred).sum()); tn = int(((y == 0) & ~pred).sum())
    positive = tp + fn
    precision = tp / (tp + fp) if tp + fp else 0.
    recall = tp / positive if positive else np.nan
    def f(b):
        return (1+b*b)*tp / ((1+b*b)*tp + fp + b*b*fn) if positive else np.nan
    return {'n': n, 'positivos': positive, 'prevalencia': positive/n if n else np.nan, 'avisos': tp+fp, 'VP': tp, 'FP': fp, 'FN': fn, 'VN': tn, 'precision': precision, 'recall': recall, 'F0.5': f(.5), 'F1': f(1.), 'Fbeta': f(beta), 'Brier': float(np.mean((p-y)**2)) if n else np.nan, 'average_precision': float(average_precision_score(y, p)) if positive else np.nan}


def choose_threshold(y, probs, beta):
    """Empates numericos <=1e-12 favorecen tau mayor; aviso p>=tau."""
    candidates = np.r_[np.unique(probs), np.nextafter(float(np.max(probs)), np.inf)]
    rows = []
    for tau in candidates:
        s = score(y, probs, probs >= tau, beta)
        rows.append({'tau': float(tau), 'Fbeta': s['Fbeta'], 'precision': s['precision'], 'recall': s['recall'], 'VP': s['VP'], 'FP': s['FP'], 'FN': s['FN']})
    table = pd.DataFrame(rows)
    if not np.isfinite(table.Fbeta).any():
        raise ValueError('No hay positivos en validacion; no puede ajustarse Fbeta')
    best = table.Fbeta.max()
    selected = table.loc[np.isclose(table.Fbeta, best, atol=1e-12, rtol=0)].tau.max()
    return float(selected), table


def model_factory(name, cfg):
    if name == 'logistica':
        # L2 es el valor por defecto con lbfgs; explicitado si la API lo permite.
        return make_pipeline(StandardScaler(), LogisticRegression(C=cfg['C'], solver='lbfgs', max_iter=10000, random_state=SEED))
    if name == 'arbol':
        return DecisionTreeClassifier(criterion='gini', random_state=SEED, **cfg)
    return make_pipeline(StandardScaler(), KNeighborsClassifier(weights='uniform', metric='euclidean', algorithm='brute', n_jobs=1, **cfg))


def select_config(name, frame, thermal):
    rows, candidate_rows = [], []
    for cfg_idx, cfg in enumerate(GRIDS[name]):
        bs = []
        for fold, (train_start, train_end, eval_start, eval_end) in enumerate(FOLDS, 1):
            tr = frame.loc[frame.valido & frame.year.between(train_start, train_end)]
            va = frame.loc[frame.valido & frame.year.between(eval_start, eval_end)]
            assert tr.objetivo_fin.max() < va.index.min()
            model = model_factory(name, cfg)
            with warnings.catch_warnings():
                warnings.simplefilter('error', ConvergenceWarning)
                model.fit(tr[FEATURES], tr.y.astype(int))
            if name != 'arbol':
                assert np.allclose(model[0].mean_, tr[FEATURES].mean().to_numpy(), atol=1e-10)
            p = model.predict_proba(va[FEATURES])[:, 1]
            brier = float(np.mean((p - va.y.to_numpy())**2))
            bs.append(brier)
            rows.append({'thermal': thermal, 'model': name, 'candidate': cfg_idx, 'params': json.dumps(cfg, sort_keys=True), 'fold': fold, 'train_start': train_start, 'train_end': train_end, 'eval_start': eval_start, 'eval_end': eval_end, 'n_train': len(tr), 'n_eval': len(va), 'Brier': brier})
        candidate_rows.append({'thermal': thermal, 'model': name, 'candidate': cfg_idx, 'params': json.dumps(cfg, sort_keys=True), 'Brier_mean': float(np.mean(bs)), 'Brier_std_population': float(np.std(bs))})
    best_score = min(r['Brier_mean'] for r in candidate_rows)
    tied = [r for r in candidate_rows if np.isclose(r['Brier_mean'], best_score, atol=1e-12, rtol=0)]
    # Orden de la rejilla: menor C, menor profundidad/mayor hoja, mayor k.
    winner = min(tied, key=lambda r: r['candidate'])
    for r in candidate_rows:
        r['selected'] = r['candidate'] == winner['candidate']
    return GRIDS[name][winner['candidate']], rows, candidate_rows


def select_principal(metrics):
    best_f = max(metrics[m]['Fbeta'] for m in CLASSIFIERS)
    tied = [m for m in CLASSIFIERS if np.isclose(metrics[m]['Fbeta'], best_f, atol=1e-12, rtol=0)]
    best_b = min(metrics[m]['Brier'] for m in tied)
    return next(m for m in tied if np.isclose(metrics[m]['Brier'], best_b, atol=1e-12, rtol=0))


def episodes(daily, thermal, first_year, last_year):
    """Rachas maximales dentro de abril-septiembre; episodios son >=3 dias.

    Un episodio de L dias contiene L-2 subventanas completas, pero las
    emisiones cubren objetivos desde 2/abril: documentar esta frontera.
    """
    rows = []
    for year in range(first_year, last_year+1):
        d = daily.loc[f'{year}-04-01':f'{year}-09-30']
        cold = (d.valido_dia & (d.tmin <= thermal)).to_numpy()
        starts = np.flatnonzero(cold & ~np.r_[False, cold[:-1]])
        ends = np.flatnonzero(cold & ~np.r_[cold[1:], False])
        for start, end in zip(starts, ends):
            length = int(end-start+1)
            if length >= 3:
                rows.append({'thermal': thermal, 'year': year, 'inicio': str(d.index[start].date()), 'fin': str(d.index[end].date()), 'dias': length, 'tmin_min': float(d.tmin.iloc[start:end+1].min()), 'subventanas_tres_dias': length-2, 'toca_borde_temporada': bool(start==0 or end==len(d)-1)})
    return pd.DataFrame(rows, columns=['thermal','year','inicio','fin','dias','tmin_min','subventanas_tres_dias','toca_borde_temporada'])


def sanity_tests(daily):
    # Modificar el futuro no puede cambiar atributos del presente.
    ref = make_examples(daily.loc[:'2015-12-31'], -3, 1981, 2015)
    d = pd.Timestamp('2010-06-15')
    changed = daily.loc[:'2015-12-31'].copy()
    changed.loc[d+pd.Timedelta(days=1):, ['tmin','tmax']] += 100
    new = make_examples(changed, -3, 1981, 2015)
    assert np.array_equal(ref.loc[d, FEATURES].to_numpy(), new.loc[d, FEATURES].to_numpy())
    assert ref.loc[d,'objetivo_fin'] == d+pd.Timedelta(days=3)
    assert list(ref.loc[d, [f'tmin_lag_{i}' for i in range(6,-1,-1)]]) == list(daily.loc[d-pd.Timedelta(days=6):d, 'tmin'])
    assert all(make_examples(daily, -3, y,y).shape[0] == 180 for y in [1981,1984,2016,2020])
    s = score([1,1,0], [.8,.2,.7], [1,0,1])
    assert np.isclose(s['F0.5'], 1.25/(1.25+1+.25))
    z = score([0,0], [.1,.2], [0,0])
    assert z['precision']==0 and np.isnan(z['recall']) and np.isnan(z['F0.5'])
    # QC: un dia invalido invalida t-6..t+3, sin rellenar el objetivo.
    bad = daily.copy(); bad.loc[d,'valido_dia'] = False
    check = make_examples(bad, -3, 2010, 2010)
    assert not check.loc[d-pd.Timedelta(days=3):d+pd.Timedelta(days=6),'valido'].any()
    assert check.loc[d-pd.Timedelta(days=4),'valido'] == make_examples(daily,-3,2010,2010).loc[d-pd.Timedelta(days=4),'valido']
    return {'future_perturbation_does_not_change_features': True, 'exact_feature_alignment': True, 'three_future_days': True, '180_candidate_dates_per_year': True, 'Fbeta_formula': True, 'no_positives_convention': True, 'invalid_full_window_no_imputation': True, 'temporal_folds_no_overlap_and_train_scalers_checked_during_fit': True}


def prepare(data_dir, out):
    begin = time.perf_counter()
    out.mkdir(parents=True, exist_ok=True)
    daily, manifest, audit = extract_cell(data_dir, out)
    tests = sanity_tests(daily)
    write_json(out/'sanity_tests.json', tests)
    # No ejemplos, etiquetas ni probabilidades de prueba durante seleccion.
    pretest_daily = daily.loc[:'2015-12-31'].copy()
    all_cv, all_means, all_val, all_alpha, all_thresholds, all_pop, all_month, all_eps = [], [], [], [], [], [], [], []
    state, decisions = {}, {}
    for thermal in THERMALS:
        print(f'PREPARE thermal={thermal:g}; solo 1981-2015', flush=True)
        frame = make_examples(pretest_daily, thermal, 1981, 2015)
        train = frame.loc[frame.valido & frame.year.le(2010)]
        val = frame.loc[frame.valido & frame.year.ge(2011)]
        configs, fitted = {}, {}
        for name in GRIDS:
            cfg, cvrows, means = select_config(name, frame, thermal)
            configs[name] = cfg; all_cv.extend(cvrows); all_means.extend(means)
            fitted[name] = model_factory(name, cfg)
            with warnings.catch_warnings():
                warnings.simplefilter('error', ConvergenceWarning)
                fitted[name].fit(train[FEATURES], train.y.astype(int))
        probs = {n: fitted[n].predict_proba(val[FEATURES])[:,1] for n in fitted}
        monthly = train.groupby('month').y.mean().to_dict()
        probs['frecuencia_mensual'] = val.month.map(monthly).to_numpy()
        probs['persistencia'] = val.persistencia.to_numpy()
        arows = []
        for alpha in [0., .25, .5, .75, 1.]:
            p = alpha*probs['logistica'] + (1-alpha)*probs['arbol']
            arows.append({'thermal': thermal, 'alpha': alpha, 'Brier': float(np.mean((p-val.y.to_numpy())**2))})
        low = min(r['Brier'] for r in arows)
        alpha = max(r['alpha'] for r in arows if np.isclose(r['Brier'],low,atol=1e-12,rtol=0))
        for r in arows: r['selected'] = r['alpha']==alpha
        all_alpha.extend(arows)
        probs['mezcla'] = alpha*probs['logistica'] + (1-alpha)*probs['arbol']
        if alpha in [0.,1.]:
            assert np.array_equal(probs['mezcla'], probs['logistica' if alpha==1 else 'arbol'])
        decisions_by_beta = {}
        for beta in [.5, 1.]:
            thresholds, metrics = {}, {}
            for name in MODELS:
                if name == 'persistencia':
                    tau = .5
                else:
                    tau, table = choose_threshold(val.y.to_numpy(), probs[name], beta)
                    table['thermal'],table['beta'],table['model']=thermal,beta,name
                    all_thresholds.extend(table.to_dict('records'))
                thresholds[name] = tau
                metrics[name] = score(val.y, probs[name], probs[name]>=tau, beta)
                all_val.append({'thermal':thermal,'beta':beta,'model':name,'tau':tau,**metrics[name]})
            principal = select_principal(metrics)
            decisions_by_beta[str(beta)] = {'thresholds':thresholds,'principal':principal,'validation_metrics':metrics}
        key = str(int(thermal))
        decisions[key] = {'thermal':thermal,'selected_configs':configs,'alpha':alpha,'monthly_training_frequencies':monthly,'decisions_by_beta':decisions_by_beta,'training_n':len(train),'validation_n':len(val)}
        state[key] = {'models':fitted,'monthly':monthly,'validation_dates':val.index,'validation_probs':probs}
        pred_val = val[['y','persistencia','objetivo_inicio','objetivo_fin']].copy()
        for n in MODELS: pred_val[f'p_{n}'] = probs[n]
        save_csv(pred_val.reset_index(),out/f'predicciones_validacion_m{abs(int(thermal))}.csv')
        for label,a,b in [('entrenamiento',1981,2010),('validacion',2011,2015)]:
            sub=frame.loc[frame.year.between(a,b)]
            all_pop.append({'thermal':thermal,'split':label,'candidate_n':len(sub),'valid_n':int(sub.valido.sum()),'invalid_n':int((~sub.valido).sum()),'positive_n':int(sub.y.sum()),'prevalence':float(sub.y.mean())})
        for month,g in train.groupby('month'):
            all_month.append({'thermal':thermal,'month':month,'n':len(g),'positive_n':int(g.y.sum()),'window_frequency':float(g.y.mean()),'tmin_mean':float(g.tmin_lag_0.mean()),'tmin_min':float(g.tmin_lag_0.min()),'tmax_mean':float(g.tmax_lag_0.mean())})
        all_eps.append(episodes(pretest_daily,thermal,1981,2015))
        print(f"  configs={configs}; alpha={alpha}; principal={decisions_by_beta['0.5']['principal']}",flush=True)
    write_json(out/'freeze.json',{'protocol_version':'1.0','seed':SEED,'feature_order':FEATURES,'thermal_definitions':THERMALS,'train':'1981-2010','validation':'2011-2015','test':'2016-2020 (NO EVALUADO EN ESTA FASE)','model_fit_uses_validation':False,'season_emission':'04-01..09-27 inclusive; 180/y','target':'all three tmin(t+1:t+3) <= thermal','seasonal_encoding':'sin/cos(2*pi*dayofyear/D), D=365 or 366 of emission year','alpha_formula':'alpha*LR+(1-alpha)*tree','alpha_tie':'higher alpha','tie_tolerance_absolute':1e-12,'threshold_rule':'p>=tau; candidates unique validation probabilities + nextafter(max,+inf); Fbeta tie higher tau','config_tie':'lower C; lower depth then larger leaf; larger k','principal_tie':'higher validation Fbeta, then lower Brier, then LR/tree/KNN/mix','beta1_scope':'secondary; same configurations, fitted models, probabilities and alpha as beta0.5','bootstrap':'1000 paired calendar moving-block samples; six blocks of30 per season within each of five fixed test years; shared mask and indices; seed2026','sources':manifest,'code_sha256':sha(__file__),'versions':{'python':platform.python_version(),'numpy':np.__version__,'pandas':pd.__version__,'sklearn':sklearn.__version__},'decisions':decisions})
    joblib.dump(state,out/'modelos_congelados.joblib',compress=3)
    for name,rows in [('cv_folds',all_cv),('cv_resumen',all_means),('metricas_validacion',all_val),('alpha_validacion',all_alpha),('busqueda_umbrales_validacion',all_thresholds),('prevalencia_pretest',all_pop),('eda_mensual_entrenamiento',all_month)]:
        save_csv(pd.DataFrame(rows),out/f'{name}.csv')
    save_csv(pd.concat(all_eps,ignore_index=True),out/'episodios_pretest.csv')
    write_json(out/'timing_prepare.json',{'seconds':time.perf_counter()-begin})
    print('FREEZE ESCRITO. La fase prepare termina sin evaluar la prueba.',flush=True)


def bootstrap_test(frame, probs, decision, thermal, beta, n_boot=1000):
    """Remuestreo por calendario antes de la mascara, pareado entre metodos."""
    rng = np.random.default_rng(SEED)
    years = sorted(frame.year.unique())
    assert len(years)==5 and len(frame)==900
    y = frame.y.to_numpy(); valid=frame.valido.to_numpy()
    allp = {n:np.asarray(probs[n],float) for n in MODELS}
    thresholds = decision['thresholds']; principal = decision['principal']
    rows, deltas = [], []
    draws = np.empty((n_boot,5,6),dtype=np.int16)
    # Inicios0..150 inclusive: ningun bloque cruza septiembre o cambia de ano.
    for rep in range(n_boot):
        picks=[]
        for j,yr in enumerate(years):
            locations = np.flatnonzero(frame.year.to_numpy()==yr)
            assert len(locations)==180
            starts=rng.integers(0,151,size=6);draws[rep,j]=starts
            picks.extend(locations[(starts[:,None]+np.arange(30)).ravel()].tolist())
        idx=np.asarray(picks,dtype=int);idx=idx[valid[idx]]
        scores={}
        for name in MODELS:
            p=allp[name][idx]
            scores[name]=score(y[idx],p,p>=thresholds[name],beta)
            rows.append({'replica':rep,'thermal':thermal,'beta':beta,'model':name,**{k:scores[name][k] for k in ['n','positivos','precision','recall','F0.5','F1','Fbeta','Brier']}})
        for comparator in MODELS:
            if comparator == principal:continue
            deltas.append({'replica':rep,'thermal':thermal,'beta':beta,'principal':principal,'comparador':comparator,'delta_F0.5':scores[principal]['F0.5']-scores[comparator]['F0.5'],'delta_F1':scores[principal]['F1']-scores[comparator]['F1'],'delta_Brier':scores[principal]['Brier']-scores[comparator]['Brier']})
        for comparator in ['logistica','arbol']:
            deltas.append({'replica':rep,'thermal':thermal,'beta':beta,'principal':'mezcla','comparador':comparator,'delta_F0.5':scores['mezcla']['F0.5']-scores[comparator]['F0.5'],'delta_F1':scores['mezcla']['F1']-scores[comparator]['F1'],'delta_Brier':scores['mezcla']['Brier']-scores[comparator]['Brier']})
    return pd.DataFrame(rows),pd.DataFrame(deltas).drop_duplicates(['replica','thermal','beta','principal','comparador']),draws


def intervals(table, groupcols, values):
    rows=[]
    for key,g in table.groupby(groupcols,dropna=False):
        key=key if isinstance(key,tuple) else (key,)
        for value in values:
            arr=g[value].to_numpy();valid=arr[np.isfinite(arr)]
            rows.append({**dict(zip(groupcols,key)),'metric':value,'lower_2.5':float(np.percentile(valid,2.5)) if len(valid) else np.nan,'upper_97.5':float(np.percentile(valid,97.5)) if len(valid) else np.nan,'replicas_estimables':len(valid),'replicas_totales':len(g),'fraction_not_estimable':1-len(valid)/len(g)})
    return pd.DataFrame(rows)


def test(out):
    begin=time.perf_counter()
    frozen=json.loads((out/'freeze.json').read_text(encoding='utf-8'))
    assert frozen['code_sha256']==sha(__file__),'El codigo cambio despues de congelar decisiones'
    state=joblib.load(out/'modelos_congelados.joblib')
    daily=pd.read_csv(out/'celda_diaria.csv',parse_dates=['fecha'],float_precision='round_trip').set_index('fecha')
    allmetrics,allannual,allpop,eps=[],[],[],[]
    boot_tables,delta_tables=[],[]
    for thermal in THERMALS:
        print(f'TEST thermal={thermal:g}; ninguna decision se reajusta',flush=True)
        key=str(int(thermal));f=frozen['decisions'][key];st=state[key]
        frame=make_examples(daily,thermal,2016,2020)
        valid=frame.valido.to_numpy();sub=frame.loc[frame.valido]
        probs={}
        for n,m in st['models'].items():
            probs[n]=np.full(len(frame),np.nan)
            probs[n][valid]=m.predict_proba(sub[FEATURES])[:,1]
        probs['frecuencia_mensual']=frame.month.map(st['monthly']).to_numpy(dtype=float)
        probs['persistencia']=frame.persistencia.to_numpy()
        probs['mezcla']=f['alpha']*probs['logistica']+(1-f['alpha'])*probs['arbol']
        if f['alpha'] in [0.,1.]:
            assert np.array_equal(probs['mezcla'][valid],probs['logistica' if f['alpha']==1 else 'arbol'][valid])
        predictions=frame[['objetivo_inicio','objetivo_fin','year','month','valido_historia','valido_objetivo','valido','y']].copy()
        for name in MODELS:predictions[f'p_{name}']=probs[name]
        for beta in [.5,1.]:
            dec=f['decisions_by_beta'][str(beta)]
            for name in MODELS:
                tau=dec['thresholds'][name]
                prediction=probs[name]>=tau
                predictions[f'aviso_beta{beta}_{name}']=pd.Series(prediction.astype(float),index=frame.index).where(frame.valido)
                allmetrics.append({'thermal':thermal,'beta':beta,'model':name,'principal':name==dec['principal'],'tau':tau,**score(frame.y[valid],probs[name][valid],prediction[valid],beta)})
                for year in range(2016,2021):
                    mask=valid&(frame.year.to_numpy()==year)
                    allannual.append({'thermal':thermal,'beta':beta,'model':name,'year':year,'principal':name==dec['principal'],**score(frame.y[mask],probs[name][mask],prediction[mask],beta)})
            b,d,draws=bootstrap_test(frame,probs,dec,thermal,beta)
            boot_tables.append(b);delta_tables.append(d)
            if thermal==-3 and beta==.5:np.save(out/'bootstrap_inicios_calendario.npy',draws)
        save_csv(predictions.reset_index(),out/f'predicciones_prueba_m{abs(int(thermal))}.csv')
        allpop.append({'thermal':thermal,'split':'prueba','candidate_n':len(frame),'valid_n':int(valid.sum()),'invalid_n':int((~valid).sum()),'positive_n':int(frame.y.sum()),'prevalence':float(frame.y.mean())})
        eps.append(episodes(daily,thermal,2016,2020))
    metrics=pd.DataFrame(allmetrics);annual=pd.DataFrame(allannual)
    boot=pd.concat(boot_tables,ignore_index=True);deltas=pd.concat(delta_tables,ignore_index=True)
    save_csv(metrics,out/'metricas_prueba.csv');save_csv(annual,out/'metricas_prueba_anuales.csv')
    save_csv(pd.DataFrame(allpop),out/'prevalencia_prueba.csv')
    save_csv(pd.concat(eps,ignore_index=True),out/'episodios_prueba.csv')
    save_csv(boot,out/'bootstrap_metricas_1000.csv');save_csv(deltas,out/'bootstrap_diferencias_1000.csv')
    save_csv(intervals(boot,['thermal','beta','model'],['precision','recall','F0.5','F1','Brier']),out/'bootstrap_intervalos_metricas.csv')
    save_csv(intervals(deltas,['thermal','beta','principal','comparador'],['delta_F0.5','delta_F1','delta_Brier']),out/'bootstrap_intervalos_diferencias.csv')
    # Hipotesis fijadas: comparar puntos estrictamente, sin llamarlos significativos.
    conclusions={}
    for thermal in THERMALS:
        key=str(int(thermal));sel=frozen['decisions'][key]['decisions_by_beta']['0.5']['principal']
        g=metrics.loc[(metrics.thermal==thermal)&(metrics.beta==.5)].set_index('model')
        diffs={ref:float(g.loc[sel,'F0.5']-g.loc[ref,'F0.5']) for ref in ['persistencia','frecuencia_mensual']}
        md={ref:float(g.loc['mezcla','Brier']-g.loc[ref,'Brier']) for ref in ['logistica','arbol']}
        conclusions[key]={'principal':sel,'alpha':frozen['decisions'][key]['alpha'],'delta_F0.5_vs_referencias':diffs,'hipotesis_principal_apoyada_puntualmente':all(v>0 for v in diffs.values()),'delta_Brier_mezcla_vs_componentes':md,'hipotesis_complementaria_apoyada_puntualmente':all(v<0 for v in md.values()),'scope':'Puntos historicos; intervalos bootstrap exploratorios, no prueba de significancia ni validacion productiva.'}
    write_json(out/'conclusiones_numericas.json',conclusions)
    write_json(out/'timing_test.json',{'seconds':time.perf_counter()-begin,'freeze_sha256':sha(out/'freeze.json'),'bootstrap_replicates':1000})
    print(metrics.loc[(metrics.thermal==-3)&(metrics.beta==.5)].to_string(index=False),flush=True)
    print(json.dumps(clean_json(conclusions['-3']),ensure_ascii=False,indent=2),flush=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('phase',choices=['prepare','test','all'])
    parser.add_argument('--data-dir',type=Path,default=Path('data'))
    parser.add_argument('--out-dir',type=Path,default=Path('resultados'))
    args=parser.parse_args()
    if args.phase in ['prepare','all']:prepare(args.data_dir,args.out_dir)
    if args.phase in ['test','all']:test(args.out_dir)


if __name__=='__main__':main()
