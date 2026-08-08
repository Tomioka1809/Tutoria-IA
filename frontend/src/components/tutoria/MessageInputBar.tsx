// src/components/tutoria/MessageInputBar.tsx
import React from 'react';
import { View, TextInput, Pressable, Text } from 'react-native';
import Feather from '@expo/vector-icons/Feather';
import { useTheme } from '@/src/theme/ThemeContext';
import { useTranslation } from 'react-i18next';

interface MessageInputBarProps {
  inputText: string;
  setInputText: (text: string) => void;
  onSend: (text: string) => void;
  onMicPress?: () => void;
  isSending: boolean;
  inputRef?: React.RefObject<TextInput | null>;
  /** Activo mientras se edita un mensaje ya enviado. */
  isEditing?: boolean;
  onCancelEdit?: () => void;
}

export function MessageInputBar({
  inputText,
  setInputText,
  onSend,
  isSending,
  inputRef,
  isEditing = false,
  onCancelEdit,
}: MessageInputBarProps) {
  const { colors } = useTheme();
  const { t } = useTranslation();
  const isTextEmpty = !inputText.trim();

  return (
    <View style={{ backgroundColor: colors.surface }} className="border-t border-border">
      {/* La barra de edicion avisa que al guardar se pierde lo que vino
          despues. Es una accion destructiva y el usuario tiene que saberlo
          antes de tocar el boton, no despues. */}
      {isEditing ? (
        <View
          className="px-4 pt-3 pb-2 flex-row items-start"
          style={{ backgroundColor: colors.background }}
        >
          <View className="w-1 self-stretch rounded-full mr-3" style={{ backgroundColor: colors.primary }} />
          <View className="flex-1">
            <Text className="text-xs font-bold" style={{ color: colors.primary }}>
              {t('tutoring.editingMessage')}
            </Text>
            <Text className="text-[11px] mt-0.5" style={{ color: colors.textSecondary }}>
              {t('tutoring.editWarningBody')}
            </Text>
          </View>
          <Pressable
            onPress={onCancelEdit}
            hitSlop={10}
            accessibilityRole="button"
            accessibilityLabel={t('tutoring.cancelEdit')}
            className="w-7 h-7 rounded-full items-center justify-center ml-2"
            style={{ backgroundColor: colors.surface }}
          >
            <Feather name="x" size={16} color={colors.textSecondary} />
          </Pressable>
        </View>
      ) : null}

      <View className="px-4 pt-3 pb-6 flex-row items-end">
        <TextInput
          ref={inputRef}
          value={inputText}
          onChangeText={setInputText}
          placeholder={t('tutoring.inputPlaceholder')}
          multiline={true}
          style={{
            backgroundColor: colors.background,
            color: colors.text,
            borderColor: isEditing ? colors.primary : 'transparent',
            borderWidth: isEditing ? 1 : 0,
          }}
          className="flex-1 rounded-3xl px-5 py-3 text-sm mr-3 font-semibold min-h-[44px] max-h-[120px]"
          placeholderTextColor={colors.textSecondary}
        />

        <Pressable
          onPress={() => onSend(inputText)}
          disabled={isSending || isTextEmpty}
          accessibilityRole="button"
          accessibilityLabel={isEditing ? t('tutoring.saveEdit') : undefined}
          className={`w-11 h-11 rounded-full items-center justify-center shadow-md mb-1 ${
            isTextEmpty || isSending ? 'bg-[#D1D1E0]' : 'bg-primary shadow-[#9A3BEE]/35'
          }`}
        >
          <Feather name={isEditing ? 'check' : 'arrow-right'} size={20} color="#FFFFFF" />
        </Pressable>
      </View>
    </View>
  );
}
