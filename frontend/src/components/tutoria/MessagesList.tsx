// src/components/tutoria/MessagesList.tsx
import React from 'react';
import { ScrollView, View, Text, ActivityIndicator } from 'react-native';
import { Conversation } from '@/src/types';
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
}

export function MessagesList({
  scrollViewRef,
  conversation,
  isLoading,
  isSending,
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

              <View
                className={`max-w-[75%] rounded-3xl px-4 py-3 shadow-sm ${
                  isUser
                    ? 'rounded-tr-none'
                    : 'rounded-tl-none'
                }`}
                style={
                  isUser
                    ? { backgroundColor: isDark ? '#7C3AED' : colors.primary }
                    : { backgroundColor: isDark ? '#2D2D3D' : colors.surface, borderColor: colors.border, borderWidth: 1 }
                }
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
              </View>
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
