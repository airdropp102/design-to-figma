const assert=require('node:assert/strict'),vm=require('node:vm'),fs=require('node:fs');
const source=fs.readFileSync('.agent/plugins/talktofigma-prototype/code.js','utf8');
const segment=source.slice(source.indexOf('async function exportNodeAsImage('),source.indexOf('async function setCornerRadius('));
const progress=[];let renders=0;
const context=vm.createContext({figma:{getNodeByIdAsync:async()=>({exportAsync:async settings=>{renders++;assert.equal(settings.format,'PNG');return new Uint8Array([0,1,2,3]);}})},sendProgressUpdate:async(...args)=>progress.push(args)});
vm.runInContext(segment,context);
(async()=>{const r=await context.exportNodeAsImage({nodeId:'1:2',commandId:'request'});assert.equal(r.imageData,'AAECAw==');assert.equal(renders,1);assert.equal(progress.length,3);assert.deepEqual(progress.map(p=>p[0]),['request','request','request']);assert.deepEqual(progress.map(p=>p[3]),[10,70,100]);assert.ok(progress.every(p=>typeof p[6]==='string'));console.log('PASS export stage evidence and preserved PNG encoding');})().catch(e=>{console.error(e);process.exit(1);});
