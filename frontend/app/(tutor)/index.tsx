import React, { useState, useCallback, useRef } from 'react';
import { ScrollView, Pressable, Text, View, RefreshControl, ActivityIndicator, Modal, Platform } from 'react-native';
import { useRouter, useFocusEffect } from 'expo-router';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useDashboard } from '@/src/components/dashboard/useDashboard';
import { DashboardHeader } from '@/src/components/dashboard/DashboardHeader';
import { Feather } from '@expo/vector-icons';
import client from '@/src/api/client';
import { useAuthStore } from '@/src/store/auth';
import { useTheme } from '@/src/theme/ThemeContext';
import { useTranslation } from 'react-i18next';

const getSafeErrorMessage = (error: unknown): string =>
  error instanceof Error ? error.message : 'unknown_error';

export default function DashboardScreen() {
  const { colors } = useTheme();
  const { t } = useTranslation();
  const router = useRouter();
  const token = useAuthStore(state => state.token);
  const { isLoading: dashboardLoading, onRefresh, firstName } = useDashboard();
  
  const insets = useSafeAreaInsets();
  const minimumBottomPadding = Platform.OS === 'ios' ? 24 : 12;
  const bottomPadding = Math.max(insets.bottom, minimumBottomPadding);
  const tabBarBaseHeight = 62;
  const totalTabBarHeight = tabBarBaseHeight + bottomPadding;
  const scrollBottomPadding = totalTabBarHeight + 24;

  const [students, setStudents] = useState<any[]>([]);
  const [loadingStudents, setLoadingStudents] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);

  const [periods, setPeriods] = useState<string[]>([]);
  const [selectedPeriod, setSelectedPeriod] = useState<string>('');
  const selectedPeriodRef = useRef<string>('');

  const [selectedStudent, setSelectedStudent] = useState<any>(null);
  const [modalVisible, setModalVisible] = useState(false);

  const fetchPeriods = useCallback(async (): Promise<string[]> => {
    try {
      const res = await client.get('/tutors/periods', {
        headers: { Authorization: `Bearer ${token}` }
      });
      const data = Array.isArray(res.data) ? res.data : [];
      setPeriods(data);
      return data;
    } catch (e) {
      console.log(
        '[TutorDashboard] No se pudieron cargar los periodos:',
        getSafeErrorMessage(e)
      );
      throw e;
    }
  }, [token]);

  const fetchStudents = useCallback(async (period?: string) => {
    setLoadingStudents(true);
    try {
      const res = await client.get('/tutors/students', {
        params: period ? { academic_period: period } : {},
        headers: { Authorization: `Bearer ${token}` }
      });
      setStudents(Array.isArray(res.data) ? res.data : []);
    } catch (e) {
      console.log(
        '[TutorDashboard] No se pudieron cargar los estudiantes:',
        getSafeErrorMessage(e)
      );
      throw e;
    } finally {
      setLoadingStudents(false);
    }
  }, [token]);

  const loadTutorData = useCallback(async (customPeriod?: string) => {
    setLoadingStudents(true);
    setLoadError(null);
    try {
      const periodList = await fetchPeriods();
      let effectivePeriod = customPeriod ?? selectedPeriodRef.current;

      if (periodList.length > 0) {
        if (!effectivePeriod || !periodList.includes(effectivePeriod)) {
          effectivePeriod = periodList[0];
        }
      } else {
        effectivePeriod = '';
      }

      selectedPeriodRef.current = effectivePeriod;
      setSelectedPeriod(effectivePeriod);
      await fetchStudents(effectivePeriod);
      setLoadError(null);
    } catch (e) {
      console.log(
        '[TutorDashboard] No se pudo cargar el dashboard:',
        getSafeErrorMessage(e)
      );
      setLoadError(
        t('errors.network', {
          defaultValue: 'No fue posible conectarse con el servidor. Revisa tu conexión a internet.'
        })
      );
    } finally {
      setLoadingStudents(false);
    }
  }, [fetchPeriods, fetchStudents, t]);

  useFocusEffect(
    useCallback(() => {
      loadTutorData();
    }, [loadTutorData])
  );

  const handleSelectPeriod = useCallback(async (period: string) => {
    if (period === selectedPeriodRef.current) return;
    selectedPeriodRef.current = period;
    setSelectedPeriod(period);
    setLoadError(null);
    try {
      await fetchStudents(period);
    } catch (e) {
      console.log(
        '[TutorDashboard] No se pudieron cargar los estudiantes:',
        getSafeErrorMessage(e)
      );
      setLoadError(
        t('errors.network', {
          defaultValue: 'No fue posible conectarse con el servidor. Revisa tu conexión a internet.'
        })
      );
    }
  }, [fetchStudents, t]);

  const handleRefresh = async () => {
    setLoadError(null);
    onRefresh();
    await loadTutorData();
  };

  const openStudentDetails = (student: any) => {
    setSelectedStudent(student);
    setModalVisible(true);
  };

  const isLoading = dashboardLoading || loadingStudents;

  return (
    <ScrollView
      style={{ flex: 1, backgroundColor: colors.background }}
      contentContainerStyle={{ paddingBottom: scrollBottomPadding }}
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
          <Text style={{ color: 'white', fontWeight: 'bold', fontSize: 16 }}>{t('dashboard.startChat')}</Text>
        </Pressable>
      </View>

      <View style={{ paddingHorizontal: 24 }}>
        <Text style={{ fontSize: 18, fontWeight: 'bold', color: colors.text, marginBottom: 12 }}>
          {t('dashboard.assignedStudents')}
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
                  onPress={() => handleSelectPeriod(p)}
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
        ) : loadError ? (
          <View style={{ backgroundColor: colors.surface, padding: 24, borderRadius: 16, alignItems: 'center', borderWidth: 1, borderColor: colors.border }}>
            <Feather name="alert-circle" size={32} color={colors.danger} style={{ marginBottom: 10 }} />
            <Text style={{ color: colors.text, textAlign: 'center', marginBottom: 16 }}>{loadError}</Text>
            <Pressable
              onPress={() => loadTutorData()}
              style={{
                backgroundColor: colors.primary,
                paddingHorizontal: 20,
                paddingVertical: 10,
                borderRadius: 12,
              }}
            >
              <Text style={{ color: 'white', fontWeight: 'bold' }}>{t('common.retry')}</Text>
            </Pressable>
          </View>
        ) : students.length === 0 ? (
          <View style={{ backgroundColor: colors.surface, padding: 24, borderRadius: 16, alignItems: 'center', borderWidth: 1, borderColor: colors.border }}>
            <Feather name="users" size={32} color={colors.primary} style={{ marginBottom: 10 }} />
            <Text style={{ color: colors.primary, textAlign: 'center' }}>{t('dashboard.noAssignedStudents')}</Text>
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
                  {student.full_name || t('dashboard.student')}
                </Text>
                <Text style={{ fontSize: 12, color: colors.primary, marginTop: 2 }}>
                  {student.email}
                </Text>
              </View>
              <Feather name="chevron-right" size={20} color={colors.textSecondary} />
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
                  <Text style={{ fontSize: 20, fontWeight: 'bold', color: colors.text }}>{t('dashboard.studentProfile')}</Text>
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
                      {t('profile.codeLabel')}: <Text style={{ fontWeight: 'bold' }}>{selectedStudent.student_code || t('dashboard.notRegistered')}</Text>
                    </Text>
                  </View>
                  
                  <View style={{ flexDirection: 'row', alignItems: 'center', marginBottom: 8 }}>
                    <Feather name="book" size={16} color={colors.primary} />
                    <Text style={{ marginLeft: 8, color: colors.text }}>
                      {t('dashboard.semester')}: <Text style={{ fontWeight: 'bold' }}>{selectedStudent.student_profile?.current_semester || t('dashboard.notRegistered')}</Text>
                    </Text>
                  </View>
                  
                  <View style={{ flexDirection: 'row', alignItems: 'center', marginBottom: 8 }}>
                    <Feather name="phone" size={16} color={colors.primary} />
                    <Text style={{ marginLeft: 8, color: colors.text }}>
                      {t('dashboard.phone')}: <Text style={{ fontWeight: 'bold' }}>{selectedStudent.phone_number || t('dashboard.notRegistered')}</Text>
                    </Text>
                  </View>

                  <View style={{ flexDirection: 'row', alignItems: 'center' }}>
                    <Feather name="activity" size={16} color={colors.primary} />
                    <Text style={{ marginLeft: 8, color: colors.text }}>
                      {t('dashboard.academicStatus')}: <Text style={{ fontWeight: 'bold' }}>{selectedStudent.student_profile?.academic_status || t('dashboard.notRegistered')}</Text>
                    </Text>
                  </View>
                </View>
                
                <Pressable 
                  onPress={() => setModalVisible(false)}
                  style={{ backgroundColor: colors.primary, padding: 16, borderRadius: 16, alignItems: 'center' }}
                >
                  <Text style={{ color: 'white', fontWeight: 'bold' }}>{t('common.close')}</Text>
                </Pressable>
              </>
            )}
          </View>
        </View>
      </Modal>

    </ScrollView>
  );
}
