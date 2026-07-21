import { View, Text, Pressable, Alert, ActivityIndicator, ScrollView } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useState, useCallback } from 'react';
import client from '../../src/api/client';
import { useAuthStore } from '../../src/store/auth';
import { useFocusEffect } from 'expo-router';
import { useTheme } from '@/src/theme/ThemeContext';

export default function AsignacionesScreen() {
  const { colors } = useTheme();
  const token = useAuthStore(state => state.token);
  const [isExecuting, setIsExecuting] = useState(false);
  const [users, setUsers] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  
  const [selectedTutor, setSelectedTutor] = useState<number | null>(null);
  const [selectedStudent, setSelectedStudent] = useState<number | null>(null);
  const [isAssigning, setIsAssigning] = useState(false);

  // Bulk Transfer
  const [fromTutor, setFromTutor] = useState<number | null>(null);
  const [toTutor, setToTutor] = useState<number | null>(null);
  const [isTransferring, setIsTransferring] = useState(false);

  const fetchUsers = async () => {
    try {
      const res = await client.get('/admin/users', {
        headers: { Authorization: `Bearer ${token}` }
      });
      setUsers(res.data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useFocusEffect(
    useCallback(() => {
      fetchUsers();
    }, [])
  );

  const tutors = users.filter(u => u.role === 'tutor' && u.is_active);
  const students = users.filter(u => u.role === 'estudiante' && u.is_active);

  const handleManualAssignment = async () => {
    if (!selectedTutor || !selectedStudent) {
      Alert.alert("Error", "Debes seleccionar un estudiante y un tutor.");
      return;
    }

    setIsAssigning(true);
    try {
      await client.post('/admin/assignments', {
        student_id: selectedStudent,
        tutor_id: selectedTutor,
        academic_period: "2026-I",
        service_type_id: 1
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      Alert.alert("Éxito", "Estudiante asignado correctamente.");
      setSelectedStudent(null);
      setSelectedTutor(null);
    } catch (e: any) {
      console.error(e);
      Alert.alert("Error", e.response?.data?.detail || "Hubo un problema al asignar.");
    } finally {
      setIsAssigning(false);
    }
  };

  const handleBulkTransfer = async () => {
    if (!fromTutor || !toTutor) {
      Alert.alert("Error", "Debes seleccionar ambos tutores.");
      return;
    }
    if (fromTutor === toTutor) {
      Alert.alert("Error", "El tutor de origen y destino no pueden ser el mismo.");
      return;
    }

    setIsTransferring(true);
    try {
      const res = await client.post('/admin/assignments/bulk-transfer', {
        from_tutor_id: fromTutor,
        to_tutor_id: toTutor,
        academic_period: "2026-I"
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      Alert.alert("Éxito", res.data.message);
      setFromTutor(null);
      setToTutor(null);
    } catch (e: any) {
      console.error(e);
      Alert.alert("Error", e.response?.data?.detail || "Problema en la reasignación grupal.");
    } finally {
      setIsTransferring(false);
    }
  };

  const handleSorteo = () => {
    Alert.alert(
      "Confirmar Sorteo", 
      "¿Ejecutar el sorteo automático? Asignará a los estudiantes sin tutor con los docentes disponibles (Max 15 c/u).",
      [
        { text: "Cancelar", style: "cancel" },
        { 
          text: "Ejecutar", 
          style: "destructive",
          onPress: async () => {
            setIsExecuting(true);
            try {
              const res = await client.post('/admin/sorteo', null, {
                headers: { Authorization: `Bearer ${token}` }
              });
              Alert.alert("Sorteo Finalizado", res.data.message);
            } catch (e: any) {
              console.error(e);
              Alert.alert("Error", e.response?.data?.detail || "Falló el sorteo.");
            } finally {
              setIsExecuting(false);
            }
          }
        }
      ]
    );
  };

  return (
    <ScrollView className="flex-1 bg-background dark:bg-black p-4">
      {/* Sorteo Masivo */}
      <View style={{ backgroundColor: colors.surface }} className=" p-6 rounded-2xl shadow-sm border border-primary/20 dark:border-white mb-6 items-center">
        <Ionicons name="shuffle" size={50} color={colors.primary} style={{ marginBottom: 10 }} />
        <Text className="text-xl font-bold text-text dark:text-white text-center mb-2">Sorteo Semestral</Text>
        <Text className="text-primary dark:text-white text-center mb-6 text-sm">
          Asigna alumnos huérfanos a docentes activos de forma equilibrada.
        </Text>
        
        <Pressable 
          onPress={handleSorteo}
          disabled={isExecuting}
          className={`bg-primary w-full py-3 rounded-xl items-center shadow-sm ${isExecuting ? 'opacity-70' : ''}`}
        >
          {isExecuting ? (
            <ActivityIndicator color="white" />
          ) : (
            <Text className="text-white font-bold">Ejecutar Algoritmo</Text>
          )}
        </Pressable>
      </View>

      {/* Reasignación Grupal (Bulk Transfer) */}
      <View style={{ backgroundColor: colors.surface }} className=" p-6 rounded-2xl shadow-sm border border-primary/20 dark:border-white mb-6">
        <Text className="text-xl font-bold text-text dark:text-white mb-2">Reasignación Grupal</Text>
        <Text className="text-xs text-primary dark:text-white mb-4">Mueve a todos los alumnos de un tutor a otro en caso de baja o emergencia.</Text>
        
        {loading ? (
          <ActivityIndicator color={colors.primary} />
        ) : (
          <>
            <Text className="text-xs font-bold text-text dark:text-white mb-1">Tutor de Origen (Quien se va)</Text>
            <ScrollView horizontal showsHorizontalScrollIndicator={false} className="mb-4">
              {tutors.map(t => (
                <Pressable
                  key={`from-${t.id}`}
                  onPress={() => setFromTutor(t.id)}
                  className={`mr-2 px-3 py-2 rounded-lg border dark:bg-white dark:border-white ${fromTutor === t.id ? 'bg-red-500 border-red-500' : 'bg-gray-50 border-gray-200'}`}
                >
                  <Text className={fromTutor === t.id ? 'text-white dark:text-black font-bold' : 'text-text dark:text-black'}>{t.full_name}</Text>
                </Pressable>
              ))}
            </ScrollView>

            <Text className="text-xs font-bold text-text dark:text-white mb-1">Tutor de Destino (Quien recibe)</Text>
            <ScrollView horizontal showsHorizontalScrollIndicator={false} className="mb-6">
              {tutors.map(t => (
                <Pressable
                  key={`to-${t.id}`}
                  onPress={() => setToTutor(t.id)}
                  className={`mr-2 px-3 py-2 rounded-lg border dark:bg-white dark:border-white ${toTutor === t.id ? 'bg-green-500 border-green-500' : 'bg-gray-50 border-gray-200'}`}
                >
                  <Text className={toTutor === t.id ? 'text-white dark:text-black font-bold' : 'text-text dark:text-black'}>{t.full_name}</Text>
                </Pressable>
              ))}
            </ScrollView>

            <Pressable 
              onPress={handleBulkTransfer}
              disabled={isTransferring || !fromTutor || !toTutor}
              className={`bg-text w-full py-3 rounded-xl items-center shadow-sm ${(!fromTutor || !toTutor) ? 'opacity-50' : ''}`}
            >
              {isTransferring ? (
                <ActivityIndicator color="white" />
              ) : (
                <Text className="text-white font-bold">Transferir Grupo</Text>
              )}
            </Pressable>
          </>
        )}
      </View>

      {/* Asignación Manual */}
      <View style={{ backgroundColor: colors.surface }} className=" p-6 rounded-2xl shadow-sm border border-primary/20 dark:border-white mb-10">
        <Text className="text-xl font-bold text-text dark:text-white mb-4">Manejo de Excepciones</Text>
        
        {loading ? (
          <ActivityIndicator color={colors.primary} />
        ) : (
          <>
            <Text className="text-xs font-bold text-text dark:text-white mb-1">Seleccionar Estudiante</Text>
            <ScrollView horizontal showsHorizontalScrollIndicator={false} className="mb-4">
              {students.length === 0 ? (
                <Text className="text-gray-400 dark:text-white italic py-2">No hay estudiantes activos.</Text>
              ) : students.map(s => (
                <Pressable
                  key={s.id}
                  onPress={() => setSelectedStudent(s.id)}
                  className={`mr-2 px-3 py-2 rounded-lg border dark:bg-white dark:border-white ${selectedStudent === s.id ? 'bg-primary border-primary' : 'bg-gray-50 border-gray-200'}`}
                >
                  <Text className={selectedStudent === s.id ? 'text-white dark:text-black font-bold' : 'text-text dark:text-black'}>{s.full_name}</Text>
                </Pressable>
              ))}
            </ScrollView>

            <Text className="text-xs font-bold text-text dark:text-white mb-1">Seleccionar Nuevo Tutor</Text>
            <ScrollView horizontal showsHorizontalScrollIndicator={false} className="mb-6">
              {tutors.length === 0 ? (
                <Text className="text-gray-400 dark:text-white italic py-2">No hay tutores activos.</Text>
              ) : tutors.map(t => (
                <Pressable
                  key={t.id}
                  onPress={() => setSelectedTutor(t.id)}
                  className={`mr-2 px-3 py-2 rounded-lg border dark:bg-white dark:border-white ${selectedTutor === t.id ? 'bg-green-500 border-green-500' : 'bg-gray-50 border-gray-200'}`}
                >
                  <Text className={selectedTutor === t.id ? 'text-white dark:text-black font-bold' : 'text-text dark:text-black'}>{t.full_name}</Text>
                </Pressable>
              ))}
            </ScrollView>

            <Pressable 
              onPress={handleManualAssignment}
              disabled={isAssigning || !selectedStudent || !selectedTutor}
              className={`bg-text w-full py-3 rounded-xl items-center shadow-sm ${(!selectedStudent || !selectedTutor) ? 'opacity-50' : ''}`}
            >
              {isAssigning ? (
                <ActivityIndicator color="white" />
              ) : (
                <Text className="text-white font-bold">Vincular Alumno-Tutor</Text>
              )}
            </Pressable>
          </>
        )}
      </View>
    </ScrollView>
  );
}
