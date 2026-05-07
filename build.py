from pathlib import Path
import os

root_dir = Path(__file__).resolve().parent
output_path = root_dir / "config.js"

# API_BASE_URL is the backend host used by the frontend.
# DEPLOYMENT_URL is kept for compatibility with older env files, but it should
# point to the same backend API host if it is used at all.
api_base_url = (os.environ.get("API_BASE_URL") or os.environ.get("DEPLOYMENT_URL") or "").strip()
resolved_base_url = api_base_url or "http://localhost:5000"

output_path.write_text(f'window.__API_BASE_URL__ = {resolved_base_url!r};\n', encoding="utf-8")
print(f"Wrote {output_path.name} with API base URL: {resolved_base_url}")
