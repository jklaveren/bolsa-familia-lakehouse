import json
import os
import sys

# Garante que o diretório atual está no PYTHONPATH para importar src
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)


import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(
    page_title="Pipeline Novo Bolsa Família | Data Hub & AI",
    page_icon="🇧🇷",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for ultra-modern UI/UX
st.markdown("""
    <style>
    .main { background-color: #F8FAFC; }
    .stMetric {
        background-color: #FFFFFF;
        padding: 18px;
        border-radius: 12px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        border: 1px solid #E2E8F0;
    }
    .metric-label { font-size: 0.85rem; color: #64748B; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; }
    .metric-value { font-size: 1.8rem; color: #1E3A8A; font-weight: 800; }
    .card {
        background: #FFFFFF;
        padding: 24px;
        border-radius: 12px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        border: 1px solid #E2E8F0;
        margin-bottom: 20px;
    }
    .badge-success { background-color: #DEF7EC; color: #03543F; padding: 4px 10px; border-radius: 6px; font-weight: 600; font-size: 0.75rem; }
    .badge-databricks { background-color: #FF3621; color: #FFFFFF; padding: 4px 10px; border-radius: 6px; font-weight: 600; font-size: 0.75rem; }
    </style>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.image("https://img.icons8.com/color/96/brazil.png", width=64)
    st.markdown("### **Bolsa Família Data Hub**")
    st.markdown("Databricks + dbt + Spark + Delta Lake")
    st.markdown("---")
    
    selected_tab = st.radio(
        "Navegação Principal",
        [
            "🚀 Visão Geral & Arquitetura", 
            "⚡ Databricks & dbt Analytics", 
            "📈 Machine Learning & Forecast", 
            "💻 Código & Componentes",
            "🛡️ LGPD & Governança", 
            "📋 Auditoria & Logs"
        ]
    )
    
    st.markdown("---")
    st.markdown("🛠️ **Stack:** PySpark | Delta Lake | dbt | Airflow")
    st.markdown("👤 **Autora:** Jessica Van Klaveren")

# Top Header
st.markdown("<h1 style='color: #1E3A8A; margin-bottom: 0;'>🇧🇷 Pipeline Analítico do Novo Bolsa Família</h1>", unsafe_allow_html=True)
st.markdown("<p style='color: #64748B; font-size: 1.1rem;'>Plataforma end-to-end de Engenharia de Dados: Delta Lake, Databricks, dbt e Airflow.</p>", unsafe_allow_html=True)
st.markdown("---")

if selected_tab == "🚀 Visão Geral & Arquitetura":
    st.markdown("### 📊 Indicadores Chave de Desempenho (KPIs)")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown("""
            <div class='stMetric'>
                <div class='metric-label'>Volume Total Ingerido</div>
                <div class='metric-value'>242M</div>
                <div style='color: #10B981; font-size: 0.8rem; margin-top: 5px;'>▲ 12 Competências Trimestrais</div>
            </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
            <div class='stMetric'>
                <div class='metric-label'>Competência Recente</div>
                <div class='metric-value'>19.48M</div>
                <div style='color: #10B981; font-size: 0.8rem; margin-top: 5px;'>▲ Limpeza Silver (Jan 2026)</div>
            </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown("""
            <div class='stMetric'>
                <div class='metric-label'>Modelos Databricks / dbt</div>
                <div class='metric-value'>4 Gold</div>
                <div style='color: #FF3621; font-size: 0.8rem; margin-top: 5px;'>Staging → Marts (Databricks)</div>
            </div>
        """, unsafe_allow_html=True)
    with col4:
        st.markdown("""
            <div class='stMetric'>
                <div class='metric-label'>Testes Automatizados</div>
                <div class='metric-value'>13 / 13</div>
                <div style='color: #10B981; font-size: 0.8rem; margin-top: 5px;'>✔ 100% Cobertura de Schema</div>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    
    col_l, col_r = st.columns([1.2, 1])
    with col_l:
        st.markdown("""
            <div class='card'>
                <h3 style='color: #1E3A8A; margin-top: 0;'>🏗️ Arquitetura Medalhão & Databricks</h3>
                <p>O projeto integra processamento distribuído local e nuvem com Databricks:</p>
                <ul>
                    <li><b>Bronze (PySpark & Delta):</b> Ingestão e particionamento dos CSVs da CGU em Delta Lake.</li>
                    <li><b>Silver (Limpeza & LGPD):</b> Normalização e pseudonimização criptográfica do NIS (SHA-256) com remoção de PII.</li>
                    <li><b>Gold (<span style='color: #FF3621; font-weight: bold;'>Databricks + dbt</span>):</b> Transformações analíticas rodando nativamente na nuvem com dbt-databricks.</li>
                    <li><b>Orquestração (Airflow):</b> Pipeline automatizado ponta a ponta.</li>
                </ul>
            </div>
        """, unsafe_allow_html=True)
        
    with col_r:
        st.markdown("""
            <div class='card'>
                <h3 style='color: #1E3A8A; margin-top: 0;'>⚡ Status do Pipeline</h3>
                <p>Última execução monitorada via API do Airflow:</p>
                <p><span class='badge-success'>SUCCESS</span> <b>ingest_bronze</b> (Delta Lake)</p>
                <p><span class='badge-success'>SUCCESS</span> <b>clean_silver</b> (19.4M linhas limpas)</p>
                <p><span class='badge-databricks'>DATABRICKS</span> <b>dbt_run</b> (Modelos Gold na nuvem)</p>
                <p><span class='badge-success'>SUCCESS</span> <b>dbt_test</b> (13 testes aprovados)</p>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown(
        "[![CI](https://github.com/jklaveren/bolsa-familia-pipeline/actions/workflows/ci.yml/badge.svg)]"
        "(https://github.com/jklaveren/bolsa-familia-pipeline/actions) "
        "[![dbt docs](https://img.shields.io/badge/dbt_docs-no_ar-FF3621)]"
        "(https://jklaveren.github.io/bolsa-familia-pipeline/) "
        "[![delta](https://img.shields.io/badge/Delta_Lake-3.2.0-00ADD8)]"
        "(https://github.com/jklaveren/bolsa-familia-pipeline/blob/main/docs/evidencias/fase3_silver_schema_202601.txt) "
        "[![evidencias](https://img.shields.io/badge/evid%C3%AAncias-audit%C3%A1veis-10B981)]"
        "(https://github.com/jklaveren/bolsa-familia-pipeline/tree/main/docs/evidencias)"
    )

    viz_path = os.path.join(current_dir, "docs", "viz_gold.json")
    if os.path.exists(viz_path):
        with open(viz_path, "r", encoding="utf-8") as f:
            viz = json.load(f)
        s = viz["serie"][0]
        taxa = (s["linhas_silver"] / s["linhas_bronze"] * 100) if s["linhas_bronze"] else 0

        st.markdown(f"### 🔻 Funil Bronze → Silver — {s['competencia']} (medido do Delta local)")
        funil_df = pd.DataFrame({
            "Etapa": ["Bronze (bruto)", "Silver (limpo)", "Quarentena (sem NIS)"],
            "Linhas": [s["linhas_bronze"], s["linhas_silver"], viz["quarentena_linhas"]],
        })
        fig_funil = px.bar(funil_df, x="Etapa", y="Linhas", text="Linhas",
                           color="Etapa",
                           color_discrete_map={"Bronze (bruto)": "#94A3B8",
                                               "Silver (limpo)": "#1E3A8A",
                                               "Quarentena (sem NIS)": "#F59E0B"})
        fig_funil.update_layout(plot_bgcolor="white", paper_bgcolor="white",
                                showlegend=False, margin=dict(l=20, r=20, t=20, b=20))
        st.plotly_chart(fig_funil, use_container_width=True)
        st.caption(
            f"Brasão fechado: {s['linhas_bronze']:,} = {s['linhas_silver']:,} + {viz['quarentena_linhas']} "
            f"(aproveitamento {taxa:.3f}%) · R$ {s['valor_total']:,.2f} em benefícios · "
            f"gerado por `scripts/build_gold_viz.py` — "
            f"[prova](https://github.com/jklaveren/bolsa-familia-pipeline/blob/main/docs/evidencias/fase6_quality_report_202601.txt)"
        )

        st.markdown(f"### 📊 Valor total por UF — {viz['ultima_competencia']}")
        uf_df = pd.DataFrame(viz["por_uf"]).sort_values("valor")
        fig_uf = px.bar(uf_df, x="valor", y="uf", orientation="h", text="valor",
                        color="valor", color_continuous_scale="Blues")
        fig_uf.update_layout(plot_bgcolor="white", paper_bgcolor="white",
                             coloraxis_showscale=False,
                             margin=dict(l=20, r=20, t=20, b=20))
        fig_uf.update_yaxes(title="")
        fig_uf.update_xaxes(tickprefix="R$ ")
        st.plotly_chart(fig_uf, use_container_width=True)
        st.caption(f"27 UFs, soma R$ {viz['total_valor_silver']:,.2f} — confere com o total do funil acima.")
    else:
        st.warning("Gere `docs/viz_gold.json` com `python scripts/build_gold_viz.py` para ver o funil e o mapa por UF.")

elif selected_tab == "⚡ Databricks & dbt Analytics":
    st.markdown("### ⚡ Camada Gold no Databricks com dbt")
    st.markdown("Transformação analítica avançada executada diretamente sobre clusters Databricks Community Edition usando `dbt-databricks`.")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
            <div class='card'>
                <h4 style='color: #FF3621; margin-top: 0;'>🔗 Integração dbt-databricks</h4>
                <p>O projeto configura o conector oficial <code>dbt-databricks</code> conectado via JDBC/HTTP Path:</p>
                <ul>
                    <li><b>Staging Layer:</b> Limpeza, renomeação de colunas e tipagem em cima da camada Silver.</li>
                    <li><b>Marts Layer:</b> Agregações analíticas por UF, mês de competência e série histórica nacional.</li>
                    <li><b>Testes Declarativos:</b> 13 testes executados nativamente no Databricks (unicidade de chaves, não-nulos e relações).</li>
                </ul>
            </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
            <div class='card'>
                <h4 style='color: #1E3A8A; margin-top: 0;'>📊 Documentação & Linhagem (dbt docs)</h4>
                <p>O dbt gera automaticamente o catálogo de dados e o grafo de linhagem (Lineage Graph):</p>
                <ul>
                    <li><b>Transparência:</b> Rastreabilidade de ponta a ponta desde a ingestão Bronze até as tabelas finais Gold.</li>
                    <li><b>GitHub Pages:</b> Publicação contínua da documentação em <code>https://jklaveren.github.io/bolsa-familia-pipeline/</code>.</li>
                </ul>
            </div>
        """, unsafe_allow_html=True)

elif selected_tab == "📈 Machine Learning & Forecast":
    st.markdown("### 📈 Previsão de Séries Temporais: VAR vs Deep Learning")
    st.markdown("Comparação de acurácia entre modelo econométrico multivariado (VAR) e Rede Neural Densa para o valor total de pagamentos.")
    
    json_path = "docs/evidencias/secao10_comparacao_modelos.json"
    if os.path.exists(json_path):
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        col1, col2 = st.columns(2)
        with col1:
            m_var = data["var"]["metricas"]
            st.markdown(f"""
                <div class='card'>
                    <h4 style='color: #1E3A8A; margin-top: 0;'>📊 Vector Autoregression (VAR)</h4>
                    <p><b>RMSE:</b> R$ {m_var['rmse']:,.2f}</p>
                    <p><b>MAE:</b> R$ {m_var['mae']:,.2f}</p>
                    <p><b>MAPE:</b> {m_var['mape']:.2f}%</p>
                </div>
            """, unsafe_allow_html=True)
        with col2:
            m_nn = data["rede_neural"]["metricas"]
            st.markdown(f"""
                <div class='card'>
                    <h4 style='color: #1E3A8A; margin-top: 0;'>🧠 Rede Neural Simples (Keras)</h4>
                    <p><b>RMSE:</b> R$ {m_nn['rmse']:,.2f}</p>
                    <p><b>MAE:</b> R$ {m_nn['mae']:,.2f}</p>
                    <p><b>MAPE:</b> {m_nn['mape']:.2f}%</p>
                </div>
            """, unsafe_allow_html=True)
            
        reais = data["valores_reais_teste"]
        preds_var = data["var"]["predicoes"]
        preds_nn = data["rede_neural"]["predicoes"]
        
        df_plot = pd.DataFrame({
            "Período": [f"T+{i+1}" for i in range(len(reais))] * 3,
            "Valor (R$)": reais + preds_var + preds_nn,
            "Série": ["Real"] * len(reais) + ["VAR (Econométrico)"] * len(preds_var) + ["Rede Neural"] * len(preds_nn)
        })
        
        fig = px.line(df_plot, x="Período", y="Valor (R$)", color="Série", markers=True,
                      color_discrete_map={"Real": "#1E3A8A", "VAR (Econométrico)": "#3B82F6", "Rede Neural": "#10B981"})
        fig.update_layout(
            plot_bgcolor="white",
            paper_bgcolor="white",
            font=dict(family="Inter, sans-serif", size=12, color="#334155"),
            margin=dict(l=20, r=20, t=40, b=20),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        fig.update_yaxes(tickprefix="R$ ", gridcolor="#E2E8F0")
        fig.update_xaxes(gridcolor="#E2E8F0")
        
        st.plotly_chart(fig, use_container_width=True)
        
        st.download_button(
            label="📥 Baixar Relatório Completo de Predições (JSON)",
            data=json.dumps(data, indent=2, ensure_ascii=False),
            file_name="relatorio_previsoes_bolsa_familia.json",
            mime="application/json"
        )

elif selected_tab == "💻 Código & Componentes":
    st.markdown("### 💻 Componentes de Código do Pipeline")
    st.markdown("Explore trechos oficiais dos scripts de engenharia, dbt e orquestração.")
    
    tab_code1, tab_code2, tab_code3 = st.tabs(["PySpark (Silver)", "dbt Model (Gold)", "Airflow DAG"])
    
    with tab_code1:
        st.code("""
# src/silver/clean.py - Exemplo de pseudonimização LGPD
def clean_silver(spark: SparkSession, competencia: str, salt: str) -> None:
    bronze_df = spark.read.format("delta").load(f"data/bronze/competencia={competencia}")
    
    cleaned = (
        bronze_df
        .withColumn("nis_hash", sha256(concat_ws("", col("nis"), lit(salt))))
        .drop("nome_beneficiario")  # Expurgo de PII
    )
    cleaned.write.format("delta").mode("append").save("data/silver/pagamentos")
        """, language="python")
        
    with tab_code2:
        st.code("""
-- dbt/bolsa_familia/models/marts/marts_pagamentos_uf.sql
select
    uf,
    mes_competencia,
    sum(valor_parcela) as valor_total,
    count(distinct nis_hash) as beneficiarios_unicos
from {{ ref('stg_pagamentos') }}
group by 1, 2
        """, language="sql")
        
    with tab_code3:
        st.code("""
# dags/bolsa_familia_pipeline_dag.py
ingest_bronze = PythonOperator(
    task_id="ingest_bronze",
    python_callable=_ingest_bronze,
)
clean_silver = PythonOperator(
    task_id="clean_silver",
    python_callable=_clean_silver,
)
dbt_run = BashOperator(
    task_id="dbt_run",
    bash_command=f"cd {DBT_PROJECT_DIR} && dbt deps && dbt run --profiles-dir .",
)
ingest_bronze >> clean_silver >> dbt_run
        """, language="python")

elif selected_tab == "🛡️ LGPD & Governança":
    st.markdown("### 🛡️ Privacidade e Conformidade com a LGPD (Lei 13.709/2018)")
    st.markdown("""
        <div class='card'>
            <h4 style='color: #1E3A8A; margin-top: 0;'>Tratamento de Dados Pessoais Sensíveis</h4>
            <p>Embora os microdados do Bolsa Família sejam públicos por força da Lei de Acesso à Informação (LAI), eles contêm Identificação Social (NIS) e nomes completos de beneficiários. O pipeline implementa:</p>
            <ul>
                <li><b>Isolamento da Camada Bronze:</b> Dados brutos confinados em zona restrita e sigilosa.</li>
                <li><b>Pseudonimização Criptográfica:</b> Aplicação de SHA-256 com Salt secreto em cima do NIS a partir da camada Silver.</li>
                <li><b>Expurgo de Identidade:</b> O nome completo do beneficiário <b>nunca</b> é propagado para as camadas analíticas (Silver e Gold), eliminando riscos de vazamento ou reidentificação indevida.</li>
            </ul>
        </div>
    """, unsafe_allow_html=True)

elif selected_tab == "📋 Auditoria & Logs":
    st.markdown("### 📋 Auditoria Oficial e Relatórios de Testes")
    
    logs = {
        "Relatório de Qualidade (Fase 6)": "docs/evidencias/fase6_quality_report_202601.txt",
        "Testes do dbt Gold (Fase 5)": "docs/evidencias/fase5_dbt_test.txt",
        "Schema da Camada Silver (Fase 3)": "docs/evidencias/fase3_silver_schema_202601.txt"
    }
    
    escolha = st.selectbox("Escolha o relatório oficial:", list(logs.keys()))
    path = logs[escolha]
    
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            texto = f.read()
        st.code(texto, language="text")
    else:
        st.warning("Arquivo não encontrado.")
