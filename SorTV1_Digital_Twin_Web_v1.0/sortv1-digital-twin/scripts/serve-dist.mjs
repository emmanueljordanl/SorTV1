import path from 'node:path';import {fileURLToPath} from 'node:url';
process.chdir(path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../dist'));await import('./serve.mjs');
