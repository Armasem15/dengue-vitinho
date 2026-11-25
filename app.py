import os
from datetime import date
import pandas as pd
import plotly.express as px
import streamlit as st
from dotenv import load_dotenv
from supabase import Client, create_client

# ==============================================================================
# 1. CONFIGURAÇÃO DA PÁGINA E ESTILOS CSS
# ==============================================================================
st.set_page_config(
    page_title="EcoAedes | Monitoramento Ambiental",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .hero-banner {
        background: linear-gradient(135deg, #064E3B 0%, #059669 60%, #0D9488 100%);
        padding: 1.5rem 2rem;
        border-radius: 14px;
        color: white;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 14px rgba(5, 150, 105, 0.2);
    }
    .hero-banner h1 {
        margin: 0;
        font-size: 1.85rem;
        font-weight: 700;
        color: #FFFFFF;
    }
    .hero-banner p {
        margin: 0.35rem 0 0 0;
        font-size: 1rem;
        color: #D1FAE5;
    }
    div[data-testid="stMetric"] {
        background-color: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-left: 5px solid #059669;
        padding: 1rem 1.2rem;
        border-radius: 10px;
        box-shadow: 0 2px 6px rgba(15, 23, 42, 0.04);
    }
    .info-card {
        background-color: #ECFDF5;
        border: 1px solid #A7F3D0;
        border-radius: 10px;
        padding: 0.9rem 1.2rem;
        color: #065F46;
        margin-bottom: 1.2rem;
    }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# 2. CONEXÃO COM O BANCO DE DADOS (SUPABASE)
# ==============================================================================
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    st.error("⚠️ Configure as variáveis SUPABASE_URL e SUPABASE_KEY no arquivo .env antes de iniciar.")
    st.stop()

@st.cache_resource
def init_supabase() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_supabase()

def carregar_locais():
    res = supabase.table("locais_coleta").select("*").order("id").execute()
    return pd.DataFrame(res.data)

def carregar_residuos():
    res = supabase.table("registros_residuos").select("*, locais_coleta(nome, bairro)").order("id", desc=True).execute()
    df = pd.DataFrame(res.data)
    if not df.empty and "locais_coleta" in df.columns:
        df["local_nome"] = df["locais_coleta"].apply(lambda x: x["nome"] if isinstance(x, dict) else "Local Removido")
        df["bairro"] = df["locais_coleta"].apply(lambda x: x["bairro"] if isinstance(x, dict) else "-")
        df = df.drop(columns=["locais_coleta"])
    return df

def carregar_reciclagem():
    res = supabase.table("controle_reciclagem").select("*").order("id", desc=True).execute()
    return pd.DataFrame(res.data)

df_locais = carregar_locais()
df_residuos = carregar_residuos()
df_reciclagem = carregar_reciclagem()

# ==============================================================================
# 3. MENU DE NAVEGAÇÃO NA BARRA LATERAL
# ==============================================================================
with st.sidebar:
    st.markdown("## 🌿 EcoAedes 2026")
    st.caption("Monitoramento Ambiental & Prevenção à Dengue")

    pagina_selecionada = st.radio(
        "Navegação do Sistema",
        [
            "📊 Painel de Indicadores",
            "📍 1. Locais de Coleta",
            "🗑️ 2. Registro de Resíduos",
            "♻️ 3. Controle de Reciclados"
        ],
        label_visibility="collapsed"
    )

    st.divider()
    st.markdown("#### 🦟 Risco de Criadouro")
    st.markdown("""
    * 🔴 **Pneus:** Crítico *(retém água e calor)*
    * 🟠 **Garrafas PET:** Alto *(acúmulo rápido)*
    * 🟡 **Vidro e Latas:** Médio *(bordas retêm água)*
    * 🟢 **Entulho/Plástico:** Variável
    """)
    st.divider()
    st.success("🟢 Conectado ao Supabase")

# ==============================================================================
# 4. CABEÇALHO FIXO NO TOPO
# ==============================================================================
st.markdown("""
<div class="hero-banner">
    <h1>🌿 EcoAedes — Monitoramento Ambiental Inteligente</h1>
    <p>Combate preventivo ao <b>Aedes aegypti</b> por meio do mapeamento de pontos críticos, coleta de resíduos e reciclagem.</p>
</div>
""", unsafe_allow_html=True)

# ==============================================================================
# TELA 1: PAINEL DE INDICADORES
# ==============================================================================
if pagina_selecionada == "📊 Painel de Indicadores":
    st.markdown("""
    <div class="info-card">
        <b>💡 Resumo Executivo:</b> Acompanhe abaixo os recipientes que acumulavam água retirados do ambiente, a taxa de reciclagem e o impacto ambiental gerado.
    </div>
    """, unsafe_allow_html=True)

    total_peso_coletado = float(df_residuos["peso_kg"].sum()) if not df_residuos.empty else 0.0
    total_focos_eliminados = int(df_residuos["qtd_recipientes"].sum()) if not df_residuos.empty else 0
    total_pontos_ativos = int((df_locais["status"] == "Ativo").sum()) if not df_locais.empty else 0

    if not df_reciclagem.empty:
        df_reciclados_ok = df_reciclagem[df_reciclagem["status"] == "Reciclado"]
        total_peso_reciclado = float(df_reciclados_ok["peso_reciclado_kg"].sum())
    else:
        total_peso_reciclado = 0.0

    taxa_reciclagem = (total_peso_reciclado / total_peso_coletado * 100) if total_peso_coletado > 0 else 0.0
    co2_evitado = total_peso_reciclado * 1.8

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("🦟 Focos Potenciais Eliminados", f"{total_focos_eliminados} un.", delta="Recipientes retirados")
    col2.metric("⚖️ Resíduos Coletados", f"{total_peso_coletado:.1f} kg", delta=f"{total_pontos_ativos} pontos ativos")
    col3.metric("♻️ Taxa de Reciclagem", f"{taxa_reciclagem:.1f}%", delta=f"{total_peso_reciclado:.1f} kg reciclados")
    col4.metric("🌎 Emissão de CO₂ Evitada", f"{co2_evitado:.1f} kg", delta="Impacto climático positivo")

    st.divider()

    if not df_residuos.empty:
        g1, g2 = st.columns(2)

        with g1:
            df_cat = df_residuos.groupby("categoria", as_index=False)["qtd_recipientes"].sum().sort_values("qtd_recipientes", ascending=False)
            fig_cat = px.bar(
                df_cat,
                x="categoria",
                y="qtd_recipientes",
                color="categoria",
                text_auto=True,
                title="🦟 Recipientes Eliminados por Categoria",
                labels={"categoria": "Categoria", "qtd_recipientes": "Unidades"},
                color_discrete_sequence=["#059669", "#0D9488", "#F59E0B", "#EF4444", "#3B82F6"]
            )
            fig_cat.update_layout(showlegend=False, plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig_cat, use_container_width=True)

        with g2:
            df_loc_peso = df_residuos.groupby("local_nome", as_index=False)["peso_kg"].sum()
            fig_local = px.pie(
                df_loc_peso,
                names="local_nome",
                values="peso_kg",
                title="📍 Peso Coletado por Local (kg)",
                hole=0.45,
                color_discrete_sequence=["#059669", "#10B981", "#34D399", "#0284C7", "#F59E0B"]
            )
            fig_local.update_traces(textposition="inside", textinfo="percent+label")
            fig_local.update_layout(showlegend=False, paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig_local, use_container_width=True)

        if not df_reciclagem.empty:
            df_status_rec = df_reciclagem.groupby(["status", "material"], as_index=False)["peso_reciclado_kg"].sum()
            fig_rec = px.bar(
                df_status_rec,
                x="peso_reciclado_kg",
                y="status",
                color="material",
                orientation="h",
                text_auto=True,
                title="♻️ Peso por Etapa de Reciclagem (kg)",
                labels={"peso_reciclado_kg": "Peso (kg)", "status": "Etapa", "material": "Material"},
                color_discrete_sequence=["#059669", "#0284C7", "#F59E0B", "#8B5CF6", "#EC4899"]
            )
            fig_rec.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", height=300)
            st.plotly_chart(fig_rec, use_container_width=True)
    else:
        st.info("Nenhum resíduo registrado ainda. Acesse '2. Registro de Resíduos' no menu lateral.")

    with st.expander("📚 Guia Didático: Relação entre Resíduos e Dengue"):
        st.markdown("""
        | Material | Tempo na Natureza | Risco para o *Aedes aegypti* | Destino Correto |
        | :--- | :--- | :--- | :--- |
        | **Pneus** | +600 anos | Guarda água da chuva e mantém temperatura ideal para os ovos. | Ecopontos e trituração. |
        | **Garrafas PET** | ~400 anos | Tampas e garrafas cortadas viram criadouros em terrenos baldios. | Cooperativas de triagem. |
        | **Latas de Alumínio** | ~200 anos | Bordas amassadas acumulam pequenas poças suficientes para larvas. | Fundição e reciclagem. |
        | **Vidro** | +4.000 anos | Potes abertos retêm água limpa sem evaporação rápida. | Usinas de reciclagem. |
        """)

# ==============================================================================
# TELA 2: LOCAIS DE COLETA (CADASTRO À ESQUERDA | TABELA E EDIÇÃO À DIREITA)
# ==============================================================================
elif pagina_selecionada == "📍 1. Locais de Coleta":
    st.subheader("📍 Cadastro e Mapeamento de Locais de Coleta")
    col_form, col_lista = st.columns([1, 1.6], gap="large")

    with col_form:
        with st.form("form_novo_local", clear_on_submit=True):
            st.markdown("#### ➕ Novo Ponto de Coleta")
            nome_local = st.text_input("Nome do Ponto", placeholder="Ex: Ecoponto Zona Norte")
            bairro_local = st.text_input("Bairro / Região", placeholder="Ex: Jardim América")
            tipo_local = st.selectbox("Classificação", ["Ecoponto", "Ponto Crítico (Terreno)", "Escola", "Comércio Parceiro"])
            status_local = st.selectbox("Status Operacional", ["Ativo", "Em Monitoramento", "Inativo"])

            if st.form_submit_button("✅ Salvar Local", use_container_width=True):
                if nome_local and bairro_local:
                    supabase.table("locais_coleta").insert({
                        "nome": nome_local,
                        "bairro": bairro_local,
                        "tipo": tipo_local,
                        "status": status_local
                    }).execute()
                    st.toast("Local cadastrado com sucesso!", icon="📍")
                    st.rerun()
                else:
                    st.warning("Preencha o nome do ponto e o bairro.")

    with col_lista:
        st.markdown("#### 📋 Pontos Cadastrados")
        if not df_locais.empty:
            st.dataframe(
                df_locais[["id", "nome", "bairro", "tipo", "status"]],
                use_container_width=True,
                hide_index=True,
                column_config={
                    "id": st.column_config.NumberColumn("ID", width="small"),
                    "nome": "Nome",
                    "bairro": "Bairro",
                    "tipo": "Classificação",
                    "status": "Status"
                }
            )

            with st.expander("✏️ Atualizar ou Excluir Local"):
                id_sel = st.selectbox("Selecione o ID do Local", df_locais["id"].tolist(), key="sel_local_id")
                row_atual = df_locais[df_locais["id"] == id_sel].iloc[0]

                u1, u2, u3 = st.columns(3)
                novo_nome = u1.text_input("Nome", value=row_atual["nome"], key="upd_nome_local")
                novo_bairro = u2.text_input("Bairro", value=row_atual["bairro"], key="upd_bairro_local")
                opcoes_status = ["Ativo", "Em Monitoramento", "Inativo"]
                novo_status = u3.selectbox(
                    "Status",
                    opcoes_status,
                    index=opcoes_status.index(row_atual["status"]) if row_atual["status"] in opcoes_status else 0,
                    key="upd_status_local"
                )

                b_upd, b_del = st.columns(2)
                if b_upd.button("💾 Atualizar", use_container_width=True):
                    supabase.table("locais_coleta").update({
                        "nome": novo_nome,
                        "bairro": novo_bairro,
                        "status": novo_status
                    }).eq("id", id_sel).execute()
                    st.toast("Local atualizado!", icon="✅")
                    st.rerun()

                if b_del.button("🗑️ Excluir", type="primary", use_container_width=True):
                    supabase.table("locais_coleta").delete().eq("id", id_sel).execute()
                    st.toast("Local removido!", icon="🗑️")
                    st.rerun()

# ==============================================================================
# TELA 3: REGISTRO DE RESÍDUOS (CADASTRO À ESQUERDA | TABELA À DIREITA)
# ==============================================================================
elif pagina_selecionada == "🗑️ 2. Registro de Resíduos":
    st.subheader("🗑️ Registro de Resíduos Potenciais Criadouros")

    if df_locais.empty:
        st.warning("⚠️ Cadastre ao menos um local de coleta antes de registrar resíduos.")
    else:
        col_form, col_lista = st.columns([1, 1.7], gap="large")

        with col_form:
            with st.form("form_novo_residuo", clear_on_submit=True):
                st.markdown("#### ➕ Nova Coleta")
                opcoes_locais = {f"{row['nome']} ({row['bairro']})": row["id"] for _, row in df_locais.iterrows()}

                local_escolhido = st.selectbox("Local da Coleta", list(opcoes_locais.keys()))
                categoria = st.selectbox("Tipo de Material", ["Pneus", "Garrafas PET", "Latas/Alumínio", "Vidro", "Entulho/Plástico"])
                qtd_recip = st.number_input("Qtd. Recipientes", min_value=1, value=10, step=1)
                peso = st.number_input("Peso (kg)", min_value=0.1, value=5.0, step=0.5)
                data_col = st.date_input("Data da Coleta", value=date.today())

                if st.form_submit_button("✅ Registrar Coleta", use_container_width=True):
                    supabase.table("registros_residuos").insert({
                        "local_id": opcoes_locais[local_escolhido],
                        "categoria": categoria,
                        "qtd_recipientes": int(qtd_recip),
                        "peso_kg": float(peso),
                        "data_coleta": str(data_col)
                    }).execute()
                    st.toast("Coleta registrada!", icon="🗑️")
                    st.rerun()

        with col_lista:
            st.markdown("#### 📋 Histórico de Coletas")
            if not df_residuos.empty:
                st.dataframe(
                    df_residuos[["id", "local_nome", "categoria", "qtd_recipientes", "peso_kg", "data_coleta"]],
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "id": st.column_config.NumberColumn("ID", width="small"),
                        "local_nome": "Local",
                        "categoria": "Material",
                        "qtd_recipientes": st.column_config.NumberColumn("Qtd.", format="%d un."),
                        "peso_kg": st.column_config.NumberColumn("Peso", format="%.2f kg"),
                        "data_coleta": st.column_config.DateColumn("Data", format="DD/MM/YYYY")
                    }
                )

                with st.expander("✏️ Atualizar ou Excluir Coleta"):
                    id_res = st.selectbox("Selecione o ID do Registro", df_residuos["id"].tolist(), key="sel_res_id")
                    res_atual = df_residuos[df_residuos["id"] == id_res].iloc[0]

                    ur1, ur2, ur3 = st.columns(3)
                    cats = ["Pneus", "Garrafas PET", "Latas/Alumínio", "Vidro", "Entulho/Plástico"]
                    nova_cat = ur1.selectbox(
                        "Material",
                        cats,
                        index=cats.index(res_atual["categoria"]) if res_atual["categoria"] in cats else 0,
                        key="upd_cat_res"
                    )
                    nova_qtd = ur2.number_input("Recipientes", min_value=1, value=int(res_atual["qtd_recipientes"]), key="upd_qtd_res")
                    novo_peso = ur3.number_input("Peso (kg)", min_value=0.1, value=float(res_atual["peso_kg"]), key="upd_peso_res")

                    br_upd, br_del = st.columns(2)
                    if br_upd.button("💾 Atualizar", key="btn_upd_res", use_container_width=True):
                        supabase.table("registros_residuos").update({
                            "categoria": nova_cat,
                            "qtd_recipientes": int(nova_qtd),
                            "peso_kg": float(novo_peso)
                        }).eq("id", id_res).execute()
                        st.toast("Registro atualizado!", icon="✅")
                        st.rerun()

                    if br_del.button("🗑️ Excluir", key="btn_del_res", type="primary", use_container_width=True):
                        supabase.table("registros_residuos").delete().eq("id", id_res).execute()
                        st.toast("Registro excluído!", icon="🗑️")
                        st.rerun()

# ==============================================================================
# TELA 4: CONTROLE DE RECICLADOS (CADASTRO À ESQUERDA | TABELA À DIREITA)
# ==============================================================================
elif pagina_selecionada == "♻️ 3. Controle de Reciclados":
    st.subheader("♻️ Controle de Triagem e Destinação Final")
    col_form, col_lista = st.columns([1, 1.7], gap="large")

    with col_form:
        with st.form("form_reciclagem", clear_on_submit=True):
            st.markdown("#### ➕ Novo Lote")
            mat_rec = st.selectbox("Material", ["Pneus", "Garrafas PET", "Latas/Alumínio", "Vidro", "Entulho/Plástico"])
            peso_rec = st.number_input("Peso (kg)", min_value=0.1, value=10.0, step=0.5)
            destino = st.text_input("Cooperativa / Destino", placeholder="Ex: Coop. ReciclaMais")
            status_rec = st.selectbox("Etapa Atual", ["Em Triagem", "Pronto para Coleta", "Reciclado"])
            data_env = st.date_input("Data", value=date.today())

            if st.form_submit_button("✅ Salvar Lote", use_container_width=True):
                if destino:
                    supabase.table("controle_reciclagem").insert({
                        "material": mat_rec,
                        "peso_reciclado_kg": float(peso_rec),
                        "cooperativa_destino": destino,
                        "status": status_rec,
                        "data_envio": str(data_env)
                    }).execute()
                    st.toast("Lote registrado!", icon="♻️")
                    st.rerun()
                else:
                    st.warning("Informe a cooperativa ou destino.")

    with col_lista:
        st.markdown("#### 📋 Lotes Registrados")
        if not df_reciclagem.empty:
            st.dataframe(
                df_reciclagem[["id", "material", "peso_reciclado_kg", "cooperativa_destino", "status", "data_envio"]],
                use_container_width=True,
                hide_index=True,
                column_config={
                    "id": st.column_config.NumberColumn("ID", width="small"),
                    "material": "Material",
                    "peso_reciclado_kg": st.column_config.NumberColumn("Peso", format="%.2f kg"),
                    "cooperativa_destino": "Destino",
                    "status": "Etapa",
                    "data_envio": st.column_config.DateColumn("Data", format="DD/MM/YYYY")
                }
            )

            with st.expander("✏️ Atualizar ou Excluir Lote"):
                id_rec = st.selectbox("Selecione o ID do Lote", df_reciclagem["id"].tolist(), key="sel_rec_id")
                rec_atual = df_reciclagem[df_reciclagem["id"] == id_rec].iloc[0]

                urc1, urc2, urc3 = st.columns(3)
                novo_dest = urc1.text_input("Destino", value=rec_atual["cooperativa_destino"], key="upd_dest_rec")
                novo_peso_rec = urc2.number_input("Peso (kg)", min_value=0.1, value=float(rec_atual["peso_reciclado_kg"]), key="upd_peso_rec")
                etapas = ["Em Triagem", "Pronto para Coleta", "Reciclado"]
                novo_status_rec = urc3.selectbox(
                    "Etapa",
                    etapas,
                    index=etapas.index(rec_atual["status"]) if rec_atual["status"] in etapas else 0,
                    key="upd_status_rec"
                )

                brc_upd, brc_del = st.columns(2)
                if brc_upd.button("💾 Atualizar", key="btn_upd_rec", use_container_width=True):
                    supabase.table("controle_reciclagem").update({
                        "cooperativa_destino": novo_dest,
                        "peso_reciclado_kg": float(novo_peso_rec),
                        "status": novo_status_rec
                    }).eq("id", id_rec).execute()
                    st.toast("Lote atualizado!", icon="✅")
                    st.rerun()

                if brc_del.button("🗑️ Excluir", key="btn_del_rec", type="primary", use_container_width=True):
                    supabase.table("controle_reciclagem").delete().eq("id", id_rec).execute()
                    st.toast("Lote excluído!", icon="🗑️")
                    st.rerun()