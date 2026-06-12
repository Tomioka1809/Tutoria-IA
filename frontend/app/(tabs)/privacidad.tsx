import React from 'react';
import { View, Text, ScrollView, Pressable, Switch } from 'react-native';
import { useRouter } from 'expo-router';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import Feather from '@expo/vector-icons/Feather';
import Ionicons from '@expo/vector-icons/Ionicons';

export default function PrivacidadScreen() {
  const router = useRouter();
  const insets = useSafeAreaInsets();
  const paddingTop = Math.max(insets.top, 16);

  const [hideAcademicInfo, setHideAcademicInfo] = React.useState(true);
  const [visibleOnlyTutors, setVisibleOnlyTutors] = React.useState(false);

  return (
    <ScrollView
      style={{ flex: 1, backgroundColor: '#F8F7FC' }}
      contentContainerStyle={{ paddingBottom: 130 }}
      showsVerticalScrollIndicator={false}
    >
      {/* Header Container */}
      <View style={{
        backgroundColor: '#9A3BEE',
        paddingTop: paddingTop + 16,
        paddingBottom: 48,
        paddingHorizontal: 24,
        borderBottomLeftRadius: 32,
        borderBottomRightRadius: 32,
      }}>
        {/* Top Header Row */}
        <View style={{
          flexDirection: 'row',
          alignItems: 'center',
          marginBottom: 20,
        }}>
          <Pressable onPress={() => router.replace('/(tabs)/profile' as any)} style={{ marginRight: 16 }}>
            <Feather name="arrow-left" size={24} color="white" />
          </Pressable>
          <Text style={{
            fontSize: 20,
            fontWeight: 'bold',
            color: 'white',
          }}>
            Privacidad
          </Text>
        </View>

        {/* Top Information Card */}
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
          marginBottom: -16, // overlap slightly with the bottom boundary
        }}>
          {/* Shield Lock Icon inside circle */}
          <View style={{
            width: 56,
            height: 56,
            borderRadius: 28,
            backgroundColor: '#F3E8FF',
            alignItems: 'center',
            justifyContent: 'center',
            marginRight: 16,
          }}>
            <Ionicons name="shield-outline" size={26} color="#9A3BEE" />
          </View>

          {/* Text details */}
          <View style={{ flex: 1 }}>
            <Text style={{
              fontSize: 16,
              fontWeight: 'bold',
              color: '#111130',
            }}>
              Tu privacidad es importante
            </Text>
            <Text style={{
              fontSize: 12,
              color: '#8E8EA0',
              fontWeight: '500',
              marginTop: 4,
              lineHeight: 16,
            }}>
              Controla cómo se muestra y protege tu información dentro de TutorIA.
            </Text>
          </View>
        </View>
      </View>

      {/* Spacer to compensate for negative margin card overflow */}
      <View style={{ height: 32 }} />

      {/* Main Options Card */}
      <View style={{ paddingHorizontal: 24, marginBottom: 24 }}>
        <View style={{
          backgroundColor: 'white',
          borderRadius: 24,
          borderWidth: 1,
          borderColor: '#EEEDFE',
          shadowColor: '#000',
          shadowOffset: { width: 0, height: 2 },
          shadowOpacity: 0.04,
          shadowRadius: 6,
          elevation: 2,
          overflow: 'hidden',
        }}>
          {/* Option 1: Ocultar información académica */}
          <View style={{
            flexDirection: 'row',
            alignItems: 'center',
            justifyContent: 'space-between',
            paddingVertical: 16,
            paddingHorizontal: 16,
          }}>
            <View style={{ flexDirection: 'row', alignItems: 'center', flex: 1, marginRight: 8 }}>
              <View style={{
                width: 40,
                height: 40,
                borderRadius: 20,
                backgroundColor: '#F3E8FF',
                alignItems: 'center',
                justifyContent: 'center',
                marginRight: 16,
              }}>
                <Ionicons name="school-outline" size={22} color="#9A3BEE" />
              </View>
              <View style={{ flex: 1 }}>
                <Text style={{ fontSize: 15, fontWeight: 'bold', color: '#1E1E2F' }}>
                  Ocultar información académica
                </Text>
                <Text style={{ fontSize: 12, color: '#8E8EA0', marginTop: 2 }}>
                  Nadie podrá ver tus datos académicos
                </Text>
              </View>
            </View>
            <Switch
              value={hideAcademicInfo}
              onValueChange={setHideAcademicInfo}
              trackColor={{ false: '#E5E7EB', true: '#9A3BEE' }}
              thumbColor="white"
              ios_backgroundColor="#E5E7EB"
            />
          </View>

          {/* Divider */}
          <View style={{ height: 1, backgroundColor: '#F3F4F6', marginLeft: 72 }} />

          {/* Option 2: Perfil visible solo para tutores */}
          <View style={{
            flexDirection: 'row',
            alignItems: 'center',
            justifyContent: 'space-between',
            paddingVertical: 16,
            paddingHorizontal: 16,
          }}>
            <View style={{ flexDirection: 'row', alignItems: 'center', flex: 1, marginRight: 8 }}>
              <View style={{
                width: 40,
                height: 40,
                borderRadius: 20,
                backgroundColor: '#F3E8FF',
                alignItems: 'center',
                justifyContent: 'center',
                marginRight: 16,
              }}>
                <Feather name="user" size={20} color="#9A3BEE" />
              </View>
              <View style={{ flex: 1 }}>
                <Text style={{ fontSize: 15, fontWeight: 'bold', color: '#1E1E2F' }}>
                  Perfil visible solo para tutores
                </Text>
                <Text style={{ fontSize: 12, color: '#8E8EA0', marginTop: 2 }}>
                  Solo tus tutores podrán ver tu perfil
                </Text>
              </View>
            </View>
            <Switch
              value={visibleOnlyTutors}
              onValueChange={setVisibleOnlyTutors}
              trackColor={{ false: '#E5E7EB', true: '#9A3BEE' }}
              thumbColor="white"
              ios_backgroundColor="#E5E7EB"
            />
          </View>

          {/* Divider */}
          <View style={{ height: 1, backgroundColor: '#F3F4F6', marginLeft: 72 }} />

          {/* Option 3: Descargar mis datos */}
          <Pressable
            style={{
              flexDirection: 'row',
              alignItems: 'center',
              justifyContent: 'space-between',
              paddingVertical: 16,
              paddingHorizontal: 16,
            }}
            onPress={() => alert('Descargar mis datos en desarrollo')}
          >
            <View style={{ flexDirection: 'row', alignItems: 'center', flex: 1 }}>
              <View style={{
                width: 40,
                height: 40,
                borderRadius: 20,
                backgroundColor: '#F3E8FF',
                alignItems: 'center',
                justifyContent: 'center',
                marginRight: 16,
              }}>
                <Feather name="download" size={20} color="#9A3BEE" />
              </View>
              <View style={{ flex: 1 }}>
                <Text style={{ fontSize: 15, fontWeight: 'bold', color: '#1E1E2F' }}>
                  Descargar mis datos
                </Text>
                <Text style={{ fontSize: 12, color: '#8E8EA0', marginTop: 2 }}>
                  Obtén una copia de tu información
                </Text>
              </View>
            </View>
            <Feather name="chevron-right" size={20} color="#94A3B8" />
          </Pressable>

          {/* Divider */}
          <View style={{ height: 1, backgroundColor: '#F3F4F6', marginLeft: 72 }} />

          {/* Option 4: Eliminar mi cuenta */}
          <Pressable
            style={{
              flexDirection: 'row',
              alignItems: 'center',
              justifyContent: 'space-between',
              paddingVertical: 16,
              paddingHorizontal: 16,
            }}
            onPress={() => alert('Eliminar mi cuenta en desarrollo')}
          >
            <View style={{ flexDirection: 'row', alignItems: 'center', flex: 1 }}>
              <View style={{
                width: 40,
                height: 40,
                borderRadius: 20,
                backgroundColor: '#FEE2E2',
                alignItems: 'center',
                justifyContent: 'center',
                marginRight: 16,
              }}>
                <Feather name="trash-2" size={20} color="#EF4444" />
              </View>
              <View style={{ flex: 1 }}>
                <Text style={{ fontSize: 15, fontWeight: 'bold', color: '#EF4444' }}>
                  Eliminar mi cuenta
                </Text>
                <Text style={{ fontSize: 12, color: '#8E8EA0', marginTop: 2 }}>
                  Elimina tu cuenta y toda tu información
                </Text>
              </View>
            </View>
          </Pressable>
        </View>
      </View>

      {/* Safety Bottom Card */}
      <View style={{ paddingHorizontal: 24 }}>
        <View style={{
          backgroundColor: '#FAF5FF',
          borderWidth: 1,
          borderColor: '#E9D5FF',
          borderRadius: 20,
          padding: 16,
          flexDirection: 'row',
          alignItems: 'center',
        }}>
          <View style={{
            width: 40,
            height: 40,
            borderRadius: 20,
            backgroundColor: '#9A3BEE',
            alignItems: 'center',
            justifyContent: 'center',
            marginRight: 16,
          }}>
            <Ionicons name="shield-checkmark" size={22} color="white" />
          </View>
          <Text style={{
            fontSize: 14,
            fontWeight: '500',
            color: '#1E1E2F',
            flex: 1,
            lineHeight: 18,
          }}>
            TutorIA protege tu información personal.
          </Text>
        </View>
      </View>
    </ScrollView>
  );
}
