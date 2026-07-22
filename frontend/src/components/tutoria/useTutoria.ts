// src/components/tutoria/useTutoria.ts
import { useState, useEffect, useRef } from 'react';
import { ScrollView } from 'react-native';
import { useChatStore } from '@/src/store/chat';
import { useAuthStore } from '@/src/store/auth';

export function useTutoria() {
  const user = useAuthStore((state) => state.user);
  const userId = user?.id;
  const userRole = user?.role;
  const conversation = useChatStore((state) => state.conversation);
  const fetchConversation = useChatStore((state) => state.fetchConversation);
  const sendMessage = useChatStore((state) => state.sendMessage);
  const isLoading = useChatStore((state) => state.isLoading);
  const isSending = useChatStore((state) => state.isSending);
  const resetConversation = useChatStore((state) => state.resetConversation);
  const [inputText, setInputText] = useState('');
  const scrollViewRef = useRef<ScrollView>(null);

  useEffect(() => {
    if (userRole === 'estudiante' || userRole === 'tutor') {
      fetchConversation();
    }
  }, [userId, userRole, fetchConversation]);

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
    resetConversation,
  };
}
