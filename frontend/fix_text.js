const fs = require('fs');

const fixFile = (file) => {
  if (!fs.existsSync(file)) return;
  let content = fs.readFileSync(file, 'utf8');

  // We want to remove text-text and replace with style={{ color: colors.text }}
  // But wait, MessagesList uses it in a variable: const textColor = isUser ? 'text-white' : 'text-text font-medium';
  if (file.includes('MessagesList.tsx')) {
    content = content.replace(/const textColor = isUser \? 'text-white' : 'text-text font-medium';/,
      "const textColor = isUser ? 'text-white' : 'font-medium';\n  const inlineTextColor = isUser ? '#FFFFFF' : colors.text;");
    content = content.replace(/<Text key=\{pIndex\} className=\{\`text-sm leading-5 mb-1 \$\{textColor\}\`\}>/, 
      "<Text key={pIndex} className={`text-sm leading-5 mb-1 ${textColor}`} style={{ color: inlineTextColor }}>");
  }
  
  if (file.includes('MessageInputBar.tsx')) {
    // text-text is in the TextInput className
    content = content.replace(/style=\{\{ backgroundColor: colors\.background \}\} className="flex-1  rounded-3xl px-5 py-3 text-sm text-text mr-3 font-semibold min-h-\[44px\] max-h-\[120px\]"/,
      'style={{ backgroundColor: colors.background, color: colors.text }} className="flex-1 rounded-3xl px-5 py-3 text-sm mr-3 font-semibold min-h-[44px] max-h-[120px]"');
  }

  if (file.includes('QuickActionsPanel.tsx')) {
    content = content.replace(/text-text/g, '');
    content = content.replace(/<Text className="text-xs  font-semibold"/g, '<Text className="text-xs font-semibold" style={{ color: colors.text }}');
  }

  if (file.includes('TutoriaHeader.tsx')) {
    content = content.replace(/<Text className="text-xl text-text">←<\/Text>/, '<Text className="text-xl" style={{ color: colors.text }}>←</Text>');
    content = content.replace(/<Text className="text-lg text-text">↻<\/Text>/, '<Text className="text-lg" style={{ color: colors.text }}>↻</Text>');
  }

  fs.writeFileSync(file, content, 'utf8');
};

fixFile('src/components/tutoria/MessagesList.tsx');
fixFile('src/components/tutoria/MessageInputBar.tsx');
fixFile('src/components/tutoria/QuickActionsPanel.tsx');
fixFile('src/components/tutoria/TutoriaHeader.tsx');
console.log('Fixed chat components text colors');
