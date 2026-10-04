export const timelineRows = events => events.map((event,index) => ({index,t_ms:event.t_ms,type:event.type,state:event.state,source:event.source}));
