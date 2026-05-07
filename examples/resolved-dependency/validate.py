import importlib.metadata


version = importlib.metadata.version("mlrm-demo-dep")

print(f"resolved mlrm-demo-dep={version}")

raise SystemExit(0)
