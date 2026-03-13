import { cpSync, existsSync } from "node:fs";
import path from "node:path";
import process from "node:process";
import { fileURLToPath, pathToFileURL } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const webRoot = path.resolve(__dirname, "..");
const standaloneEntry = path.join(webRoot, ".next", "standalone", "server.js");
const standaloneRoot = path.join(webRoot, ".next", "standalone");
const staticSourceDir = path.join(webRoot, ".next", "static");
const staticTargetDir = path.join(standaloneRoot, ".next", "static");
const publicSourceDir = path.join(webRoot, "public");
const publicTargetDir = path.join(standaloneRoot, "public");

function parseArg(name) {
  const exact = `--${name}`;
  const prefix = `${exact}=`;
  for (let index = 0; index < process.argv.length; index += 1) {
    const current = process.argv[index];
    if (current === exact) {
      return process.argv[index + 1];
    }
    if (current.startsWith(prefix)) {
      return current.slice(prefix.length);
    }
  }
  return undefined;
}

const port = parseArg("port");
const hostname = parseArg("hostname") ?? parseArg("host");

if (port && !process.env.PORT) {
  process.env.PORT = port;
}

if (hostname && !process.env.HOSTNAME) {
  process.env.HOSTNAME = hostname;
}

if (!existsSync(standaloneEntry)) {
  console.error("Standalone build output not found. Please run `npm run build` first.");
  process.exit(1);
}

if (existsSync(staticSourceDir)) {
  cpSync(staticSourceDir, staticTargetDir, { recursive: true, force: true });
}

if (existsSync(publicSourceDir)) {
  cpSync(publicSourceDir, publicTargetDir, { recursive: true, force: true });
}

await import(pathToFileURL(standaloneEntry).href);
