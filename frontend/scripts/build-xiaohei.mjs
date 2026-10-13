import { spawnSync } from "node:child_process";
import { createHash } from "node:crypto";
import { existsSync, readFileSync, mkdirSync, writeFileSync } from "node:fs";
import { createRequire } from "node:module";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const frontend = fileURLToPath(new URL("../", import.meta.url));
const root = path.resolve(frontend, "..");
const source = path.join(root, "games", "xiaohei-web");
const output = path.join(frontend, "public", "games", "xiaohei");
const base = "/games/xiaohei/";
const sync = process.argv.includes("--sync");

function run(command, args, cwd = root) {
  const result = spawnSync(command, args, { cwd, stdio: "inherit" });
  if (result.error) throw result.error;
  if (result.status !== 0) throw new Error(`${command} exited with ${result.status}`);
}

// npm's Windows entry point is a JS file; avoid a shell and path quoting issues.
function npm(args) {
  const npmCli = process.env.npm_execpath;
  if (!npmCli) throw new Error("Run this script through npm run build:xiaohei or npm run sync:xiaohei.");
  run(process.execPath, [npmCli, ...args], source);
}

try {
  if (!existsSync(path.join(source, "package.json"))) {
    run("git", ["submodule", "update", "--init", "--", "games/xiaohei-web"]);
  }
  if (sync) {
    const status = spawnSync("git", ["status", "--porcelain"], { cwd: source, encoding: "utf8" });
    if (status.status !== 0) throw new Error("Cannot inspect XiaoHei submodule status.");
    if (status.stdout.trim()) throw new Error("XiaoHei has local changes. Commit or stash them before syncing.");
    run("git", ["fetch", "origin", "main"], source);
    run("git", ["checkout", "--detach", "origin/main"], source);
  }

  const lockHash = createHash("sha256").update(readFileSync(path.join(source, "package-lock.json"))).digest("hex");
  const stamp = path.join(source, "node_modules", ".platform-lock-hash");
  if (sync || !existsSync(stamp) || readFileSync(stamp, "utf8") !== lockHash) {
    npm(["ci"]);
    mkdirSync(path.dirname(stamp), { recursive: true });
    writeFileSync(stamp, lockHash);
  }

  const requireSource = createRequire(path.join(source, "package.json"));
  run(process.execPath, [requireSource.resolve("typescript/bin/tsc"), "-b"], source);
  const { build } = await import(pathToFileURL(requireSource.resolve("vite")).href);
  const { default: react } = await import(pathToFileURL(requireSource.resolve("@vitejs/plugin-react")).href);
  await build({
    configFile: false,
    root: source,
    base,
    plugins: [
      {
        name: "xiaohei-platform-asset-paths",
        enforce: "pre",
        transform(code, id) {
          if (!id.replaceAll("\\", "/").startsWith(`${source.replaceAll("\\", "/")}/src/`)) return null;
          // Upstream React markup uses root-absolute public asset URLs.
          return code.replace(/(["'`])\/(assets\/|wechat-mini-game-code\.png)/g, `$1${base}$2`);
        },
      },
      react(),
    ],
    build: { outDir: output, emptyOutDir: true },
  });
  console.log(`XiaoHei ready at ${base}`);
  if (sync) console.log("Review the result, then git add games/xiaohei-web to record the updated version.");
} catch (error) {
  console.error(`XiaoHei build failed: ${error.message}`);
  process.exitCode = 1;
}
