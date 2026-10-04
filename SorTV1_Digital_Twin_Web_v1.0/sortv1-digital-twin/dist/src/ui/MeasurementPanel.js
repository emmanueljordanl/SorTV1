export const pendingMeasurements = dimensions => Object.entries(dimensions).filter(([,d]) => d.status === 'TBC-MEDIR' || d.status === 'REFERENCE');
