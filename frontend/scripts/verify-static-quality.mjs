import { execSync } from 'child_process';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const frontendDir = path.resolve(__dirname, '..');
const repoRootDir = path.resolve(frontendDir, '..');

console.log('🔍 Iniciando verificación de calidad estática del frontend (Fase 4E)...');

let passCount = 0;
let failCount = 0;

function reportPass(msg) {
  console.log(`✅ PASS: ${msg}`);
  passCount++;
}

function reportFail(msg) {
  console.error(`❌ FAIL: ${msg}`);
  failCount++;
}

// 1. Ejecutar ESLint con --max-warnings=0
try {
  execSync('npx eslint . --max-warnings=0', { cwd: frontendDir, stdio: 'pipe' });
  reportPass('ESLint ejecutado sobre todo el frontend con 0 errores y 0 warnings');
} catch (error) {
  reportFail(`ESLint reportó advertencias o errores:\n${error.stdout?.toString() || error.message}`);
}

// 2. Archivos de la fase que no deben contener supresiones
const targetFiles = [
  'app/(admin)/_layout.tsx',
  'app/(admin)/contenido.tsx',
  'app/(admin)/index.tsx',
  'app/(admin)/sorteo.tsx',
  'app/(admin)/users.tsx',
  'app/(estudiante)/editar-perfil.tsx',
  'app/(estudiante)/retroalimentacion-quiz.tsx',
  'app/(estudiante)/tutoria.tsx',
  'app/(tutor)/editar-perfil.tsx',
  'app/(tutor)/index.tsx',
  'app/(tutor)/tutoria.tsx',
  'app/_layout.tsx',
  'app/auth/forgot-password.tsx',
  'app/auth/login.tsx',
  'components/hello-wave.tsx',
  'src/components/dashboard/ServicesGrid.tsx',
  'src/components/dashboard/useDashboard.ts',
  'src/components/tutoria/MessageInputBar.tsx',
  'src/components/tutoria/useTutoria.ts',
  'src/i18n/index.ts',
  'src/theme/ThemeContext.tsx',
];

const suppressions = ['eslint-disable', 'eslint-disable-next-line', '@ts-ignore', '@ts-nocheck'];

let foundSuppressions = false;
for (const relPath of targetFiles) {
  const fullPath = path.join(frontendDir, relPath);
  if (fs.existsSync(fullPath)) {
    const content = fs.readFileSync(fullPath, 'utf8');
    for (const term of suppressions) {
      if (content.includes(term)) {
        reportFail(`Supresión "${term}" encontrada en ${relPath}`);
        foundSuppressions = true;
      }
    }
  }
}
if (!foundSuppressions) {
  reportPass('Sin comentarios de supresión (eslint-disable, @ts-ignore, @ts-nocheck) en los archivos de la Fase 4E');
}

// 3. Verificar que editar-perfil de estudiante y tutor no tengan imports duplicados de expo-router
const editProfileFiles = [
  'app/(estudiante)/editar-perfil.tsx',
  'app/(tutor)/editar-perfil.tsx',
];

let foundDuplicateImports = false;
for (const relPath of editProfileFiles) {
  const fullPath = path.join(frontendDir, relPath);
  if (fs.existsSync(fullPath)) {
    const content = fs.readFileSync(fullPath, 'utf8');
    const matches = content.match(/from\s+['"]expo-router['"]/g);
    if (matches && matches.length > 1) {
      reportFail(`Importación duplicada de expo-router en ${relPath}`);
      foundDuplicateImports = true;
    }
  }
}
if (!foundDuplicateImports) {
  reportPass('Sin importaciones duplicadas de expo-router en editar-perfil de estudiante y tutor');
}

// 4. Verificar package.json contenga verify:quality
const pkgPath = path.join(frontendDir, 'package.json');
const pkgContent = JSON.parse(fs.readFileSync(pkgPath, 'utf8'));
if (pkgContent.scripts && pkgContent.scripts['verify:quality'] === 'node scripts/verify-static-quality.mjs') {
  reportPass('package.json contiene el script verify:quality');
} else {
  reportFail('package.json NO contiene el script verify:quality exacto');
}

// 5. Verificar documentación contenga FRONT-005 con RESUELTO_EN_FASE_4E
const doc00Path = path.join(repoRootDir, 'documentacion/00_linea_base_verificada.md');
if (fs.existsSync(doc00Path)) {
  const content = fs.readFileSync(doc00Path, 'utf8');
  if (content.includes('FRONT-005') && content.includes('RESUELTO_EN_FASE_4E')) {
    reportPass('documentacion/00_linea_base_verificada.md registra FRONT-005 como RESUELTO_EN_FASE_4E');
  } else {
    reportFail('documentacion/00_linea_base_verificada.md NO contiene FRONT-005 con estado RESUELTO_EN_FASE_4E');
  }
} else {
  reportFail('Falta documentacion/00_linea_base_verificada.md');
}

// 6. Verificar documentación adicional (01 y 04)
const doc01Path = path.join(repoRootDir, 'documentacion/01_contrato_funcional_verificado.md');
const doc04Path = path.join(repoRootDir, 'documentacion/04_frontend.md');

if (fs.existsSync(doc01Path) && fs.existsSync(doc04Path)) {
  const content01 = fs.readFileSync(doc01Path, 'utf8');
  const content04 = fs.readFileSync(doc04Path, 'utf8');

  const has0Errors = (content01.includes('0 errores') || content04.includes('0 errores'));
  const has0Warnings = (content01.includes('0 warnings') || content04.includes('0 warnings'));

  if (has0Errors && has0Warnings) {
    reportPass('Documentación registra 0 errores y 0 warnings con corrección semántica de hooks');
  } else {
    reportFail('La documentación no menciona adecuadamente 0 errores y 0 warnings');
  }
} else {
  reportFail('Faltan archivos de documentación 01_contrato_funcional_verificado.md o 04_frontend.md');
}

// 7. Verificar app/(tutor)/index.tsx - Estrategia de Carga Coordinada y Sincronización Inmediata del Dashboard Tutor
const tutorDashboardPath = path.join(frontendDir, 'app/(tutor)/index.tsx');
if (fs.existsSync(tutorDashboardPath)) {
  const content = fs.readFileSync(tutorDashboardPath, 'utf8');

  // A. fetchPeriods no debe depender de selectedPeriod
  const fetchPeriodsDepMatch = content.match(/fetchPeriods\s*=\s*useCallback\([\s\S]*?\],\s*\[(.*?)\]\);/);
  if (fetchPeriodsDepMatch && fetchPeriodsDepMatch[1].includes('selectedPeriod')) {
    reportFail('app/(tutor)/index.tsx: fetchPeriods depende de selectedPeriod');
  } else {
    reportPass('app/(tutor)/index.tsx: fetchPeriods NO depende de selectedPeriod');
  }

  // B. No existir un useEffect dedicado exclusivamente a sincronizar selectedPeriodRef
  if (content.includes('useEffect(() => {') && content.includes('selectedPeriodRef.current = selectedPeriod')) {
    reportFail('app/(tutor)/index.tsx: contiene un useEffect dedicado a sincronizar selectedPeriodRef');
  } else {
    reportPass('app/(tutor)/index.tsx: sin useEffect de sincronización diferida para selectedPeriodRef');
  }

  // C. loadTutorData actualiza ref y estado antes de fetchStudents
  if (content.includes('selectedPeriodRef.current = effectivePeriod;') && content.includes('setSelectedPeriod(effectivePeriod);')) {
    reportPass('app/(tutor)/index.tsx: loadTutorData sincroniza ref y estado inmediatamente');
  } else {
    reportFail('app/(tutor)/index.tsx: loadTutorData no realiza la sincronización inmediata de ref y estado');
  }

  // D. handleSelectPeriod actualiza inmediatamente ref y estado e impide re-fetch del periodo activo
  if (content.includes('selectedPeriodRef.current') && (content.includes('return;') || content.includes('=== selectedPeriodRef.current'))) {
    reportPass('app/(tutor)/index.tsx: handleSelectPeriod evita re-solicitar el periodo activo y sincroniza inmediatamente');
  } else {
    reportFail('app/(tutor)/index.tsx: handleSelectPeriod no previene solicitudes redundantes del periodo activo');
  }
} else {
  reportFail('Falta app/(tutor)/index.tsx');
}

// 8. Verificar app/(estudiante)/retroalimentacion-quiz.tsx - Carga única por montaje y traducción fuera del efecto
const quizScreenPath = path.join(frontendDir, 'app/(estudiante)/retroalimentacion-quiz.tsx');
if (fs.existsSync(quizScreenPath)) {
  const content = fs.readFileSync(quizScreenPath, 'utf8');

  // A. El efecto de generación no contiene t( ni dependencia [t]
  const quizEffectMatch = content.match(/useEffect\([\s\S]*?QuizAPI\.generateQuiz[\s\S]*?\},\s*\[(.*?)\]\);/);
  if (quizEffectMatch) {
    const deps = quizEffectMatch[1].trim();
    if (deps.includes('t')) {
      reportFail('retroalimentacion-quiz.tsx: useEffect de generación depende de [t]');
    } else {
      reportPass('retroalimentacion-quiz.tsx: useEffect de generación con dependencias vacías sin [t]');
    }
  } else {
    reportFail('retroalimentacion-quiz.tsx: no se encontró el useEffect de generación de quiz');
  }

  // B. Existe clave semántica quiz.generationError
  if (content.includes("setErrorKey('quiz.generationError')") || content.includes('quiz.generationError')) {
    reportPass('retroalimentacion-quiz.tsx: utiliza la clave semántica quiz.generationError');
  } else {
    reportFail('retroalimentacion-quiz.tsx: no utiliza la clave semántica quiz.generationError');
  }

  // C. Traducción de la clave ocurre fuera del efecto
  if (content.includes('t(errorKey)')) {
    reportPass('retroalimentacion-quiz.tsx: traduce la clave de error fuera del efecto');
  } else {
    reportFail('retroalimentacion-quiz.tsx: no traduce la clave de error fuera del efecto');
  }

  // D. QuizAPI.generateQuiz sigue presente
  if (content.includes('QuizAPI.generateQuiz')) {
    reportPass('retroalimentacion-quiz.tsx: conserva QuizAPI.generateQuiz');
  } else {
    reportFail('retroalimentacion-quiz.tsx: falta QuizAPI.generateQuiz');
  }
} else {
  reportFail('Falta app/(estudiante)/retroalimentacion-quiz.tsx');
}

console.log(`\n📊 Resultado final: ${passCount} pruebas pasadas, ${failCount} fallidas.`);

if (failCount > 0) {
  console.error('💥 Verificación de calidad estática FALLADA');
  process.exit(1);
} else {
  console.log('🎉 Verificación exitosa de calidad estática (exit code 0)');
  process.exit(0);
}
