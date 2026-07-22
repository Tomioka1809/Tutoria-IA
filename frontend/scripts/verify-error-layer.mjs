import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { Buffer } from 'node:buffer';
import ts from 'typescript';
import assert from 'assert';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const frontendDir = path.resolve(__dirname, '..');

function readFile(relativePath) {
  const fullPath = path.join(frontendDir, relativePath);
  return fs.readFileSync(fullPath, 'utf8');
}

console.log('🔍 Iniciando verificación estática y funcional de la capa de errores...');

const apiErrorContent = readFile('src/api/api-error.ts');
const errorFeedbackContent = readFile('src/services/error-feedback.ts');
const sessionStoreContent = readFile('src/store/session.ts');
const chatStoreContent = readFile('src/store/chat.ts');
const notificationStoreContent = readFile('src/store/notification.ts');
const authStoreContent = readFile('src/store/auth.ts');
const streakStoreContent = readFile('src/store/streak.ts');
const useCalendarContent = readFile('src/components/calendar/useCalendar.ts');
const esJsonContent = readFile('src/i18n/locales/es.json');
const enJsonContent = readFile('src/i18n/locales/en.json');

// 1. api-error.ts no importa módulos prohibidos
if (/import.*from.*['"](react|react-native|expo|zustand|i18next|\.\.\/store|\.\.\/components)/i.test(apiErrorContent)) {
  console.error('❌ FAIL 1: api-error.ts importa módulos prohibidos');
  process.exit(1);
}
console.log('✅ PASS 1: api-error.ts es un módulo puro');

// 2. error-feedback.ts utiliza normalizeApiError, Map, 1500ms, notify y errors.close
if (!errorFeedbackContent.includes('normalizeApiError')) {
  console.error('❌ FAIL 2: error-feedback.ts no utiliza normalizeApiError');
  process.exit(1);
}
if (!errorFeedbackContent.includes('Map') || !errorFeedbackContent.includes('1500')) {
  console.error('❌ FAIL: error-feedback.ts no utiliza Map o ventana de 1500 ms');
  process.exit(1);
}
if (!errorFeedbackContent.includes('notify')) {
  console.error('❌ FAIL: error-feedback.ts no admite la opción notify');
  process.exit(1);
}
if (errorFeedbackContent.includes('common.close') || !errorFeedbackContent.includes('errors.close')) {
  console.error('❌ FAIL: error-feedback.ts debe utilizar errors.close (no common.close)');
  process.exit(1);
}
console.log('✅ PASS 2, 3, 4: error-feedback.ts verificado con Map, 1500ms, notify y errors.close');

// 5 & 6. Los 5 stores importan reportApiError y no contienen console.error ni Alert.alert
const stores = [
  { name: 'session.ts', content: sessionStoreContent },
  { name: 'chat.ts', content: chatStoreContent },
  { name: 'notification.ts', content: notificationStoreContent },
  { name: 'auth.ts', content: authStoreContent },
  { name: 'streak.ts', content: streakStoreContent },
];

for (const store of stores) {
  if (!store.content.includes('reportApiError')) {
    console.error(`❌ FAIL 5: ${store.name} no importa o no usa reportApiError`);
    process.exit(1);
  }
  if (store.content.includes('console.error')) {
    console.error(`❌ FAIL 6: ${store.name} contiene console.error`);
    process.exit(1);
  }
  if (store.content.includes('Alert.alert')) {
    console.error(`❌ FAIL 6: ${store.name} contiene Alert.alert directamente`);
    process.exit(1);
  }
}
console.log('✅ PASS 5 & 6: Los 5 stores utilizan reportApiError y no contienen console.error ni Alert.alert');

// Configuración de notify: false en operaciones con consumidor visual
if (!sessionStoreContent.includes('createSession') || !sessionStoreContent.includes('notify: false')) {
  console.error('❌ FAIL: session.ts no configura notify: false para createSession');
  process.exit(1);
}
if (!sessionStoreContent.includes('updateSessionStatus') || !sessionStoreContent.includes('notify: false')) {
  console.error('❌ FAIL: session.ts no configura notify: false para updateSessionStatus');
  process.exit(1);
}
if (!authStoreContent.includes('updateProfile') || !authStoreContent.includes('notify: false')) {
  console.error('❌ FAIL: auth.ts no configura notify: false para updateProfile');
  process.exit(1);
}
if (!authStoreContent.includes('changePassword') || !authStoreContent.includes('notify: false')) {
  console.error('❌ FAIL: auth.ts no configura notify: false para changePassword');
  process.exit(1);
}
console.log('✅ PASS: Configuración notify: false en createSession, updateSessionStatus, updateProfile y changePassword');

// Consumidores intactos
if (!useCalendarContent.includes('alert(')) {
  console.error('❌ FAIL: useCalendar.ts no conserva sus alertas visuales');
  process.exit(1);
}
console.log('✅ PASS: Consumidores verificados intactos');

// Conservan métodos públicos principales
assert(sessionStoreContent.includes('fetchSessions') && sessionStoreContent.includes('createSession') && sessionStoreContent.includes('updateSessionStatus'));
assert(chatStoreContent.includes('fetchConversation') && chatStoreContent.includes('sendMessage') && chatStoreContent.includes('resetConversation'));
assert(notificationStoreContent.includes('fetchNotifications') && notificationStoreContent.includes('markAsRead'));
assert(authStoreContent.includes('updateProfile') && authStoreContent.includes('changePassword'));
assert(streakStoreContent.includes('fetchStreak'));
console.log('✅ PASS 7: Nombres de métodos públicos conservados');

// auth.ts conserva tutoria-auth-storage
if (!authStoreContent.includes('tutoria-auth-storage')) {
  console.error('❌ FAIL 8: auth.ts no conserva tutoria-auth-storage');
  process.exit(1);
}
console.log('✅ PASS 8: auth.ts conserva tutoria-auth-storage');

// chat.ts conserva rollback optimista
if (!chatStoreContent.includes('filter') || !chatStoreContent.includes('tempUserMsg.id')) {
  console.error('❌ FAIL 9: chat.ts no conserva la lógica de rollback optimista');
  process.exit(1);
}
console.log('✅ PASS 9: chat.ts conserva rollback optimista');

// ES y EN contienen nuevas claves y mantienen paridad
const esObj = JSON.parse(esJsonContent);
const enObj = JSON.parse(enJsonContent);

const requiredErrorKeys = [
  'title', 'close', 'network', 'timeout', 'unauthorized', 'forbidden', 'notFound',
  'conflict', 'validation', 'server', 'unknown', 'loadSessions', 'createSession',
  'updateSession', 'loadConversation', 'sendMessage', 'resetConversation',
  'loadNotifications', 'markNotification', 'updateProfile', 'changePassword', 'loadStreak'
];

if (!esObj.errors || !enObj.errors) {
  console.error('❌ FAIL 10: es.json o en.json no poseen sección errors');
  process.exit(1);
}

for (const key of requiredErrorKeys) {
  if (!esObj.errors[key] || !enObj.errors[key]) {
    console.error(`❌ FAIL 10: Clave errors.${key} ausente en es.json o en.json`);
    process.exit(1);
  }
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

const esKeys = getKeyPaths(esObj);
const enKeys = getKeyPaths(enObj);

assert.strictEqual(esKeys.length, enKeys.length, 'Cantidad de claves ES y EN no coincide');
assert.deepStrictEqual(esKeys, enKeys, 'Las claves de es.json y en.json no tienen paridad exacta');
console.log('✅ PASS 10 & 11: Paridad completa ES/EN confirmada');

// PRUEBAS FUNCIONALES DE normalizeApiError (Cases A - S)
console.log('🧪 Ejecutando pruebas funcionales de normalizeApiError...');
const transpileResult = ts.transpileModule(apiErrorContent, {
  compilerOptions: { module: ts.ModuleKind.ESNext, target: ts.ScriptTarget.ES2022 }
});

const moduleUrl = 'data:text/javascript;base64,' + Buffer.from(transpileResult.outputText).toString('base64');
const { normalizeApiError } = await import(moduleUrl);

// Case A: Axios-like sin response
const errA = normalizeApiError({ isAxiosError: true, message: 'Network Error' });
assert.strictEqual(errA.kind, 'network');
assert.strictEqual(errA.retryable, true);
console.log('  [A] Axios sin response -> kind=network, retryable=true');

// Case B: ECONNABORTED (timeout)
const errB = normalizeApiError({ code: 'ECONNABORTED', message: 'timeout of 5000ms exceeded' });
assert.strictEqual(errB.kind, 'timeout');
assert.strictEqual(errB.retryable, true);
console.log('  [B] ECONNABORTED -> kind=timeout, retryable=true');

// Case C: HTTP 401
const errC = normalizeApiError({ response: { status: 401 } });
assert.strictEqual(errC.kind, 'unauthorized');
assert.strictEqual(errC.retryable, false);
console.log('  [C] HTTP 401 -> kind=unauthorized, retryable=false');

// Case D: HTTP 403
const errD = normalizeApiError({ response: { status: 403 } });
assert.strictEqual(errD.kind, 'forbidden');
console.log('  [D] HTTP 403 -> kind=forbidden');

// Case E: HTTP 404
const errE = normalizeApiError({ response: { status: 404 } });
assert.strictEqual(errE.kind, 'not_found');
console.log('  [E] HTTP 404 -> kind=not_found');

// Case F: HTTP 409 con detail
const errF = normalizeApiError({ response: { status: 409, data: { detail: '  Conflicto de  horario  ' } } });
assert.strictEqual(errF.kind, 'conflict');
assert.strictEqual(errF.detail, 'Conflicto de horario');
console.log('  [F] HTTP 409 -> kind=conflict, detail normalizado');

// Case G: HTTP 422 con arreglo detail
const errG = normalizeApiError({
  response: {
    status: 422,
    data: { detail: [{ msg: 'Campo requerido' }, { msg: 'Formato inválido' }] }
  }
});
assert.strictEqual(errG.kind, 'validation');
assert.strictEqual(errG.detail, 'Campo requerido; Formato inválido');
console.log('  [G] HTTP 422 -> kind=validation, msgs unidos');

// Case H: HTTP 500 con detalle interno (must NOT expose detail)
const errH = normalizeApiError({ response: { status: 500, data: { detail: 'Database error trace at line 99' } } });
assert.strictEqual(errH.kind, 'server');
assert.strictEqual(errH.detail, undefined);
console.log('  [H] HTTP 500 -> kind=server, detail suprimido');

// Case I: Error desconocido con fallback
const errI = normalizeApiError(new Error('Unusual failure'), 'errors.loadSessions');
assert.strictEqual(errI.kind, 'unknown');
assert.strictEqual(errI.messageKey, 'errors.loadSessions');
console.log('  [I] Unknown -> kind=unknown, messageKey=fallback');

// Case J: Detail > 240 chars
const longDetail = 'A'.repeat(300);
const errJ = normalizeApiError({ response: { status: 400, data: { detail: longDetail } } });
assert.strictEqual(errJ.detail.length, 240);
console.log('  [J] Detail > 240 chars truncado a 240');

// Case K: HTTP 418 (unrecognized status) con detail
const errK = normalizeApiError({ response: { status: 418, data: { detail: 'detalle interno' } } });
assert.strictEqual(errK.kind, 'unknown');
assert.strictEqual(errK.detail, undefined);
console.log('  [K] HTTP 418 -> kind=unknown, detail suprimido');

// Case L: HTTP 404 con detail
const errL = normalizeApiError({ response: { status: 404, data: { detail: 'recurso no encontrado' } } });
assert.strictEqual(errL.kind, 'not_found');
assert.strictEqual(errL.detail, undefined);
console.log('  [L] HTTP 404 con detail -> kind=not_found, detail suprimido');

// Case M: HTTP 401 con detail
const errM = normalizeApiError({ response: { status: 401, data: { detail: 'invalid token' } } });
assert.strictEqual(errM.kind, 'unauthorized');
assert.strictEqual(errM.detail, undefined);
console.log('  [M] HTTP 401 con detail -> kind=unauthorized, detail suprimido');

// Case N: HTTP 400 con detalle seguro
const errN = normalizeApiError({ response: { status: 400, data: { detail: 'Campo requerido' } } });
assert.strictEqual(errN.kind, 'validation');
assert.strictEqual(errN.detail, 'Campo requerido');
console.log('  [N] HTTP 400 con detalle seguro -> conservado');

// Case O: HTTP 409 con Bearer/JWT
const errO = normalizeApiError({ response: { status: 409, data: { detail: 'Error con Authorization: Bearer eyJhbGci...' } } });
assert.strictEqual(errO.kind, 'conflict');
assert.strictEqual(errO.detail, undefined);
console.log('  [O] HTTP 409 con token/secret -> detail suprimido por seguridad');

// Case P: HTTP 422 con Authorization header
const errP = normalizeApiError({ response: { status: 422, data: { detail: 'invalid Authorization header' } } });
assert.strictEqual(errP.kind, 'validation');
assert.strictEqual(errP.detail, undefined);
console.log('  [P] HTTP 422 con Authorization -> detail suprimido por seguridad');

// Case Q: HTTP 400 con traza de stack
const errQ = normalizeApiError({ response: { status: 400, data: { detail: 'Traceback (most recent call last):\n File "app.py", line 10' } } });
assert.strictEqual(errQ.kind, 'validation');
assert.strictEqual(errQ.detail, undefined);
console.log('  [Q] HTTP 400 con traza -> detail suprimido');

// Case R: HTTP 500 con traza
const errR = normalizeApiError({ response: { status: 500, data: { detail: 'at functionName (file.js:10)' } } });
assert.strictEqual(errR.kind, 'server');
assert.strictEqual(errR.detail, undefined);
console.log('  [R] HTTP 500 con traza -> detail suprimido');

// Case S: Detail de validación superior a 240 caracteres
const errS = normalizeApiError({ response: { status: 400, data: { detail: 'V'.repeat(300) } } });
assert.strictEqual(errS.kind, 'validation');
assert.strictEqual(errS.detail.length, 240);
console.log('  [S] Detail de validación > 240 chars -> truncado a 240');

console.log('🎉 Verificación exitosa de la capa de errores (exit code 0)');
process.exit(0);
