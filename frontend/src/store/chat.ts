import { create } from 'zustand';
import client from '../api/client';
import { Message, Conversation } from '../types';

interface ChatState {
  conversation: Conversation | null;
  isLoading: boolean;
  isSending: boolean;
  fetchConversation: () => Promise<void>;
  sendMessage: (content: string) => Promise<void>;
}

export const useChatStore = create<ChatState>((set, get) => ({
  conversation: null,
  isLoading: false,
  isSending: false,
  fetchConversation: async () => {
    set({ isLoading: true });
    try {
      const response = await client.get<Conversation>('/chat/conversation');
      set({ conversation: response.data });
    } catch (error) {
      console.error('Failed to fetch chat conversation:', error);
    } finally {
      set({ isLoading: false });
    }
  },
  sendMessage: async (content: string) => {
    // Optimistic user message addition for modern UX
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
      
      // Replace optimistic message and add model response
      set((state) => {
        if (!state.conversation) return {};
        // Filter out temporary local message and append verified server responses
        const verifiedMessages = state.conversation.messages.filter(
          (m) => m.id !== tempUserMsg.id
        );
        return {
          conversation: {
            ...state.conversation,
            messages: [...verifiedMessages, response.data],
          },
        };
      });
      
      // Refresh to fetch final backend message state (including model response message)
      await get().fetchConversation();
    } catch (error) {
      console.error('Failed to send chat message:', error);
      // Remove optimistic message on failure
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
}));
