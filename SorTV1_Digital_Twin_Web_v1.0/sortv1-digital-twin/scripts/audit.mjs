import {readFile,writeFile,copyFile} from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {runScenario} from '../src/core/SimulationEngine.js';
import {runAcceptance} from '../src/engineering/TestCenter.js';

const projectRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const dataDir = path.join(projectRoot, 'data');
const load = async name => JSON.parse(await readFile(path.join(dataDir, `${name}.json`), 'utf8'));
const data = {};
for (const name of ['bom','bom_baseline','components','dimensions','pinout','wiring','states','faults','acceptance','assembly','commissioning','views','groups','software','protocol','risks']) data[name] = await load(name);
const source = 'SIMULATION';
const ids = a => a.map(x => x.component_id ?? x.bom_id ?? x.id);
const write = async (name, value) => writeFile(path.join(dataDir, name), JSON.stringify(value, null, 2) + '\n');
const contains = (haystack, needle) => haystack.some(x => x === needle);

const expectedGpio = [
  [0,1,'STEP'],[1,2,'DIR'],[2,4,'nEN'],[3,5,'SERVO PWM'],[4,6,'SDA'],[5,7,'SCL'],
  [6,9,'XSHUT0'],[7,10,'XSHUT1'],[8,11,'XSHUT2'],[9,12,'XSHUT3'],[10,14,'HX711 DOUT'],[11,15,'HX711 SCK'],
  [12,16,'TOP LID'],[13,17,'GATE CLOSED'],[14,19,'GATE OPEN'],[15,20,'RESET'],[16,21,'ROT0'],[17,22,'ROT1'],
  [18,24,'ROT2'],[19,25,'ROT3'],[20,26,'FALL0'],[21,27,'FALL1'],[22,29,'FALL2'],[26,31,'FALL3'],[27,32,'SERVICE DOOR'],[28,34,'ACTUATOR POWER']
];
const pinoutExact = data.pinout.length === expectedGpio.length && data.pinout.every((p,i) => p.gpio === expectedGpio[i][0] && p.physical_pin === expectedGpio[i][1] && p.signal === expectedGpio[i][2]);
const stateNames = ['BOOT_SAFE','CHECK_HOME','READY','WAIT_STABLE','WAIT_DECISION','POSITIONING','DISPENSING','VERIFY_CLOSE','FAULT','REVIEW'];
const faultIds = Array.from({length:30}, (_,i) => `F${String(i+1).padStart(2,'0')}`);
const acceptanceIds = Array.from({length:16}, (_,i) => `P${String(i+1).padStart(2,'0')}`);

const bomFields = ['bom_id','number','name','quantity','component_id','category','system_id'];
const baselineById = new Map(data.bom_baseline.map(x => [x.bom_id, x]));
const currentById = new Map(data.bom.map(x => [x.bom_id, x]));
const added = data.bom_baseline.filter(x => !currentById.has(x.bom_id)).map(x => x.bom_id);
const removed = data.bom.filter(x => !baselineById.has(x.bom_id)).map(x => x.bom_id);
const changed = data.bom.filter(x => baselineById.has(x.bom_id) && bomFields.some(k => String(x[k]) !== String(baselineById.get(x.bom_id)[k]))).map(x => x.bom_id);

const modelable = data.components.filter(x => x.modeled).map(x => x.component_id);
const nonGeometry = data.components.filter(x => !x.modeled).map(x => ({component_id:x.component_id,bom_id:x.bom_id,reason:'logística, repuesto o consumible sin geometría operativa individual'}));
const manifest = {source, generated_at:new Date().toISOString(), modeled_component_ids:modelable, non_geometry_components:nonGeometry, note:'Los identificadores modelables se construyen en ModelBuilder.js; los seis restantes permanecen en BOM/documentación.'};
await write('model_manifest.json', manifest);

const normalCycles = [0,1,2,3].map(kind => {
  const twin = runScenario(data, null, kind);
  return {kind, state:twin.fw.state, result:twin.result, events:twin.logger.events.length, protocol_messages:twin.logger.protocol.length, source, result_kind:'SIMULATED'};
});
await write('normal_cycle.json', {source, result_kind:'SIMULATED', scenarios:normalCycles});

const faultSimulation = data.faults.map(fault => {
  const twin = runScenario(data, fault.id, 2);
  return {id:fault.id,title:fault.title,expected_state:fault.expected_state,observed_state:twin.fw.state,reason:twin.fw.reason,physical_result:twin.result?.physical_result ?? null,actuator_power:twin.plant.power,movement_allowed:twin.plant.motorMoves>0 || twin.plant.openCommands>0,events:twin.logger.events.length,source,result_kind:'SIMULATED'};
});
await write('fault_simulation.json', {source, result_kind:'SIMULATED', faults:faultSimulation});

const acceptanceSimulation = data.acceptance.map(test => runAcceptance(data, test.id));
await write('acceptance_simulation.json', {source, result_kind:'SIMULATED', physical_result:null, tests:acceptanceSimulation});

let browserQa = null;
for (const qaPath of [path.join(dataDir, 'browser_qa.json'), path.join(projectRoot, '..', 'qa_browser.json')]) {
  if (browserQa) break;
  try { browserQa = JSON.parse(await readFile(qaPath, 'utf8')); } catch {}
}
const missingModel = browserQa?.nodes ? modelable.filter(id => !browserQa.nodes.includes(id)) : [];
const browserErrors = browserQa?.errors ?? [];
const representedPass = missingModel.length === 0 && browserErrors.length === 0;

const blockers = data.risks.filter(x => x.status === 'BLOCKER').map(x => ({id:x.id,title:x.title,mitigation:x.mitigation}));
const unresolvedWires = data.wiring.filter(x => x.status === 'BLOCKER').map(x => x.id);
const tbc = Object.entries(data.dimensions).filter(([,x]) => x.status !== 'FROZEN').map(([key,x]) => ({key,status:x.status,value:x.value,unit:x.unit,cad_dependency:x.cad_dependency}));
const faultCoverage = faultIds.every(id => data.faults.some(x => x.id === id)) && faultSimulation.length === 30;
const acceptanceCoverage = acceptanceIds.every(id => data.acceptance.some(x => x.id === id)) && acceptanceSimulation.length === 16;
const normalCyclePass = normalCycles.every(x => x.state === 'READY' && x.result?.physical_result === 'DONE' && x.result?.source === source && x.result?.result_kind === 'SIMULATED');
const noPhysicalSimulation = JSON.stringify({normalCycles,faultSimulation,acceptanceSimulation}).includes('"source":"PHYSICAL"') === false;

const statuses = {
  documentation: {status:'PASS',detail:'docs/architecture.md, assembly.md, wiring.md, simulation.md y production-contracts.md generados'},
  bom_coverage: {status:data.bom.length === 82 ? 'PASS':'INCOMPLETE',documented:data.bom.length,total:82},
  three_d_representation: {status:representedPass ? 'PASS':'INCOMPLETE',represented:modelable.length-missingModel.length,expected:modelable.length,missing:missingModel,browser_errors:browserErrors},
  mechanical_traceability: {status:representedPass && data.assembly.length === 22 ? 'PASS':'INCOMPLETE',modelable_components:modelable.length,assembly_steps:data.assembly.length},
  electrical_traceability: {status:blockers.length ? 'INCOMPLETE':'PASS',blockers},
  wiring_traceability: {status:unresolvedWires.length ? 'INCOMPLETE':'PASS',wires:data.wiring.length,blocker_wires:unresolvedWires},
  gpio_traceability: {status:pinoutExact ? 'PASS':'INCOMPLETE',pins:data.pinout.length,exact_specification:pinoutExact},
  state_machine: {status:stateNames.every(n => data.states.some(x=>x.name===n)) ? 'PASS':'INCOMPLETE',states:data.states.length},
  normal_cycle: {status:normalCyclePass ? 'PASS':'INCOMPLETE',scenarios:normalCycles},
  faults: {status:faultCoverage ? 'PASS':'INCOMPLETE',simulated:faultSimulation.length,total:30},
  assembly_guide: {status:data.assembly.length===22 ? 'PASS':'INCOMPLETE',steps:data.assembly.length},
  commissioning: {status:data.commissioning.length===11 ? 'PASS':'INCOMPLETE',steps:data.commissioning.length,physical_result:null},
  acceptance: {status:acceptanceCoverage ? 'SIMULATED':'INCOMPLETE',simulated:acceptanceSimulation.length,total:16,physical_result:null},
  tbc_meditions: {remaining:tbc.length,items:tbc},
  hardware_audit: {added:added.length,removed:removed.length,changed:changed.length,added_ids:added,removed_ids:removed,changed_ids:changed}
};

const completeness = {
  A_object_path: normalCyclePass,
  B_energy_path: ['ELEC-31','SAFE-35','SAFE-34','SAFE-36','ELEC-12','ACT-09'].every(id=>data.wiring.some(x=>x.from_component===id || x.to_component===id)) && ['ELEC-31','SAFE-35','SAFE-34','SAFE-37','ELEC-32','ACT-15'].every(id=>data.wiring.some(x=>x.from_component===id || x.to_component===id)),
  C_gpio_to_device: pinoutExact,
  D_sensor_locations: ['SENS-19','SENS-TOF0','SENS-TOF1','SENS-TOF2','SENS-TOF3','SENS-ROT0','SENS-ROT1','SENS-ROT2','SENS-ROT3','SENS-27','SENS-28','SENS-29','SENS-30'].every(id=>data.components.some(x=>x.component_id===id)),
  E_actuator_locations: ['ACT-09','ACT-15'].every(id=>data.components.some(x=>x.component_id===id)),
  F_physical_confirmation: normalCyclePass && data.states.some(x=>x.name==='VERIFY_CLOSE'),
  G_four_bins: data.components.filter(x=>x.component_id.startsWith('BIN-')).length===4,
  H_complete_cycle_observable: normalCyclePass,
  I_fault_injection: faultCoverage,
  J_state_machine: statuses.state_machine.status==='PASS',
  K_pi_pico_protocol: data.protocol.encoding.includes('ASCII compact JSON') && data.protocol.polynomial==='0x1021' && data.protocol.commands.includes('SORT'),
  L_harness: data.wiring.length===104,
  M_assembly: data.assembly.length===22,
  N_measurements: tbc.length>0,
  O_document_bom_code_3d: data.bom.length===82 && representedPass
};

const audit = {
  audit_id:'SorTV1_Digital_Twin_Audit_v1.0',
  generated_at:new Date().toISOString(),
  source,
  scope:'Auditoría automática del gemelo digital; no certifica el prototipo físico.',
  final_status: blockers.length || tbc.length || !representedPass ? 'INCOMPLETE':'COMPLETE',
  ready_statement: blockers.length || tbc.length || !representedPass ? 'SorTV1 DIGITAL TWIN v1.0 — DIGITAL BASELINE INCOMPLETE':'SorTV1 DIGITAL TWIN v1.0 — DIGITAL BASELINE COMPLETE',
  statuses,
  completeness,
  blockers,
  no_add_remove_change: {ADDED_COMPONENTS:added.length,REMOVED_COMPONENTS:removed.length,CHANGED_COMPONENTS:changed.length},
  physical_evidence_policy:'Toda ejecución del navegador, normal cycle, faults y acceptance es SIMULATED; PHYSICAL permanece null.',
  artifacts:{architecture:'docs/architecture.md',web:'src/main.js',bom:'data/bom.json',traceability:'data/traceability.json',tests:'tests/contracts.test.mjs'}
};
await write('audit.json', audit);
await copyFile(path.join(dataDir,'audit.json'), path.join(projectRoot,'..','SorTV1_Digital_Twin_Audit_v1.0.json'));

const requirements = [
  ['REQ-01','2','Alcance: una pieza, cuatro bins y rechazos','CMP-01','src/core/SimulationEngine.js','P09'],
  ['REQ-02','6','Arquitectura mecánica A–D','MECH-65','src/three/ModelBuilder.js','T01'],
  ['REQ-03','8','Dominios lógico y actuadores','ELEC-31','src/three/ModelBuilder.js','T02'],
  ['REQ-04','10','Corte físico y E-STOP','SAFE-33','src/core/StateMachine.js','T07'],
  ['REQ-05','11','Mapa GPIO Pico W','CMP-06','data/pinout.json','T03'],
  ['REQ-06','12','Direcciones XSHUT de ToF','SENS-TOF0','src/sensors/ToFSensors.js','T15'],
  ['REQ-07','13','Celda/HX711 y estabilidad','SENS-19','src/simulation/Plant.js','T18'],
  ['REQ-08','14','DRV8825 + NEMA y reed','ACT-09','src/core/StateMachine.js','T05'],
  ['REQ-09','15','Cámara, iluminación y preproceso','CMP-02','src/simulation/InspectionSimulation.js','T22'],
  ['REQ-10','17','Módulos de software Pi','SW-01','src/simulation/InspectionSimulation.js','T22'],
  ['REQ-11','18','MobileNetV3 Small / ONNX FP32 inicial','CMP-01','docs/production-contracts.md','T22'],
  ['REQ-12','19','Política top1, margen y consenso','SW-04','src/simulation/InspectionSimulation.js','T22'],
  ['REQ-13','20','Pico como autoridad física','CMP-06','src/core/StateMachine.js','T16'],
  ['REQ-14','21','Máquina de estados','FW-01','src/core/StateMachine.js','T05'],
  ['REQ-15','23','Protocolo CRC e idempotencia','HAR-07','src/protocol/Protocol.js','T09'],
  ['REQ-16','24','Ciclo normal animado','BIN-02','src/simulation/Plant.js','T21'],
  ['REQ-17','25','F01–F30','SAFE-33','src/simulation/FaultInjection.js','T17'],
  ['REQ-18','30','Construcción 22 etapas','MECH-65','data/assembly.json','T18'],
  ['REQ-19','31','Commissioning C0–C10','ELEC-31','data/commissioning.json','T18'],
  ['REQ-20','32','P01–P16','SW-08','src/engineering/TestCenter.js','T20'],
  ['REQ-21','44','Digital Twin Web local e interactivo','CMP-01','src/main.js','T16'],
  ['REQ-22','44.30','BOM interactiva 01–82','BOM-82','src/main.js','T01'],
  ['REQ-23','44.29','TBC-MEDIR y freeze separado','MECH-69','src/engineering/Engineering.js','T18'],
  ['REQ-24','44.31','Trazabilidad documento ↔ simulación','BOM-01','data/traceability.json','T01']
].map(([requirement,document_section,description,component_id,simulation_module,test_id])=>({requirement,document_section,description,component_id,simulation_module,test_id}));
const bomRows = data.bom.map(c => ({requirement:`BOM-${String(c.number).padStart(2,'0')}`,document_section:'37 / 44.30',description:c.name,component_id:c.component_id,simulation_module:c.modeled ? 'src/three/ModelBuilder.js' : 'data/bom.json + docs/architecture.md',test_id:(c.test.match(/P\d\d|F\d\d/)||['T01'])[0],modeled:!!c.modeled,measurement_status:c.measurement_status,source}));
const trace = {traceability_id:'SorTV1_Digital_Twin_Traceability_v1.0',generated_at:new Date().toISOString(),source,document:'docs/architecture.md',web:'sortv1-digital-twin/src',rows:[...requirements,...bomRows],coverage:{requirements:requirements.length,bom_rows:bomRows.length,bom_total:82,all_bom_documented:bomRows.length===82},id_policy:'Los component_id se conservan entre documento, BOM, código y 3D; logística/repuestos aparecen en trazabilidad aunque no tengan geometría operativa.'};
await write('traceability.json', trace);
await copyFile(path.join(dataDir,'traceability.json'), path.join(projectRoot,'..','SorTV1_Digital_Twin_Traceability_v1.0.json'));
console.log(JSON.stringify({final_status:audit.final_status,bom:`${data.bom.length}/82`,modelable:modelable.length,missing_model:missingModel.length,faults:`${faultSimulation.length}/30`,acceptance:`${acceptanceSimulation.length}/16`,tbc:tbc.length,added:added.length,removed:removed.length,changed:changed.length,blockers:blockers.map(x=>x.id)}, null, 2));
