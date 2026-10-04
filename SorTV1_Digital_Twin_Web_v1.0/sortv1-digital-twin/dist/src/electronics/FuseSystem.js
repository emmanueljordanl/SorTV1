export const FUSE_COMPONENTS = ['SAFE-35','SAFE-36','SAFE-37'];
export const getFuseNodes = model => FUSE_COMPONENTS.map(id => model.nodes.get(id)).filter(Boolean);
