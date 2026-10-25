"""Interfaz local exclusiva para el Seguimiento 2026-2."""

from __future__ import annotations

import json
from pathlib import Path

import streamlit as st

from src.abstract_extractor import extract_directory, save_results
from src.requirement_three import run_term_ranking


ROOT = Path(__file__).parent
ABSTRACTS_PATH = ROOT / "data" / "processed" / "abstracts.json"
RANKING_PATH = ROOT / "data" / "processed" / "term_ranking.json"


def inject_style() -> None:
    """Detalles visuales locales; el tema principal se configura en config.toml."""
    st.markdown(
        """
        <style>
        .block-container {max-width: 1180px; padding-top: 2.2rem; padding-bottom: 3rem;}
        [data-testid="stSidebar"] {border-right: 0;}
        [data-testid="stSidebar"] .stRadio label {padding: .35rem 0; font-weight: 600;}
        .hero {background: linear-gradient(115deg, #18334A 0%, #24516B 56%, #C65D46 160%);
               color: #fff; border-radius: 22px; padding: 2.1rem 2.3rem; margin-bottom: 1.5rem;
               box-shadow: 0 14px 30px rgba(24, 51, 74, .16);}
        .hero-kicker {font-size: .78rem; letter-spacing: .12em; text-transform: uppercase;
                      color: #F4D8A2; font-weight: 700; margin-bottom: .45rem;}
        .hero h1 {font-size: 2.15rem; margin: 0 0 .55rem; color: #fff; line-height: 1.15;}
        .hero p {font-size: 1.02rem; margin: 0; color: #EAF1F4; max-width: 680px;}
        .tag {display: inline-block; margin-top: 1rem; margin-right: .4rem; padding: .32rem .66rem;
              border-radius: 999px; background: rgba(255,255,255,.14); color: #fff; font-size: .82rem;}
        .section-label {font-size: .78rem; letter-spacing: .1em; text-transform: uppercase;
                        color: #C65D46; font-weight: 800; margin-bottom: .15rem;}
        .step {border-left: 3px solid #F4B860; padding: .2rem 0 .2rem .75rem; min-height: 72px;}
        .step strong {color: #18334A;}
        [data-testid="stMetric"] {background: #fff; border: 1px solid #E6DDD0; padding: .8rem 1rem;
                                    border-radius: 14px; box-shadow: 0 5px 14px rgba(45, 52, 54, .05);}
        [data-testid="stDataFrame"] {border-radius: 14px; overflow: hidden; border: 1px solid #E6DDD0;}
        .stButton > button {border-radius: 10px; font-weight: 700; padding: .58rem 1.05rem;}
        </style>
        """,
        unsafe_allow_html=True,
    )


def download_path(path: Path, label: str, key: str) -> None:
    """Permite guardar los resultados sin buscar manualmente las carpetas."""
    if path.exists():
        st.download_button(label, path.read_bytes(), file_name=path.name, key=key)


def load_json(path: Path) -> dict | None:
    """Lee un resultado previamente generado sin interrumpir la interfaz."""
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def hero() -> None:
    st.markdown(
        """
        <div class="hero">
          <div class="hero-kicker">Análisis de Algoritmos · Seguimiento 2026-2</div>
          <h1>Del abstract al ranking</h1>
          <p>Explora el corpus de 20 artículos y compara tres formas explícitas de ordenar los términos más frecuentes.</p>
          <span class="tag">Counting Sort</span><span class="tag">Radix Sort</span><span class="tag">Bucket Sort</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def overview() -> None:
    abstracts = load_json(ABSTRACTS_PATH)
    ranking = load_json(RANKING_PATH)
    total_articles = sum(1 for item in abstracts or [] if item.get("abstract"))
    total_terms = ranking.get("unique_terms", "—") if ranking else "—"
    col1, col2, col3 = st.columns(3)
    col1.metric("Abstracts listos", total_articles or "Pendiente", "corpus controlado")
    col2.metric("Términos distintos", total_terms, "después del preprocesamiento" if ranking else "genera el ranking")
    col3.metric("Algoritmos comparados", 3, "sin sort() ni sorted()")


def learning_path() -> None:
    st.markdown('<div class="section-label">Recorrido sugerido</div>', unsafe_allow_html=True)
    first, second = st.columns(2)
    with first:
        st.markdown("<div class='step'><strong>1 · Prepara el corpus</strong><br>Extrae los abstracts de los PDF y conserva el resultado reproducible.</div>", unsafe_allow_html=True)
    with second:
        st.markdown("<div class='step'><strong>2 · Compara los ordenamientos</strong><br>Genera el top 15, revisa los tiempos y descarga la evidencia.</div>", unsafe_allow_html=True)


def extract_abstracts_page() -> None:
    st.markdown('<div class="section-label">Paso 1</div>', unsafe_allow_html=True)
    st.header("Preparar el corpus")
    st.write("La aplicación lee los 20 PDF, localiza sus abstracts y crea el archivo que utilizarán los tres algoritmos.")
    with st.container(border=True):
        left, right = st.columns([3, 2])
        with left:
            st.markdown("#### ¿Qué ocurrirá?")
            st.write("Se recorrerán los archivos de `data/pdfs`. El texto se guarda en `abstracts.json` para que el ranking sea reproducible.")
        with right:
            run_extraction = st.button("Extraer abstracts", type="primary", width="stretch")
        if run_extraction:
            with st.spinner("Leyendo los PDF y localizando abstracts..."):
                results = extract_directory(ROOT / "data" / "pdfs")
                save_results(results, ABSTRACTS_PATH)
            found = sum(result.status == "found" for result in results)
            st.success(f"Corpus preparado: {found} abstracts encontrados de {len(results)} PDF.")
            st.dataframe(
                [{"Artículo": result.file_name, "Estado": result.status, "Página": result.page_found,
                  "Título": result.title, "Autores": result.authors or "No disponible"} for result in results],
                width="stretch",
                hide_index=True,
            )
    download_path(ABSTRACTS_PATH, "Descargar corpus de abstracts", "download_abstracts")


def ranking_chart(methods: dict) -> None:
    """Dibuja el top 10 de Counting Sort; los tres rankings ya fueron validados iguales."""
    rows = methods["counting_sort"]["top_terms"][:10]
    st.bar_chart(rows, x="term", y="frequency", color="#C65D46", horizontal=True)


def render_ranking(results: dict) -> None:
    st.success("Ranking completado y validado: los tres algoritmos entregaron el mismo orden.")
    st.caption(f"{results['total_tokens']} tokens procesados · {results['unique_terms']} términos distintos · {results['preprocessing']}")

    col1, col2, col3 = st.columns(3)
    for column, (name, data) in zip((col1, col2, col3), results["methods"].items()):
        column.metric(name.replace("_", " ").title(), f"{data['average_execution_ms']:.4f} ms", "promedio por ejecución")

    left, right = st.columns([1.05, 1])
    with left:
        st.subheader("Términos que dominan el corpus")
        ranking_chart(results["methods"])
        st.caption("Visualización del top 10 obtenido por Counting Sort. Los tres métodos fueron validados contra el mismo ranking.")
    with right:
        st.subheader("Lectura rápida")
        top = results["methods"]["counting_sort"]["top_terms"][:5]
        for position, item in enumerate(top, start=1):
            st.write(f"**{position}. {item['term']}**  ·  {item['frequency']} apariciones")
        st.info("Counting y Bucket: O(n + k). Radix: O(d·(n + 10)); con base decimal fija se comporta linealmente para un número acotado de dígitos.")

    st.subheader("Los 15 términos más frecuentes")
    table_rows = []
    for position in range(results["top_limit"]):
        row = {"Puesto": position + 1}
        for name, data in results["methods"].items():
            term = data["top_terms"][position]
            row[name.replace("_", " ").title()] = f"{term['term']} ({term['frequency']})"
        table_rows.append(row)
    st.dataframe(table_rows, width="stretch", hide_index=True)

    with st.expander("Entender el cálculo interno"):
        st.markdown("- **Counting Sort:** cuenta cuántos términos hay por frecuencia y calcula posiciones de salida.")
        st.markdown("- **Radix Sort:** ordena por unidades, decenas y otros dígitos mediante pasadas estables.")
        st.markdown("- **Bucket Sort:** agrupa cada término en el bucket de su frecuencia y lee los buckets desde el mayor.")
        st.write("Los empates conservan el orden de primera aparición de la palabra en el corpus.")


def ranking_page() -> None:
    st.markdown('<div class="section-label">Paso 2</div>', unsafe_allow_html=True)
    st.header("Crear y comparar el ranking")
    if not ABSTRACTS_PATH.exists():
        st.warning("Primero prepara el corpus desde la opción “Extraer abstracts”.")
        return
    st.write("Los tres algoritmos reciben la misma lista de frecuencias. La aplicación mide el tiempo promedio y valida que el ranking coincida exactamente.")
    with st.container(border=True):
        controls, action = st.columns([3, 1])
        with controls:
            repetitions = st.slider("Repeticiones para promediar el tiempo", min_value=1, max_value=200, value=30)
            st.caption("Más repeticiones reducen el efecto de tareas externas del computador sobre la medición.")
        with action:
            st.write("")
            generate = st.button("Generar ranking", type="primary", width="stretch")
        if generate:
            with st.spinner("Contando términos y ejecutando los tres ordenamientos..."):
                results = run_term_ranking(ABSTRACTS_PATH, top_limit=15, repetitions=repetitions)
                RANKING_PATH.parent.mkdir(parents=True, exist_ok=True)
                RANKING_PATH.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
                st.session_state["ranking_results"] = results

    results = st.session_state.get("ranking_results") or load_json(RANKING_PATH)
    if results:
        render_ranking(results)
    download_path(RANKING_PATH, "Descargar ranking de términos (JSON)", "download_term_ranking")


st.set_page_config(page_title="Seguimiento 2026-2", page_icon="📊", layout="wide")
inject_style()
with st.sidebar:
    st.markdown("## 📊 Laboratorio de términos")
    st.caption("Seguimiento 2026-2")
    page = st.radio("Navegación", ("Preparar corpus", "Ranking de términos"), label_visibility="collapsed")
    st.divider()
    st.caption("Herramientas explícitas")
    st.write("Counting Sort\n\nRadix Sort\n\nBucket Sort")

hero()
overview()
st.write("")
learning_path()
st.write("")

if page == "Preparar corpus":
    extract_abstracts_page()
else:
    ranking_page()
