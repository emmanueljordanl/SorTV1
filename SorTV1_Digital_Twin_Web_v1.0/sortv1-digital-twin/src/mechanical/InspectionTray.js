export const INSPECTION_COMPONENTS = ['MECH-66','SENS-19','ELEC-HX711','MECH-21'];
export const getInspectionNodes = model => INSPECTION_COMPONENTS.map(id => model.nodes.get(id)).filter(Boolean);
