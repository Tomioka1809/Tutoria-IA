// src/components/tutoria/MessagesList.tsx
import React from 'react';
import { ScrollView, View, Text, ActivityIndicator, Pressable } from 'react-native';
import * as Haptics from 'expo-haptics';
import { Conversation, Message } from '@/src/types';
import { useTheme } from '@/src/theme/ThemeContext';
import { useTranslation } from 'react-i18next';
import { TutorIAAvatar } from '@/src/components/tutoria/TutorIAAvatar';

// Helper function to parse and render bold text marked with ** and line breaks
const renderFormattedText = (text: string, isUser: boolean, colors: any, isDark: boolean) => {
  if (!text) return null;
  const paragraphs = text.split('\n');
  const textColor = isUser ? 'text-white' : 'font-medium';
  const inlineTextColor = isUser ? '#FFFFFF' : (isDark ? '#F3F4F6' : colors.text);
  
  return paragraphs.map((paragraph, pIndex) => {
    if (!paragraph.trim() && pIndex !== paragraphs.length - 1) {
      return <View key={pIndex} style={{ height: 8 }} />;
    }
    
    const parts = paragraph.split(/\*\*([^*]+)\*\*/g);
    return (
      <Text key={pIndex} className={`text-sm leading-5 mb-1 ${textColor}`} style={{ color: inlineTextColor }}>
        {parts.map((part, index) => {
          if (index % 2 === 1) {
            return (
              <Text key={index} style={{ fontWeight: 'bold' }}>
                {part}
              </Text>
            );
          }
          return part;
        })}
      </Text>
    );
  });
};

interface MessagesListProps {
  scrollViewRef: React.RefObject<ScrollView | null>;
  conversation: Conversation | null;
  isLoading: boolean;
  isSending: boolean;
  onEditMessage?: (message: Message) => void;
  editingMessageId?: number | null;
}

export function MessagesList({
  scrollViewRef,
  conversation,
  isLoading,
  isSending,
  onEditMessage,
  editingMessageId,
}: MessagesListProps) {
  const { colors, isDark } = useTheme();
  const { t } = useTranslation();
  return (
    <ScrollView
      ref={scrollViewRef}
      style={{ backgroundColor: colors.background }} className="flex-1  px-6 pt-4"
      contentContainerStyle={{ paddingBottom: 24 }}
      showsVerticalScrollIndicator={false}
    >
      {isLoading ? (
        <ActivityIndicator size="large" color={colors.primary} className="mt-12" />
      ) : (
        conversation?.messages.map((msg) => {
          const isUser = msg.role === 'user';
          // Solo los mensajes propios se editan. Se comprueba aqui y no solo en
          // el servidor para que el long-press ni siquiera responda sobre una
          // respuesta de TutorIA.
          const isEditable = isUser && !!onEditMessage;
          const isBeingEdited = editingMessageId === msg.id;

          const handleLongPress = () => {
            if (!isEditable) return;
            // El aviso tactil confirma que el gesto se registro: sin el, el
            // usuario no sabe si mantuvo presionado lo suficiente.
            Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium).catch(() => {});
            onEditMessage(msg);
          };

          return (
            <View
              key={msg.id}
              className={`flex-row mb-4 ${isUser ? 'justify-end' : 'justify-start'}`}
            >
              {!isUser ? (
                <View style={{ backgroundColor: colors.surface }} className="w-8 h-8 rounded-full  items-center justify-center border border-primary/20 mr-2 self-end shadow-sm">
                  <TutorIAAvatar size={28} />
                </View>
              ) : null}

              <Pressable
                onLongPress={handleLongPress}
                delayLongPress={350}
                disabled={!isEditable}
                accessibilityRole={isEditable ? 'button' : undefined}
                accessibilityLabel={isEditable ? t('tutoring.editHint') : undefined}
                className={`max-w-[75%] rounded-3xl px-4 py-3 shadow-sm ${
                  isUser
                    ? 'rounded-tr-none'
                    : 'rounded-tl-none'
                }${isEditable ? ' active:opacity-75' : ''}`}
                // El prop `style` tiene que ser un objeto o un array de objetos.
                // NativeWind aplana el style inline para fusionarlo con las
                // clases, y en ese paso una funcion se convierte en {}: la
                // forma `({ pressed }) => [...]` se pierde entera y la burbuja
                // se queda sin fondo ni borde. El feedback de pulsacion va por
                // el modificador `active:`, que es la via soportada.
                style={[
                  isUser
                    ? { backgroundColor: isDark ? '#7C3AED' : colors.primary }
                    : { backgroundColor: isDark ? '#2D2D3D' : colors.surface, borderColor: colors.border, borderWidth: 1 },
                  // El mensaje en edicion queda atenuado para que se vea cual
                  // de todos es el que esta cargado en la barra de abajo.
                  isBeingEdited ? { opacity: 0.55 } : null,
                ]}
              >
                <View>
                  {renderFormattedText(msg.content, isUser, colors, isDark)}
                </View>
                <Text
                  className={`text-[9px] mt-1.5 text-right ${isUser ? 'text-white/60' : ''}`}
                  style={!isUser ? { color: isDark ? 'rgba(255,255,255,0.4)' : 'rgba(17,17,48,0.4)' } : undefined}
                >
                  {new Date(msg.sent_at).toLocaleTimeString([], {
                    hour: '2-digit',
                    minute: '2-digit',
                  })}
                </Text>
              </Pressable>
            </View>
          );
        })
      )}

      {isSending ? (
        <View className="flex-row mb-4 justify-start items-center">
          <View style={{ backgroundColor: colors.surface }} className="w-8 h-8 rounded-full  items-center justify-center border border-primary/20 mr-2 shadow-sm">
            <TutorIAAvatar size={28} />
          </View>
          <View style={{ backgroundColor: colors.surface }} className=" border border-primary/10 rounded-2xl rounded-tl-none px-4 py-3 shadow-sm">
            <Text className="text-xs font-semibold italic" style={{ color: isDark ? 'rgba(255,255,255,0.5)' : 'rgba(17,17,48,0.5)' }}>{t('tutoring.thinking')}</Text>
          </View>
        </View>
      ) : null}
    </ScrollView>
  );
}
