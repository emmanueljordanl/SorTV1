/** Mechanical identity helpers; geometry is built by three/ModelBuilder.js. */
export const CABINET_COMPONENTS = ['MECH-65','MECH-TOP','MECH-DOOR','MECH-PANEL','MECH-REAR','MECH-LEFT','MECH-RIGHT'];
export const getCabinetNodes = model => CABINET_COMPONENTS.map(id => model.nodes.get(id)).filter(Boolean);
