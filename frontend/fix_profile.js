const fs = require('fs');

const files = [
  'app/(tutor)/perfil-tutor.tsx',
  'app/(estudiante)/perfil-tutor.tsx',
  'app/(tutor)/configuracion.tsx',
  'app/(estudiante)/configuracion.tsx',
  'app/(tutor)/editar-perfil.tsx',
  'app/(estudiante)/editar-perfil.tsx'
];

files.forEach(file => {
  if (!fs.existsSync(file)) return;
  let content = fs.readFileSync(file, 'utf8');
  let changed = false;

  if (content.includes('#1E1E2F') || content.includes('#F5F5FB') || content.includes('#F8F9FA')) {
    content = content.replace(/'#1E1E2F'/g, "colors.text");
    content = content.replace(/'#F5F5FB'/g, "colors.background");
    content = content.replace(/'#F8F9FA'/g, "colors.surface");
    changed = true;
  }
  
  // also fix <Text className="text-[#1E1E2F]..."> to style={{ color: colors.text }}
  content = content.replace(/className="([^"]*)text-\[#1E1E2F\]([^"]*)"/g, 'style={{ color: colors.text }} className="$1$2"');
  
  if (changed) {
    if (!content.includes('const { colors } = useTheme()')) {
      content = content.replace(/(export default function \w+\([^)]*\)\s*\{)/, "$1\n  const { colors } = useTheme();");
    }
    fs.writeFileSync(file, content, 'utf8');
    console.log('Fixed', file);
  }
});
