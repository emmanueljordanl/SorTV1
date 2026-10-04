export const REED_COMPONENTS = ['SENS-ROT0','SENS-ROT1','SENS-ROT2','SENS-ROT3'];
export const getReedNodes = model => REED_COMPONENTS.map(id => model.nodes.get(id)).filter(Boolean);
