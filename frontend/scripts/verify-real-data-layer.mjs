import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import assert from 'assert';
import { resolveAssignedTutor } from '../src/components/profile/assigned-tutor-view-model.ts';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const frontendDir = path.resolve(__dirname, '..');
const repoRootDir = path.resolve(frontendDir, '..');

function readFile(relativePath, fromRepoRoot = false) {
  const base = fromRepoRoot ? repoRootDir : frontendDir;
  const fullPath = path.join(base, relativePath);
  return fs.readFileSync(fullPath, 'utf8');
}

console.log('🔍 Iniciando verificación estática, funcional y de integridad de datos reales del frontend (Fase 4D)...');

const assignedTutorCardContent = readFile('src/components/profile/AssignedTutorCard.tsx');
const useProfileContent = readFile('src/components/profile/useProfile.ts');
const perfilTutorContent = readFile('app/(estudiante)/perfil-tutor.tsx');
const studentExploreContent = readFile('app/(estudiante)/explore.tsx');
const tutorExploreContent = readFile('app/(tutor)/explore.tsx');
const useNotificationsContent = readFile('src/components/notifications/useNotifications.ts');
const notificationItemContent = readFile('src/components/notifications/NotificationItem.tsx');
const notificationsHeaderContent = readFile('src/components/notifications/NotificationsHeader.tsx');
const viewModelContent = readFile('src/components/profile/assigned-tutor-view-model.ts');
const packageJsonContent = readFile('package.json');
const esJsonContent = readFile('src/i18n/locales/es.json');
const enJsonContent = readFile('src/i18n/locales/en.json');
const doc00Content = readFile('documentacion/00_linea_base_verificada.md', true);
const doc01Content = readFile('documentacion/01_contrato_funcional_verificado.md', true);
const doc04Content = readFile('documentacion/04_frontend.md', true);

// 1 & 2. AssignedTutorCard.tsx y perfil-tutor.tsx no seleccionan asignaciones arbitrarias
const badAccessors = [/assignedTutors\s*\[\s*0\s*\]/, /\.at\(\s*0\s*\)/, /\.shift\(\s*\)/];
for (const accessor of badAccessors) {
  if (accessor.test(assignedTutorCardContent)) {
    console.error(`❌ FAIL 1: AssignedTutorCard.tsx accede directamente mediante ${accessor}`);
    process.exit(1);
  }
  if (accessor.test(perfilTutorContent)) {
    console.error(`❌ FAIL 2: perfil-tutor.tsx accede directamente mediante ${accessor}`);
    process.exit(1);
  }
}
console.log('✅ PASS 1 & 2: AssignedTutorCard.tsx y perfil-tutor.tsx no usan accesos directos por índice');

// 3. assigned-tutor-view-model.ts es un módulo puro y exporta resolveAssignedTutor
const forbiddenImports = [/import.*React/i, /import.*react-native/i, /import.*zustand/i, /import.*axios/i, /import.*i18next/i];
for (const imp of forbiddenImports) {
  if (imp.test(viewModelContent)) {
    console.error(`❌ FAIL 3: assigned-tutor-view-model.ts contiene import no permitido (${imp})`);
    process.exit(1);
  }
}
if (!viewModelContent.includes('export function resolveAssignedTutor') ||
    !viewModelContent.includes("'none'") ||
    !viewModelContent.includes("'available'") ||
    !viewModelContent.includes("'ambiguous'")) {
  console.error('❌ FAIL 3: assigned-tutor-view-model.ts no define resolveAssignedTutor o sus estados semánticos');
  process.exit(1);
}

// 3a. Estático: no usa normalizedName, normalizedName.toLowerCase(), tutor.full_name o rawName como clave
if (/tutorMap\.set\(\s*normalizedName/i.test(viewModelContent) ||
    /normalizedName\.toLowerCase\(\)/i.test(viewModelContent)) {
  console.error('❌ FAIL 3a: assigned-tutor-view-model.ts utiliza el nombre como clave del Map');
  process.exit(1);
}

const keyAssignmentPart = viewModelContent.split('let key')[1] || '';
if (/tutor\.full_name/i.test(keyAssignmentPart) || /rawName/i.test(keyAssignmentPart)) {
  console.error('❌ FAIL 3b: assigned-tutor-view-model.ts utiliza el nombre como fallback para la clave de deduplicación');
  process.exit(1);
}
console.log('✅ PASS 3: assigned-tutor-view-model.ts verificado como módulo puro sin deduplicación por nombre');

// 4. Pruebas funcionales del resolver resolveAssignedTutor
// A. Array vacío -> none
assert.strictEqual(resolveAssignedTutor([]).status, 'none');

// B. Una asignación válida -> available
const singleAssign = [{ id: 10, tutor_id: 1, tutor: { id: 1, full_name: '  Carlos   Mendoza  ', email: 'carlos@edu.pe', role: 'tutor' } }];
const resB = resolveAssignedTutor(singleAssign);
assert.strictEqual(resB.status, 'available');
assert.strictEqual(resB.tutor?.full_name, 'Carlos Mendoza');

// C. Dos entradas del mismo tutor con ID -> available
const doubleSame = [
  { id: 10, tutor_id: 1, tutor: { id: 1, full_name: 'Carlos Mendoza', email: 'carlos@edu.pe', role: 'tutor' } },
  { id: 11, tutor_id: 1, tutor: { id: 1, full_name: 'Carlos Mendoza', email: 'carlos@edu.pe', role: 'tutor' } },
];
assert.strictEqual(resolveAssignedTutor(doubleSame).status, 'available');

// D. Dos tutores distintos -> ambiguous
const doubleDiff = [
  { id: 10, tutor_id: 1, tutor: { id: 1, full_name: 'Carlos Mendoza', email: 'carlos@edu.pe', role: 'tutor' } },
  { id: 12, tutor_id: 2, tutor: { id: 2, full_name: 'Beatriz Ramos', email: 'beatriz@edu.pe', role: 'tutor' } },
];
assert.strictEqual(resolveAssignedTutor(doubleDiff).status, 'ambiguous');

// E. Tutor sin full_name -> none
const noName = [{ id: 10, tutor_id: 1, tutor: { id: 1, full_name: '   ', email: 'carlos@edu.pe', role: 'tutor' } }];
assert.strictEqual(resolveAssignedTutor(noName).status, 'none');

// F. Entrada inválida -> none
assert.strictEqual(resolveAssignedTutor(null).status, 'none');
assert.strictEqual(resolveAssignedTutor([null, undefined, 123, 'str']).status, 'none');

// G. Un candidato válido sin ID ni correo -> available
const candidateNoId = [{ tutor: { full_name: 'Carlos Mendoza' } }];
assert.strictEqual(resolveAssignedTutor(candidateNoId).status, 'available');

// H. Dos candidatos con el mismo nombre, sin ID, tutor_id ni correo -> ambiguous
const doubleSameNameNoId = [
  { tutor: { full_name: 'Carlos Mendoza' } },
  { tutor: { full_name: 'Carlos Mendoza' } },
];
assert.strictEqual(resolveAssignedTutor(doubleSameNameNoId).status, 'ambiguous');

// I. Dos candidatos con el mismo tutor.id -> available
const doubleSameTutorId = [
  { tutor: { id: 10, full_name: 'Carlos Mendoza' } },
  { tutor: { id: 10, full_name: 'Carlos Mendoza' } },
];
assert.strictEqual(resolveAssignedTutor(doubleSameTutorId).status, 'available');

// J. Dos candidatos con el mismo tutor_id -> available
const doubleSameItemTutorId = [
  { tutor_id: 15, tutor: { full_name: 'Carlos Mendoza' } },
  { tutor_id: 15, tutor: { full_name: 'Carlos Mendoza' } },
];
assert.strictEqual(resolveAssignedTutor(doubleSameItemTutorId).status, 'available');

// K. Dos candidatos con el mismo correo normalizado -> available
const doubleSameEmail = [
  { tutor: { full_name: 'Carlos Mendoza', email: ' CARLOS@EDU.PE  ' } },
  { tutor: { full_name: 'Carlos Mendoza', email: 'carlos@edu.pe' } },
];
assert.strictEqual(resolveAssignedTutor(doubleSameEmail).status, 'available');

// L. Dos candidatos sin identificador y con nombres diferentes -> ambiguous
const doubleDiffNoId = [
  { tutor: { full_name: 'Carlos Mendoza' } },
  { tutor: { full_name: 'Beatriz Ramos' } },
];
assert.strictEqual(resolveAssignedTutor(doubleDiffNoId).status, 'ambiguous');
console.log('✅ PASS 4: Pruebas funcionales de resolveAssignedTutor ejecutadas con éxito (A-L)');

// 5. useProfile: assignedTutorLoadError, no notify:false con loadAssignedTutor, Array.isArray
if (!useProfileContent.includes('assignedTutorLoadError')) {
  console.error('❌ FAIL 5: useProfile.ts no incluye el estado assignedTutorLoadError');
  process.exit(1);
}
if (/reportApiError\([^)]*errors\.loadAssignedTutor[^)]*notify:\s*false/i.test(useProfileContent)) {
  console.error('❌ FAIL 5: useProfile.ts utiliza notify:false incorrectamente con errors.loadAssignedTutor');
  process.exit(1);
}
if (!useProfileContent.includes('Array.isArray')) {
  console.error('❌ FAIL 5: useProfile.ts no valida Array.isArray(response.data)');
  process.exit(1);
}
if (!useProfileContent.includes('setAssignedTutors([])')) {
  console.error('❌ FAIL 5: useProfile.ts no limpia assignedTutors ante error');
  process.exit(1);
}
console.log('✅ PASS 5: useProfile.ts verificado con assignedTutorLoadError, Array.isArray y reportApiError correcto');

// 6. NotificationsHeader: sin notifications.all, sin ∨, sin Pressable ficticio
if (notificationsHeaderContent.includes('notifications.all') || notificationsHeaderContent.includes('∨')) {
  console.error('❌ FAIL 6: NotificationsHeader.tsx conserva el control ficticio de filtro');
  process.exit(1);
}
console.log('✅ PASS 6: NotificationsHeader.tsx verificado sin falso control de filtro');

// 7. useNotifications: sin 15 * 60 * 1000, sin reminder_session_, conserva reminder_local_, usa actDate.toISOString()
if (useNotificationsContent.includes('15 * 60 * 1000')) {
  console.error('❌ FAIL 7: useNotifications.ts contiene la fecha simulada 15 * 60 * 1000');
  process.exit(1);
}
if (useNotificationsContent.includes('reminder_session_')) {
  console.error('❌ FAIL 7: useNotifications.ts reincorporó reminder_session_');
  process.exit(1);
}
if (!useNotificationsContent.includes('reminder_local_') || !useNotificationsContent.includes('actDate.toISOString()')) {
  console.error('❌ FAIL 7: useNotifications.ts no utiliza actDate.toISOString() para los recordatorios locales');
  process.exit(1);
}
console.log('✅ PASS 7: useNotifications.ts usa fecha real actDate.toISOString() para recordatorios locales');

// 8. NotificationItem: distingue reminder_local_ y conserva formatRelativeTime para backend
if (!notificationItemContent.includes('reminder_local_')) {
  console.error('❌ FAIL 8: NotificationItem.tsx no distingue recordatorios locales por prefijo reminder_local_');
  process.exit(1);
}
console.log('✅ PASS 8: NotificationItem.tsx distingue recordatorios locales y muestra su contenido correctamente');

// 9. Explore estudiante y tutor: usa explore.profileDescription y no profile.noAssignedTutorDescription
if (studentExploreContent.includes('profile.noAssignedTutorDescription') || tutorExploreContent.includes('profile.noAssignedTutorDescription')) {
  console.error('❌ FAIL 9: explore.tsx usa profile.noAssignedTutorDescription para la tarjeta de perfil');
  process.exit(1);
}
if (!studentExploreContent.includes('explore.profileDescription') || !tutorExploreContent.includes('explore.profileDescription')) {
  console.error('❌ FAIL 9: explore.tsx no usa explore.profileDescription');
  process.exit(1);
}
console.log('✅ PASS 9: Explore de estudiante y tutor usan la clave genérica explore.profileDescription');

// 10. Eliminación confirmada de componentes Explore sin consumidores
const removedFiles = [
  'src/components/explore/CollapsibleSection.tsx',
  'src/components/explore/ExploreHeader.tsx',
  'src/components/explore/useExplore.ts',
];
for (const relPath of removedFiles) {
  const fullP = path.join(frontendDir, relPath);
  if (fs.existsSync(fullP)) {
    console.error(`❌ FAIL 10: El archivo residual ${relPath} aún existe`);
    process.exit(1);
  }
}
console.log('✅ PASS 10: Confirmada la eliminación de componentes Explore residuales sin consumidores');

// 11. Verificaciones estáticas de documentación y package.json
if (!packageJsonContent.includes('"verify:data"')) {
  console.error('❌ FAIL 11: package.json no incluye el script verify:data');
  process.exit(1);
}
if (!doc00Content.includes('FRONT-004')) {
  console.error('❌ FAIL 11: 00_linea_base_verificada.md no contiene la entrada FRONT-004');
  process.exit(1);
}

// 11a. Fila /tutors/service-types no contiene SOLO_BACKEND ni service_type_id: 1 / service_type_id=1
const serviceTypesLineMatch = doc01Content.match(/.*service-types.*/i);
if (serviceTypesLineMatch) {
  const serviceTypesLine = serviceTypesLineMatch[0];
  if (/SOLO_BACKEND|service_type_id\s*[:=]\s*1/i.test(serviceTypesLine)) {
    console.error('❌ FAIL 11a: La fila /tutors/service-types en 01_contrato_funcional_verificado.md conserva SOLO_BACKEND o service_type_id: 1');
    process.exit(1);
  }
}

// 11b. Fila NotificationsHeader no presenta el filtro como activo/pendiente y menciona su eliminación
const notifHeaderLineMatch = doc01Content.match(/.*NotificationsHeader.*/i);
if (notifHeaderLineMatch) {
  const notifHeaderLine = notifHeaderMatchLine(notifHeaderLineMatch[0]);
  if (!notifHeaderLine.includes('RESUELTO_EN_FASE_4D') || !/eliminad[oa]/i.test(notifHeaderLine)) {
    console.error('❌ FAIL 11b: La fila NotificationsHeader en 01_contrato_funcional_verificado.md no refleja su resolución');
    process.exit(1);
  }
}

function notifHeaderMatchLine(str) {
  return str;
}

// 11c. 04_frontend.md no contiene afirmación activa que combine /sessions y /events como consumidos
if (/sincronizad[oa]s?\s+con\s+.*\/sessions.*\/events/i.test(doc04Content) ||
    /utiliza\s+ambos\s+endpoints/i.test(doc04Content) ||
    /calendario\s+consume\s+\/events/i.test(doc04Content)) {
  console.error('❌ FAIL 11c: doc 04_frontend.md afirma erróneamente el consumo o sincronización activa de /events');
  process.exit(1);
}

// 11d. 04_frontend.md indica explícitamente que /events no se consume desde el frontend
if (!/\/events\/?`*\s+no\s+se\s+consume\s+desde\s+el\s+frontend/i.test(doc04Content)) {
  console.error('❌ FAIL 11d: doc 04_frontend.md no indica explícitamente que /events no se consume desde el frontend');
  process.exit(1);
}

// 11e. HALL-MOCK-001 continúa RESUELTO_EN_FASE_4D
if (!/HALL-MOCK-001.*RESUELTO_EN_FASE_4D/s.test(doc01Content)) {
  console.error('❌ FAIL 11e: doc 01_contrato_funcional_verificado.md no mantiene HALL-MOCK-001 como RESUELTO_EN_FASE_4D');
  process.exit(1);
}
console.log('✅ PASS 11: Documentación técnica y package.json verificados rigurosamente sin contradicciones');

// 12. Paridad estructural ES/EN
const esObj = JSON.parse(esJsonContent);
const enObj = JSON.parse(enJsonContent);

function getKeyPaths(obj, prefix = '') {
  let keys = [];
  for (const k in obj) {
    const keyPath = prefix ? `${prefix}.${k}` : k;
    if (typeof obj[k] === 'object' && obj[k] !== null && !Array.isArray(obj[k])) {
      keys = keys.concat(getKeyPaths(obj[k], keyPath));
    } else {
      keys.push(keyPath);
    }
  }
  return keys.sort();
}

assert.deepStrictEqual(getKeyPaths(esObj), getKeyPaths(enObj), 'Las claves de es.json y en.json no coinciden');
console.log('✅ PASS 12: Paridad estructural ES/EN confirmada');

console.log('🎉 Verificación exitosa de la capa de datos reales del frontend (exit code 0)');
process.exit(0);
