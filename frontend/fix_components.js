const fs = require('fs');
const glob = require('glob');

const files = glob.sync('src/components/**/*.tsx');

files.forEach(file => {
  let content = fs.readFileSync(file, 'utf8');
  let originalContent = content;

  if (content.includes('#1E1E2F') || content.includes('#F5F5FB') || content.includes('#F8F9FA') || content.includes('#111130')) {
    content = content.replace(/'#1E1E2F'/g, "colors.text");
    content = content.replace(/'#111130'/g, "colors.text");
    content = content.replace(/'#F5F5FB'/g, "colors.background");
    content = content.replace(/'#F8F9FA'/g, "colors.surface");
    
    // text colors
    content = content.replace(/className="([^"]*)text-\[#1E1E2F\]([^"]*)"/g, 'style={{ color: colors.text }} className="$1$2"');
    content = content.replace(/className="([^"]*)text-\[#111130\]([^"]*)"/g, 'style={{ color: colors.text }} className="$1$2"');
    
    // bg colors
    content = content.replace(/className="([^"]*)bg-\[#F5F5FB\]([^"]*)"/g, 'style={{ backgroundColor: colors.background }} className="$1$2"');
    content = content.replace(/className="([^"]*)bg-\[#F8F9FA\]([^"]*)"/g, 'style={{ backgroundColor: colors.surface }} className="$1$2"');
  }
  
  if (content !== originalContent) {
    fs.writeFileSync(file, content, 'utf8');
    console.log('Fixed', file);
  }
});
