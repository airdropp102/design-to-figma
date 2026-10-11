const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const source = fs.readFileSync(process.argv[2] || '.agent/vendor/talktofigma/src/cursor_mcp_plugin/code.js', 'utf8');
const start = source.indexOf('async function getDocumentInfo()');
const end = source.indexOf('\nasync function getSelection()', start);
assert(start >= 0 && end > start);
async function check(fileKey) {
  let mutations = 0;
  const figma = {
    fileKey, editorType: 'figma', mode: 'default',
    root: { id: '0:0', name: 'Untitled' },
    currentPage: { id: '0:1', name: 'Page 1', children: [], loadAsync: async () => {} },
    createFrame: () => { mutations++; throw Error('read must not mutate'); }
  };
  const context = vm.createContext({figma});
  vm.runInContext(source.slice(start, end), context);
  const result = await vm.runInContext('getDocumentInfo()', context);
  assert.equal(result.fileName, 'Untitled');
  assert.equal(result.fileKey, fileKey || null);
  assert.equal(result.editorType, 'figma');
  assert.equal(result.mode, 'default');
  assert.equal(result.currentPage.id, '0:1');
  assert.equal(result.fileIdentityAvailable, !!fileKey);
  assert.equal(mutations, 0);
}
(async () => { await check('rXrX1FHInMsxbejkvSP9Wl'); await check(undefined); console.log('PASS: live identity, unavailable key, read-only document inspection'); })().catch(e => { console.error(e); process.exit(1); });
