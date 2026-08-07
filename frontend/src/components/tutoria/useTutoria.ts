// src/components/tutoria/useTutoria.ts
import { useState, useEffect, useRef, useCallback } from 'react';
import { ScrollView } from 'react-native';
import { useChatStore } from '@/src/store/chat';
import { useAuthStore } from '@/src/store/auth';
import { Message } from '@/src/types';

export function useTutoria() {
  const user = useAuthStore((state) => state.user);
  const userId = user?.id;
  const userRole = user?.role;
  const conversation = useChatStore((state) => state.conversation);
  const fetchConversation = useChatStore((state) => state.fetchConversation);
  const sendMessage = useChatStore((state) => state.sendMessage);
  const editMessage = useChatStore((state) => state.editMessage);
  const isLoading = useChatStore((state) => state.isLoading);
  const isSending = useChatStore((state) => state.isSending);
  const resetConversation = useChatStore((state) => state.resetConversation);
  const [inputText, setInputText] = useState('');
  const [editingMessageId, setEditingMessageId] = useState<number | null>(null);
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

  // Si la conversacion se reinicia o el mensaje en edicion desaparece, el modo
  // edicion queda apuntando a un id que ya no existe y el guardado fallaria con
  // un 404. Se cierra solo.
  useEffect(() => {
    if (editingMessageId === null) return;
    const sigueExistiendo = conversation?.messages.some((m) => m.id === editingMessageId);
    if (!sigueExistiendo) {
      setEditingMessageId(null);
      setInputText('');
    }
  }, [conversation?.messages, editingMessageId]);

  const startEditing = useCallback((message: Message) => {
    if (message.role !== 'user') return;
    setEditingMessageId(message.id);
    setInputText(message.content);
  }, []);

  const cancelEditing = useCallback(() => {
    setEditingMessageId(null);
    setInputText('');
  }, []);

  const handleSend = async (textToSend: string) => {
    const trimmed = textToSend.trim();
    if (!trimmed) return;

    // El mismo boton envia o guarda segun el modo, para no partir la barra en
    // dos controles que hacen casi lo mismo.
    if (editingMessageId !== null) {
      const messageId = editingMessageId;
      setEditingMessageId(null);
      setInputText('');
      await editMessage(messageId, trimmed);
      return;
    }

    setInputText('');
    await sendMessage(trimmed);
  };

  const handleQuickAction = async (actionText: string) => {
    const trimmed = actionText.trim();
    if (!trimmed) return;

    // Una accion rapida siempre es un mensaje nuevo, nunca una edicion. No
    // puede delegar en handleSend: cancelEditing no actualiza el closure de
    // esta misma pasada, asi que handleSend seguiria viendo el modo edicion
    // abierto y guardaria la accion rapida encima del mensaje editado.
    if (editingMessageId !== null) cancelEditing();
    setInputText('');
    await sendMessage(trimmed);
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
    editingMessageId,
    startEditing,
    cancelEditing,
  };
}
