// app/(tutor)/tutoria.tsx
import React, { useEffect, useRef, useState } from 'react';
import { useTheme } from '@/src/theme/ThemeContext';
import { KeyboardAvoidingView, Platform, TextInput, Keyboard } from 'react-native';
import { useIsFocused } from '@react-navigation/native';
import { useRouter } from 'expo-router';
import { useTutoria } from '@/src/components/tutoria/useTutoria';
import { TutoriaHeader } from '@/src/components/tutoria/TutoriaHeader';
import { MessagesList } from '@/src/components/tutoria/MessagesList';
import { QuickActionsPanel } from '@/src/components/tutoria/QuickActionsPanel';
import { MessageInputBar } from '@/src/components/tutoria/MessageInputBar';

export default function TutoriaScreen() {
  const { colors } = useTheme();
  const router = useRouter();
  const {
    user,
    conversation,
    isLoading,
    isSending,
    inputText,
    setInputText,
    scrollViewRef,
    handleSend,
    handleQuickAction,
    resetConversation,
  } = useTutoria();

  const inputRef = useRef<TextInput>(null);
  const isFocused = useIsFocused();
  const [keyboardVisible, setKeyboardVisible] = useState(false);

  useEffect(() => {
    if (isFocused && (user?.role === 'estudiante' || user?.role === 'tutor')) {
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

  return (
    <KeyboardAvoidingView
      behavior="padding"
      keyboardVerticalOffset={0}
      className="flex-1"
      style={{
        backgroundColor: colors.surface,
        paddingBottom: keyboardVisible ? 0 : (Platform.OS === 'ios' ? 88 : 76)
      }}
    >
      <TutoriaHeader onRefresh={resetConversation} onBackPress={() => router.back()} />

      <MessagesList
        scrollViewRef={scrollViewRef}
        conversation={conversation}
        isLoading={isLoading}
        isSending={isSending}
      />

      <QuickActionsPanel onActionPress={handleQuickAction} userRole={user?.role} />

      <MessageInputBar
        inputText={inputText}
        setInputText={setInputText}
        onSend={handleSend}
        isSending={isSending}
        inputRef={inputRef}
      />
    </KeyboardAvoidingView>
  );
}
