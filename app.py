from flask import Flask, render_template, request, jsonify
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.utils import PlotlyJSONEncoder
import json, os, uuid, traceback

app = Flask(__name__)
app.secret_key = 'autodash-2024'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

ALLOWED = {'csv', 'xlsx', 'xls'}

def allowed(name):
    return '.' in name and name.rsplit('.', 1)[1].lower() in ALLOWED

def load_file(path):
    ext = path.rsplit('.', 1)[1].lower()
    if ext == 'csv':
        for enc in ['utf-8', 'latin-1', 'cp1252']:
            try:
                return pd.read_csv(path, encoding=enc)
            except Exception:
                pass
        raise ValueError("Impossible de lire le CSV")
    return pd.read_excel(path)

CONTEXTS = {
    'ventes': {
        'keywords': ['vente','ventes','sale','sales','revenue','ca','chiffre','commande','order',
                     'produit','product','client','prix','price','montant','amount','article'],
        'title':       'Dashboard Automatique: Aperçu des Ventes et Tendances',
        'icon_total':  '€',  'label_total': 'Total Ventes',
        'icon_avg':    '$',  'label_avg':   'Moyenne/Vente',
        'icon_count':  '🛒', 'label_count': 'Nb Commandes',
        'icon_cat':    '🏷', 'label_cat':   'Total Produits',
        'color1':'#1a73e8','color2':'#34a853','color3':'#fa7b17','color4':'#137333',
    },
    'sinistres': {
        'keywords': ['sinistre','sinistres','claim','claims','police','assurance','insurance',
                     'dommage','damage','incident','accident','remboursement'],
        'title':       'Dashboard Automatique: Aperçu des Sinistres',
        'icon_total':  '⚠',  'label_total': 'Total Sinistres',
        'icon_avg':    '💰', 'label_avg':   'Coût Moyen',
        'icon_count':  '📋', 'label_count': 'Nb Dossiers',
        'icon_cat':    '🏢', 'label_cat':   'Compagnies',
        'color1':'#d93025','color2':'#e37400','color3':'#1a73e8','color4':'#7b1fa2',
    },
    'rh': {
        'keywords': ['employe','employee','salaire','salary','departement','department',
                     'poste','position','recrutement','conge','effectif','staff','rh'],
        'title':       'Dashboard Automatique: Aperçu RH',
        'icon_total':  '👥', 'label_total': 'Total Employés',
        'icon_avg':    '💶', 'label_avg':   'Salaire Moyen',
        'icon_count':  '🏢', 'label_count': 'Départements',
        'icon_cat':    '📅', 'label_cat':   'Ancienneté Moy.',
        'color1':'#1a73e8','color2':'#0f9d58','color3':'#7b1fa2','color4':'#e37400',
    },
    'finance': {
        'keywords': ['budget','depense','expense','profit','perte','loss','investissement',
                     'actif','passif','bilan','tresorerie','cash'],
        'title':       'Dashboard Automatique: Aperçu Financier',
        'icon_total':  '💵', 'label_total': 'Total Budget',
        'icon_avg':    '📊', 'label_avg':   'Moyenne',
        'icon_count':  '📁', 'label_count': 'Nb Entrées',
        'icon_cat':    '📈', 'label_cat':   'Catégories',
        'color1':'#0f9d58','color2':'#1a73e8','color3':'#fa7b17','color4':'#d93025',
    },
    'logistique': {
        'keywords': ['livraison','delivery','stock','inventaire','inventory','entrepot',
                     'warehouse','expedition','shipment','fournisseur','transport','colis'],
        'title':       'Dashboard Automatique: Aperçu Logistique',
        'icon_total':  '📦', 'label_total': 'Total Stock',
        'icon_avg':    '🚚', 'label_avg':   'Délai Moyen',
        'icon_count':  '🏭', 'label_count': 'Entrepôts',
        'icon_cat':    '🔄', 'label_cat':   'Mouvements',
        'color1':'#fa7b17','color2':'#1a73e8','color3':'#0f9d58','color4':'#7b1fa2',
    },
}
GENERIC = {
    'title':       'Dashboard Automatique: Analyse des Données',
    'icon_total':  '📊', 'label_total': 'Total',
    'icon_avg':    '∅',  'label_avg':   'Moyenne',
    'icon_count':  '🔢', 'label_count': 'Entrées',
    'icon_cat':    '🗂', 'label_cat':   'Catégories',
    'color1':'#1a73e8','color2':'#0f9d58','color3':'#fa7b17','color4':'#7b1fa2',
}

def detect_ctx(df):
    cols = ' '.join(df.columns.str.lower())
    best, best_s = None, 0
    for ctx in CONTEXTS.values():
        s = sum(1 for kw in ctx['keywords'] if kw in cols)
        if s > best_s:
            best_s, best = s, ctx
    return best or GENERIC

def fmt(v):
    try: v = float(v)
    except: return str(v)
    if abs(v) >= 1e6: return f"{v/1e6:.1f}M"
    if abs(v) >= 1e3: return f"{v:,.0f}".replace(',', ' ')
    return f"{v:.2f}".rstrip('0').rstrip('.')

BASE_LAYOUT = dict(
    template='plotly_white', paper_bgcolor='white', plot_bgcolor='white',
    margin=dict(l=40, r=20, t=30, b=50), height=260,
    font=dict(family='Inter,sans-serif', size=11),
    xaxis=dict(gridcolor='#f0f0f0'), yaxis=dict(gridcolor='#f0f0f0'),
)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return jsonify({'error': 'Aucun fichier reçu'}), 400
    f = request.files['file']
    if not f or not f.filename:
        return jsonify({'error': 'Fichier vide'}), 400
    if not allowed(f.filename):
        return jsonify({'error': 'Format non supporté. Utilisez CSV, XLSX ou XLS.'}), 400

    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    path = os.path.join(app.config['UPLOAD_FOLDER'], f"{uuid.uuid4()}_{f.filename}")
    f.save(path)

    try:
        df = load_file(path)
    except Exception as e:
        os.remove(path)
        return jsonify({'error': f'Lecture impossible : {e}'}), 400

    try:
        ctx       = detect_ctx(df)
        num_cols  = df.select_dtypes(include='number').columns.tolist()
        cat_cols  = df.select_dtypes(include=['object','category']).columns.tolist()

        # KPIs
        if num_cols:
            kpi_total = fmt(df[num_cols[0]].sum())
            kpi_avg   = fmt(df[num_cols[0]].mean())
        else:
            kpi_total = str(len(df))
            kpi_avg   = '—'
        kpi_count   = f"{len(df):,}".replace(',', ' ')
        kpi_cat_cnt = len(df[cat_cols[0]].unique()) if cat_cols else len(num_cols)

        # Detect date col
        date_col = None
        for col in df.columns:
            if df[col].dtype == object:
                parsed = pd.to_datetime(df[col], errors='coerce')
                if parsed.notna().sum() > len(df) * 0.4:
                    df[col] = parsed
                    date_col = col
                    break

        charts = []
        PALETTE = [ctx['color1'],ctx['color2'],ctx['color3'],ctx['color4'],
                   '#9c27b0','#00bcd4','#ff5722']

        # Chart 1 – Line
        if date_col and num_cols:
            tmp = df[[date_col, num_cols[0]]].dropna().sort_values(date_col)
            tmp['_p'] = tmp[date_col].dt.to_period('M').astype(str)
            mon = tmp.groupby('_p')[num_cols[0]].sum().reset_index()
            fig = go.Figure(go.Scatter(
                x=mon['_p'], y=mon[num_cols[0]],
                mode='lines+markers',
                line=dict(color=ctx['color1'], width=2),
                marker=dict(size=5),
                fill='tozeroy', fillcolor=ctx['color1']+'22',
            ))
            lay = {**BASE_LAYOUT, 'xaxis': dict(gridcolor='#f0f0f0', tickangle=-30)}
            fig.update_layout(**lay)
            charts.append({'id':'chart-line',
                'title': f"Tendances {ctx['label_total']} Mensuelles",
                'subtitle':'Line Chart · Plotly',
                'data': json.dumps(fig, cls=PlotlyJSONEncoder)})
        elif num_cols:
            fig = px.line(df.head(100), y=num_cols[0], color_discrete_sequence=[ctx['color1']])
            fig.update_layout(**BASE_LAYOUT)
            charts.append({'id':'chart-line',
                'title': f"Évolution — {num_cols[0]}",
                'subtitle':'Line Chart · Plotly',
                'data': json.dumps(fig, cls=PlotlyJSONEncoder)})

        # Chart 2 – Pie
        if cat_cols and num_cols:
            grp = df.groupby(cat_cols[0])[num_cols[0]].sum().reset_index().nlargest(7, num_cols[0])
            fig2 = px.pie(grp, names=cat_cols[0], values=num_cols[0],
                          color_discrete_sequence=PALETTE, hole=0.05)
            fig2.update_traces(textposition='inside', textinfo='percent')
            fig2.update_layout(paper_bgcolor='white', margin=dict(l=10,r=10,t=30,b=10),
                height=260, font=dict(family='Inter,sans-serif',size=11),
                legend=dict(orientation='v', x=1.0, y=0.5, font=dict(size=10)))
            charts.append({'id':'chart-pie',
                'title': f"Répartition par {cat_cols[0]}",
                'subtitle':'Pie Chart · Plotly',
                'data': json.dumps(fig2, cls=PlotlyJSONEncoder)})

        # Chart 3 – Bar
        if cat_cols and num_cols:
            grp2 = df.groupby(cat_cols[0])[num_cols[0]].sum().reset_index().nlargest(5, num_cols[0])
            fig3 = go.Figure(go.Bar(
                x=grp2[cat_cols[0]], y=grp2[num_cols[0]],
                marker_color=ctx['color1'],
                text=grp2[num_cols[0]].apply(fmt),
                textposition='outside',
            ))
            lay3 = {**BASE_LAYOUT, 'xaxis': dict(gridcolor='#f0f0f0', tickangle=-15)}
            fig3.update_layout(**lay3)
            charts.append({'id':'chart-bar',
                'title': f"Top 5 {cat_cols[0]}",
                'subtitle':'Bar Chart · Plotly',
                'data': json.dumps(fig3, cls=PlotlyJSONEncoder)})

        table_html = df.tail(10).to_html(classes='data-table', index=False, border=0, na_rep='—')

        return jsonify({
            'success':  True,
            'context':  ctx,
            'kpi':      {'total':kpi_total,'avg':kpi_avg,'count':kpi_count,'cat_count':kpi_cat_cnt},
            'charts':   charts,
            'table':    table_html,
            'filename': f.filename,
        })

    except Exception as e:
        return jsonify({'error': str(e), 'trace': traceback.format_exc()}), 500
    finally:
        if os.path.exists(path):
            os.remove(path)

if __name__ == '__main__':
    os.makedirs('uploads', exist_ok=True)
    app.run(debug=True, port=5000)
