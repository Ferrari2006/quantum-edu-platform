from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from backend.api.routes import router as api_router


def create_app() -> FastAPI:
    app = FastAPI(title="quantum-edu-platform")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router, prefix="/api")

    @app.get("/", response_class=HTMLResponse)
    def home():
        return """
        <!doctype html>
        <html lang="zh-CN">
          <head>
            <meta charset="UTF-8" />
            <meta name="viewport" content="width=device-width, initial-scale=1.0" />
            <title>quantum-edu-platform</title>
            <style>
              body { margin: 0; font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Arial, "PingFang SC", "Microsoft YaHei", sans-serif; background: #0b0c10; color: #e5e7eb; }
              .wrap { max-width: 920px; margin: 0 auto; padding: 28px 18px; }
              .title { font-size: 22px; font-weight: 700; margin-bottom: 8px; }
              .card { border: 1px solid #1f2937; background: #0f172a; border-radius: 12px; padding: 14px; line-height: 1.7; }
              a { color: #93c5fd; text-decoration: none; }
              a:hover { text-decoration: underline; }
              .links { display: flex; gap: 12px; flex-wrap: wrap; margin-top: 12px; }
              .pill { border: 1px solid #1f2937; background: #111827; padding: 8px 10px; border-radius: 999px; }
              code { color: #e5e7eb; }
            </style>
          </head>
          <body>
            <div class="wrap">
              <div class="title">quantum-edu-platform（后端）</div>
              <div class="card">
                <div>这是平台后端的最小可运行版本。</div>
                <div class="links">
                  <a class="pill" href="/docs">OpenAPI 文档</a>
                  <a class="pill" href="/health">/health</a>
                  <a class="pill" href="/api/health">/api/health</a>
                </div>
                <div style="margin-top:12px;">前端（React）需要本机安装 Node.js/npm 后在 <code>frontend/</code> 启动。</div>
              </div>
            </div>
          </body>
        </html>
        """

    @app.get("/health")
    def health():
        return {"ok": True}

    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True)
