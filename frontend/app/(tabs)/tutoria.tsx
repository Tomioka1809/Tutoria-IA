// app/(tabs)/tutoria.tsx
import React, { useEffect, useRef, useState } from 'react';
import { View, Text, KeyboardAvoidingView, Platform, TextInput, Keyboard } from 'react-native';
import { useIsFocused } from '@react-navigation/native';
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

  const inputRef = useRef<TextInput>(null);
  const isFocused = useIsFocused();
  const [keyboardVisible, setKeyboardVisible] = useState(false);

  useEffect(() => {
    if (isFocused && user?.role === 'estudiante') {
      const timer = setTimeout(() => {
        inputRef.current?.focus();
      }, 150);
      return () => clearTimeout(timer);
    }
  }, [isFocused, user?.role]);

  useEffect(() => {
    const showEvent = Platform.OS === 'ios' ? 'keyboardWillShow' : 'keyboardDidShow';
    const hideEvent = Platform.OS === 'ios' ? 'keyboardWillHide' : 'keyboardDidHide';

    const showSubscription = Keyboard.addListener(showEvent, () => {
      setKeyboardVisible(true);
    });
    const hideSubscription = Keyboard.addListener(hideEvent, () => {
      setKeyboardVisible(false);
    });

    return () => {
      showSubscription.remove();
      hideSubscription.remove();
    };
  }, []);

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
      behavior="padding"
      keyboardVerticalOffset={0}
      className="flex-1 bg-white"
      style={{
        paddingBottom: keyboardVisible ? 0 : (Platform.OS === 'ios' ? 88 : 76)
      }}
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
        inputRef={inputRef}
      />
    </KeyboardAvoidingView>
  );
}
