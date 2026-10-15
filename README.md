# YPEF Partner Document Signing Tool

Streamlit app for overlaying partner signatures and fund stamps on Word or PDF documents, converting them to A4 YourNest letterhead.

## Streamlit Community Cloud

1. Open [share.streamlit.io](https://share.streamlit.io/) and sign in with GitHub.
2. **Create app** → repository `Akshatb848/Document-Signing-Tool` → branch `master`.
3. Main file: `streamlit_app.py`.
4. In **Advanced settings → Secrets**, paste:

```toml
APP_PASSWORD = "your-login-password"
OPERATOR_NAME = "Sanjay Jha"
```

5. Deploy. The public app URL will look like `https://<name>.streamlit.app`.

Local `.env` is not uploaded. The cloud app only works after `APP_PASSWORD` is set in secrets.

## Run locally

```bash
python run.py
```

Then open http://localhost:8501/
