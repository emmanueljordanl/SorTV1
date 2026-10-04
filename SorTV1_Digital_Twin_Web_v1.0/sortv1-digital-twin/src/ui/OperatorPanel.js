export const OPERATOR_STATES = ['LISTO','PROCESANDO','REVISIÓN','FALLO'];
export const isOperatorState = state => ['READY','WAIT_STABLE','WAIT_DECISION','POSITIONING','DISPENSING','VERIFY_CLOSE','FAULT','REVIEW'].includes(state);
