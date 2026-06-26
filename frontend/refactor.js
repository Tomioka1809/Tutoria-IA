const fs = require('fs');
const path = require('path');

const hexMap = {
  '#9A3BEE': 'primary',
  '#F8F7FC': 'background',
  '#EEEDFE': 'border',
  '#26215C': 'text',
  '#7F77DD': 'primary', // Lighter purple mapped to primary for simplicity
  '#8E8EA0': 'textSecondary',
  '#EF4444': 'danger',
  '#22C55E': 'success',
  '#F59E0B': 'warning',
  // '#FFFFFF': 'surface' is tricky, let's only do it for specific cases
};

function processFile(filePath) {
  let content = fs.readFileSync(filePath, 'utf8');
  let original = content;

  // 1. Replace tailwind arbitrary values like bg-[#9A3BEE] with bg-primary
  for (const [hex, name] of Object.entries(hexMap)) {
    const hexUpper = hex.toUpperCase();
    const hexLower = hex.toLowerCase();
    
    // Replace classNames (e.g. bg-[#9A3BEE])
    const classRegex = new RegExp(`(bg|text|border)-\\[(${hexUpper}|${hexLower})\\]`, 'g');
    content = content.replace(classRegex, `$1-${name}`);
  }

  // Also handle white in classNames carefully (only for bg, not text on buttons)
  content = content.replace(/bg-white/g, 'bg-surface');
  content = content.replace(/bg-\[\#FFFFFF\]/gi, 'bg-surface');
  content = content.replace(/bg-\[\#ffffff\]/gi, 'bg-surface');

  // 2. Replace inline styles like backgroundColor: '#F8F7FC' with backgroundColor: colors.background
  let needsUseTheme = false;
  for (const [hex, name] of Object.entries(hexMap)) {
    const hexUpper = hex.toUpperCase();
    const hexLower = hex.toLowerCase();
    
    // Replace inline styles (e.g. color: '#9A3BEE')
    const inlineRegex = new RegExp(`['"](${hexUpper}|${hexLower})['"]`, 'g');
    if (inlineRegex.test(content)) {
        // Need to be careful not to replace it if it's already inside a string or not in a style object
        // Actually, since they are hex codes, it's very safe to just replace them with colors.X
        // BUT only if we also inject useTheme!
        content = content.replace(inlineRegex, `colors.${name}`);
        needsUseTheme = true;
    }
  }

  // Handle white in inline styles specifically for background/border, avoid replacing text colors
  if (content.includes("backgroundColor: 'white'") || content.includes('backgroundColor: "#FFFFFF"')) {
    content = content.replace(/backgroundColor:\s*['"](white|#FFFFFF|#ffffff)['"]/g, 'backgroundColor: colors.surface');
    needsUseTheme = true;
  }

  if (content !== original) {
    // Inject useTheme import if needed and not present
    if (needsUseTheme && !content.includes('useTheme()')) {
      // Find the component declaration to inject `const { colors } = useTheme();`
      // Usually it's `export default function XYZ() {` or `const XYZ = () => {`
      const componentRegex = /(export default function \w+\([^)]*\)\s*\{|const \w+\s*=\s*\([^)]*\)\s*=>\s*\{)/;
      const match = content.match(componentRegex);
      if (match) {
        content = content.replace(match[0], `${match[0]}\n  const { colors } = useTheme();`);
      }

      // Inject import
      if (!content.includes('ThemeContext')) {
        const importStatement = "import { useTheme } from '@/src/theme/ThemeContext';\n";
        // Find last import
        const lastImportIndex = content.lastIndexOf('import ');
        if (lastImportIndex !== -1) {
          const endOfLine = content.indexOf('\n', lastImportIndex);
          content = content.slice(0, endOfLine + 1) + importStatement + content.slice(endOfLine + 1);
        } else {
          content = importStatement + content;
        }
      }
    }
    
    fs.writeFileSync(filePath, content, 'utf8');
    console.log(`Refactored ${filePath}`);
  }
}

function walkDir(dir) {
  const files = fs.readdirSync(dir);
  for (const file of files) {
    const filePath = path.join(dir, file);
    const stat = fs.statSync(filePath);
    if (stat.isDirectory()) {
      walkDir(filePath);
    } else if (filePath.endsWith('.tsx')) {
      processFile(filePath);
    }
  }
}

// Skip auth since it's already refactored
const dirs = [
  'app/(tutor)', 
  'app/(estudiante)', 
  'app/(admin)',
  'src/components'
];

for (const dir of dirs) {
  if (fs.existsSync(dir)) {
    walkDir(dir);
  }
}

console.log('Done refactoring colors.');
