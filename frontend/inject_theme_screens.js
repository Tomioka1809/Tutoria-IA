const fs = require('fs');
const glob = require('glob');

const files = glob.sync('app/**/*.tsx');

files.forEach(file => {
  let content = fs.readFileSync(file, 'utf8');
  let originalContent = content;

  // Add useTheme import if not exists
  if (content.includes('export default function') && !content.includes('import { useTheme } from')) {
    content = content.replace(/(import React.*)/, "$1\nimport { useTheme } from '@/src/theme/ThemeContext';");
  }

  // Add const { colors } = useTheme(); to export default function
  if (content.includes('export default function') && !content.includes('const { colors } = useTheme()')) {
    content = content.replace(/(export default function \w+\([^)]*\)\s*\{)/, "$1\n  const { colors } = useTheme();");
  }

  // Replace bg-[#F5F5FB] and bg-[#F8F9FA] with colors.background
  content = content.replace(/className="([^"]*)bg-\[#F5F5FB\]([^"]*)"/g, "style={{ backgroundColor: colors.background }} className=\"$1$2\"");
  content = content.replace(/className="([^"]*)bg-\[#F8F9FA\]([^"]*)"/g, "style={{ backgroundColor: colors.background }} className=\"$1$2\"");

  // Replace text-[#1E1E2F] and text-[#111130] with colors.text
  content = content.replace(/className="([^"]*)text-\[#1E1E2F\]([^"]*)"/g, "style={{ color: colors.text }} className=\"$1$2\"");
  content = content.replace(/className="([^"]*)text-\[#111130\]([^"]*)"/g, "style={{ color: colors.text }} className=\"$1$2\"");

  // Specific case for tutor profile text inside black/white styles
  content = content.replace(/text-black/g, "text-text");

  if (content !== originalContent) {
    fs.writeFileSync(file, content, 'utf8');
    console.log('Updated', file);
  }
});
