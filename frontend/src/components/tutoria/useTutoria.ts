// src/components/tutoria/useTutoria.ts
import { useState, useEffect, useRef } from 'react';
import { ScrollView } from 'react-native';
import { useChatStore } from '@/src/store/chat';
import { useAuthStore } from '@/src/store/auth';

export function useTutoria() {
  const { user } = useAuthStore();
  const { conversation, fetchConversation, sendMessage, isLoading, isSending } = useChatStore();
  const [inputText, setInputText] = useState('');
  const scrollViewRef = useRef<ScrollView>(null);

  useEffect(() => {
    if (user?.role === 'estudiante') {
      fetchConversation();
    }
  }, []);

  useEffect(() => {
    if (scrollViewRef.current) {
      scrollViewRef.current.scrollToEnd({ animated: true });
    }
  }, [conversation?.messages]);

  const handleSend = async (textToSend: string) => {
    const trimmed = textToSend.trim();
    if (!trimmed) return;

    setInputText('');
    await sendMessage(trimmed);
  };

  const handleQuickAction = (actionText: string) => {
    handleSend(actionText);
  };

  const handleMicPress = () => {
    alert('🎤 Entrada de voz (micrófono) en desarrollo para la siguiente versión.');
  };

  return {
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
  };
}
