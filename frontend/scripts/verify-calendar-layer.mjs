import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { Buffer } from 'node:buffer';
import ts from 'typescript';
import assert from 'assert';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const frontendDir = path.resolve(__dirname, '..');
const repoRootDir = path.resolve(frontendDir, '..');

function readFile(relativePath, fromRepoRoot = false) {
  const base = fromRepoRoot ? repoRootDir : frontendDir;
  const fullPath = path.join(base, relativePath);
  return fs.readFileSync(fullPath, 'utf8');
}

console.log('🔍 Iniciando verificación estática y funcional de la capa de calendario (Fase 4C)...');

const calendarItemsContent = readFile('src/components/calendar/calendar-items.ts');
const useCalendarContent = readFile('src/components/calendar/useCalendar.ts');
const addActivityModalContent = readFile('src/components/calendar/AddActivityModal.tsx');
const activityDetailsModalContent = readFile('src/components/calendar/ActivityDetailsModal.tsx');
const calendarActivitiesListContent = readFile('src/components/calendar/CalendarActivitiesList.tsx');
const useNotificationsContent = readFile('src/components/notifications/useNotifications.ts');
const activityStoreContent = readFile('src/store/activity.ts');
const packageJsonContent = readFile('package.json');
const esJsonContent = readFile('src/i18n/locales/es.json');
const enJsonContent = readFile('src/i18n/locales/en.json');
const doc00Content = readFile('documentacion/00_linea_base_verificada.md', true);
const doc01Content = readFile('documentacion/01_contrato_funcional_verificado.md', true);
const doc04Content = readFile('documentacion/04_frontend.md', true);
const readmeContent = readFile('README.md');

// 1. calendar-items.ts es un módulo puro
if (/import.*from.*['"](react|react-native|expo|zustand|axios|@react-native-async-storage\/async-storage|\.\.\/store|hooks|i18next)/i.test(calendarItemsContent)) {
  console.error('❌ FAIL 1: calendar-items.ts importa módulos prohibidos');
  process.exit(1);
}
console.log('✅ PASS 1: calendar-items.ts es un módulo puro');

// 2 & 3. Tipos e identidades conceptuales
if (!calendarItemsContent.includes('CalendarItemSource') ||
    !calendarItemsContent.includes('local_activity') ||
    !calendarItemsContent.includes('tutoring_session')) {
  console.error('❌ FAIL 2 & 3: calendar-items.ts no define CalendarItemSource o sus orígenes');
  process.exit(1);
}
console.log('✅ PASS 2 & 3: CalendarItemSource, local_activity y tutoring_session definidos');

// 4. Prefijos de ID
if (!calendarItemsContent.includes('activity:') || !calendarItemsContent.includes('session:')) {
  console.error('❌ FAIL 4: IDs en calendar-items.ts no utilizan prefijos activity: y session:');
  process.exit(1);
}
console.log('✅ PASS 4: Prefijos activity: y session: utilizados');

// 5 & 6. useCalendar y useNotifications usan calendar-items.ts
if (!useCalendarContent.includes('calendar-items') || !useNotificationsContent.includes('calendar-items')) {
  console.error('❌ FAIL 5 & 6: useCalendar o useNotifications no importan calendar-items');
  process.exit(1);
}
console.log('✅ PASS 5 & 6: useCalendar y useNotifications integrados con calendar-items');

// 7, 8 & 9. Ausencia de /events/, EventsAPI o EventStore en frontend
if (fs.existsSync(path.join(frontendDir, 'src/api/events.ts')) ||
    fs.existsSync(path.join(frontendDir, 'src/store/event.ts')) ||
    fs.existsSync(path.join(frontendDir, 'src/store/events.ts'))) {
  console.error('❌ FAIL: Se detectaron archivos de EventsAPI o EventStore');
  process.exit(1);
}

function searchDirForPattern(dir, pattern) {
  const files = fs.readdirSync(dir);
  for (const file of files) {
    const fullPath = path.join(dir, file);
    const stat = fs.statSync(fullPath);
    if (stat.isDirectory()) {
      searchDirForPattern(fullPath, pattern);
    } else if (file.endsWith('.ts') || file.endsWith('.tsx') || file.endsWith('.js')) {
      const content = fs.readFileSync(fullPath, 'utf8');
      if (pattern.test(content)) {
        console.error(`❌ FAIL 7: Se encontró consumo de /events/ en ${fullPath}`);
        process.exit(1);
      }
    }
  }
}
searchDirForPattern(path.join(frontendDir, 'src'), /client\.(get|post|put|delete).*\/events/i);
searchDirForPattern(path.join(frontendDir, 'app'), /client\.(get|post|put|delete).*\/events/i);
console.log('✅ PASS 7, 8, 9: Sin consumo de /events/, EventsAPI ni EventStore en frontend');

// 10 & 11. useActivityStore utiliza shouldRetainStoredActivity y conserva tutoria-activities-storage
if (!activityStoreContent.includes('shouldRetainStoredActivity')) {
  console.error('❌ FAIL 10: activity.ts no utiliza shouldRetainStoredActivity');
  process.exit(1);
}
if (activityStoreContent.includes('if (!actDate) return false')) {
  console.error('❌ FAIL 10: activity.ts contiene if (!actDate) return false');
  process.exit(1);
}
if (!activityStoreContent.includes('tutoria-activities-storage') ||
    !activityStoreContent.includes('addActivity') ||
    !activityStoreContent.includes('deleteActivity') ||
    !activityStoreContent.includes('clearPastActivities')) {
  console.error('❌ FAIL 11: useActivityStore alteró su contrato público o su clave de almacenamiento');
  process.exit(1);
}
console.log('✅ PASS 10 & 11: activity.ts verificado con shouldRetainStoredActivity y tutoria-activities-storage');

// Check notifications: useNotifications.ts no importa useSessionStore, no contiene fetchSessions ni reminder_session_
if (useNotificationsContent.includes('useSessionStore') ||
    useNotificationsContent.includes('fetchSessions') ||
    useNotificationsContent.includes('reminder_session_')) {
  console.error('❌ FAIL: useNotifications.ts contiene referencias a useSessionStore, fetchSessions o reminder_session_');
  process.exit(1);
}
if (!useNotificationsContent.includes('reminder_local_')) {
  console.error('❌ FAIL: useNotifications.ts no conserva reminder_local_');
  process.exit(1);
}
console.log('✅ PASS: useNotifications.ts no duplica sesiones y conserva recordatorios locales');

// Check useCalendar: no hardcoded dates, no serviceTypeId = 1, includes errors.loadTutorData
if (useCalendarContent.includes('new Date(2026, 4, 19)') || useCalendarContent.includes('new Date(2026, 4, 1)')) {
  console.error('❌ FAIL: useCalendar.ts contiene fechas iniciales hardcodeadas');
  process.exit(1);
}
if (/let\s+serviceTypeId\s*=\s*1/.test(useCalendarContent) || useCalendarContent.includes('serviceRes.data[0].id')) {
  console.error('❌ FAIL: useCalendar.ts contiene fallback serviceTypeId = 1 o data[0].id');
  process.exit(1);
}
if (!useCalendarContent.includes('errors.loadTutorData')) {
  console.error('❌ FAIL: useCalendar.ts no utiliza errors.loadTutorData');
  process.exit(1);
}
if (useCalendarContent.includes('console.error')) {
  console.error('❌ FAIL: useCalendar.ts contiene console.error');
  process.exit(1);
}
console.log('✅ PASS: useCalendar.ts verificado sin fechas duras, sin fallback serviceTypeId y con loadTutorData visible');

// 14b. El fallo de carga del calendario debe llegar a la persona usuaria.
// fetchTutorData y fetchSessions reportan con notify:false a proposito, para no emitir
// un aviso ademas del bloque de error en pantalla. Esa decision solo es valida mientras
// el hook exponga el estado y AMBAS pantallas lo rendericen; si una no lo hace, el error
// queda invisible y el calendario aparece vacio sin explicacion.
if (!useCalendarContent.includes('loadError') || !useCalendarContent.includes('retryLoad')) {
  console.error('❌ FAIL 14b: useCalendar.ts no expone loadError y retryLoad');
  process.exit(1);
}
if (!/setLoadError\(/.test(useCalendarContent)) {
  console.error('❌ FAIL 14b: useCalendar.ts no registra el fallo de carga en loadError');
  process.exit(1);
}
const calendarScreens = [
  ['app/(estudiante)/calendar.tsx', readFile('app/(estudiante)/calendar.tsx')],
  ['app/(tutor)/calendar.tsx', readFile('app/(tutor)/calendar.tsx')],
];
for (const [relPath, content] of calendarScreens) {
  if (!content.includes('loadError')) {
    console.error(`❌ FAIL 14b: ${relPath} no muestra loadError; el fallo de carga queda silencioso`);
    process.exit(1);
  }
  if (!content.includes('retryLoad')) {
    console.error(`❌ FAIL 14b: ${relPath} no ofrece reintentar la carga`);
    process.exit(1);
  }
}
console.log('✅ PASS 14b: El fallo de carga del calendario es visible y reintentable en ambas pantallas');

// Check AddActivityModal: no selectedDate.setHours
if (addActivityModalContent.includes('selectedDate.setHours')) {
  console.error('❌ FAIL: AddActivityModal.tsx muta selectedDate con setHours');
  process.exit(1);
}
console.log('✅ PASS: AddActivityModal.tsx no muta selectedDate');

// Check ActivityDetailsModal: uses catch { without unused variable
if (/catch\s*\(\s*\w+\s*\)/.test(activityDetailsModalContent)) {
  console.error('❌ FAIL: ActivityDetailsModal.tsx contiene catch con variable declarada no utilizada');
  process.exit(1);
}
if (!activityDetailsModalContent.includes('catch {')) {
  console.error('❌ FAIL: ActivityDetailsModal.tsx no utiliza la sintaxis catch {');
  process.exit(1);
}
console.log('✅ PASS: ActivityDetailsModal.tsx verificado con catch { sin variable no utilizada');

// Check strict typing in CalendarActivitiesList and buildCalendarItems
if (calendarActivitiesListContent.includes(': any') || calendarActivitiesListContent.includes('<any>')) {
  console.error('❌ FAIL: CalendarActivitiesListProps o sus funciones contienen any');
  process.exit(1);
}
if (calendarItemsContent.includes('activities: any[]') || calendarItemsContent.includes('sessions: any[]')) {
  console.error('❌ FAIL: buildCalendarItems utiliza any[]');
  process.exit(1);
}
console.log('✅ PASS: Tipado estricto en CalendarActivitiesList y buildCalendarItems sin any[]');

// 15. Sin eslint-disable react-hooks/exhaustive-deps en archivos del calendario
const calendarFiles = [
  useCalendarContent,
  addActivityModalContent,
  activityDetailsModalContent,
  calendarActivitiesListContent,
  useNotificationsContent
];
for (const content of calendarFiles) {
  if (content.includes('eslint-disable') && content.includes('react-hooks/exhaustive-deps')) {
    console.error('❌ FAIL 15: Se detectó eslint-disable react-hooks/exhaustive-deps en archivos del calendario');
    process.exit(1);
  }
}
console.log('✅ PASS 15: Sin supresiones eslint-disable en react-hooks/exhaustive-deps');

// 16. Paridad ES y EN incluyendo errors.loadTutorData
const esObj = JSON.parse(esJsonContent);
const enObj = JSON.parse(enJsonContent);

if (!esObj.errors?.loadTutorData || !enObj.errors?.loadTutorData) {
  console.error('❌ FAIL 16: errors.loadTutorData ausente en es.json o en.json');
  process.exit(1);
}

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
console.log('✅ PASS 16: Paridad estructural ES/EN confirmada');

// 17. package.json contiene verify:calendar
if (!packageJsonContent.includes('"verify:calendar"')) {
  console.error('❌ FAIL 17: package.json no contiene script verify:calendar');
  process.exit(1);
}
console.log('✅ PASS 17: package.json contiene script verify:calendar');

// 18 & 19. Documentación contiene secciones 2.4 y 2.5
if (!doc04Content.includes('2.4 UX Optimista en el Chat RAG') ||
    !doc04Content.includes('2.5 Modelo Puro del Calendario') ||
    !doc01Content.includes('DECISION_FUNCIONAL_RESUELTA_EN_FASE_4C') ||
    !/fase[ _]?4c/i.test(doc00Content) ||
    !readmeContent.includes('verify:calendar')) {
  console.error('❌ FAIL 18 & 19: Documentación incompleta sobre la decisión funcional de la Fase 4C');
  process.exit(1);
}
console.log('✅ PASS 18 & 19: Documentación y README verificados con 2.4 UX Optimista y 2.5 Modelo Puro');

// PRUEBAS FUNCIONALES DE calendar-items.ts (Casos A - N)
console.log('🧪 Ejecutando pruebas funcionales de calendar-items.ts...');

const transpileResult = ts.transpileModule(calendarItemsContent, {
  compilerOptions: { module: ts.ModuleKind.ESNext, target: ts.ScriptTarget.ES2022 }
});

const moduleUrl = 'data:text/javascript;base64,' + Buffer.from(transpileResult.outputText).toString('base64');
const {
  parseLocalActivityDate,
  shouldRetainStoredActivity,
  mapActivityToCalendarItem,
  mapSessionToCalendarItem,
  buildCalendarItems,
  isUpcomingCalendarItem
} = await import(moduleUrl);

// Case A: Actividad local válida (date=2026-07-22, time=09:30)
const dateA = parseLocalActivityDate({ date: '2026-07-22', time: '09:30' });
assert(dateA instanceof Date);
assert.strictEqual(dateA.getFullYear(), 2026);
assert.strictEqual(dateA.getMonth(), 6);
assert.strictEqual(dateA.getDate(), 22);
assert.strictEqual(dateA.getHours(), 9);
assert.strictEqual(dateA.getMinutes(), 30);
console.log('  [A] Actividad local válida -> Date local 2026-07-22 09:30:00');

// Case B: Actividad con fecha imposible (2026-02-30)
const dateB = parseLocalActivityDate({ date: '2026-02-30', time: '10:00' });
assert.strictEqual(dateB, null);
console.log('  [B] Fecha imposible (2026-02-30) -> null sin excepción');

// Case C: Actividad con hora inválida (25:70)
const dateC = parseLocalActivityDate({ date: '2026-07-22', time: '25:70' });
assert.strictEqual(dateC, null);
console.log('  [C] Hora inválida (25:70) -> null sin excepción');

// Case D: Sesión ISO válida
const sessionD = mapSessionToCalendarItem({
  id: 10,
  scheduled_at: '2026-08-15T14:00:00Z',
  title: 'Tutoría de Cálculo',
  status: 'programada'
});
assert(sessionD);
assert.strictEqual(sessionD.source, 'tutoring_session');
assert.strictEqual(sessionD.isBackend, true);
assert.strictEqual(sessionD.rawId, 10);
console.log('  [D] Sesión ISO válida -> CalendarItem con source=tutoring_session');

// Case E: Diferenciación de IDs sin colisión
const itemActE = mapActivityToCalendarItem({ id: 5, name: 'Tarea 5', date: '2026-07-22', time: '09:00' });
const itemSessE = mapSessionToCalendarItem({ id: 5, scheduled_at: '2026-07-22T09:00:00Z' });
assert(itemActE && itemSessE);
assert.strictEqual(itemActE.id, 'activity:5');
assert.strictEqual(itemSessE.id, 'session:5');
assert.notStrictEqual(itemActE.id, itemSessE.id);
console.log('  [E] IDs sin colisión -> activity:5 !== session:5');

// Case F: Ordenamiento ascendente por startsAt
const actF1 = { id: '1', name: 'Tarde', date: '2026-07-22', time: '16:00' };
const actF2 = { id: '2', name: 'Temprano', date: '2026-07-22', time: '08:00' };
const sessF3 = { id: 3, scheduled_at: '2026-07-22T12:00:00' };

const itemsF = buildCalendarItems([actF1, actF2], [sessF3]);
assert.strictEqual(itemsF.length, 3);
assert.strictEqual(itemsF[0].timeStr, '08:00');
assert.strictEqual(itemsF[1].timeStr, '12:00');
assert.strictEqual(itemsF[2].timeStr, '16:00');
console.log('  [F] Elementos ordenados por startsAt ascendente');

// Case G: Desempate estable por id
const actG1 = { id: 'B', name: 'B', date: '2026-07-22', time: '10:00' };
const actG2 = { id: 'A', name: 'A', date: '2026-07-22', time: '10:00' };
const itemsG = buildCalendarItems([actG1, actG2], []);
assert.strictEqual(itemsG[0].id, 'activity:A');
assert.strictEqual(itemsG[1].id, 'activity:B');
console.log('  [G] Empate en fecha desempata de forma estable por id');

// Case H: Filtro de próximo (upcoming)
const futureItem = mapActivityToCalendarItem({ id: 'fut', date: '2099-01-01', time: '10:00' });
assert(futureItem && isUpcomingCalendarItem(futureItem, new Date(2026, 0, 1)));
console.log('  [H] Elemento futuro clasificado como próximo');

// Case I: Elemento pasado
const pastItem = mapActivityToCalendarItem({ id: 'past', date: '2020-01-01', time: '10:00' });
assert(pastItem && !isUpcomingCalendarItem(pastItem, new Date(2026, 0, 1)));
console.log('  [I] Elemento pasado identificado correctamente');

// Case J: Tolerancia a datos inválidos en buildCalendarItems
const invalidItems = buildCalendarItems([{ id: 'bad', date: 'invalid', time: 'bad' }], []);
assert.strictEqual(invalidItems.length, 0);
console.log('  [J] buildCalendarItems tolera objetos inválidos sin crash');

// Case K: shouldRetainStoredActivity con actividad inválida
assert.strictEqual(shouldRetainStoredActivity({ date: 'invalida', time: 'invalida' }), true);
console.log('  [K] shouldRetainStoredActivity con datos inválidos -> true (se retiene)');

// Case L: shouldRetainStoredActivity con actividad pasada válida
assert.strictEqual(shouldRetainStoredActivity({ date: '2020-01-01', time: '10:00' }, new Date(2026, 0, 1)), false);
console.log('  [L] shouldRetainStoredActivity con actividad pasada válida -> false (se elimina)');

// Case M: shouldRetainStoredActivity con actividad futura válida
assert.strictEqual(shouldRetainStoredActivity({ date: '2099-01-01', time: '10:00' }, new Date(2026, 0, 1)), true);
console.log('  [M] shouldRetainStoredActivity con actividad futura válida -> true (se retiene)');

// Case N: buildCalendarItems excluye elementos inválidos de la vista sin excepción
const mixedItems = buildCalendarItems([
  { id: 'ok', date: '2026-07-22', time: '10:00' },
  { id: 'bad', date: '2026-02-30', time: '10:00' }
], []);
assert.strictEqual(mixedItems.length, 1);
assert.strictEqual(mixedItems[0].id, 'activity:ok');
console.log('  [N] buildCalendarItems excluye actividades inválidas de la vista sin lanzar excepción');

console.log('🎉 Verificación exitosa de la capa de calendario (exit code 0)');
process.exit(0);
