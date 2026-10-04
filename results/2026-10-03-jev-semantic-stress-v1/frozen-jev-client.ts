/** Portable MCP client: resolve a configured server instead of importing another checkout. */
import { Client } from '@modelcontextprotocol/client';
import { StdioClientTransport } from '@modelcontextprotocol/client/stdio';
import { execFileSync } from 'node:child_process';
import { readFile, writeFile } from 'node:fs/promises';

const [serverName, operation, inputFile, outputFile] = process.argv.slice(2);
if (!serverName || !operation || !inputFile || !outputFile) {
  throw new Error('Usage: node jev-client.ts SERVER TOOL INPUT_JSON OUTPUT_JSON');
}
const allowed = new Set(['run_capability', 'get_capability', 'get_run']);
if (!allowed.has(operation)) throw new Error('Unsupported review operation');
// Reserve the operation before contacting the server. An uncertain call must
// not be resubmitted just because a response file was never written.
await writeFile(outputFile + '.started.json', JSON.stringify({ at: new Date().toISOString(), serverName, operation, inputFile }) + '\n', { flag: 'wx' });
// The host's configuration owns executable paths and credentials. Never log it.
const config = JSON.parse(execFileSync('codex', ['mcp', 'get', serverName, '--json'], { encoding: 'utf8' }));
const transportConfig = config.transport;
if (!transportConfig || transportConfig.type !== 'stdio' || typeof transportConfig.command !== 'string') {
  throw new Error('This small adapter requires a configured stdio MCP server');
}
const env: Record<string, string> = {};
for (const [key, value] of Object.entries(process.env)) if (value !== undefined) env[key] = value;
for (const [key, value] of Object.entries(transportConfig.env ?? {})) {
  if (typeof value === 'string') env[key] = value;
}
const transport = new StdioClientTransport({ command: transportConfig.command,
  args: transportConfig.args ?? [], cwd: transportConfig.cwd ?? undefined, env, stderr: 'inherit' });
const client = new Client({ name: 'omkt-review-harness', version: '0.1.0' });
try {
  await client.connect(transport);
  const args = JSON.parse(await readFile(inputFile, 'utf8'));
  const result = await client.callTool({ name: operation, arguments: args }, { timeout: 180000 });
  await writeFile(outputFile, JSON.stringify(result, null, 2) + '\n', { flag: 'wx' });
  if (result.isError) process.exitCode = 1;
} finally {
  await client.close();
}
