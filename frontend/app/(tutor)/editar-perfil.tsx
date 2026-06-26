// app/(tutor)/editar-perfil.tsx
import React, { useState, useRef, useCallback } from 'react';
import {
  View,
  Text,
  TextInput,
  Pressable,
  ScrollView,
  Platform,
  Alert,
  Image,
  ActivityIndicator,
  StyleSheet,
} from 'react-native';
import { useFocusEffect } from 'expo-router';
import { useRouter } from 'expo-router';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import Feather from '@expo/vector-icons/Feather';
import * as ImagePicker from 'expo-image-picker';
import { useAuthStore } from '@/src/store/auth';
import { useTheme } from '@/src/theme/ThemeContext';

export default function EditarPerfilScreen() {
  const { colors } = useTheme();
  const router = useRouter();
  const insets = useSafeAreaInsets();
  const paddingTop = Math.max(insets.top, 16);
  // Bottom tab bar height — keep button above it
  const tabBarHeight = Platform.OS === 'ios' ? 88 : 76;

  const { user, updateProfile, profileImage, setProfileImage } = useAuthStore();

  // ── Form state ────────────────────────────────────────────────
  const [nombre, setNombre] = useState('');
  const [codigo, setCodigo] = useState('');
  const [celular, setCelular] = useState('');
  const [experiencia, setExperiencia] = useState('');
  const [oficina, setOficina] = useState('');
  const [pendingImage, setPendingImage] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  // Each time the screen comes into focus, reset fields to current store values
  useFocusEffect(
    useCallback(() => {
      setNombre(user?.full_name ?? '');
      setCodigo(user?.tutor_code ?? '');
      setCelular(user?.phone_number ?? '');
      setExperiencia(user?.expertise_areas ?? '');
      setOficina(user?.office_location ?? '');
      setPendingImage(profileImage);
    }, [user, profileImage])
  );

  // ── Image picker ──────────────────────────────────────────────
  const handlePickImage = async () => {
    const { status } = await ImagePicker.requestMediaLibraryPermissionsAsync();
    if (status !== 'granted') {
      Alert.alert(
        'Permiso requerido',
        'Necesitamos permiso para acceder a tu galería.'
      );
      return;
    }
    const result = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: 'images' as any,
      allowsEditing: true,
      aspect: [1, 1],
      quality: 0.8,
    });
    if (!result.canceled && result.assets.length > 0) {
      setPendingImage(result.assets[0].uri);
    }
  };

  // ── Save ──────────────────────────────────────────────────────
  const handleSave = async () => {
    if (!nombre.trim()) {
      Alert.alert('Campo requerido', 'El nombre no puede estar vacío.');
      return;
    }
    if (!codigo.trim()) {
      Alert.alert('Campo requerido', 'El código no puede estar vacío.');
      return;
    }

    setSaving(true);

    try {
      await updateProfile({
        full_name: nombre.trim(),
        tutor_code: codigo.trim(),
        phone_number: celular.trim(),
        expertise_areas: experiencia.trim(),
        office_location: oficina.trim(),
      });
      setProfileImage(pendingImage);
      
      Alert.alert('¡Listo!', 'Perfil actualizado correctamente.', [
        {
          text: 'OK',
          onPress: () => router.replace('/(tutor)/configuracion' as any),
        },
      ]);
    } catch (error) {
      Alert.alert('Error', 'No se pudo actualizar el perfil. Intenta de nuevo.');
    } finally {
      setSaving(false);
    }
  };

  // ── Render ────────────────────────────────────────────────────
  return (
    <View style={{ flex: 1, backgroundColor: colors.background }}>
      <ScrollView
        contentContainerStyle={{
          paddingBottom: tabBarHeight + 24,
        }}
        showsVerticalScrollIndicator={false}
        keyboardShouldPersistTaps="handled"
      >
        {/* ── Purple Header ───────────────────────────────────── */}
        <View
          style={{
            backgroundColor: colors.primary,
            paddingTop: paddingTop + 16,
            paddingBottom: 80,
            paddingHorizontal: 24,
            borderBottomLeftRadius: 36,
            borderBottomRightRadius: 36,
          }}
        >
          <View style={{ flexDirection: 'row', alignItems: 'center' }}>
            <Pressable
              onPress={() => router.replace('/(tutor)/configuracion' as any)}
              style={{ marginRight: 16, padding: 4 }}
              hitSlop={{ top: 12, bottom: 12, left: 12, right: 12 }}
            >
              <Feather name="arrow-left" size={24} color="white" />
            </Pressable>
            <Text
              style={{
                fontSize: 22,
                fontWeight: 'bold',
                color: 'white',
                letterSpacing: 0.3,
              }}
            >
              Editar perfil
            </Text>
          </View>
        </View>

        {/* ── Surface Card ──────────────────────────────────────── */}
        <View
          style={{
            marginHorizontal: 20,
            marginTop: -52,
            backgroundColor: colors.surface,
            borderRadius: 28,
            paddingHorizontal: 24,
            paddingBottom: 28,
            shadowColor: '#7B2FE0',
            shadowOffset: { width: 0, height: 6 },
            shadowOpacity: 0.1,
            shadowRadius: 20,
            elevation: 6,
          }}
        >
          {/* ── Avatar ──────────────────────────────────────── */}
          <View
            style={{ alignItems: 'center', marginTop: -44, marginBottom: 28 }}
          >
            <View style={{ position: 'relative' }}>
              {pendingImage ? (
                <Image
                  source={{ uri: pendingImage }}
                  style={[styles.avatar, { borderColor: colors.surface }]}
                  resizeMode="cover"
                />
              ) : (
                <View style={[styles.avatar, { backgroundColor: '#CBD5E1', borderColor: colors.surface }]} />
              )}

              {/* Pencil button */}
              <Pressable
                onPress={handlePickImage}
                style={[styles.pencilBtn, { backgroundColor: colors.surface, borderColor: colors.border }]}
                hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}
              >
                <Feather name="edit-2" size={14} color={colors.primary} />
              </Pressable>
            </View>
            <Text
              style={{
                marginTop: 12,
                fontSize: 12,
                color: colors.primary,
                fontWeight: '600',
              }}
            >
              Cambiar foto
            </Text>
          </View>

          {/* ── Fields ──────────────────────────────────────── */}

          {/* Nombre */}
          <View style={styles.fieldGroup}>
            <Text style={[styles.label, { color: colors.text }]}>Nombre</Text>
            <TextInput style={[styles.input, { color: colors.text, backgroundColor: colors.background, borderColor: colors.border }]}
              value={nombre}
              onChangeText={setNombre}
              placeholder="Ingresa tu nombre"
              placeholderTextColor="#C4C4D4"
              returnKeyType="next"
              autoCorrect={false}
            />
          </View>

          {/* Código */}
          <View style={styles.fieldGroup}>
            <Text style={[styles.label, { color: colors.text }]}>Código</Text>
            <TextInput style={[styles.input, { color: colors.text, backgroundColor: colors.background, borderColor: colors.border }]}
              value={codigo}
              onChangeText={setCodigo}
              placeholder="Ingresa tu código"
              placeholderTextColor="#C4C4D4"
              keyboardType="numeric"
              returnKeyType="next"
            />
          </View>

          {/* Celular */}
          <View style={styles.fieldGroup}>
            <Text style={[styles.label, { color: colors.text }]}>Celular</Text>
            <TextInput style={[styles.input, { color: colors.text, backgroundColor: colors.background, borderColor: colors.border }]}
              value={celular}
              onChangeText={setCelular}
              placeholder="Ingresa tu celular"
              placeholderTextColor="#C4C4D4"
              keyboardType="phone-pad"
              returnKeyType="next"
            />
          </View>

          {/* Área de experiencia */}
          <View style={styles.fieldGroup}>
            <Text style={[styles.label, { color: colors.text }]}>Área de experiencia</Text>
            <TextInput style={[styles.input, { color: colors.text, backgroundColor: colors.background, borderColor: colors.border }]}
              value={experiencia}
              onChangeText={setExperiencia}
              placeholder="Ej. Redes, Base de Datos..."
              placeholderTextColor="#C4C4D4"
              returnKeyType="next"
            />
          </View>

          {/* Oficina */}
          <View style={{ marginBottom: 28 }}>
            <Text style={[styles.label, { color: colors.text }]}>Ubicación de Oficina</Text>
            <TextInput style={[styles.input, { color: colors.text, backgroundColor: colors.background, borderColor: colors.border }]}
              value={oficina}
              onChangeText={setOficina}
              placeholder="Ej. Pabellón B - 2do Piso"
              placeholderTextColor="#C4C4D4"
              returnKeyType="done"
            />
          </View>

          {/* ── Botones de acción ─────────────────────────────── */}
          <View style={{ flexDirection: 'row', justifyContent: 'space-between', marginTop: 8 }}>
            <Pressable
              onPress={() => router.replace('/(tutor)/configuracion' as any)}
              disabled={saving}
              style={({ pressed }) => ({
                flex: 1,
                backgroundColor: colors.background,
                borderWidth: 1,
                borderColor: colors.border,
                borderRadius: 16,
                paddingVertical: 17,
                alignItems: 'center',
                justifyContent: 'center',
                marginRight: 10,
                opacity: pressed ? 0.7 : 1,
              })}
            >
              <Text
                style={{
                  fontSize: 16,
                  fontWeight: 'bold',
                  color: colors.textSecondary,
                  letterSpacing: 0.5,
                }}
              >
                Cancelar
              </Text>
            </Pressable>

            <Pressable
              onPress={handleSave}
              disabled={saving}
              style={({ pressed }) => ({
                flex: 1,
                backgroundColor: pressed ? '#7B2FD4' : colors.primary,
                borderRadius: 16,
                paddingVertical: 17,
                alignItems: 'center',
                justifyContent: 'center',
                shadowColor: colors.primary,
                shadowOffset: { width: 0, height: 4 },
                shadowOpacity: 0.35,
                shadowRadius: 10,
                elevation: 6,
                opacity: saving ? 0.7 : 1,
              })}
            >
              {saving ? (
                <ActivityIndicator color="white" size="small" />
              ) : (
                <Text
                  style={{
                    fontSize: 16,
                    fontWeight: 'bold',
                    color: 'white',
                    letterSpacing: 0.5,
                  }}
                >
                  Confirmar
                </Text>
              )}
            </Pressable>
          </View>
        </View>
      </ScrollView>
    </View>
  );
}

// ── Styles ────────────────────────────────────────────────────────
const styles = StyleSheet.create({
  avatar: {
    width: 100,
    height: 100,
    borderRadius: 50,
    borderWidth: 3,
    borderColor: 'white',
  },
  pencilBtn: {
    position: 'absolute',
    bottom: 2,
    right: 2,
    width: 30,
    height: 30,
    borderRadius: 15,
    backgroundColor: 'white',
    alignItems: 'center',
    justifyContent: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.15,
    shadowRadius: 4,
    elevation: 4,
    borderWidth: 1,
    borderColor: '#EEEDFE',
  },
  fieldGroup: {
    marginBottom: 20,
  },
  label: {
    fontSize: 14,
    fontWeight: '700',
    /* color dynamically applied */
    marginBottom: 8,
  },
  input: {
    backgroundColor: '#FAFAFA',
    borderWidth: 1.5,
    borderColor: '#E5E7EB',
    borderRadius: 12,
    paddingHorizontal: 16,
    paddingVertical: Platform.OS === 'ios' ? 14 : 11,
    fontSize: 15,
    /* color dynamically applied */
  },
});
