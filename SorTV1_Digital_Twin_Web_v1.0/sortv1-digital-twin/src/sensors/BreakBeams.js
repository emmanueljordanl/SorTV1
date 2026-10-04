export const BREAK_BEAM_COMPONENTS = ['SENS-27','SENS-28','SENS-29','SENS-30'];
export const getBreakBeamNodes = model => BREAK_BEAM_COMPONENTS.map(id => model.nodes.get(id)).filter(Boolean);
