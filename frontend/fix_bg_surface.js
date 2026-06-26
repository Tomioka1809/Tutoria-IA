const fs = require('fs');
const glob = require('glob');

const files = glob.sync('{src/components/**/*.tsx,app/**/*.tsx}');

files.forEach(file => {
  let content = fs.readFileSync(file, 'utf8');
  let originalContent = content;

  // Replace bg-surface in className with a style prop, assuming there's no existing style prop
  // This might be tricky if there is already a style prop, but let's try.
  // First, we replace `className="...bg-surface..."` to include `style={{ backgroundColor: colors.surface }}` 
  // ONLY if the line doesn't already have `style={{`.
  
  const lines = content.split('\n');
  for (let i = 0; i < lines.length; i++) {
    if (lines[i].includes('bg-surface') && !lines[i].includes('style=')) {
      lines[i] = lines[i].replace(/className="([^"]*)\bbg-surface\b([^"]*)"/g, 'style={{ backgroundColor: colors.surface }} className="$1$2"');
    }
  }
  content = lines.join('\n');
  
  if (content !== originalContent) {
    if (!content.includes('const { colors } = useTheme()') && !content.includes('colors.')) {
      // We might need useTheme, but most components already have it from earlier.
    }
    fs.writeFileSync(file, content, 'utf8');
    console.log('Fixed', file);
  }
});
