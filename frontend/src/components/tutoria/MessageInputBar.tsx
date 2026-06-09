// src/components/tutoria/MessageInputBar.tsx
import React from 'react';
import { View, TextInput, Pressable, Text } from 'react-native';

interface MessageInputBarProps {
  inputText: string;
  setInputText: (text: string) => void;
  onSend: (text: string) => void;
  onMicPress: () => void;
  isSending: boolean;
}

export function MessageInputBar({
  inputText,
  setInputText,
  onSend,
  onMicPress,
  isSending,
}: MessageInputBarProps) {
  const isSendDisabled = !inputText.trim() || isSending;

  return (
    <View className="bg-white px-4 pt-3 pb-6 border-t border-[#EEEDFE] flex-row items-center">
      <TextInput
        value={inputText}
        onChangeText={setInputText}
        placeholder="Escribe tu mensaje..."
        className="flex-1 bg-[#F5F5FB] rounded-full px-5 py-3 text-sm text-[#26215C] mr-3 font-semibold"
        placeholderTextColor="#8E8EA0"
      />

      <Pressable
        onPress={onMicPress}
        className="w-11 h-11 rounded-full bg-[#9A3BEE] items-center justify-center mr-2 shadow-md shadow-[#9A3BEE]/35"
      >
        <Text className="text-lg">🎤</Text>
      </Pressable>

      <Pressable
        onPress={() => onSend(inputText)}
        disabled={isSendDisabled}
        className={`w-11 h-11 rounded-full items-center justify-center shadow-md ${
          !isSendDisabled ? 'bg-[#9A3BEE] shadow-[#9A3BEE]/35' : 'bg-[#9A3BEE]/40'
        }`}
      >
        <Text className="text-white font-bold text-base">➔</Text>
      </Pressable>
    </View>
  );
}
