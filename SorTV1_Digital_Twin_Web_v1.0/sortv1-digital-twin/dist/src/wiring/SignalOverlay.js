export const signalWires = wires => wires.filter(w => !['POWER','ACTUATORS'].includes(w.kind));
