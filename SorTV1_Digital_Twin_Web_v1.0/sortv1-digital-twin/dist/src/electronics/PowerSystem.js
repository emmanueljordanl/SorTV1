export const POWER_COMPONENTS = ['ELEC-03','ELEC-31','SAFE-34','SAFE-35','SAFE-36','SAFE-37'];
export const getPowerNodes = model => POWER_COMPONENTS.map(id => model.nodes.get(id)).filter(Boolean);
