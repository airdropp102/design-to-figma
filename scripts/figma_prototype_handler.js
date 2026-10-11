// Included into the local Figma plugin; no direct socket/API fallback.
async function applyPrototype(params) {
  if (!params || figma.fileKey !== params.fileKey || figma.currentPage.id !== params.pageId) throw Error('Prototype document identity mismatch');
  if (!Array.isArray(params.ownedRootIds) || !params.ownedRootIds.length) throw Error('Missing owned roots');
  const roots = new Set(params.ownedRootIds);
  const pageId = params.pageId;
  const checked = new Map();
  async function owned(id) {
    if (checked.has(id)) return checked.get(id);
    const node = await figma.getNodeByIdAsync(id);
    if (!node) throw Error('Missing node ' + id);
    let cursor = node, rootId = null;
    while (cursor && cursor.type !== 'PAGE') {
      if (roots.has(cursor.id)) rootId = cursor.id;
      cursor = cursor.parent;
    }
    if (!cursor || cursor.id !== pageId || !rootId) throw Error('Node outside owned roots/page: ' + id);
    checked.set(id,node); return node;
  }
  for (const id of roots) {
    const n = await owned(id);
    if (n.type !== 'FRAME' || !n.parent || n.parent.id !== pageId) throw Error('Owned root must be a top-level frame');
  }
  const plans = new Map();
  for (const u of params.updates || []) {
    const n = await owned(u.nodeId);
    if (typeof n.setReactionsAsync !== 'function') throw Error('Node cannot receive reactions');
    if (!['ON_CLICK','ON_HOVER','ON_PRESS'].includes(u.trigger)) throw Error('Unsupported trigger');
    if (!['NAVIGATE','OVERLAY','SCROLL_TO','BACK','CLOSE'].includes(u.action)) throw Error('Unsupported action');
    const duration = u.duration === undefined ? 0.3 : u.duration;
    if (!Number.isFinite(duration) || duration < 0 || duration > 2) throw Error('Invalid duration');
    const transitionType = u.transition === undefined ? 'DISSOLVE' : u.transition;
    if (!['DISSOLVE','SMART_ANIMATE','SCROLL_ANIMATE','NONE'].includes(transitionType)) throw Error('Unsupported transition');
    let action;
    if (u.action === 'BACK' || u.action === 'CLOSE') action = {type:u.action};
    else {
      const destination = await owned(u.destinationId);
      if (u.action !== 'SCROLL_TO' && (destination.type !== 'FRAME' || destination.parent.id !== pageId)) throw Error('Navigation target must be a top-level frame');
      if (u.action === 'SCROLL_TO') {
        const top = n => { while(n.parent && n.parent.type !== 'PAGE') n=n.parent; return n.id; };
        if (top(n) !== top(destination)) throw Error('Scroll destination must be in same frame');
      }
      action = {type:'NODE',destinationId:u.destinationId,navigation:u.action,transition:transitionType === 'NONE' ? null : {type:transitionType,easing:{type:'EASE_OUT'},duration}};
    }
    if (!plans.has(n.id)) plans.set(n.id,{node:n,reactions:[]});
    const list = plans.get(n.id).reactions;
    if (list.some(r=>r.trigger.type===u.trigger)) throw Error('Duplicate trigger for node');
    list.push({trigger:{type:u.trigger},actions:[action]});
  }
  const scroll = [];
  for (const id of params.scrollFrameIds || []) {
    const n=await owned(id);if(n.type!=='FRAME')throw Error('Scroll target must be frame');scroll.push(n);
  }
  const viewports = [];
  for (const v of params.viewportHeights || []) {
    const n=await owned(v.nodeId);
    if (!roots.has(n.id) || typeof n.resize !== 'function' || !Number.isFinite(v.height) || v.height<100 || v.height>2000) throw Error('Invalid viewport');
    viewports.push({node:n,height:v.height});
  }
  // All sources/destinations are preflighted before any write. Failure while
  // writing is not atomic: caller must read live state before retrying.
  if (!params.readOnly) {
    for (const p of plans.values()) await p.node.setReactionsAsync(p.reactions);
    for (const v of viewports) v.node.resize(v.node.width,v.height);
    for (const n of scroll) {n.overflowDirection='VERTICAL';n.clipsContent=true;}
  }
  return {prototypePluginVersion:'1.0.0',readOnly:!!params.readOnly,nodes:Array.from(plans.values()).map(p=>({id:p.node.id,reactions:p.node.reactions})),scrollFrames:scroll.map(n=>({id:n.id,overflowDirection:n.overflowDirection,clipsContent:n.clipsContent})),viewports:viewports.map(v=>({id:v.node.id,width:v.node.width,height:v.node.height}))};
}
