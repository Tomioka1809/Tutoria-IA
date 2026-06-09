// app/(tabs)/tutoria.tsx
import React from 'react';
import { View, Text, KeyboardAvoidingView, Platform } from 'react-native';
import { useTutoria } from '@/src/components/tutoria/useTutoria';
import { TutoriaHeader } from '@/src/components/tutoria/TutoriaHeader';
import { MessagesList } from '@/src/components/tutoria/MessagesList';
import { QuickActionsPanel } from '@/src/components/tutoria/QuickActionsPanel';
import { MessageInputBar } from '@/src/components/tutoria/MessageInputBar';

export default function TutoriaScreen() {
  const {
    user,
    conversation,
    fetchConversation,
    isLoading,
    isSending,
    inputText,
    setInputText,
    scrollViewRef,
    handleSend,
    handleQuickAction,
    handleMicPress,
  } = useTutoria();

  if (user?.role !== 'estudiante') {
    return (
      <View className="flex-1 bg-[#F5F5FB] justify-center items-center px-6">
        <Text className="text-4xl mb-4">🦖</Text>
        <Text className="text-lg font-bold text-[#26215C] text-center">TutorIA Chatbot</Text>
        <Text className="text-sm text-[#26215C]/60 text-center mt-2">
          El chatbot TutorIA está disponible exclusivamente para estudiantes con el fin de resolver consultas académicas.
        </Text>
      </View>
    );
  }

  return (
    <KeyboardAvoidingView
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      keyboardVerticalOffset={Platform.OS === 'ios' ? 90 : 0}
      className="flex-1 bg-white"
    >
      <TutoriaHeader onRefresh={fetchConversation} />

      <MessagesList
        scrollViewRef={scrollViewRef}
        conversation={conversation}
        isLoading={isLoading}
        isSending={isSending}
      />

      <QuickActionsPanel onActionPress={handleQuickAction} />

      <MessageInputBar
        inputText={inputText}
        setInputText={setInputText}
        onSend={handleSend}
        onMicPress={handleMicPress}
        isSending={isSending}
      />
    </KeyboardAvoidingView>
  );
}
