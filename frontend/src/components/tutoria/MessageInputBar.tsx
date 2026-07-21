// src/components/tutoria/MessageInputBar.tsx
import React, { useState, useRef, useEffect } from 'react';
import { View, TextInput, Pressable, Text, Keyboard } from 'react-native';
import { useTheme } from '@/src/theme/ThemeContext';
import { useTranslation } from 'react-i18next';

interface MessageInputBarProps {
  inputText: string;
  setInputText: (text: string) => void;
  onSend: (text: string) => void;
  onMicPress?: () => void;
  isSending: boolean;
  inputRef?: React.RefObject<TextInput | null>;
}

export function MessageInputBar({
  inputText,
  setInputText,
  onSend,
  isSending,
  inputRef,
}: MessageInputBarProps) {
  const { colors } = useTheme();
  const { t } = useTranslation();
  const isTextEmpty = !inputText.trim();

  return (
    <View style={{ backgroundColor: colors.surface }} className=" px-4 pt-3 pb-6 border-t border-border flex-row items-end">
      <TextInput
        ref={inputRef}
        value={inputText}
        onChangeText={setInputText}
        placeholder={t('tutoring.inputPlaceholder')}
        multiline={true}
        style={{ backgroundColor: colors.background, color: colors.text }} className="flex-1 rounded-3xl px-5 py-3 text-sm mr-3 font-semibold min-h-[44px] max-h-[120px]"
        placeholderTextColor={colors.textSecondary}
      />

      <Pressable
        onPress={() => onSend(inputText)}
        disabled={isSending || isTextEmpty}
        className={`w-11 h-11 rounded-full items-center justify-center shadow-md mb-1 ${
          isTextEmpty || isSending ? 'bg-[#D1D1E0]' : 'bg-primary shadow-[#9A3BEE]/35'
        }`}
      >
        <Text className="text-white font-bold text-base">➔</Text>
      </Pressable>
    </View>
  );
}
