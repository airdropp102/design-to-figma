"""Prepare a local TalkToFigma development plugin without editing pinned vendor files."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / '.agent/vendor/talktofigma/src/cursor_mcp_plugin'
DEST = ROOT / '.agent/plugins/talktofigma-identity'


def prepare():
    code = (SOURCE / 'code.js').read_text()
    marker = '  const page = figma.currentPage;\n  return {\n'
    start = code.index('async function getDocumentInfo()')
    end = code.index('\nasync function getSelection()', start)
    function = code[start:end]
    if function.count(marker) != 1:
        raise RuntimeError('Pinned document-info source changed; refusing ambiguous patch')
    function = function.replace(marker, '  const page = figma.currentPage;\n  const liveFileKey = figma.fileKey || null;\n  return {\n    fileName: figma.root.name,\n    fileKey: liveFileKey,\n    fileIdentityAvailable: Boolean(liveFileKey),\n    editorType: figma.editorType,\n    mode: figma.mode,\n    identityPluginVersion: "1.0.0",\n')
    code = code[:start] + function + code[end:]
    manifest = json.loads((SOURCE / 'manifest.json').read_text())
    manifest['name'] = 'TalkToFigma — Document Identity (local)'
    manifest['enablePrivatePluginApi'] = True
    DEST.mkdir(parents=True, exist_ok=True)
    for name, content in [('code.js', code), ('ui.html', (SOURCE / 'ui.html').read_text()), ('manifest.json', json.dumps(manifest, indent=2) + '\n')]:
        target = DEST / name
        if target.exists() and target.read_text() != content:
            raise RuntimeError(f'Existing local plugin differs; preserving {target}')
        target.write_text(content)
    print(DEST / 'manifest.json')


if __name__ == '__main__':
    prepare()
