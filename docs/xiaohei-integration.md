# 小黑网站接入与更新

平台 `/#/game` 嵌入同域静态子应用 `/games/xiaohei/`，保留平台导航。
子应用包含上游宣传页及轻量试玩；完整微信小游戏不包含在此仓库中。
原有两个游戏的后端及 Python 原型继续保留，但不再从游戏页提供入口。

## 初次运行

需要 Node.js 22.12+（建议 Node.js 24 LTS）和 Git。
上游使用 React 19 / Vite 7，与平台 React 18 / Vite 5 分别安装和构建。

```powershell
git submodule update --init --recursive
cd frontend
npm.cmd ci
npm.cmd run dev
```

`predev` / `prebuild` 会自动构建小黑子应用，首次运行自动安装其依赖。
生成内容位于 `frontend/public/games/xiaohei/`，不提交 Git；平台构建会把它复制到 `frontend/dist/games/xiaohei/`。
部署整个 `frontend/dist/` 即可，无需为小黑网站单独启动服务器。

构建脚本在内存中改写上游源码里的 `/assets/` 和小游戏码路径，并设置 Vite base；不修改上游源码。
平台样式、React 版本及 Hash 路由与子应用隔离。

## 手动同步上游

在平台 `frontend/` 执行：

```powershell
npm.cmd run sync:xiaohei
npm.cmd run build
```

同步命令检查子模块是否有本地改动，获取 `origin/main`，切换到其提交并重装锁定依赖、检查 TypeScript、构建。
检查试玩和图片正常后，在平台根目录记录新版本：

```powershell
git add games/xiaohei-web
git commit -m "chore: update XiaoHei website"
```

然后按平台正常发布流程部署。仅拉取上游不会更新已部署的静态文件。
其他开发者拉取平台提交后执行 `git submodule update --init --recursive`，即可使用记录的相同版本。
上游代码本地修改应先在子模块中自行提交；同步脚本不会覆盖这些修改。

## 自动更新 PR

`.github/workflows/update-xiaohei.yml` 每周检查一次，也可在 GitHub Actions 手动触发。
只有检测到子模块新版本且平台构建成功才创建或更新 PR，不自动合并或部署。
仓库需要启用 Actions，并允许 GitHub Actions 创建 pull request；组织策略也需允许相关权限。
如这些权限不可用，可继续使用手动同步命令。

## 小游戏码

当前上游没有可用小游戏码。若要提供完整游戏入口，在上游添加
`public/wechat-mini-game-code.png` 并提交，然后同步平台。
平台 iframe 提供“独立打开”和“全屏体验”；上游页面本身目前为中文。

## 回退

从平台历史中选择已验证的子模块提交，在子模块中 checkout 该提交，重新构建并提交平台中的版本指针。
不要在生产部署时无条件追踪最新上游；以平台提交记录的版本为准。
