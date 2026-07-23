// src/components/profile/ProfileHeader.tsx
import React from 'react';
import { View, Text, Image } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { User } from '@/src/types';
import { useAuthStore } from '@/src/store/auth';
import { useTheme } from '@/src/theme/ThemeContext';
import { useTranslation } from 'react-i18next';

interface ProfileHeaderProps {
  user: User | null;
}

export function ProfileHeader({ user }: ProfileHeaderProps) {
  const { colors } = useTheme();
  const { t } = useTranslation();
  const insets = useSafeAreaInsets();
  const paddingTop = Math.max(insets.top, 16);
  const isStudent = user?.role === 'estudiante';
  const profileImage = useAuthStore((s) => s.profileImage);

  return (
    <View style={{
      backgroundColor: colors.primary,
      paddingTop: paddingTop + 16,
      paddingBottom: isStudent ? 48 : 24,
      paddingHorizontal: 24,
      borderBottomLeftRadius: 32,
      borderBottomRightRadius: 32,
    }}>
      {/* Top Header Row */}
      <View style={{
        marginBottom: 20,
      }}>
        <Text style={{
          fontSize: 24,
          fontWeight: 'bold',
          color: 'white',
        }}>
          {t('profile.title')}
        </Text>
      </View>
      
      {/* Student Card */}
      <View style={{
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
        marginBottom: isStudent ? 24 : 0,
      }}>
        {/* Avatar */}
        {profileImage ? (
          <Image
            source={{ uri: profileImage }}
            style={{
              width: 64,
              height: 64,
              borderRadius: 32,
              backgroundColor: '#CBD5E1',
              marginRight: 16,
            }}
            resizeMode="cover"
          />
        ) : (
          <View style={{
            width: 64,
            height: 64,
            borderRadius: 32,
            backgroundColor: '#CBD5E1',
            marginRight: 16,
          }} />
        )}
        
        {/* Student/Tutor details */}
        <View style={{ flex: 1 }}>
          <Text style={{
            fontSize: 18,
            fontWeight: 'bold',
            color: colors.text,
          }}>
            {user?.full_name || 'Sebastián Quispe'}
          </Text>
          <Text style={{
            fontSize: 13,
            color: colors.textSecondary,
            fontWeight: '500',
            marginTop: 4,
          }}>
            {t('profile.code', { code: isStudent ? (user?.student_code || t('common.notSpecified')) : (user?.tutor_code || t('common.notSpecified')) })}
          </Text>
          {isStudent ? (
            <>
              <Text style={{
                fontSize: 12,
                color: colors.textSecondary,
                fontWeight: '500',
                marginTop: 2,
              }} numberOfLines={1}>
                {user?.email || 'estudiante@unsaac.edu.pe'}
              </Text>
              <Text style={{
                fontSize: 11,
                color: colors.textSecondary,
                fontWeight: '500',
                marginTop: 2,
              }}>
                {t('profile.semester', { semester: user?.current_semester || t('common.notSpecified') })}
              </Text>
            </>
          ) : (
            <Text style={{
              fontSize: 12,
              color: colors.textSecondary,
              fontWeight: '500',
              marginTop: 2,
            }} numberOfLines={1}>
              {user?.email || 'tutor@unsaac.edu.pe'}
            </Text>
          )}
        </View>
      </View>

      {/* "Mi tutor" Section Title */}
      {isStudent && (
        <Text style={{
          fontSize: 16,
          fontWeight: 'bold',
          color: colors.text,
          marginTop: 8,
          marginBottom: 4,
        }}>
          {t('profile.myTutor')}
        </Text>
      )}
    </View>
  );
}

