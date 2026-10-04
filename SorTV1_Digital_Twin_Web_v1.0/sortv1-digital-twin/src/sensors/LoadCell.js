export const LOAD_COMPONENTS = ['SENS-19','ELEC-HX711'];
export const getLoadNodes = model => LOAD_COMPONENTS.map(id => model.nodes.get(id)).filter(Boolean);
