# 两个游戏推广网页的接入与维护

平台 `/#/game` 提供小黑和女巫两个入口；选中后在同域 iframe 内展示推广网页，并可独立打开或全屏查看。原有平台导航保留。

## 小黑

- `/games/xiaohei/`
- 来源：`games/xiaohei-web` 固定版本子模块。
- 沿用现有独立构建和路径适配，保留上游已有的轻量试玩。
- 更新方法见 [小黑网站接入与更新](xiaohei-integration.md)。

## 女巫

- `/games/quantum-orb/`
- 源码及图片直接跟踪在 `frontend/public/games/quantum-orb/`。
- 静态 HTML/CSS/JS，无需另装依赖。Vite 开发时直接提供，平台构建时复制进 `frontend/dist/games/quantum-orb/`。
- 内容包含商店故事、量子门图鉴、单比特状态演示，不接入完整小游戏后端。
- 小程序码尚未提供。拿到真实图片后添加到该目录的 `assets/`，替换 `index.html` 中 `.qr-placeholder`，并更新“待接入”提示。
- 宣传画面含已明确标注的界面概念图，后续可换成实机截图。

## 开发与部署

在 `frontend` 执行 `npm ci`、`npm run dev`；生产构建使用 `npm run build`，小黑子应用自动先构建。上传完整的 `frontend/dist/`，两个推广页面及素材会一起部署。

`vite.config.js` 为两个游戏子目录提供开发／预览的 index.html 解析。生产静态服务需支持目录 index（例如 Nginx 的 `index index.html`）。

后续修改女巫网站请以此处的源码为准；原独立目录 `quantum-orb-promo/dist/` 是接入前的交付来源，不会自动同步。

完整游戏仍在微信内运行。只有部署网页并放入有效小程序码后才能形成完整的扫码入口。
