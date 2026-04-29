import json

import requests
import streamlit as st

API_URL = "http://localhost:8000/api"

st.set_page_config(page_title="AutoPatch AI", page_icon="\U0001fa79", layout="wide")

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

if "last_result" not in st.session_state:
    st.session_state.last_result = None
if "last_ticket" not in st.session_state:
    st.session_state.last_ticket = None

with st.sidebar:
    st.header("Code Search Index")

    try:
        status_resp = requests.get(f"{API_URL}/index/status", timeout=5)
        if status_resp.status_code == 200:
            stats = status_resp.json()
            if stats["indexed"]:
                st.success(f"Indexed: {stats['total_chunks']} chunks")
            else:
                st.warning("Repository not indexed yet")
        else:
            stats = {"indexed": False}
    except requests.ConnectionError:
        st.error("Backend not connected")
        stats = {"indexed": False}

    if st.button("Index Repository", use_container_width=True):
        with st.spinner("Indexing repository..."):
            try:
                resp = requests.post(f"{API_URL}/index", timeout=300)
                if resp.status_code == 200:
                    data = resp.json()
                    st.success(
                        f"Indexed {data['files_indexed']} files "
                        f"({data['chunks_created']} chunks)"
                    )
                else:
                    st.error(f"Indexing failed: {resp.text}")
            except requests.ConnectionError:
                st.error("Cannot connect to backend")
            except Exception as e:
                st.error(f"Error: {e}")

    st.divider()
    st.caption(
        "Index your repository to enable semantic search. "
        "Re-index after code changes."
    )

st.markdown('<p class="main-header">AutoPatch AI</p>', unsafe_allow_html=True)
st.markdown(
    '<p class="sub-header">Paste a bug \u2192 get a patch. Powered by LLM.</p>',
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

    if st.session_state.last_result:
        st.divider()
        st.subheader("Refine Fix")
        feedback = st.text_area(
            "Feedback",
            height=100,
            placeholder="e.g. The fix should dispatch fetchProducts inside a useEffect hook",
            help="Describe what's wrong with the generated fix so the LLM can revise it.",
        )
        refine_submitted = st.button("Refine Fix", use_container_width=True)
    else:
        feedback = ""
        refine_submitted = False


def display_patches(data):
    patches = data.get("patches", [])

    if patches:
        st.success(
            f"Patch generated! "
            f"{len(patches)} file{'s' if len(patches) != 1 else ''} affected."
        )
    else:
        st.warning("LLM did not return any file patches.")

    st.markdown(f"**Explanation:** {data['explanation']}")

    for i, patch in enumerate(patches):
        has_warning = patch.get("warning", "")
        label = patch["file_path"]
        if has_warning:
            label += "  [quality warning]"

        with st.expander(label, expanded=i == 0):
            if has_warning:
                st.warning(has_warning)

            tab_diff, tab_fixed, tab_original = st.tabs(
                ["Diff", "Fixed Code", "Original Code"]
            )

            with tab_diff:
                if patch["diff"]:
                    st.code(patch["diff"], language="diff")
                else:
                    st.info("No differences detected.")

            with tab_fixed:
                st.code(patch["fixed_code"])

            with tab_original:
                st.code(patch["original_code"])

    if patches:
        with st.expander("Raw JSON"):
            st.json(data)


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
                    resp = requests.post(
                        f"{API_URL}/generate-fix", json=payload, timeout=120
                    )

                    if resp.status_code == 200:
                        data = resp.json()
                        st.session_state.last_result = data
                        st.session_state.last_ticket = payload
                        display_patches(data)
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

    elif refine_submitted:
        if not feedback:
            st.error("Please provide feedback describing what to fix.")
        else:
            prev = st.session_state.last_result
            ticket = st.session_state.last_ticket

            refine_payload = {
                "title": ticket["title"],
                "description": ticket["description"],
                "file_hint": ticket.get("file_hint"),
                "feedback": feedback,
                "previous_patches": prev["patches"],
            }

            with st.spinner("Refining fix with your feedback..."):
                try:
                    resp = requests.post(
                        f"{API_URL}/refine-fix", json=refine_payload, timeout=120
                    )

                    if resp.status_code == 200:
                        data = resp.json()
                        st.session_state.last_result = data
                        display_patches(data)
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

    elif st.session_state.last_result:
        display_patches(st.session_state.last_result)

    else:
        st.info("Fill in a bug ticket on the left and click **Generate Fix**.")
