import { create } from 'zustand';
import client from '../api/client';
import { Message, Conversation } from '../types';
import { reportApiError } from '../services/error-feedback';

interface ChatState {
  conversation: Conversation | null;
  isLoading: boolean;
  isSending: boolean;
  fetchConversation: () => Promise<void>;
  sendMessage: (content: string) => Promise<void>;
  editMessage: (messageId: number, content: string) => Promise<void>;
  resetConversation: () => Promise<void>;
}

export const useChatStore = create<ChatState>((set, get) => ({
  conversation: null,
  isLoading: false,
  isSending: false,
  fetchConversation: async () => {
    if (!get().conversation) {
      set({ isLoading: true });
    }
    try {
      const response = await client.get<Conversation>('/chat/conversation', {
        headers: {
          'Cache-Control': 'no-cache',
          'Pragma': 'no-cache',
          'Expires': '0',
        },
      });
      set({ conversation: response.data });
    } catch (error) {
      reportApiError(error, 'errors.loadConversation');
    } finally {
      set({ isLoading: false });
    }
  },
  sendMessage: async (content: string) => {
    const activeConv = get().conversation;
    if (!activeConv) return;

    const tempUserMsg: Message = {
      id: Date.now(),
      conversation_id: activeConv.id,
      role: 'user',
      content,
      sent_at: new Date().toISOString(),
    };

    set((state) => ({
      conversation: state.conversation
        ? {
            ...state.conversation,
            messages: [...state.conversation.messages, tempUserMsg],
          }
        : null,
      isSending: true,
    }));

    try {
      const response = await client.post<Message>('/chat/message', { content });

      set((state) => {
        if (!state.conversation) return {};
        return {
          conversation: {
            ...state.conversation,
            messages: [...state.conversation.messages, response.data],
          },
        };
      });

      await get().fetchConversation();
    } catch (error) {
      reportApiError(error, 'errors.sendMessage');
      set((state) => ({
        conversation: state.conversation
          ? {
              ...state.conversation,
              messages: state.conversation.messages.filter(
                (m) => m.id !== tempUserMsg.id
              ),
            }
          : null,
      }));
    } finally {
      set({ isSending: false });
    }
  },
  editMessage: async (messageId: number, content: string) => {
    const activeConv = get().conversation;
    if (!activeConv) return;

    const trimmed = content.trim();
    if (!trimmed) return;

    // Se muestra el texto nuevo y se recortan los mensajes posteriores antes de
    // que responda el servidor: es lo que va a pasar igual, y sin el recorte la
    // pregunta editada convive unos segundos con la respuesta que la contradice.
    const previous = activeConv.messages;
    const index = previous.findIndex((m) => m.id === messageId);
    if (index === -1) return;

    set((state) => ({
      conversation: state.conversation
        ? {
            ...state.conversation,
            messages: [
              ...previous.slice(0, index),
              { ...previous[index], content: trimmed },
            ],
          }
        : null,
      isSending: true,
    }));

    try {
      // El servidor devuelve la conversacion entera: el cliente no puede saber
      // cuantos mensajes se descartaron a partir de una sola respuesta.
      const response = await client.patch<Conversation>(`/chat/message/${messageId}`, {
        content: trimmed,
      });
      set({ conversation: response.data });
    } catch (error) {
      reportApiError(error, 'errors.editMessage');
      set((state) => ({
        conversation: state.conversation
          ? { ...state.conversation, messages: previous }
          : null,
      }));
    } finally {
      set({ isSending: false });
    }
  },
  resetConversation: async () => {
    set({ isLoading: true });
    try {
      await client.delete('/chat/conversation');
      await get().fetchConversation();
    } catch (error) {
      reportApiError(error, 'errors.resetConversation');
      set({ isLoading: false });
    }
  },
}));
