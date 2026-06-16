// app/(tabs)/editar-perfil.tsx
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

export default function EditarPerfilScreen() {
  const router = useRouter();
  const insets = useSafeAreaInsets();
  const paddingTop = Math.max(insets.top, 16);
  // Bottom tab bar height — keep button above it
  const tabBarHeight = Platform.OS === 'ios' ? 88 : 76;

  const { user, updateUser, profileImage, setProfileImage } = useAuthStore();

  // ── Form state ────────────────────────────────────────────────
  // We capture the store values ONCE per screen visit (via useFocusEffect)
  // so user edits are never overwritten by reactive effects.
  const [nombre, setNombre] = useState('');
  const [codigo, setCodigo] = useState('');
  const [carrera, setCarrera] = useState('');
  const [semestre, setSemestre] = useState('');
  const [pendingImage, setPendingImage] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  // Each time the screen comes into focus, reset fields to current store values
  useFocusEffect(
    useCallback(() => {
      setNombre(user?.full_name ?? 'Sebastián Quispe');
      setCodigo(user?.student_code ?? '2123456');
      setCarrera(user?.school ?? 'Ingeniería Informática y de Sistemas');
      setSemestre(user?.semester ?? 'VI Semestre');
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
  const handleSave = () => {
    if (!nombre.trim()) {
      Alert.alert('Campo requerido', 'El nombre no puede estar vacío.');
      return;
    }
    if (!codigo.trim()) {
      Alert.alert('Campo requerido', 'El código no puede estar vacío.');
      return;
    }
    if (!carrera.trim()) {
      Alert.alert('Campo requerido', 'La carrera no puede estar vacía.');
      return;
    }
    if (!semestre.trim()) {
      Alert.alert('Campo requerido', 'El semestre no puede estar vacío.');
      return;
    }

    setSaving(true);

    // Update global store — persisted via AsyncStorage (Zustand persist middleware)
    updateUser({
      full_name: nombre.trim(),
      student_code: codigo.trim(),
      school: carrera.trim(),
      semester: semestre.trim(),
    });
    setProfileImage(pendingImage);

    setSaving(false);

    Alert.alert('¡Listo!', 'Perfil actualizado correctamente.', [
      {
        text: 'OK',
        onPress: () => router.replace('/(tabs)/configuracion' as any),
      },
    ]);
  };

  // ── Render ────────────────────────────────────────────────────
  return (
    <View style={{ flex: 1, backgroundColor: '#F8F7FC' }}>
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
            backgroundColor: '#9A3BEE',
            paddingTop: paddingTop + 16,
            paddingBottom: 80,
            paddingHorizontal: 24,
            borderBottomLeftRadius: 36,
            borderBottomRightRadius: 36,
          }}
        >
          <View style={{ flexDirection: 'row', alignItems: 'center' }}>
            <Pressable
              onPress={() => router.replace('/(tabs)/configuracion' as any)}
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

        {/* ── White Card ──────────────────────────────────────── */}
        <View
          style={{
            marginHorizontal: 20,
            marginTop: -52,
            backgroundColor: 'white',
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
                  style={styles.avatar}
                  resizeMode="cover"
                />
              ) : (
                <View style={[styles.avatar, { backgroundColor: '#CBD5E1' }]} />
              )}

              {/* Pencil button */}
              <Pressable
                onPress={handlePickImage}
                style={styles.pencilBtn}
                hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}
              >
                <Feather name="edit-2" size={14} color="#9A3BEE" />
              </Pressable>
            </View>
            <Text
              style={{
                marginTop: 12,
                fontSize: 12,
                color: '#9A3BEE',
                fontWeight: '600',
              }}
            >
              Cambiar foto
            </Text>
          </View>

          {/* ── Fields ──────────────────────────────────────── */}

          {/* Nombre */}
          <View style={styles.fieldGroup}>
            <Text style={styles.label}>Nombre</Text>
            <TextInput
              style={styles.input}
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
            <Text style={styles.label}>Código</Text>
            <TextInput
              style={styles.input}
              value={codigo}
              onChangeText={setCodigo}
              placeholder="Ingresa tu código"
              placeholderTextColor="#C4C4D4"
              keyboardType="numeric"
              returnKeyType="next"
            />
          </View>

          {/* Carrera */}
          <View style={styles.fieldGroup}>
            <Text style={styles.label}>Carrera</Text>
            <TextInput
              style={styles.input}
              value={carrera}
              onChangeText={setCarrera}
              placeholder="Ingresa tu carrera"
              placeholderTextColor="#C4C4D4"
              returnKeyType="next"
              autoCorrect={false}
            />
          </View>

          {/* Semestre */}
          <View style={{ marginBottom: 28 }}>
            <Text style={styles.label}>Semestre</Text>
            <TextInput
              style={styles.input}
              value={semestre}
              onChangeText={setSemestre}
              placeholder="Ej: VI Semestre"
              placeholderTextColor="#C4C4D4"
              returnKeyType="done"
            />
          </View>

          {/* ── Guardar cambios ─────────────────────────────── */}
          <Pressable
            onPress={handleSave}
            disabled={saving}
            style={({ pressed }) => ({
              backgroundColor: pressed ? '#7B2FD4' : '#9A3BEE',
              borderRadius: 16,
              paddingVertical: 17,
              alignItems: 'center',
              justifyContent: 'center',
              shadowColor: '#9A3BEE',
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
                Guardar cambios
              </Text>
            )}
          </Pressable>
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
    color: '#1E1E2F',
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
    color: '#1E1E2F',
  },
});
