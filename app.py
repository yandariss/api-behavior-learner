import json
import tempfile
from pathlib import Path

import streamlit as st

from api_behavior_learner.grouper import EndpointGrouper
from api_behavior_learner.har_parser import HARParser
from api_behavior_learner.llm_analyzer import LLMAnalyzer
from api_behavior_learner.spec_generator import SpecGenerator

st.set_page_config(
    page_title="API Behavior Learner",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    .stApp { background: #f5f7fb; color: #172033; }
    [data-testid="stHeader"] { background: rgba(245,247,251,.94); }
    [data-testid="stSidebar"] { background: #ffffff; border-right: 1px solid #e2e8f0; }
    .hero { padding: 2.5rem 2.8rem; border: 1px solid #dbe4f0; border-radius: 24px; background: linear-gradient(135deg,#ffffff 0%,#eef5ff 55%,#f3efff 100%); box-shadow: 0 18px 45px rgba(30,64,115,.12); }
    .eyebrow { color: #2563eb; font-size: .78rem; font-weight: 800; letter-spacing: .18em; text-transform: uppercase; }
    .hero h1 { color: #13213a; font-size: 3.2rem; line-height: 1.05; margin: .5rem 0 1rem; }
    .hero p { color: #53657f; font-size: 1.05rem; max-width: 720px; }
    .step { background: #ffffff; border: 1px solid #dbe4f0; border-radius: 14px; padding: 1rem; min-height: 112px; box-shadow: 0 8px 22px rgba(30,64,115,.06); }
    .step b { color: #172033; display: block; margin-bottom: .4rem; }
    .step span { color: #667892; font-size: .9rem; }
    .metric-card { background: #ffffff; border: 1px solid #dbe4f0; border-radius: 16px; padding: 1rem 1.2rem; box-shadow: 0 8px 22px rgba(30,64,115,.06); }
    .metric-label { color: #71819a; font-size: .78rem; text-transform: uppercase; letter-spacing: .08em; }
    .metric-value { color: #172033; font-size: 2rem; font-weight: 800; }
    .endpoint { background: #ffffff; border: 1px solid #dbe4f0; border-radius: 12px; padding: .8rem 1rem; margin: .45rem 0; box-shadow: 0 4px 12px rgba(30,64,115,.04); }
    .method { display: inline-block; border-radius: 6px; padding: .2rem .45rem; margin-right: .65rem; font-size: .72rem; font-weight: 800; }
    .get { color: #087f5b; background: #d3f9e8; } .post { color: #1d4ed8; background: #dbeafe; }
    .put { color: #9a6700; background: #fff3bf; } .delete { color: #c92a2a; background: #ffe3e3; }
    .path { color: #263b5b; font-family: monospace; } .status { color: #71819a; float: right; font-size: .82rem; }
    div[data-testid="stFileUploader"] { background: #ffffff; border: 1px dashed #9bb7df; border-radius: 18px; padding: .6rem; }
    .stButton > button, .stDownloadButton > button { border-radius: 10px; border: 1px solid #2563eb; background: #2563eb; color: #ffffff; font-weight: 700; }
    .stButton > button:hover, .stDownloadButton > button:hover { border-color: #1d4ed8; background: #1d4ed8; }
    </style>
    """,
    unsafe_allow_html=True,
)


def metric(label, value):
    st.markdown(
        f'<div class="metric-card"><div class="metric-label">{label}</div><div class="metric-value">{value}</div></div>',
        unsafe_allow_html=True,
    )


def analyze(uploaded_file, use_llm, api_title, api_version):
    with tempfile.NamedTemporaryFile(suffix=".har", delete=False) as tmp_file:
        tmp_file.write(
            uploaded_file
            if isinstance(uploaded_file, bytes)
            else uploaded_file.getbuffer()
        )
        tmp_path = tmp_file.name
    try:
        transactions = HARParser(tmp_path).load()
        endpoints = EndpointGrouper(transactions).group()
        analyzer = LLMAnalyzer() if use_llm else LLMAnalyzer(api_key="")
        generator = SpecGenerator(analyzer)
        return (
            transactions,
            endpoints,
            generator.generate_markdown(endpoints),
            generator.generate_openapi(endpoints, api_title, api_version),
        )
    finally:
        Path(tmp_path).unlink(missing_ok=True)


def main():
    st.markdown(
        '<div class="hero"><div class="eyebrow">◈ API intelligence lab</div><h1>Turn traffic into API intelligence.</h1><p>Upload HTTP traffic. Discover endpoint behavior. Export clean Markdown docs and OpenAPI specs in seconds.</p></div>',
        unsafe_allow_html=True,
    )
    st.write("")
    steps = st.columns(3)
    for column, title, text in zip(
        steps,
        ["01 · Capture", "02 · Analyze", "03 · Export"],
        [
            "Drop a HAR file from browser DevTools.",
            "Detect routes, schemas, methods, and auth.",
            "Download Markdown and OpenAPI 3.0.",
        ],
    ):
        with column:
            st.markdown(
                f'<div class="step"><b>{title}</b><span>{text}</span></div>',
                unsafe_allow_html=True,
            )
    st.write("")

    with st.sidebar:
        st.markdown("## ◈ Control panel")
        use_llm = st.toggle(
            "AI descriptions", value=False, help="Uses OPENAI_API_KEY when configured."
        )
        api_title = st.text_input("API title", "Discovered API")
        api_version = st.text_input("Version", "1.0.0")
        st.divider()
        st.caption(
            "Privacy first: files process in this app session and are not committed to the repository."
        )

    uploaded_file = st.file_uploader(
        "Drop HAR file here",
        type=["har"],
        help="Export from DevTools → Network → Save all as HAR",
    )
    sample_path = Path("samples/sample.har")
    use_sample = st.button("Load demo HAR", disabled=not sample_path.exists())

    if uploaded_file is None and use_sample:
        uploaded_file = sample_path.read_bytes()

    if uploaded_file is None:
        st.info("Upload a HAR file or load the demo to begin.")
        st.markdown("### What you get")
        st.markdown(
            "- Endpoint patterns with dynamic IDs normalized\n- Request and response JSON schemas\n- Authentication scheme detection\n- OpenAPI 3.0 and Markdown downloads"
        )
        return

    try:
        with st.spinner("Mapping API behavior..."):
            transactions, endpoints, markdown_docs, openapi_spec = analyze(
                uploaded_file, use_llm, api_title, api_version
            )
        auth_count = len(openapi_spec.get("components", {}).get("securitySchemes", {}))
        methods = sorted(
            {method for endpoint in endpoints.values() for method in endpoint.methods}
        )
        st.success(f"Analysis complete · {len(endpoints)} endpoint patterns discovered")
        cards = st.columns(4)
        with cards[0]:
            metric("Transactions", len(transactions))
        with cards[1]:
            metric("Endpoints", len(endpoints))
        with cards[2]:
            metric("HTTP methods", len(methods))
        with cards[3]:
            metric("Auth schemes", auth_count)
        st.write("")

        overview, docs, spec, raw = st.tabs(
            ["Overview", "Markdown docs", "OpenAPI spec", "Raw JSON"]
        )
        with overview:
            st.subheader("Discovered surface")
            filter_col, method_col, status_col = st.columns([2, 1, 1])
            with filter_col:
                search = (
                    st.text_input(
                        "Search endpoints",
                        placeholder="Search by path, e.g. /users",
                        label_visibility="collapsed",
                    )
                    .strip()
                    .lower()
                )
            with method_col:
                method_filter = st.selectbox(
                    "Method",
                    ["All methods"] + methods,
                    label_visibility="collapsed",
                )
            all_statuses = sorted(
                {
                    str(code)
                    for endpoint in endpoints.values()
                    for code in endpoint.status_codes
                }
            )
            with status_col:
                status_filter = st.selectbox(
                    "Status",
                    ["All statuses"] + all_statuses,
                    label_visibility="collapsed",
                )

            visible_count = 0
            for pattern, endpoint in sorted(endpoints.items()):
                if search and search not in pattern.lower():
                    continue
                status_codes = ", ".join(
                    sorted(str(code) for code in endpoint.status_codes)
                )
                if (
                    status_filter != "All statuses"
                    and status_filter not in status_codes.split(", ")
                ):
                    continue
                for method in sorted(endpoint.methods):
                    if method_filter != "All methods" and method != method_filter:
                        continue
                    visible_count += 1
                    method_class = (
                        method.lower()
                        if method.lower() in {"get", "post", "put", "delete"}
                        else "get"
                    )
                    st.markdown(
                        f'<div class="endpoint"><span class="method {method_class}">{method}</span><span class="path">{pattern}</span><span class="status">{status_codes}</span></div>',
                        unsafe_allow_html=True,
                    )
            if visible_count == 0:
                st.info("No endpoints match current filters.")
            else:
                st.caption(f"Showing {visible_count} endpoint operations")
        with docs:
            st.download_button(
                "Download Markdown", markdown_docs, "api-docs.md", "text/markdown"
            )
            st.markdown(markdown_docs)
        with spec:
            st.download_button(
                "Download OpenAPI JSON",
                json.dumps(openapi_spec, indent=2),
                "openapi.json",
                "application/json",
            )
            st.json(openapi_spec)
        with raw:
            st.json(
                {
                    "transactions": len(transactions),
                    "endpoints": len(endpoints),
                    "methods": methods,
                }
            )
    except Exception as error:  # noqa: BLE001
        st.error("Could not analyze this HAR file.")
        with st.expander("Technical details"):
            st.exception(error)


if __name__ == "__main__":
    main()
