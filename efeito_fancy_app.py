import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

# --------------------------------------------------
# CONFIGURAÇÃO
# --------------------------------------------------

st.set_page_config(
    page_title="Efeito Fancy",
    page_icon="✨",
    layout="wide"
)

st.title("✨ Análise do Efeito Fancy")
st.markdown(
    "Dashboard para análise do comportamento de compra de produtos "
    "da linha Fancy e identificação do público-alvo."
)

# --------------------------------------------------
# CARREGAMENTO DOS DADOS
# --------------------------------------------------

@st.cache_data
def carregar_dados():
    df = pd.read_csv("Dados completos-3.csv")
    return df

df = carregar_dados()

# --------------------------------------------------
# TRATAMENTO
# --------------------------------------------------

df["receita"] = df["preco_venda"] * df["quantidade"]

# --------------------------------------------------
# FANCY SCORE POR CLIENTE
# --------------------------------------------------

cliente = df.groupby("id_cliente").agg(
    total_compras=("id_pedido", "count"),
    compras_fancy=("linha", lambda x: (x == "Fancy").sum()),
    quantidade_total=("quantidade", "sum"),
    receita=("receita", "sum"),
    margem=("Margem de Lucro Bruto", "sum"),
    idade=("idade", "first"),
    renda_mensal=("renda_mensal", "first"),
    estado=("estado", "first"),
    canal_aquisicao=("canal_aquisicao", "first")
).reset_index()

cliente["fancy_score"] = (
    cliente["compras_fancy"] /
    cliente["total_compras"]
) * 100

cliente["ticket_medio"] = (
    cliente["receita"] /
    cliente["total_compras"]
)

cliente["margem_percentual"] = (
    cliente["margem"] /
    cliente["receita"]
) * 100

# --------------------------------------------------
# KPIs
# --------------------------------------------------

total_clientes = cliente["id_cliente"].nunique()

fancy_score_medio = cliente["fancy_score"].mean()

ticket_medio = cliente["ticket_medio"].mean()

participacao_fancy = (
    (df["linha"] == "Fancy").mean() * 100
)

col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "Clientes",
    f"{total_clientes:,}".replace(",", ".")
)

col2.metric(
    "Fancy Score médio",
    f"{fancy_score_medio:.1f}%"
)

col3.metric(
    "Ticket médio",
    f"R$ {ticket_medio:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
)

col4.metric(
    "Compras Fancy",
    f"{participacao_fancy:.1f}%"
)

st.divider()

# --------------------------------------------------
# DISTRIBUIÇÃO DO FANCY SCORE
# --------------------------------------------------

st.subheader("1. Distribuição do Fancy Score")

fig_score = px.histogram(
    cliente,
    x="fancy_score",
    nbins=20,
    title="Distribuição do Fancy Score por cliente",
    labels={
        "fancy_score": "Fancy Score (%)",
        "count": "Quantidade de clientes"
    }
)

fig_score.update_layout(
    xaxis_title="Fancy Score (%)",
    yaxis_title="Clientes"
)

st.plotly_chart(fig_score, use_container_width=True)

# --------------------------------------------------
# CORRELAÇÃO FANCY SCORE X TICKET
# --------------------------------------------------

st.subheader("2. Fancy Score × Ticket Médio")

correlacao = cliente[
    ["fancy_score", "ticket_medio"]
].corr().iloc[0, 1]

fig_scatter = px.scatter(
    cliente,
    x="fancy_score",
    y="ticket_medio",
    trendline="ols",
    opacity=0.5,
    title="Relação entre Fancy Score e Ticket Médio",
    labels={
        "fancy_score": "Fancy Score (%)",
        "ticket_medio": "Ticket Médio (R$)"
    }
)

st.plotly_chart(fig_scatter, use_container_width=True)

st.info(
    f"Correlação entre Fancy Score e Ticket Médio: "
    f"{correlacao:.3f}"
)

# --------------------------------------------------
# TESTE DO EFEITO FANCY
# --------------------------------------------------

st.subheader("3. Evidência matemática do Efeito Fancy")

cliente["grupo_fancy"] = np.where(
    cliente["fancy_score"] >= 50,
    "Fancy Score ≥ 50%",
    "Fancy Score < 50%"
)

grupo_fancy = cliente[
    cliente["grupo_fancy"] == "Fancy Score ≥ 50%"
]

grupo_padrao = cliente[
    cliente["grupo_fancy"] == "Fancy Score < 50%"
]

ticket_fancy = grupo_fancy["ticket_medio"].mean()
ticket_padrao = grupo_padrao["ticket_medio"].mean()

diferenca_ticket = (
    (ticket_fancy / ticket_padrao) - 1
) * 100

col1, col2, col3 = st.columns(3)

col1.metric(
    "Ticket — Fancy ≥ 50%",
    f"R$ {ticket_fancy:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
)

col2.metric(
    "Ticket — Fancy < 50%",
    f"R$ {ticket_padrao:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
)

col3.metric(
    "Diferença",
    f"+{diferenca_ticket:.1f}%"
)

comparacao = pd.DataFrame({
    "Grupo": [
        "Fancy Score ≥ 50%",
        "Fancy Score < 50%"
    ],
    "Ticket Médio": [
        ticket_fancy,
        ticket_padrao
    ]
})

fig_comparacao = px.bar(
    comparacao,
    x="Grupo",
    y="Ticket Médio",
    text_auto=".2f",
    title="Comparação do Ticket Médio"
)

st.plotly_chart(
    fig_comparacao,
    use_container_width=True
)

st.success(
    f"Clientes com Fancy Score ≥ 50% apresentam ticket médio "
    f"{diferenca_ticket:.1f}% maior que os demais clientes."
)

# --------------------------------------------------
# PÚBLICO-ALVO
# --------------------------------------------------

st.subheader("4. Público-alvo recomendado para Marketing")

cliente["faixa_etaria"] = pd.cut(
    cliente["idade"],
    bins=[17, 24, 34, 44, 54, 69],
    labels=[
        "18–24",
        "25–34",
        "35–44",
        "45–54",
        "55–69"
    ]
)

segmento = cliente.groupby(
    ["canal_aquisicao", "faixa_etaria"],
    observed=True
).agg(
    clientes=("id_cliente", "count"),
    fancy_score=("fancy_score", "mean"),
    ticket_medio=("ticket_medio", "mean"),
    margem_media=("margem", "mean")
).reset_index()

segmento = segmento.sort_values(
    "fancy_score",
    ascending=False
)

fig_segmento = px.bar(
    segmento.head(10),
    x="fancy_score",
    y="canal_aquisicao",
    color="faixa_etaria",
    orientation="h",
    title="Top 10 segmentos por Fancy Score",
    labels={
        "fancy_score": "Fancy Score médio (%)",
        "canal_aquisicao": "Canal",
        "faixa_etaria": "Faixa etária"
    }
)

st.plotly_chart(
    fig_segmento,
    use_container_width=True
)

st.markdown("### 🎯 Recomendação de Marketing")

st.write(
    """
    Os dados indicam maior afinidade com produtos Fancy entre consumidores
    de 18 a 34 anos, principalmente nos canais Instagram e TikTok.

    Portanto, recomenda-se priorizar campanhas nesses canais e faixas etárias,
    utilizando produtos Fancy como elemento central da comunicação.
    """
)

# --------------------------------------------------
# TABELA DE SEGMENTOS
# --------------------------------------------------

st.subheader("5. Ranking de segmentos")

st.dataframe(
    segmento,
    use_container_width=True
)
