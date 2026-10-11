// Injected before main() into a local copy of the pinned TalkToFigma server.
server.tool('apply_prototype',
  'Write real Figma prototype reactions on agent-owned nodes. Preflight file/page and roots; replace reactions only on supplied source nodes. Returns live reactions. A failed write may be partial; reconcile before retry.',
  {
    fileKey:z.string(),pageId:z.string(),ownedRootIds:z.array(z.string()).min(1),
    readOnly:z.boolean().optional().describe('Read current live reactions/settings without mutation; use to reconcile after a partial failure.'),
    viewportHeights:z.array(z.object({nodeId:z.string(),height:z.number().min(100).max(2000)})).optional(),
    scrollFrameIds:z.array(z.string()).optional(),
    updates:z.array(z.object({nodeId:z.string(),trigger:z.enum(['ON_CLICK','ON_HOVER','ON_PRESS']),action:z.enum(['NAVIGATE','OVERLAY','SCROLL_TO','BACK','CLOSE']),destinationId:z.string().optional(),transition:z.enum(['DISSOLVE','SMART_ANIMATE','SCROLL_ANIMATE','NONE']).optional(),duration:z.number().min(0).max(2).optional()}))
  },
  async (params:any) => {
    try {
      const result=await sendCommandToFigma('apply_prototype' as any,params);
      return {content:[{type:'text' as const,text:JSON.stringify(result)}]};
    } catch(e) {
      return {isError:true,content:[{type:'text' as const,text:String(e)}]};
    }
  }
);
