// src/components/profile/ProfileHeader.tsx
import React from 'react';
import { View, Text, Pressable } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import Feather from '@expo/vector-icons/Feather';
import { User } from '@/src/types';

interface ProfileHeaderProps {
  user: User | null;
}

export function ProfileHeader({ user }: ProfileHeaderProps) {
  const insets = useSafeAreaInsets();
  const router = useRouter();
  const paddingTop = Math.max(insets.top, 16);
  const isStudent = user?.role === 'estudiante';

  return (
    <View style={{
      backgroundColor: '#9A3BEE',
      paddingTop: paddingTop + 16,
      paddingBottom: isStudent ? 48 : 24,
      paddingHorizontal: 24,
      borderBottomLeftRadius: 32,
      borderBottomRightRadius: 32,
    }}>
      {/* Top Header Row */}
      <View style={{
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: 20,
      }}>
        <Text style={{
          fontSize: 24,
          fontWeight: 'bold',
          color: 'white',
        }}>
          Perfil
        </Text>
        <Pressable onPress={() => router.push('/(tabs)/configuracion' as any)}>
          <Feather name="settings" size={24} color="white" />
        </Pressable>
      </View>
      
      {/* Student Card */}
      <View style={{
        backgroundColor: 'white',
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
        {/* Grey Avatar */}
        <View style={{
          width: 64,
          height: 64,
          borderRadius: 32,
          backgroundColor: '#CBD5E1',
          marginRight: 16,
        }} />
        
        {/* Student details */}
        <View style={{ flex: 1 }}>
          <Text style={{
            fontSize: 18,
            fontWeight: 'bold',
            color: '#111130',
          }}>
            {user?.full_name || 'Sebastián Quispe'}
          </Text>
          <Text style={{
            fontSize: 13,
            color: '#8E8EA0',
            fontWeight: '500',
            marginTop: 4,
          }}>
            Código: {user?.student_code || '2123456'}
          </Text>
          <Text style={{
            fontSize: 12,
            color: '#8E8EA0',
            fontWeight: '500',
            marginTop: 2,
          }} numberOfLines={1}>
            {user?.school || 'Ingeniería Informática y de Sistemas'}
          </Text>
          <Text style={{
            fontSize: 11,
            color: '#8E8EA0',
            fontWeight: '500',
            marginTop: 2,
          }}>
            VI Semestre
          </Text>
        </View>
      </View>

      {/* "Mi tutor" Section Title */}
      {isStudent && (
        <Text style={{
          fontSize: 16,
          fontWeight: 'bold',
          color: '#111130',
          marginTop: 8,
          marginBottom: 4,
        }}>
          Mi tutor
        </Text>
      )}
    </View>
  );
}
