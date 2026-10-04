export const SERVO_LINKAGE_COMPONENTS = ['ACT-15','MECH-16','MECH-17'];
export const getServoLinkageNodes = model => SERVO_LINKAGE_COMPONENTS.map(id => model.nodes.get(id)).filter(Boolean);
