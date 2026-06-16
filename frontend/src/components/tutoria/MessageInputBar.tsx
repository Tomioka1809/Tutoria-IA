// src/components/tutoria/MessageInputBar.tsx
import React, { useState, useRef, useEffect } from 'react';
import { View, TextInput, Pressable, Text, Keyboard } from 'react-native';

interface MessageInputBarProps {
  inputText: string;
  setInputText: (text: string) => void;
  onSend: (text: string) => void;
  onMicPress?: () => void;
  isSending: boolean;
  inputRef?: React.RefObject<TextInput | null>;
}

// Predefined list of UNSAAC tutoring queries for simulated voice message transcription
const SIMULATED_VOICE_QUERIES = [
  "¿Cuáles son los momentos clave de las tutorías por semestre?",
  "¿Puedo solicitar el cambio de mi tutor académico?",
  "¿Qué servicios ofrece la Unidad de Bienestar Universitario?",
  "¿Qué pasa si tengo matrícula condicionada?",
  "¿Cuál es el número máximo de estudiantes por tutor?",
  "¿Cuáles son los objetivos principales del programa de tutorías?"
];

export function MessageInputBar({
  inputText,
  setInputText,
  onSend,
  onMicPress,
  isSending,
  inputRef,
}: MessageInputBarProps) {
  const [isRecording, setIsRecording] = useState(false);
  const [recordingSeconds, setRecordingSeconds] = useState(0);
  const timerRef = useRef<NodeJS.Timeout | null>(null);

  const isTextEmpty = !inputText.trim();

  useEffect(() => {
    // Cleanup timer on unmount
    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
    };
  }, []);

  const handleMicPress = () => {
    if (isSending || isRecording) return;
    
    // Dismiss keyboard first to show the recording bar clearly
    Keyboard.dismiss();

    setIsRecording(true);
    setRecordingSeconds(0);

    // Start timer to count seconds
    let seconds = 0;
    const intervalId = setInterval(() => {
      seconds += 1;
      setRecordingSeconds(seconds);
    }, 1000);
    timerRef.current = intervalId;

    // Simulate 2 seconds of recording, then stop and send
    setTimeout(() => {
      setIsRecording((wasRecording) => {
        if (wasRecording) {
          if (timerRef.current) {
            clearInterval(timerRef.current);
            timerRef.current = null;
          }
          
          // Select a random query to simulate transcription
          const randomIndex = Math.floor(Math.random() * SIMULATED_VOICE_QUERIES.length);
          const transcript = SIMULATED_VOICE_QUERIES[randomIndex];
          
          // Send the simulated transcript
          onSend(transcript);
        }
        return false;
      });
    }, 2000);
  };

  const formatTime = (secs: number) => {
    const minutes = Math.floor(secs / 60);
    const seconds = secs % 60;
    return `${minutes}:${seconds < 10 ? '0' : ''}${seconds}`;
  };

  return (
    <View className="bg-white px-4 pt-3 pb-6 border-t border-[#EEEDFE] flex-row items-center">
      {isRecording ? (
        <View className="flex-1 bg-[#FFF0F0] rounded-full px-5 py-3 flex-row items-center mr-3 border border-red-200">
          <View className="w-2.5 h-2.5 rounded-full bg-red-500 mr-2" style={{ backgroundColor: 'red' }} />
          <Text className="text-xs font-semibold text-red-500 mr-auto">Grabando nota de voz...</Text>
          <Text className="text-xs font-bold text-red-600">{formatTime(recordingSeconds)}</Text>
        </View>
      ) : (
        <TextInput
          ref={inputRef}
          value={inputText}
          onChangeText={setInputText}
          placeholder="Mensaje"
          className="flex-1 bg-[#F5F5FB] rounded-full px-5 py-3 text-sm text-[#26215C] mr-3 font-semibold"
          placeholderTextColor="#8E8EA0"
        />
      )}

      {isTextEmpty ? (
        // Microphone action (when text is empty)
        <Pressable
          onPress={handleMicPress}
          disabled={isSending}
          className={`w-11 h-11 rounded-full items-center justify-center shadow-md ${
            isRecording ? 'bg-red-500 shadow-red-500/35' : 'bg-[#9A3BEE] shadow-[#9A3BEE]/35'
          }`}
          style={isRecording ? { backgroundColor: '#FF3B30', transform: [{ scale: 1.15 }] } : null}
        >
          <Text className="text-lg text-white">🎤</Text>
        </Pressable>
      ) : (
        // Send action (when text is not empty)
        <Pressable
          onPress={() => onSend(inputText)}
          disabled={isSending}
          className="w-11 h-11 rounded-full bg-[#9A3BEE] shadow-[#9A3BEE]/35 items-center justify-center shadow-md"
        >
          <Text className="text-white font-bold text-base">➔</Text>
        </Pressable>
      )}
    </View>
  );
}
