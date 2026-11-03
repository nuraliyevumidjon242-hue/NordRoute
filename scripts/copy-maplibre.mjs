import { copyFile, mkdir } from "node:fs/promises";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const vendor = resolve(root, "static", "vendor");
await mkdir(vendor, { recursive: true });
await Promise.all([
  copyFile(resolve(root, "node_modules", "maplibre-gl", "dist", "maplibre-gl.js"), resolve(vendor, "maplibre-gl.js")),
  copyFile(resolve(root, "node_modules", "maplibre-gl", "dist", "maplibre-gl.css"), resolve(vendor, "maplibre-gl.css")),
]);
