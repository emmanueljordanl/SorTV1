export const BEARING_COMPONENTS = ['MECH-70-0','MECH-70-1','MECH-71-0','MECH-71-1'];
export const getBearingNodes = model => BEARING_COMPONENTS.map(id => model.nodes.get(id)).filter(Boolean);
