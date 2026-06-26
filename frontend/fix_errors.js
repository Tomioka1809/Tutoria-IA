const fs = require('fs');

const missingColorsFiles = [
  'app/(estudiante)/editar-perfil.tsx',
  'app/(tutor)/editar-perfil.tsx',
  'app/_layout.tsx',
  'app/modal.tsx',
  'src/components/calendar/CalendarHeader.tsx',
  'src/components/calendar/CalendarMonthView.tsx',
  'src/components/dashboard/ServicesGrid.tsx',
  'src/components/notifications/NotificationItem.tsx',
  'src/components/notifications/NotificationsHeader.tsx',
  'src/components/tutoria/QuickActionsPanel.tsx',
  'src/components/tutoria/TutoriaHeader.tsx'
];

missingColorsFiles.forEach(file => {
  if (!fs.existsSync(file)) return;
  let content = fs.readFileSync(file, 'utf8');
  
  if (!content.includes('import { useTheme }')) {
    content = content.replace(/(import React.*)/, "$1\nimport { useTheme } from '@/src/theme/ThemeContext';");
  }
  
  // Need to inject const { colors } = useTheme(); into components
  // Sometimes it's export function, sometimes export default function
  if (!content.includes('const { colors } = useTheme()')) {
    content = content.replace(/(export (?:default )?function \w+\([^)]*\)\s*\{)/, "$1\n  const { colors } = useTheme();");
    content = content.replace(/(export const \w+\s*=\s*\([^)]*\)\s*=>\s*\{)/, "$1\n  const { colors } = useTheme();");
  }
  
  fs.writeFileSync(file, content, 'utf8');
});

// Fix duplicated styles in specific files
const fixDuplicateStyle = (file) => {
  if (!fs.existsSync(file)) return;
  let content = fs.readFileSync(file, 'utf8');
  
  // app/(tutor)/tutoria.tsx and app/(estudiante)/tutoria.tsx
  if (file.includes('tutoria.tsx') && content.includes('style={{ backgroundColor: colors.surface }} className="flex-1 "')) {
    content = content.replace(
      /style=\{\{ backgroundColor: colors\.surface \}\} className="flex-1 "\s*style=\{\{([\s\S]*?)\}\}/,
      'className="flex-1"\n      style={{\n        backgroundColor: colors.surface,$1}}'
    );
  }
  
  // AddActivityModal.tsx
  if (file.includes('AddActivityModal.tsx')) {
    content = content.replace(/style=\{\{ color: colors\.text \}\} style=\{\{ backgroundColor: colors\.surface \}\}/g, 
      'style={{ color: colors.text, backgroundColor: colors.surface }}');
  }

  fs.writeFileSync(file, content, 'utf8');
}

fixDuplicateStyle('app/(tutor)/tutoria.tsx');
fixDuplicateStyle('app/(estudiante)/tutoria.tsx');
fixDuplicateStyle('src/components/calendar/AddActivityModal.tsx');

console.log('Fixed errors!');
