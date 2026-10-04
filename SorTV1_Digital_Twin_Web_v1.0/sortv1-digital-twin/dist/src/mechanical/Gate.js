export const GATE_COMPONENTS = ['MECH-67','MECH-72','SENS-22','SENS-23'];
export const getGateNodes = model => GATE_COMPONENTS.map(id => model.nodes.get(id)).filter(Boolean);
