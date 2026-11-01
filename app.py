import json
import tempfile
from pathlib import Path

import streamlit as st

from api_behavior_learner.grouper import EndpointGrouper
from api_behavior_learner.har_parser import HARParser
from api_behavior_learner.llm_analyzer import LLMAnalyzer
from api_behavior_learner.spec_generator import SpecGenerator


def main():
    st.set_page_config(
        page_title="API Behavior Learner",
        page_icon="🔍",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    st.title("🔍 API Behavior Learner")
    st.markdown(
        "Reverse engineer REST APIs from HTTP traffic logs. Upload a HAR file to automatically generate OpenAPI specs and documentation."
    )

    st.sidebar.header("Settings")
    use_llm = st.sidebar.checkbox("Use OpenAI LLM for smart analysis", value=False)
    api_title = st.sidebar.text_input("API Title", value="API")
    api_version = st.sidebar.text_input("API Version", value="1.0.0")

    st.header("📤 Upload HAR File")

    uploaded_file = st.file_uploader(
        "Drag and drop or click to upload a .har file",
        type=["har"],
        help="Export HAR from browser DevTools (Network tab → Save as HAR)",
    )

    if uploaded_file is not None:
        with st.spinner("Processing HAR file..."):
            try:
                # Save uploaded file temporarily
                with tempfile.NamedTemporaryFile(
                    suffix=".har", delete=False
                ) as tmp_file:
                    tmp_file.write(uploaded_file.getbuffer())
                    tmp_path = tmp_file.name

                # Parse HAR
                har_parser = HARParser(tmp_path)
                transactions = har_parser.load()

                st.success(f"✅ Found {len(transactions)} HTTP transactions")

                # Group endpoints
                grouper = EndpointGrouper(transactions)
                endpoints = grouper.group()

                st.info(f"📍 Detected {len(endpoints)} unique endpoint patterns")

                # Analyze
                analyzer = LLMAnalyzer() if use_llm else LLMAnalyzer(api_key="")
                spec_gen = SpecGenerator(analyzer)

                # Generate specs
                markdown_docs = spec_gen.generate_markdown(endpoints)
                openapi_spec = spec_gen.generate_openapi(
                    endpoints, title=api_title, version=api_version
                )

                # Display results in tabs
                tab1, tab2, tab3 = st.tabs(
                    ["📄 Markdown Docs", "📋 OpenAPI Spec", "📊 Summary"]
                )

                with tab1:
                    st.subheader("API Documentation (Markdown)")
                    st.markdown(markdown_docs)
                    st.download_button(
                        label="⬇️ Download Markdown",
                        data=markdown_docs,
                        file_name="api-docs.md",
                        mime="text/markdown",
                    )

                with tab2:
                    st.subheader("OpenAPI 3.0.0 Specification")
                    st.json(openapi_spec)
                    st.download_button(
                        label="⬇️ Download OpenAPI JSON",
                        data=json.dumps(openapi_spec, indent=2),
                        file_name="openapi.json",
                        mime="application/json",
                    )

                with tab3:
                    st.subheader("Analysis Summary")
                    col1, col2, col3 = st.columns(3)
                    col1.metric("HTTP Transactions", len(transactions))
                    col2.metric("Endpoint Patterns", len(endpoints))
                    methods_count = len(
                        {m for ep in endpoints.values() for m in ep.methods}
                    )
                    col3.metric("Methods Detected", methods_count)

                    st.subheader("Endpoints Found")
                    for pattern, endpoint in sorted(endpoints.items()):
                        methods = ", ".join(sorted(endpoint.methods))
                        status_codes = ", ".join(
                            sorted(str(s) for s in endpoint.status_codes)
                        )
                        st.write(
                            f"- **{pattern}** → {methods} (Status: {status_codes})"
                        )

                # Cleanup
                Path(tmp_path).unlink()

            except Exception as e:  # noqa: BLE001
                st.error(f"❌ Error processing HAR file: {e!s}")

    else:
        st.info("👆 Upload a HAR file to get started")
        with st.expander("How to export a HAR file"):
            st.markdown("""
            **Chrome / Edge:**
            1. Open DevTools (F12)
            2. Go to Network tab
            3. Navigate to API or reload page
            4. Right-click any request → Save all as HAR

            **Firefox:**
            1. Open DevTools (F12)
            2. Go to Network tab
            3. Right-click → Save All as HAR

            **Safari:**
            1. Show Develop menu (Preferences → Advanced)
            2. Develop → Show Web Inspector
            3. Network tab → File → Export
            """)


if __name__ == "__main__":
    main()
