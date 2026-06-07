import React, { useState, useEffect, useRef } from 'react';
import { View, Text, TextInput, ScrollView, Pressable, KeyboardAvoidingView, Platform, ActivityIndicator } from 'react-native';
import { useChatStore } from '../../src/store/chat';
import { useAuthStore } from '../../src/store/auth';

export default function TutoriaScreen() {
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
      {/* Header section matching mockup */}
      <View className="bg-white border-b border-[#EEEDFE] px-6 pt-16 pb-4 flex-row items-center justify-between">
        <View className="flex-row items-center flex-1">
          <Pressable onPress={() => {}} className="mr-3 p-1">
            <Text className="text-xl text-[#26215C]">←</Text>
          </Pressable>
          
          <View className="w-10 h-10 rounded-full bg-[#9A3BEE]/10 items-center justify-center border border-[#9A3BEE]/25 mr-3">
            <Text className="text-xl">🦖</Text>
          </View>
          
          <View className="flex-1">
            <Text className="text-sm font-extrabold text-[#111130]">TutorIA AI</Text>
            <View className="flex-row items-center mt-0.5">
              <View className="w-2 h-2 rounded-full bg-[#10B981] mr-1.5" />
              <Text className="text-[10px] text-[#8E8EA0] font-semibold">En línea</Text>
            </View>
          </View>
        </View>

        <Pressable onPress={() => fetchConversation()} className="p-2">
          <Text className="text-lg text-[#26215C]">↻</Text>
        </Pressable>
      </View>

      {/* Messages area */}
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
                    {msg.content}
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

      {/* Quick Access panel matching mockup */}
      <View className="px-6 py-3 bg-[#F5F5FB] flex-row flex-wrap">
        <Pressable
          onPress={() => handleQuickAction('¿Cuál es mi plan de estudios actual?')}
          className="bg-white border border-[#EEEDFE] rounded-2xl px-4 py-2.5 mr-2 mb-2 flex-row items-center shadow-sm"
        >
          <Text className="text-xs text-[#26215C] font-semibold">📄 Plan de estudios</Text>
        </Pressable>
        <Pressable
          onPress={() => handleQuickAction('¿Cuándo es mi próxima tutoría?')}
          className="bg-white border border-[#EEEDFE] rounded-2xl px-4 py-2.5 mr-2 mb-2 flex-row items-center shadow-sm"
        >
          <Text className="text-xs text-[#26215C] font-semibold">📅 Tutorías</Text>
        </Pressable>
        <Pressable
          onPress={() => handleQuickAction('¿Dónde encuentro los reglamentos universitarios?')}
          className="bg-white border border-[#EEEDFE] rounded-2xl px-4 py-2.5 mb-2 flex-row items-center shadow-sm"
        >
          <Text className="text-xs text-[#26215C] font-semibold">📄 Reglamentos</Text>
        </Pressable>
      </View>

      {/* Input bar matching mockup */}
      <View className="bg-white px-4 pt-3 pb-6 border-t border-[#EEEDFE] flex-row items-center">
        <TextInput
          value={inputText}
          onChangeText={setInputText}
          placeholder="Escribe tu mensaje..."
          className="flex-1 bg-[#F5F5FB] rounded-full px-5 py-3 text-sm text-[#26215C] mr-3 font-semibold"
          placeholderTextColor="#8E8EA0"
        />

        <Pressable
          onPress={handleMicPress}
          className="w-11 h-11 rounded-full bg-[#9A3BEE] items-center justify-center mr-2 shadow-md shadow-[#9A3BEE]/35"
        >
          <Text className="text-lg">🎤</Text>
        </Pressable>

        <Pressable
          onPress={() => handleSend(inputText)}
          disabled={!inputText.trim() || isSending}
          className={`w-11 h-11 rounded-full items-center justify-center shadow-md ${
            inputText.trim() && !isSending ? 'bg-[#9A3BEE] shadow-[#9A3BEE]/35' : 'bg-[#9A3BEE]/40'
          }`}
        >
          <Text className="text-white font-bold text-base">➔</Text>
        </Pressable>
      </View>
    </KeyboardAvoidingView>
  );
}
