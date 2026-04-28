import json

import requests
import streamlit as st

API_URL = "http://localhost:8000/api/generate-fix"

st.set_page_config(page_title="AutoPatch AI", page_icon="🩹", layout="wide")

st.markdown(
    """
    <style>
        .main-header { font-size: 2.4rem; font-weight: 700; margin-bottom: 0; }
        .sub-header  { color: #888; font-size: 1.1rem; margin-top: 0; }
        .diff-add    { color: #22c55e; }
        .diff-remove { color: #ef4444; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown('<p class="main-header">AutoPatch AI</p>', unsafe_allow_html=True)
st.markdown(
    '<p class="sub-header">Paste a bug → get a patch. Powered by LLM.</p>',
    unsafe_allow_html=True,
)

st.divider()

col_input, col_output = st.columns([1, 1], gap="large")

with col_input:
    st.subheader("Bug Ticket")

    title = st.text_input("Title", placeholder="e.g. Fix export button issue")
    description = st.text_area(
        "Description",
        height=150,
        placeholder="e.g. Export fails when user status is pending. "
        "The export_user_data function doesn't handle non-active statuses.",
    )
    file_hint = st.text_input(
        "File hint (optional)",
        placeholder="e.g. user_service.py",
        help="Narrow the code search to files matching this name.",
    )

    submitted = st.button("Generate Fix", type="primary", use_container_width=True)

with col_output:
    st.subheader("Patch Result")

    if submitted:
        if not title or not description:
            st.error("Please fill in both the title and description.")
        else:
            payload = {"title": title, "description": description}
            if file_hint:
                payload["file_hint"] = file_hint

            with st.spinner("Fetching context & calling LLM..."):
                try:
                    resp = requests.post(API_URL, json=payload, timeout=60)

                    if resp.status_code == 200:
                        data = resp.json()

                        st.success("Patch generated!")

                        st.markdown(f"**File:** `{data['file_path']}`")
                        st.markdown(f"**Explanation:** {data['explanation']}")

                        tab_diff, tab_fixed, tab_original, tab_json = st.tabs(
                            ["Diff", "Fixed Code", "Original Code", "Raw JSON"]
                        )

                        with tab_diff:
                            if data["diff"]:
                                st.code(data["diff"], language="diff")
                            else:
                                st.info("No differences detected (code may already be correct).")

                        with tab_fixed:
                            st.code(data["fixed_code"], language="python")

                        with tab_original:
                            st.code(data["original_code"], language="python")

                        with tab_json:
                            st.json(data)

                    else:
                        error_detail = resp.json().get("detail", resp.text)
                        st.error(f"API error ({resp.status_code}): {error_detail}")

                except requests.ConnectionError:
                    st.error(
                        "Cannot connect to the backend. "
                        "Make sure the FastAPI server is running on http://localhost:8000"
                    )
                except Exception as e:
                    st.error(f"Unexpected error: {e}")
    else:
        st.info("Fill in a bug ticket on the left and click **Generate Fix**.")
