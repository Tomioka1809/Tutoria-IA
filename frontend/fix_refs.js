const fs = require('fs');
const path = require('path');

function replaceInFile(filePath, replacements) {
    if (!fs.existsSync(filePath)) return;
    let content = fs.readFileSync(filePath, 'utf8');
    for (const [search, replace] of replacements) {
        content = content.replace(search, replace);
    }
    fs.writeFileSync(filePath, content, 'utf8');
    console.log(`Fixed ${filePath}`);
}

// 1. Fix centro-ayuda.tsx
const centroAyudaReplacements = [
    [/const PURPLE = colors\.primary;/g, "const PURPLE = '#9A3BEE';"],
    [/color: colors\.textSecondary/g, "color: '#8E8EA0'"]
];
replaceInFile('app/(estudiante)/centro-ayuda.tsx', centroAyudaReplacements);
replaceInFile('app/(tutor)/centro-ayuda.tsx', centroAyudaReplacements);

// 2. Fix perfil-tutor.tsx
const perfilTutorReplacements = [
    [/const PURPLE = colors\.primary;/g, "const PURPLE = '#9A3BEE';"],
    [/color: colors\.textSecondary/g, "color: '#8E8EA0'"],
    [/backgroundColor: colors\.surface/g, "backgroundColor: 'white'"],
    [/borderColor: colors\.border/g, "borderColor: '#EEEDFE'"]
];
replaceInFile('app/(estudiante)/perfil-tutor.tsx', perfilTutorReplacements);
replaceInFile('app/(tutor)/perfil-tutor.tsx', perfilTutorReplacements);

// 3. Fix editar-perfil.tsx
const editarPerfilReplacements = [
    [/backgroundColor: colors\.surface/g, "backgroundColor: 'white'"],
    [/borderColor: colors\.border/g, "borderColor: '#EEEDFE'"]
];
replaceInFile('app/(estudiante)/editar-perfil.tsx', editarPerfilReplacements);
replaceInFile('app/(tutor)/editar-perfil.tsx', editarPerfilReplacements);

console.log('All reference errors fixed.');
