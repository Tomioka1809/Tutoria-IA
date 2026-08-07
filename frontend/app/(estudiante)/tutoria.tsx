// app/(estudiante)/tutoria.tsx
import React, { useEffect, useRef, useState } from 'react';
import { useTheme } from '@/src/theme/ThemeContext';
import { View, Text, KeyboardAvoidingView, Platform, TextInput, Keyboard, ActivityIndicator } from 'react-native';
import { useIsFocused } from '@react-navigation/native';
import { useRouter } from 'expo-router';
import { useTutoria } from '@/src/components/tutoria/useTutoria';
import { TutoriaHeader } from '@/src/components/tutoria/TutoriaHeader';
import { MessagesList } from '@/src/components/tutoria/MessagesList';
import { QuickActionsPanel } from '@/src/components/tutoria/QuickActionsPanel';
import { MessageInputBar } from '@/src/components/tutoria/MessageInputBar';
import { useTranslation } from 'react-i18next';
import { TutorIAAvatar } from '@/src/components/tutoria/TutorIAAvatar';

export default function TutoriaScreen() {
  const { colors } = useTheme();
  const { t } = useTranslation();
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
    editingMessageId,
    startEditing,
    cancelEditing,
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

  if (!user) {
    return (
      <View style={{ flex: 1, backgroundColor: colors.background, justifyContent: 'center', alignItems: 'center' }}>
        <ActivityIndicator size="large" color={colors.primary} />
      </View>
    );
  }

  if (user.role !== 'estudiante') {
    return (
      <View style={{ backgroundColor: colors.background }} className="flex-1  justify-center items-center px-6">
        <View style={{ marginBottom: 16 }}>
          <TutorIAAvatar size={64} />
        </View>
        <Text className="text-lg font-bold text-text text-center">{t('tutoring.welcomeTitle')}</Text>
        <Text className="text-sm text-text/60 text-center mt-2">
          {t('tutoring.studentOnly')}
        </Text>
      </View>
    );
  }

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
        onEditMessage={startEditing}
        editingMessageId={editingMessageId}
      />

      <QuickActionsPanel onActionPress={handleQuickAction} userRole={user?.role} />

      <MessageInputBar
        inputText={inputText}
        setInputText={setInputText}
        onSend={handleSend}
        isSending={isSending}
        inputRef={inputRef}
        isEditing={editingMessageId !== null}
        onCancelEdit={cancelEditing}
      />
    </KeyboardAvoidingView>
  );
}
