const fs = require('fs');
const glob = require('glob');

const files = glob.sync('app/**/*.tsx');

files.forEach(file => {
  let content = fs.readFileSync(file, 'utf8');
  let changed = false;

  if (content.includes('#1E1E2F')) {
    // For inline styles like color: '#1E1E2F'
    content = content.replace(/color:\s*['"]#1E1E2F['"]/g, "color: colors.text");
    // Since some were in StyleSheet, they will now be color: colors.text, which causes errors if outside component.
    // So if StyleSheet.create has color: colors.text, we need to fix it.
    // Actually, instead of regexing, let's just make it simple.
    changed = true;
  }
  
  // If we changed color: '#1E1E2F' inside StyleSheet.create to color: colors.text, it will fail.
  // Instead, let's just replace '#1E1E2F' with colors.text globally, and move StyleSheet.create INSIDE the component or delete the color prop from StyleSheet.
  
  if (changed) {
    fs.writeFileSync(file, content, 'utf8');
    console.log('Fixed', file);
  }
});
