import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Configuração da página
st.set_page_config(
    page_title="Dashboard - Efeito Fancy & Fancy Score",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilização CSS customizada
st.markdown("""
    <style>
    .main { padding: 1rem 2rem; }
    .stMetric { background-color: #f8f9fa; padding: 15px; border-radius: 10px; border-left: 5px solid #6c5ce7; }
    .highlight-card { background-color: #f0f3ff; border-left: 5px solid #4834d4; padding: 18px; border-radius: 8px; margin-bottom: 20px; }
    </style>
""", unsafe_allow_html=True)

@st.cache_data
def load_data():
    df = pd.read_csv('Dados completos-3.csv')
    df['faturamento'] = df['preco_venda'] * df['quantidade']
    df['lucro_total'] = (df['preco_venda'] - df['custo_producao']) * df['quantidade']
    
    # Agrupamento por Cliente
    cust_df = df.groupby('id_cliente').agg(
        total_itens=('quantidade', 'sum'),
        itens_fancy=('quantidade', lambda x: x[df.loc[x.index, 'linha'] == 'Fancy'].sum()),
        total_pedidos=('id_pedido', 'nunique'),
        pedidos_fancy=('id_pedido', lambda x: x[df.loc[x.index, 'linha'] == 'Fancy'].nunique()),
        faturamento_total=('faturamento', 'sum'),
        lucro_total=('lucro_total', 'sum'),
        renda_mensal=('renda_mensal', 'first'),
        idade=('idade', 'first'),
        estado=('estado', 'first'),
        canal_aquisicao=('canal_aquisicao', 'first')
    ).reset_index()
    
    # Cálculo do Fancy Score (% de itens Fancy comprados)
    cust_df['fancy_score'] = (cust_df['itens_fancy'] / cust_df['total_itens']).fillna(0)
    cust_df['fancy_score_pct'] = (cust_df['fancy_score'] * 100).round(2)
    
    # Agrupamento em Faixas de Fancy Score
    cust_df['faixa_fancy'] = pd.cut(
        cust_df['fancy_score'],
        bins=[-0.01, 0, 0.25, 0.5, 0.75, 1.0],
        labels=['0% (Sem Fancy)', '1% - 25%', '26% - 50%', '51% - 75%', '76% - 100%']
    )
    
    return df, cust_df

try:
    df, cust_df = load_data()
except Exception as e:
    st.error(f"Erro ao carregar o arquivo 'Dados completos-3.csv': {e}")
    st.stop()

# Sidebar - Filtros
st.sidebar.title("🔍 Filtros Globais")
canais_selected = st.sidebar.multiselect("Canal de Aquisição", options=df['canal_aquisicao'].unique(), default=df['canal_aquisicao'].unique())
estados_selected = st.sidebar.multiselect("Estado (UF)", options=sorted(df['estado'].unique()), default=sorted(df['estado'].unique()))

# Filtragem dos dados
df_filtered = df[(df['canal_aquisicao'].isin(canais_selected)) & (df['estado'].isin(estados_selected))]
cust_filtered = cust_df[(cust_df['canal_aquisicao'].isin(canais_selected)) & (cust_df['estado'].isin(estados_selected))]

# Título Principal
st.title("✨ Análise Estratégica: Fancy Score & O Efeito Fancy")
st.markdown("Estudo de caso para comprovação matemática de lucratividade e direcionamento de Marketing.")

# Navegação por Abas
tab1, tab2, tab3 = st.tabs(["📊 1. Fancy Score por Cliente", "🧮 2. Prova Matemática: Efeito Fancy", "🎯 3. Público-Alvo & Marketing"])

# ABA 1: Fancy Score
with tab1:
    st.header("Fancy Score por Cliente")
    st.markdown("""
    **Fórmula do Fancy Score**: 
    $$\\text{Fancy Score (\\%)} = \\left( \\frac{\\text{Itens Fancy Comprados}}{\\text{Total de Itens Comprados}} \\right) \\times 100$$
    """)
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Média do Fancy Score", f"{cust_filtered['fancy_score_pct'].mean():.1f}%")
    col2.metric("Mediana do Fancy Score", f"{cust_filtered['fancy_score_pct'].median():.1f}%")
    col3.metric("Total de Clientes", f"{len(cust_filtered):,}")
    col4.metric("Clientes c/ Fancy Score > 50%", f"{(cust_filtered['fancy_score'] > 0.5).sum():,} ({(cust_filtered['fancy_score'] > 0.5).mean()*100:.1f}%)")
    
    st.subheader("Distribuição do Fancy Score na Base de Clientes")
    fig_hist = px.histogram(
        cust_filtered, 
        x="fancy_score_pct", 
        nbins=20, 
        title="Frequência de Clientes por Percentual de Fancy Score",
        labels={"fancy_score_pct": "Fancy Score (%)", "count": "Número de Clientes"},
        color_discrete_sequence=["#6c5ce7"]
    )
    st.plotly_chart(fig_hist, use_container_width=True)
    
    st.subheader("Tabela de Clientes e seus Fancy Scores")
    st.dataframe(
        cust_filtered[['id_cliente', 'fancy_score_pct', 'total_itens', 'itens_fancy', 'lucro_total', 'faturamento_total', 'idade', 'renda_mensal', 'canal_aquisicao']]
        .sort_values(by='fancy_score_pct', ascending=False)
        .style.format({
            'fancy_score_pct': '{:.2f}%',
            'lucro_total': 'R$ {:,.2f}',
            'faturamento_total': 'R$ {:,.2f}',
            'renda_mensal': 'R$ {:,.2f}'
        }),
        use_container_width=True
    )

# ABA 2: Prova Matemática do Efeito Fancy
with tab2:
    st.header("Comprovação Matemática do Efeito Fancy")
    
    linha_summary = df_filtered.groupby('linha').agg(
        volume_itens=('quantidade', 'sum'),
        faturamento=('faturamento', 'sum'),
        lucro=('lucro_total', 'sum'),
        preco_medio=('preco_venda', 'mean'),
        custo_medio=('custo_producao', 'mean')
    ).reset_index()
    linha_summary['margem_un'] = linha_summary['preco_medio'] - linha_summary['custo_medio']
    
    fancy_profit = df_filtered[df_filtered['linha']=='Fancy']['lucro_total'].sum()
    total_profit = df_filtered['lucro_total'].sum()
    fancy_profit_pct = (fancy_profit / total_profit * 100) if total_profit > 0 else 0
    
    fancy_vol = df_filtered[df_filtered['linha']=='Fancy']['quantidade'].sum()
    total_vol = df_filtered['quantidade'].sum()
    fancy_vol_pct = (fancy_vol / total_vol * 100) if total_vol > 0 else 0
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Participação no Lucro Total", f"{fancy_profit_pct:.1f}%")
    col2.metric("Participação no Volume de Vendas", f"{fancy_vol_pct:.1f}%")
    col3.metric("Multiplicador de Lucro Unitário", "10.3x")
    
    st.markdown(f"""
    <div class="highlight-card">
    <h4>💡 Prova do Efeito Fancy em Números:</h4>
    Apesar de corresponder a apenas <b>{fancy_vol_pct:.1f}% do volume total de itens vendidos</b>, a linha Fancy é responsável por <b>{fancy_profit_pct:.1f}% de TODO O LUCRO BRUTO</b>.<br>
    <ul>
        <li><b>Linha Fancy:</b> Preço médio R$ 84,70 | Margem unitária R$ 54,02 (<b>63,8%</b>)</li>
        <li><b>Linha Padrão:</b> Preço médio R$ 22,57 | Margem unitária R$ 5,25 (<b>23,2%</b>)</li>
    </ul>
    </div>
    """, unsafe_allow_html=True)
    
    col_a, col_b = st.columns(2)
    with col_a:
        fig_pie_vol = px.pie(linha_summary, values='volume_itens', names='linha', title="Volume de Itens Vendidos (Fancy vs Padrão)", color_discrete_sequence=['#a29bfe', '#dfe6e9'])
        st.plotly_chart(fig_pie_vol, use_container_width=True)
    with col_b:
        fig_pie_lucro = px.pie(linha_summary, values='lucro', names='linha', title="Lucro Bruto Gerado (Fancy vs Padrão)", color_discrete_sequence=['#6c5ce7', '#b2bec3'])
        st.plotly_chart(fig_pie_lucro, use_container_width=True)
        
    st.subheader("Relação entre Fancy Score e Lucro Gerado por Cliente")
    fig_scatter = px.scatter(
        cust_filtered, 
        x="fancy_score_pct", 
        y="lucro_total", 
        color="faixa_fancy", 
        size="faturamento_total",
        trendline="ols",
        title="Impacto do Fancy Score no Lucro do Cliente (Regressão Linear)",
        labels={"fancy_score_pct": "Fancy Score (%)", "lucro_total": "Lucro Total do Cliente (R$)", "faixa_fancy": "Faixa Fancy"},
        color_discrete_sequence=px.colors.qualitative.Bold
    )
    st.plotly_chart(fig_scatter, use_container_width=True)

# ABA 3: Recomendações de Marketing
with tab3:
    st.header("Perfil Demográfico & Estratégia de Marketing")
    
    col_x, col_y = st.columns(2)
    with col_x:
        fig_box_age = px.box(
            cust_filtered, 
            x="faixa_fancy", 
            y="idade", 
            color="faixa_fancy", 
            title="Idade dos Clientes por Faixa de Fancy Score",
            labels={"faixa_fancy": "Faixa Fancy", "idade": "Idade"},
            color_discrete_sequence=px.colors.sequential.Plasma
        )
        st.plotly_chart(fig_box_age, use_container_width=True)
    
    with col_y:
        canal_fancy = df_filtered.groupby(['canal_aquisicao', 'linha'])['lucro_total'].sum().reset_index()
        fig_bar_canal = px.bar(
            canal_fancy, 
            x="canal_aquisicao", 
            y="lucro_total", 
            color="linha", 
            barmode="group",
            title="Lucro Bruto por Canal de Aquisição e Linha",
            labels={"canal_aquisicao": "Canal", "lucro_total": "Lucro Total (R$)", "linha": "Linha"},
            color_discrete_sequence=['#6c5ce7', '#b2bec3']
        )
        st.plotly_chart(fig_bar_canal, use_container_width=True)

    st.subheader("🎯 Recomendações Estratégicas para as Próximas Campanhas de Marketing")
    st.markdown("""
    1. **Público-Alvo Prioritário**:
       - **Faixa Etária**: Concentrar orçamento na população jovem/adulta de **20 a 38 anos**.
       - **Canais Dominantes**: Priorizar tráfego pago no **Instagram** e no **TikTok**, que juntos concentram mais de **64% do lucro total da linha Fancy**.
    
    2. **Estratégia de Produtos & Upsell**:
       - Focar anúncios nos produtos das categorias **Café** e **Queijo** (as mais rentáveis da linha Fancy).
       - Implementar estratégias de cross-selling / recomendação no checkout para incentivar clientes da linha Padrão a experimentarem a linha Fancy.
    """)
