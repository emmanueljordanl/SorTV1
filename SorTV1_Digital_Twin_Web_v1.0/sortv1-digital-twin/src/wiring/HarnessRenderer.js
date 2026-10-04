export const harnessFilter = (wires, harnessId) => wires.filter(w => !harnessId || w.harness_id === harnessId);
