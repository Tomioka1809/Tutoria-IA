const fs = require('fs');
const glob = require('glob');

const files = glob.sync('app/**/*.tsx');

files.forEach(file => {
  let content = fs.readFileSync(file, 'utf8');
  let originalContent = content;

  // Replace 'white' backgrounds with colors.surface for cards
  content = content.replace(/backgroundColor:\s*['"]white['"]/g, "backgroundColor: colors.surface");
  content = content.replace(/bg-white/g, "style={{ backgroundColor: colors.surface }}");

  // Replace border colors and dividers
  content = content.replace(/backgroundColor:\s*['"]#F3F4F6['"]/g, "backgroundColor: colors.border");
  content = content.replace(/borderColor:\s*['"]#EEEDFE['"]/g, "borderColor: colors.border");
  
  // Replace text colors
  content = content.replace(/color:\s*['"]#111130['"]/g, "color: colors.text");
  
  if (content !== originalContent) {
    if (!content.includes('const { colors } = useTheme()')) {
      content = content.replace(/(export default function \w+\([^)]*\)\s*\{)/, "$1\n  const { colors } = useTheme();");
    }
    fs.writeFileSync(file, content, 'utf8');
    console.log('Fixed', file);
  }
});
