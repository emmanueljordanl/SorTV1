export const LIMIT_COMPONENTS = ['SENS-22','SENS-23','SENS-24','SENS-25'];
export const getLimitNodes = model => LIMIT_COMPONENTS.map(id => model.nodes.get(id)).filter(Boolean);
