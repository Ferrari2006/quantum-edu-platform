import { readdirSync, readFileSync, writeFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const root = fileURLToPath(new URL('../../docs/quantum/', import.meta.url));
const resources = [];
function walk(directory) {
  for (const item of readdirSync(directory, { withFileTypes: true })) {
    if (['sources', 'templates'].includes(item.name)) continue;
    const filename = path.join(directory, item.name);
    if (item.isDirectory()) { walk(filename); continue; }
    if (!/\.(md|txt)$/.test(item.name) || ['README.md', 'manifest.md'].includes(item.name)) continue;
    const text = readFileSync(filename, 'utf8');
    const frontmatter = text.match(/^---\r?\n([\s\S]*?)\r?\n---/);
    const meta = {};
    for (const line of (frontmatter?.[1] || '').split(/\r?\n/)) {
      const match = line.match(/^(\w+):\s*(.*)$/);
      if (match) meta[match[1]] = match[2].replace(/^['"]|['"]$/g, '');
    }
    resources.push({ id: path.relative(root, filename).replaceAll('\\', '/'), title: meta.title || item.name.replace(/\.(md|txt)$/, ''), source: meta.source || '项目资料', type: meta.doc_type || 'document', sourceUrl: /^https?:\/\//.test(meta.source_url || '') ? meta.source_url : '', updated: meta.retrieved_at || meta.updated || '', version: meta.version === 'null' ? '' : meta.version || '', license: meta.license === 'null' ? '' : meta.license || '', topic: meta.topic || '', textLength: text.length });
  }
}
walk(root);
writeFileSync(new URL('../src/data/resourceCatalog.json', import.meta.url), JSON.stringify({ resources }, null, 2) + '\n');
console.log(`Resource catalog: ${resources.length} documents`);
