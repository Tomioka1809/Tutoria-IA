import React from 'react';
import { View, Text, ScrollView, Pressable } from 'react-native';
import { useRouter } from 'expo-router';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import Feather from '@expo/vector-icons/Feather';
import Ionicons from '@expo/vector-icons/Ionicons';
import { useTheme } from '@/src/theme/ThemeContext';
import { useTranslation } from 'react-i18next';
import { useTabBarPadding } from '@/src/hooks/useTabBarPadding';

const PURPLE = '#9A3BEE';
const PURPLE_LIGHT = '#F3E8FF';
const BLUE = '#3B82F6';
const BLUE_LIGHT = '#EFF6FF';
const CYAN = '#06B6D4';
const CYAN_LIGHT = '#ECFEFF';
const ORANGE = '#F97316';
const ORANGE_LIGHT = '#FFF7ED';

interface HelpCenterScreenProps {
  /** Ruta de perfil del rol, usada solo si no hay historial al que volver. */
  profileRoute: string;
}

/**
 * Centro de ayuda compartido por estudiante y tutor.
 *
 * Las dos rutas eran identicas salvo el destino del boton atras y el calculo del
 * paddingBottom. Se adopta el comportamiento que ya tenia la version de tutor: padding
 * derivado del safe area en lugar de 130 fijo, y vuelta al historial cuando existe.
 */
export function HelpCenterScreen({ profileRoute }: HelpCenterScreenProps) {
  const { colors } = useTheme();
  const { t } = useTranslation();
  const router = useRouter();
  const insets = useSafeAreaInsets();
  const paddingTop = Math.max(insets.top, 16);
  const { scrollBottomPadding } = useTabBarPadding();

  const handleBack = () => {
    if (router.canGoBack()) {
      router.back();
      return;
    }
    router.replace(profileRoute as any);
  };

  const faqItems = [1, 2, 3].map((item) => ({
    question: t(`help.question${item}`),
    answer: t(`help.answer${item}`),
  }));

  return (
    <ScrollView
      style={{ flex: 1, backgroundColor: colors.background }}
      contentContainerStyle={{ paddingBottom: scrollBottomPadding }}
      showsVerticalScrollIndicator={false}
    >
      {/* ─── Header morado ─────────────────────────────────── */}
      <View
        style={{
          backgroundColor: PURPLE,
          paddingTop: paddingTop + 16,
          paddingBottom: 48,
          paddingHorizontal: 24,
          borderBottomLeftRadius: 32,
          borderBottomRightRadius: 32,
        }}
      >
        {/* Fila superior: flecha + título + ícono */}
        <View
          style={{
            flexDirection: 'row',
            alignItems: 'center',
            justifyContent: 'space-between',
            marginBottom: 20,
          }}
        >
          <Pressable
            onPress={handleBack}
            style={{ marginRight: 16 }}
            hitSlop={{ top: 12, bottom: 12, left: 12, right: 12 }}
          >
            <Feather name="arrow-left" size={24} color="white" />
          </Pressable>

          <Text
            style={{
              fontSize: 20,
              fontWeight: 'bold',
              color: 'white',
              flex: 1,
            }}
          >
            {t('help.title')}
          </Text>

          <View
            style={{
              width: 40,
              height: 40,
              borderRadius: 20,
              borderWidth: 2,
              borderColor: 'rgba(255,255,255,0.6)',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <Feather name="help-circle" size={22} color="white" />
          </View>
        </View>

        {/* Tarjeta principal superpuesta */}
        <View
          style={{
            backgroundColor: colors.surface,
            borderRadius: 24,
            padding: 20,
            flexDirection: 'row',
            alignItems: 'center',
            shadowColor: '#000',
            shadowOffset: { width: 0, height: 4 },
            shadowOpacity: 0.08,
            shadowRadius: 12,
            elevation: 4,
            marginBottom: -16,
          }}
        >
          <View
            style={{
              width: 56,
              height: 56,
              borderRadius: 16,
              backgroundColor: PURPLE_LIGHT,
              alignItems: 'center',
              justifyContent: 'center',
              marginRight: 16,
            }}
          >
            <Ionicons name="help-circle-outline" size={30} color={PURPLE} />
          </View>

          <View style={{ flex: 1 }}>
            <Text style={{ fontSize: 16, fontWeight: 'bold', color: colors.text }}>
              {t('help.needHelp')}
            </Text>
            <Text
              style={{
                fontSize: 12,
                color: '#8E8EA0',
                fontWeight: '500',
                marginTop: 4,
                lineHeight: 17,
              }}
            >
              {t('help.description')}
            </Text>
          </View>
        </View>
      </View>

      {/* Espaciado para compensar el card superpuesto */}
      <View style={{ height: 32 }} />

      {/* ─── Preguntas frecuentes ──────────────────────────── */}
      <View style={{ paddingHorizontal: 24, marginBottom: 16 }}>
        <View
          style={{
            backgroundColor: colors.surface,
            borderRadius: 24,
            borderWidth: 1,
            borderColor: colors.border,
            shadowColor: '#000',
            shadowOffset: { width: 0, height: 2 },
            shadowOpacity: 0.04,
            shadowRadius: 6,
            elevation: 2,
            overflow: 'hidden',
            paddingVertical: 4,
          }}
        >
          {/* Título de sección */}
          <View
            style={{
              flexDirection: 'row',
              alignItems: 'center',
              paddingHorizontal: 16,
              paddingVertical: 16,
            }}
          >
            <Ionicons name="help-circle-outline" size={22} color={PURPLE} style={{ marginRight: 10 }} />
            <Text style={{ fontSize: 16, fontWeight: 'bold', color: colors.text }}>
              {t('help.faq')}
            </Text>
          </View>

          {/* Divisor */}
          <View style={{ height: 1, backgroundColor: colors.border, marginHorizontal: 16 }} />

          {faqItems.map((item, index) => (
            <View key={index}>
              <View style={{ paddingHorizontal: 16, paddingVertical: 14 }}>
                {/* Pregunta con bullet morado */}
                <View style={{ flexDirection: 'row', alignItems: 'flex-start', marginBottom: 4 }}>
                  <View
                    style={{
                      width: 8,
                      height: 8,
                      borderRadius: 4,
                      backgroundColor: PURPLE,
                      marginTop: 5,
                      marginRight: 10,
                    }}
                  />
                  <Text style={{ fontSize: 14, fontWeight: '700', color: colors.text, flex: 1 }}>
                    {item.question}
                  </Text>
                </View>
                {/* Respuesta alineada con el texto */}
                <View style={{ paddingLeft: 18 }}>
                  <Text style={{ fontSize: 13, color: '#8E8EA0', lineHeight: 18 }}>
                    {item.answer}
                  </Text>
                </View>
              </View>
              {index < faqItems.length - 1 && (
                <View style={{ height: 1, backgroundColor: colors.border, marginHorizontal: 16 }} />
              )}
            </View>
          ))}
        </View>
      </View>

      {/* ─── Soporte ───────────────────────────────────────── */}
      <View style={{ paddingHorizontal: 24, marginBottom: 16 }}>
        <View
          style={{
            backgroundColor: colors.surface,
            borderRadius: 24,
            borderWidth: 1,
            borderColor: colors.border,
            shadowColor: '#000',
            shadowOffset: { width: 0, height: 2 },
            shadowOpacity: 0.04,
            shadowRadius: 6,
            elevation: 2,
            padding: 20,
            flexDirection: 'row',
            alignItems: 'flex-start',
          }}
        >
          <View
            style={{
              width: 56,
              height: 56,
              borderRadius: 16,
              backgroundColor: BLUE_LIGHT,
              alignItems: 'center',
              justifyContent: 'center',
              marginRight: 16,
            }}
          >
            <Ionicons name="headset-outline" size={28} color={BLUE} />
          </View>

          <View style={{ flex: 1 }}>
            <Text style={{ fontSize: 16, fontWeight: 'bold', color: colors.text, marginBottom: 8 }}>
              {t('help.support')}
            </Text>
            <InfoRow label={t('help.email')} value="soporte@tutoria.unsaac.edu.pe" colors={colors} />
            <InfoRow label={t('help.service')} value={t('help.weekdays')} colors={colors} />
            <InfoRow label={t('help.hours')} value="8:00 AM - 5:00 PM" colors={colors} />
          </View>
        </View>
      </View>

      {/* ─── Guía rápida ───────────────────────────────────── */}
      <View style={{ paddingHorizontal: 24, marginBottom: 16 }}>
        <View
          style={{
            backgroundColor: colors.surface,
            borderRadius: 24,
            borderWidth: 1,
            borderColor: colors.border,
            shadowColor: '#000',
            shadowOffset: { width: 0, height: 2 },
            shadowOpacity: 0.04,
            shadowRadius: 6,
            elevation: 2,
            padding: 20,
            flexDirection: 'row',
            alignItems: 'flex-start',
          }}
        >
          <View
            style={{
              width: 56,
              height: 56,
              borderRadius: 16,
              backgroundColor: CYAN_LIGHT,
              alignItems: 'center',
              justifyContent: 'center',
              marginRight: 16,
            }}
          >
            <Ionicons name="book-outline" size={28} color={CYAN} />
          </View>

          <View style={{ flex: 1 }}>
            <Text style={{ fontSize: 16, fontWeight: 'bold', color: colors.text, marginBottom: 8 }}>
              {t('help.quickGuide')}
            </Text>
            <BulletText text={t('help.guideProfile')} />
            <BulletText text={t('help.guideCalendar')} />
            <BulletText text={t('help.guideTutorIA')} />
          </View>
        </View>
      </View>

      {/* ─── Mensaje final ─────────────────────────────────── */}
      <View style={{ paddingHorizontal: 24, marginBottom: 8 }}>
        <View
          style={{
            backgroundColor: colors.surface,
            borderRadius: 20,
            borderWidth: 1,
            borderColor: '#FFE8D6',
            shadowColor: '#000',
            shadowOffset: { width: 0, height: 2 },
            shadowOpacity: 0.04,
            shadowRadius: 6,
            elevation: 2,
            padding: 16,
            flexDirection: 'row',
            alignItems: 'center',
          }}
        >
          <View
            style={{
              width: 44,
              height: 44,
              borderRadius: 12,
              backgroundColor: ORANGE_LIGHT,
              alignItems: 'center',
              justifyContent: 'center',
              marginRight: 14,
            }}
          >
            <Ionicons name="information-circle-outline" size={26} color={ORANGE} />
          </View>
          <Text style={{ fontSize: 13, color: colors.text, flex: 1, lineHeight: 18 }}>
            {t('help.supportNotice')}
          </Text>
        </View>
      </View>
    </ScrollView>
  );
}

/* ── Componentes auxiliares ───────────────────────────────── */

function InfoRow({ label, value, colors }: { label: string; value: string; colors: any }) {
  return (
    <View style={{ flexDirection: 'row', marginBottom: 4, flexWrap: 'wrap' }}>
      <Text style={{ fontSize: 13, fontWeight: '700', color: colors.text, marginRight: 4 }}>
        {label}
      </Text>
      <Text style={{ fontSize: 13, color: '#8E8EA0', flex: 1 }}>{value}</Text>
    </View>
  );
}

function BulletText({ text }: { text: string }) {
  return (
    <View style={{ flexDirection: 'row', alignItems: 'flex-start', marginBottom: 4 }}>
      <Text style={{ color: '#8E8EA0', marginRight: 6, marginTop: 1, fontSize: 13 }}>•</Text>
      <Text style={{ fontSize: 13, color: '#8E8EA0', flex: 1, lineHeight: 18 }}>{text}</Text>
    </View>
  );
}
