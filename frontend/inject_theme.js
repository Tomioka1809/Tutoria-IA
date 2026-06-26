const fs = require('fs');

const filesToFix = [
  'src/components/profile/ProfileMenu.tsx',
  'src/components/profile/ProfileHeader.tsx',
  'src/components/profile/AssignedTutorCard.tsx',
  'src/components/notifications/NotificationsList.tsx',
  'src/components/dashboard/DashboardHeader.tsx',
  'src/components/dashboard/StreakCard.tsx',
  'src/components/tutoria/TutoriaTabBarButton.tsx',
  'src/components/tutoria/MessageInputBar.tsx',
  'src/components/calendar/ScheduleSessionModal.tsx'
];

for (const filePath of filesToFix) {
  let content = fs.readFileSync(filePath, 'utf8');
  
  // Need to find the component signature and inject `const { colors } = useTheme();`
  // We can look for `export function ... {` or `export const ... = ... => {` or `const ... = ... => {`
  const regex = /(export\s+function\s+\w+\s*\([^)]*\)\s*\{|export\s+const\s+\w+\s*=\s*\([^)]*\)\s*=>\s*\{|const\s+\w+\s*=\s*\([^)]*\)\s*=>\s*\{|function\s+\w+\s*\([^)]*\)\s*\{)/;
  
  const match = content.match(regex);
  if (match) {
    // Check if it already has useTheme, if not inject it
    if (!content.includes('const { colors } = useTheme();')) {
      content = content.replace(match[0], `${match[0]}\n  const { colors } = useTheme();`);
    }
    
    // Check if useTheme is imported
    if (!content.includes("import { useTheme } from '@/src/theme/ThemeContext';") && !content.includes("import { useTheme }")) {
      const importStatement = "import { useTheme } from '@/src/theme/ThemeContext';\n";
      const lastImportIndex = content.lastIndexOf('import ');
      if (lastImportIndex !== -1) {
        const endOfLine = content.indexOf('\n', lastImportIndex);
        content = content.slice(0, endOfLine + 1) + importStatement + content.slice(endOfLine + 1);
      } else {
        content = importStatement + content;
      }
    }
    
    fs.writeFileSync(filePath, content, 'utf8');
    console.log(`Injected useTheme into ${filePath}`);
  } else {
    console.log(`Could not find component signature in ${filePath}`);
  }
}
