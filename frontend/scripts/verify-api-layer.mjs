import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { Buffer } from 'node:buffer';
import { execSync } from 'child_process';
import ts from 'typescript';
import assert from 'assert';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const frontendDir = path.resolve(__dirname, '..');
const projectRootDir = path.resolve(frontendDir, '..');

function readFile(relativePath) {
  const fullPath = path.join(frontendDir, relativePath);
  return fs.readFileSync(fullPath, 'utf8');
}

console.log('🔍 Iniciando verificación estática y funcional de la capa API...');

// Check if frontend/.env is ignored by Git
try {
  const gitCheck = execSync('git check-ignore -v frontend/.env', { cwd: projectRootDir, encoding: 'utf8' });
  if (!gitCheck || gitCheck.trim() === '') {
    console.error('❌ FAIL: frontend/.env no está ignorado por Git.');
    process.exit(1);
  }
  console.log('✅ PASS: frontend/.env está correctamente ignorado por Git');
} catch (error) {
  console.error('❌ FAIL: Falló la verificación de git check-ignore para frontend/.env', error);
  process.exit(1);
}

const clientContent = readFile('src/api/client.ts');
const servicesContent = readFile('src/api/services.ts');
const apiConfigContent = readFile('src/api/api-config.ts');
const authSessionContent = readFile('src/api/auth-session.ts');
const authStoreContent = readFile('src/store/auth.ts');
const envExampleContent = readFile('.env.example');

// 1 & 14. Detección de IPs privadas en src/api
const privateIpRegex = /\b(192\.168\.\d+\.\d+|10\.\d+\.\d+\.\d+|172\.(1[6-9]|2\d|3[01])\.\d+\.\d+)\b/;
if (privateIpRegex.test(clientContent) || privateIpRegex.test(servicesContent) || privateIpRegex.test(apiConfigContent) || privateIpRegex.test(authSessionContent)) {
  console.error('❌ FAIL 1 & 14: Se detectaron IPs privadas hardcodeadas en frontend/src/api');
  process.exit(1);
}
console.log('✅ PASS 1 & 14: Sin IPs privadas hardcodeadas en src/api');

// 2 & 3. No require() en client.ts y services.ts
if (/\brequire\s*\(/.test(clientContent)) {
  console.error('❌ FAIL 2: client.ts contiene require()');
  process.exit(1);
}
if (/\brequire\s*\(/.test(servicesContent)) {
  console.error('❌ FAIL 3: services.ts contiene require()');
  process.exit(1);
}
console.log('✅ PASS 2 & 3: Sin require() dinámico en client.ts y services.ts');

// 4. No fetch() en services.ts
if (/\bfetch\s*\(/.test(servicesContent)) {
  console.error('❌ FAIL 4: services.ts contiene fetch()');
  process.exit(1);
}
console.log('✅ PASS 4: Sin fetch() directo en services.ts');

// 5 & 6. services.ts usa client.get y conserva /quiz/generate
if (!servicesContent.includes('client.get') || !servicesContent.includes("'/quiz/generate'")) {
  console.error('❌ FAIL 5 & 6: services.ts no utiliza client.get o no conserva /quiz/generate');
  process.exit(1);
}
console.log('✅ PASS 5 & 6: QuizAPI utiliza client.get para /quiz/generate');

// 7 & 8. client.ts utiliza EXPO_PUBLIC_API_URL y hostUri
if (!clientContent.includes('EXPO_PUBLIC_API_URL') || !clientContent.includes('hostUri')) {
  console.error('❌ FAIL 7 & 8: client.ts no utiliza EXPO_PUBLIC_API_URL o hostUri');
  process.exit(1);
}
console.log('✅ PASS 7 & 8: client.ts configura URL con EXPO_PUBLIC_API_URL y hostUri');

// 9 & 10. Control de status 401 vs 403
if (clientContent.includes('403') && clientContent.includes('status === 403')) {
  console.error('❌ FAIL 9: client.ts trata 403 como motivo de logout');
  process.exit(1);
}
if (!clientContent.includes('401')) {
  console.error('❌ FAIL 10: client.ts no maneja 401 para desautorización');
  process.exit(1);
}
console.log('✅ PASS 9 & 10: client.ts maneja 401 únicamente (no 403)');

// 11. auth-session.ts no importa auth.ts ni client.ts
if (authSessionContent.includes('store/auth') || authSessionContent.includes('api/client')) {
  console.error('❌ FAIL 11: auth-session.ts importa auth.ts o client.ts');
  process.exit(1);
}
console.log('✅ PASS 11: auth-session.ts no posee dependencias circulares');

// 12. auth.ts registra configureApiAuth
if (!authStoreContent.includes('configureApiAuth')) {
  console.error('❌ FAIL 12: auth.ts no registra configureApiAuth');
  process.exit(1);
}
console.log('✅ PASS 12: auth.ts registra callbacks en configureApiAuth');

// 13. api-config.ts no importa Expo, React Native, Axios o Zustand
if (/import.*from.*['"](expo|react-native|axios|zustand)/i.test(apiConfigContent)) {
  console.error('❌ FAIL 13: api-config.ts importa módulos prohibidos');
  process.exit(1);
}
console.log('✅ PASS 13: api-config.ts es un módulo puro');

// 15. .env.example documenta EXPO_PUBLIC_API_URL
if (!envExampleContent.includes('EXPO_PUBLIC_API_URL')) {
  console.error('❌ FAIL 15: .env.example no documenta EXPO_PUBLIC_API_URL');
  process.exit(1);
}
console.log('✅ PASS 15: .env.example documenta EXPO_PUBLIC_API_URL');

// Prueba funcional de resolveApiUrl mediante transpilación TypeScript
console.log('🧪 Ejecutando pruebas funcionales de resolveApiUrl...');
const transpileResult = ts.transpileModule(apiConfigContent, {
  compilerOptions: { module: ts.ModuleKind.ESNext, target: ts.ScriptTarget.ES2022 }
});

const moduleUrl = 'data:text/javascript;base64,' + Buffer.from(transpileResult.outputText).toString('base64');
const { resolveApiUrl } = await import(moduleUrl);

// Test A: Priority
const resA = resolveApiUrl({ envUrl: 'https://api.ejemplo.edu/api/v1/' });
assert.strictEqual(resA, 'https://api.ejemplo.edu/api/v1');
console.log('  [A] Priority envUrl:', resA);

// Test B: Expo Detection
const resB = resolveApiUrl({ expoHostUri: '192.168.1.20:8081' });
assert.strictEqual(resB, 'http://192.168.1.20:8000/api/v1');
console.log('  [B] Expo hostUri:', resB);

// Test C: Expo Scheme
const resC = resolveApiUrl({ expoHostUri: 'exp://10.0.0.8:8081' });
assert.strictEqual(resC, 'http://10.0.0.8:8000/api/v1');
console.log('  [C] Expo scheme hostUri:', resC);

// Test D: Fallback
const resD = resolveApiUrl({});
assert.strictEqual(resD, 'http://localhost:8000/api/v1');
console.log('  [D] Fallback:', resD);

// Test E: HTTPS valid with trailing slash
const resE = resolveApiUrl({ envUrl: 'https://api.ejemplo.edu/api/v1/' });
assert.strictEqual(resE, 'https://api.ejemplo.edu/api/v1');
console.log('  [E] Valid HTTPS with trailing slash:', resE);

// Test F: HTTP valid
const resF = resolveApiUrl({ envUrl: 'http://localhost:8000/api/v1' });
assert.strictEqual(resF, 'http://localhost:8000/api/v1');
console.log('  [F] Valid HTTP:', resF);

// Test G: FTP protocol (must throw Error)
assert.throws(() => {
  resolveApiUrl({ envUrl: 'ftp://servidor/api/v1' });
}, /Must start with 'http:\/\/' or 'https:\/\/'/);
console.log('  [G] FTP protocol throws Error as expected');

// Test H: Without protocol (must throw Error)
assert.throws(() => {
  resolveApiUrl({ envUrl: 'servidor:8000/api/v1' });
}, /Must start with 'http:\/\/' or 'https:\/\/'/);
console.log('  [H] Missing protocol throws Error as expected');

// Test I: HTTP URL without hostname (must throw Error)
assert.throws(() => {
  resolveApiUrl({ envUrl: 'http://' });
}, /Missing valid hostname/);
console.log('  [I] Missing hostname throws Error as expected');

// Test J: Value with whitespace
const resJ = resolveApiUrl({ envUrl: '  https://api.ejemplo.edu/api/v1/  ' });
assert.strictEqual(resJ, 'https://api.ejemplo.edu/api/v1');
console.log('  [J] Value with whitespace normalized:', resJ);

console.log('🎉 Verificación exitosa de la capa API (exit code 0)');
process.exit(0);
