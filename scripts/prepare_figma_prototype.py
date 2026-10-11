"""Generate isolated TalkToFigma prototype extension; leave pinned source intact."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent

def prepare():
    plugin=ROOT/'.agent/plugins/talktofigma-prototype'
    server=ROOT/'.agent/mcp/talktofigma-prototype'
    code=(ROOT/'.agent/plugins/talktofigma-identity/code.js').read_text()
    marker='    case "get_document_info":'
    if code.count(marker)!=1: raise RuntimeError('Ambiguous plugin dispatch marker')
    code=code.replace(marker,'    case "apply_prototype":\n      return await applyPrototype(params);\n'+marker)
    code=code.replace('    identityPluginVersion: "1.0.0",','    identityPluginVersion: "1.0.0",\n    prototypePluginVersion: "1.0.0",')
    code+='\n'+(ROOT/'scripts/figma_prototype_handler.js').read_text()
    # Export diagnostics travel through the existing MCP progress channel.
    before='    const bytes = await node.exportAsync(settings);'
    after='''    const exportCommandId = params.commandId;
    await sendProgressUpdate(exportCommandId, "export_node_as_image", "started", 10, 3, 0, "Rendering PNG in Figma");
    const bytes = await node.exportAsync(settings);
    await sendProgressUpdate(exportCommandId, "export_node_as_image", "in_progress", 70, 3, 1, "PNG rendered; encoding " + bytes.length + " bytes");'''
    if code.count(before)!=1:raise RuntimeError('Ambiguous export marker')
    code=code.replace(before,after)
    code=code.replace('    const base64 = customBase64Encode(bytes);','    const base64 = customBase64Encode(bytes);\n    await sendProgressUpdate(exportCommandId, "export_node_as_image", "completed", 100, 3, 3, "Encoded PNG; returning result");')
    manifest=json.loads((ROOT/'.agent/plugins/talktofigma-identity/manifest.json').read_text())
    manifest['name']='TalkToFigma — Prototype (local)'
    plugin.mkdir(parents=True,exist_ok=True);server.mkdir(parents=True,exist_ok=True)
    (plugin/'code.js').write_text(code)
    (plugin/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    (plugin/'ui.html').write_text((ROOT/'.agent/plugins/talktofigma-identity/ui.html').read_text())
    upstream=(ROOT/'.agent/vendor/talktofigma/src/talk_to_figma_mcp/server.ts').read_text()
    marker='// Start the server\n'
    if upstream.count(marker)!=1: raise RuntimeError('Ambiguous server marker')
    (server/'server.ts').write_text(upstream.replace(marker,(ROOT/'scripts/figma_prototype_tool.ts').read_text()+'\n'+marker))
    print(plugin/'manifest.json');print(server/'server.ts')

if __name__=='__main__':prepare()
