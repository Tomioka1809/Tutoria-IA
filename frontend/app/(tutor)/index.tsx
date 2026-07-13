import React, { useState, useCallback, useEffect } from 'react';
import { ScrollView, Pressable, Text, View, RefreshControl, ActivityIndicator, Modal } from 'react-native';
import { useRouter, useFocusEffect } from 'expo-router';
import { useDashboard } from '@/src/components/dashboard/useDashboard';
import { DashboardHeader } from '@/src/components/dashboard/DashboardHeader';
import { Feather } from '@expo/vector-icons';
import client from '@/src/api/client';
import { useAuthStore } from '@/src/store/auth';
import { useTheme } from '@/src/theme/ThemeContext';

export default function DashboardScreen() {
  const { colors } = useTheme();
  const router = useRouter();
  const token = useAuthStore(state => state.token);
  const { isLoading: dashboardLoading, onRefresh, firstName } = useDashboard();
  
  const [students, setStudents] = useState<any[]>([]);
  const [loadingStudents, setLoadingStudents] = useState(true);

  const [periods, setPeriods] = useState<string[]>([]);
  const [selectedPeriod, setSelectedPeriod] = useState<string>('');

  const [selectedStudent, setSelectedStudent] = useState<any>(null);
  const [modalVisible, setModalVisible] = useState(false);

  const fetchPeriods = async () => {
    try {
      const res = await client.get('/tutors/periods', {
        headers: { Authorization: `Bearer ${token}` }
      });
      setPeriods(res.data);
      if (res.data.length > 0 && !selectedPeriod) {
        setSelectedPeriod(res.data[0]);
      }
    } catch (e) {
      console.error('Failed to load academic periods', e);
    }
  };

  const fetchStudents = async (period?: string) => {
    setLoadingStudents(true);
    try {
      const res = await client.get('/tutors/students', {
        params: period ? { academic_period: period } : {},
        headers: { Authorization: `Bearer ${token}` }
      });
      setStudents(res.data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoadingStudents(false);
    }
  };

  useFocusEffect(
    useCallback(() => {
      fetchPeriods();
    }, [])
  );

  useEffect(() => {
    if (selectedPeriod) {
      fetchStudents(selectedPeriod);
    } else {
      fetchStudents();
    }
  }, [selectedPeriod]);

  const handleRefresh = async () => {
    onRefresh();
    await fetchPeriods();
    if (selectedPeriod) {
      await fetchStudents(selectedPeriod);
    } else {
      await fetchStudents();
    }
  };

  const openStudentDetails = (student: any) => {
    setSelectedStudent(student);
    setModalVisible(true);
  };

  const isLoading = dashboardLoading || loadingStudents;

  return (
    <ScrollView
      style={{ flex: 1, backgroundColor: colors.background }}
      contentContainerStyle={{ paddingBottom: 110 }}
      refreshControl={
        <RefreshControl
          refreshing={isLoading}
          onRefresh={handleRefresh}
          colors={[colors.primary]}
        />
      }
    >
      <DashboardHeader firstName={firstName} />

      {/* Action Button: Iniciar Chat */}
      <View style={{ paddingHorizontal: 24, marginBottom: 24 }}>
        <Pressable
          onPress={() => router.push('/(tutor)/tutoria')}
          style={{
            backgroundColor: colors.primary,
            borderRadius: 16,
            paddingVertical: 18,
            alignItems: 'center',
            justifyContent: 'center',
            shadowColor: colors.primary,
            shadowOffset: { width: 0, height: 4 },
            shadowOpacity: 0.2,
            shadowRadius: 6,
            elevation: 4,
          }}
        >
          <Text style={{ color: 'white', fontWeight: 'bold', fontSize: 16 }}>Iniciar Chat</Text>
        </Pressable>
      </View>

      <View style={{ paddingHorizontal: 24 }}>
        <Text style={{ fontSize: 18, fontWeight: 'bold', color: colors.text, marginBottom: 12 }}>
          Mis Alumnos Asignados
        </Text>

        {periods.length > 0 && (
          <ScrollView
            horizontal
            showsHorizontalScrollIndicator={false}
            contentContainerStyle={{ paddingBottom: 16 }}
          >
            {periods.map((p) => {
              const isSelected = selectedPeriod === p;
              return (
                <Pressable
                  key={p}
                  onPress={() => setSelectedPeriod(p)}
                  style={{
                    backgroundColor: isSelected ? colors.primary : colors.surface,
                    paddingHorizontal: 16,
                    paddingVertical: 8,
                    borderRadius: 20,
                    marginRight: 8,
                    borderWidth: 1,
                    borderColor: isSelected ? colors.primary : colors.border,
                    shadowColor: isSelected ? colors.primary : '#000',
                    shadowOffset: { width: 0, height: 2 },
                    shadowOpacity: isSelected ? 0.2 : 0.05,
                    shadowRadius: 3,
                    elevation: 2,
                  }}
                >
                  <Text
                    style={{
                      color: isSelected ? 'white' : colors.text,
                      fontWeight: isSelected ? 'bold' : 'normal',
                      fontSize: 14,
                    }}
                  >
                    {p}
                  </Text>
                </Pressable>
              );
            })}
          </ScrollView>
        )}
        
        {loadingStudents ? (
          <ActivityIndicator color={colors.primary} style={{ marginTop: 20 }} />
        ) : students.length === 0 ? (
          <View style={{ backgroundColor: colors.surface, padding: 24, borderRadius: 16, alignItems: 'center', borderWidth: 1, borderColor: '#E5E5E5' }}>
            <Feather name="users" size={32} color={colors.primary} style={{ marginBottom: 10 }} />
            <Text style={{ color: colors.primary, textAlign: 'center' }}>No tienes alumnos asignados para este periodo.</Text>
          </View>
        ) : (
          students.map(student => (
            <Pressable
              key={student.id}
              onPress={() => openStudentDetails(student)}
              style={{
                backgroundColor: colors.surface,
                padding: 16,
                borderRadius: 16,
                marginBottom: 12,
                flexDirection: 'row',
                alignItems: 'center',
                shadowColor: '#000',
                shadowOffset: { width: 0, height: 2 },
                shadowOpacity: 0.05,
                shadowRadius: 4,
                elevation: 2,
              }}
            >
              <View style={{ width: 40, height: 40, borderRadius: 20, backgroundColor: colors.border, alignItems: 'center', justifyContent: 'center', marginRight: 12 }}>
                <Feather name="user" size={20} color={colors.primary} />
              </View>
              <View style={{ flex: 1 }}>
                <Text style={{ fontSize: 16, fontWeight: 'bold', color: colors.text }}>
                  {student.full_name || 'Estudiante'}
                </Text>
                <Text style={{ fontSize: 12, color: colors.primary, marginTop: 2 }}>
                  {student.email}
                </Text>
              </View>
              <Feather name="chevron-right" size={20} color="#C4C4C4" />
            </Pressable>
          ))
        )}
      </View>

      {/* Modal Detalles del Estudiante */}
      <Modal visible={modalVisible} animationType="slide" transparent={true}>
        <View style={{ flex: 1, justifyContent: 'flex-end', backgroundColor: 'rgba(0,0,0,0.5)' }}>
          <View style={{ backgroundColor: colors.surface, padding: 24, borderTopLeftRadius: 24, borderTopRightRadius: 24 }}>
            {selectedStudent && (
              <>
                <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
                  <Text style={{ fontSize: 20, fontWeight: 'bold', color: colors.text }}>Perfil del Estudiante</Text>
                  <Pressable onPress={() => setModalVisible(false)}>
                    <Feather name="x" size={24} color={colors.text} />
                  </Pressable>
                </View>

                <View style={{ backgroundColor: colors.background, padding: 16, borderRadius: 16, marginBottom: 20 }}>
                  <Text style={{ fontSize: 18, fontWeight: 'bold', color: colors.text, marginBottom: 4 }}>{selectedStudent.full_name}</Text>
                  <Text style={{ color: colors.primary, fontSize: 14, marginBottom: 12 }}>{selectedStudent.email}</Text>
                  
                  <View style={{ flexDirection: 'row', alignItems: 'center', marginBottom: 8 }}>
                    <Feather name="hash" size={16} color={colors.primary} />
                    <Text style={{ marginLeft: 8, color: colors.text }}>
                      Código: <Text style={{ fontWeight: 'bold' }}>{selectedStudent.student_code || 'No registrado'}</Text>
                    </Text>
                  </View>
                  
                  <View style={{ flexDirection: 'row', alignItems: 'center', marginBottom: 8 }}>
                    <Feather name="book" size={16} color={colors.primary} />
                    <Text style={{ marginLeft: 8, color: colors.text }}>
                      Semestre: <Text style={{ fontWeight: 'bold' }}>{selectedStudent.student_profile?.current_semester || 'No registrado'}</Text>
                    </Text>
                  </View>
                  
                  <View style={{ flexDirection: 'row', alignItems: 'center', marginBottom: 8 }}>
                    <Feather name="phone" size={16} color={colors.primary} />
                    <Text style={{ marginLeft: 8, color: colors.text }}>
                      Celular: <Text style={{ fontWeight: 'bold' }}>{selectedStudent.phone_number || 'No registrado'}</Text>
                    </Text>
                  </View>

                  <View style={{ flexDirection: 'row', alignItems: 'center' }}>
                    <Feather name="activity" size={16} color={colors.primary} />
                    <Text style={{ marginLeft: 8, color: colors.text }}>
                      Estado Académico: <Text style={{ fontWeight: 'bold' }}>{selectedStudent.student_profile?.academic_status || 'No registrado'}</Text>
                    </Text>
                  </View>
                </View>
                
                <Pressable 
                  onPress={() => setModalVisible(false)}
                  style={{ backgroundColor: colors.text, padding: 16, borderRadius: 16, alignItems: 'center' }}
                >
                  <Text style={{ color: 'white', fontWeight: 'bold' }}>Cerrar</Text>
                </Pressable>
              </>
            )}
          </View>
        </View>
      </Modal>

    </ScrollView>
  );
}
