from fastapi import FastAPI

app = FastAPI(title="GridFit", version="0.1.0")


@app.get("/health")
def health() -> dict[str, str]:
    """Decision-support API that helps mini-grid operators check whether businesses fit within available power capacity."""
    return {"status": "ok"}
