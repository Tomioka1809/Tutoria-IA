const fs = require('fs');

const fixCentroAyuda = (file) => {
  if (!fs.existsSync(file)) return;
  let content = fs.readFileSync(file, 'utf8');
  content = content.replace(/function InfoRow\(\{ label, value \}: \{ label: string; value: string \}\) \{/g, 
    "function InfoRow({ label, value, colors }: { label: string; value: string; colors: any }) {");
  content = content.replace(/<InfoRow label="([^"]+)" value="([^"]+)" \/>/g, '<InfoRow label="$1" value="$2" colors={colors} />');
  fs.writeFileSync(file, content, 'utf8');
  console.log('Fixed', file);
};

const fixEditarPerfil = (file) => {
  if (!fs.existsSync(file)) return;
  let content = fs.readFileSync(file, 'utf8');
  // Instead of using colors.text in StyleSheet, we remove the color prop from StyleSheet and apply it inline!
  // Wait, or we just put it back to '#1E1E2F' and apply it inline.
  content = content.replace(/color: colors\.text,/g, "/* color dynamically applied */");
  content = content.replace(/<Text style=\{styles\.label\}>/g, '<Text style={[styles.label, { color: colors.text }]}>');
  content = content.replace(/<TextInput\s*style=\{styles\.input\}/g, '<TextInput style={[styles.input, { color: colors.text }]}');
  fs.writeFileSync(file, content, 'utf8');
  console.log('Fixed', file);
};

fixCentroAyuda('app/(estudiante)/centro-ayuda.tsx');
fixCentroAyuda('app/(tutor)/centro-ayuda.tsx');
fixEditarPerfil('app/(estudiante)/editar-perfil.tsx');
fixEditarPerfil('app/(tutor)/editar-perfil.tsx');
