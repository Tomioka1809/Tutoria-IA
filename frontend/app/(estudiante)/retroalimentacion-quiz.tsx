// app/(estudiante)/retroalimentacion-quiz.tsx
import React, { useState, useEffect } from 'react';
import { View, Text, Pressable, ScrollView, Animated } from 'react-native';
import { useRouter } from 'expo-router';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import Feather from '@expo/vector-icons/Feather';
import { useTheme } from '@/src/theme/ThemeContext';
import { QuizAPI, QuizQuestion } from '@/src/api/services';
import { useTranslation } from 'react-i18next';

export default function QuizScreen() {
  const { colors } = useTheme();
  const { t } = useTranslation();
  const router = useRouter();
  const insets = useSafeAreaInsets();
  
  const [questions, setQuestions] = useState<QuizQuestion[]>([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [selectedOption, setSelectedOption] = useState<number | null>(null);
  const [isAnswered, setIsAnswered] = useState(false);
  const [correctCount, setCorrectCount] = useState(0);
  const [isFinished, setIsFinished] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Generar 20 preguntas desde la base de datos usando AI
    QuizAPI.generateQuiz()
      .then(data => {
        setQuestions(data);
        setIsLoading(false);
      })
      .catch(err => {
        console.error("Failed to generate quiz", err);
        setError(t('quiz.generationError'));
        setIsLoading(false);
      });
  }, []);

  if (isLoading) {
    return (
      <View style={{ flex: 1, backgroundColor: colors.background, justifyContent: 'center', alignItems: 'center', padding: 24 }}>
        <Text style={{ color: colors.text, fontSize: 18, marginBottom: 16 }}>{t('quiz.generating')}</Text>
        <Text style={{ color: colors.textSecondary, textAlign: 'center' }}>{t('quiz.analyzing')}</Text>
      </View>
    );
  }

  if (error || questions.length === 0) {
    return (
      <View style={{ flex: 1, backgroundColor: colors.background, justifyContent: 'center', alignItems: 'center', padding: 24 }}>
        <Text style={{ color: '#EF4444', textAlign: 'center', marginBottom: 24 }}>{error || t('quiz.noQuestions')}</Text>
        <Pressable
          onPress={() => router.replace('/(estudiante)/' as any)}
          style={{
            backgroundColor: colors.primary,
            paddingVertical: 12,
            paddingHorizontal: 24,
            borderRadius: 12,
          }}
        >
          <Text style={{ color: 'white', fontWeight: 'bold' }}>{t('quiz.backHome')}</Text>
        </Pressable>
      </View>
    );
  }

  const currentQuestion = questions[currentIndex];

  const handleOptionSelect = (index: number) => {
    if (isAnswered) return;
    setSelectedOption(index);
    setIsAnswered(true);

    if (index === currentQuestion.correctAnswerIndex) {
      setCorrectCount(prev => prev + 1);
    }
  };

  const handleNext = () => {
    if (currentIndex < questions.length - 1) {
      setCurrentIndex(prev => prev + 1);
      setSelectedOption(null);
      setIsAnswered(false);
    } else {
      setIsFinished(true);
    }
  };

  const handleBack = () => {
    router.replace('/(estudiante)/' as any);
  };

  if (isFinished) {
    return (
      <View style={{ flex: 1, backgroundColor: colors.background, paddingTop: insets.top, paddingHorizontal: 24, alignItems: 'center', justifyContent: 'center' }}>
        <Feather name="award" size={80} color={colors.primary} style={{ marginBottom: 24 }} />
        <Text style={{ fontSize: 24, fontWeight: 'bold', color: colors.text, marginBottom: 8 }}>{t('quiz.finished')}</Text>
        <Text style={{ fontSize: 16, color: colors.textSecondary, marginBottom: 32, textAlign: 'center' }}>
          {t('quiz.score', { correct: correctCount, total: questions.length })}
        </Text>
        <Pressable
          onPress={handleBack}
          style={{
            backgroundColor: colors.primary,
            paddingVertical: 16,
            paddingHorizontal: 32,
            borderRadius: 16,
            width: '100%',
            alignItems: 'center',
          }}
        >
          <Text style={{ color: 'white', fontSize: 16, fontWeight: 'bold' }}>{t('quiz.backHome')}</Text>
        </Pressable>
      </View>
    );
  }

  return (
    <View style={{ flex: 1, backgroundColor: colors.background }}>
      {/* Header */}
      <View style={{
        paddingTop: insets.top + 16,
        paddingHorizontal: 20,
        paddingBottom: 16,
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'space-between',
        borderBottomWidth: 1,
        borderBottomColor: colors.border,
        backgroundColor: colors.surface,
      }}>
        <Pressable onPress={handleBack} style={{ flexDirection: 'row', alignItems: 'center' }}>
          <Feather name="arrow-left" size={20} color={colors.textSecondary} />
          <Text style={{ marginLeft: 8, color: colors.textSecondary, fontSize: 14, fontWeight: '600' }}>{t('quiz.backHome')}</Text>
        </Pressable>
        <View style={{ backgroundColor: colors.background, paddingHorizontal: 12, paddingVertical: 4, borderRadius: 12 }}>
          <Text style={{ color: colors.primary, fontWeight: 'bold', fontSize: 13 }}>
            {currentIndex + 1} / {questions.length}
          </Text>
        </View>
      </View>

      <ScrollView contentContainerStyle={{ padding: 24, paddingBottom: 100 }}>
        {/* Question */}
        <Text style={{ fontSize: 20, fontWeight: 'bold', color: colors.text, marginBottom: 24, lineHeight: 28 }}>
          {currentQuestion.question}
        </Text>

        {/* Options */}
        <View style={{ gap: 12 }}>
          {currentQuestion.options.map((option, index) => {
            const isSelected = selectedOption === index;
            const isCorrect = index === currentQuestion.correctAnswerIndex;
            
            let bgColor = colors.surface;
            let borderColor = colors.border;
            let textColor = colors.text;

            if (isAnswered) {
              if (isCorrect) {
                bgColor = '#DCFCE7'; // Green light
                borderColor = '#22C55E';
                textColor = '#166534';
              } else if (isSelected && !isCorrect) {
                bgColor = '#FEE2E2'; // Red light
                borderColor = '#EF4444';
                textColor = '#991B1B';
              }
            }

            return (
              <Pressable
                key={index}
                onPress={() => handleOptionSelect(index)}
                style={{
                  backgroundColor: bgColor,
                  borderWidth: 1,
                  borderColor: borderColor,
                  borderRadius: 16,
                  padding: 16,
                  flexDirection: 'row',
                  alignItems: 'center',
                }}
              >
                <View style={{
                  width: 24, height: 24, borderRadius: 12, borderWidth: 2, borderColor: isAnswered ? (isCorrect ? '#22C55E' : (isSelected ? '#EF4444' : colors.border)) : colors.border,
                  alignItems: 'center', justifyContent: 'center', marginRight: 12,
                  backgroundColor: isAnswered && (isCorrect || isSelected) ? (isCorrect ? '#22C55E' : '#EF4444') : 'transparent'
                }}>
                  {isAnswered && (isCorrect || isSelected) && (
                    <Feather name={isCorrect ? 'check' : 'x'} size={14} color="white" />
                  )}
                </View>
                <Text style={{ flex: 1, fontSize: 15, color: textColor, fontWeight: isSelected ? '600' : '400' }}>
                  {option}
                </Text>
              </Pressable>
            );
          })}
        </View>

        {/* Explanation */}
        {isAnswered && (
          <View style={{
            marginTop: 24,
            padding: 16,
            backgroundColor: selectedOption === currentQuestion.correctAnswerIndex ? '#F0FDF4' : '#FEF2F2',
            borderRadius: 12,
            borderLeftWidth: 4,
            borderLeftColor: selectedOption === currentQuestion.correctAnswerIndex ? '#22C55E' : '#EF4444',
          }}>
            <Text style={{ fontWeight: 'bold', color: selectedOption === currentQuestion.correctAnswerIndex ? '#166534' : '#991B1B', marginBottom: 4 }}>
              {selectedOption === currentQuestion.correctAnswerIndex ? t('quiz.correct') : t('quiz.incorrect')}
            </Text>
            <Text style={{ color: selectedOption === currentQuestion.correctAnswerIndex ? '#166534' : '#991B1B', fontSize: 14, lineHeight: 20 }}>
              {currentQuestion.explanation}
            </Text>
          </View>
        )}
      </ScrollView>

      {/* Footer / Next Button */}
      {isAnswered && (
        <View style={{
          position: 'absolute',
          bottom: 0,
          left: 0,
          right: 0,
          padding: 24,
          paddingBottom: Math.max(insets.bottom, 24),
          backgroundColor: colors.surface,
          borderTopWidth: 1,
          borderTopColor: colors.border,
        }}>
          <Pressable
            onPress={handleNext}
            style={{
              backgroundColor: colors.primary,
              paddingVertical: 16,
              borderRadius: 16,
              alignItems: 'center',
              flexDirection: 'row',
              justifyContent: 'center',
            }}
          >
            <Text style={{ color: 'white', fontSize: 16, fontWeight: 'bold', marginRight: 8 }}>
              {currentIndex < questions.length - 1 ? t('quiz.nextQuestion') : t('quiz.viewResults')}
            </Text>
            <Feather name="arrow-right" size={20} color="white" />
          </Pressable>
        </View>
      )}
    </View>
  );
}
