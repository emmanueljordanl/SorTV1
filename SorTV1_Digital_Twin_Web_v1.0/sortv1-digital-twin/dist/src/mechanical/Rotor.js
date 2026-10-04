export const ROTOR_COMPONENTS = ['MECH-68','MECH-69','MECH-70-0','MECH-70-1','MECH-71-0','MECH-71-1'];
export const getRotorNodes = model => ROTOR_COMPONENTS.map(id => model.nodes.get(id)).filter(Boolean);
