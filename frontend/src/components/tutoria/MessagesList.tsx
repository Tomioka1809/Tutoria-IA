// src/components/tutoria/MessagesList.tsx
import React from 'react';
import { ScrollView, View, Text, ActivityIndicator } from 'react-native';
import { Conversation } from '@/src/types';

// Helper function to parse and render bold text marked with **
const renderFormattedText = (text: string) => {
  if (!text) return null;
  const parts = text.split(/\*\*([^*]+)\*\*/g);
  return parts.map((part, index) => {
    if (index % 2 === 1) {
      return (
        <Text key={index} style={{ fontWeight: 'bold' }}>
          {part}
        </Text>
      );
    }
    return part;
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
  return (
    <ScrollView
      ref={scrollViewRef}
      className="flex-1 bg-[#F5F5FB] px-6 pt-4"
      contentContainerStyle={{ paddingBottom: 24 }}
      showsVerticalScrollIndicator={false}
    >
      {isLoading ? (
        <ActivityIndicator size="large" color="#9A3BEE" className="mt-12" />
      ) : (
        conversation?.messages.map((msg) => {
          const isUser = msg.role === 'user';
          return (
            <View
              key={msg.id}
              className={`flex-row mb-4 ${isUser ? 'justify-end' : 'justify-start'}`}
            >
              {!isUser ? (
                <View className="w-8 h-8 rounded-full bg-white items-center justify-center border border-[#7F77DD]/20 mr-2 self-end shadow-sm">
                  <Text className="text-base">🦖</Text>
                </View>
              ) : null}

              <View
                className={`max-w-[75%] rounded-3xl px-4 py-3 shadow-sm ${
                  isUser
                    ? 'bg-[#9A3BEE] rounded-tr-none'
                    : 'bg-white border border-[#EEEDFE] rounded-tl-none'
                }`}
              >
                <Text
                  className={`text-sm leading-5 ${
                    isUser ? 'text-white' : 'text-[#26215C] font-medium'
                  }`}
                >
                  {renderFormattedText(msg.content)}
                </Text>
                <Text
                  className={`text-[9px] mt-1.5 text-right ${
                    isUser ? 'text-white/60' : 'text-[#26215C]/40'
                  }`}
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
          <View className="w-8 h-8 rounded-full bg-white items-center justify-center border border-[#7F77DD]/20 mr-2 shadow-sm">
            <Text className="text-base">🦖</Text>
          </View>
          <View className="bg-white border border-[#7F77DD]/10 rounded-2xl rounded-tl-none px-4 py-3 shadow-sm">
            <Text className="text-xs text-[#26215C]/50 font-semibold italic">🦖 TutorIA está pensando...</Text>
          </View>
        </View>
      ) : null}
    </ScrollView>
  );
}
