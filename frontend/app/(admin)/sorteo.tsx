import { View, Text, Pressable, Alert, ActivityIndicator, ScrollView } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useState, useCallback } from 'react';
import client from '../../src/api/client';
import { useAuthStore } from '../../src/store/auth';
import { useFocusEffect } from 'expo-router';
import { useTheme } from '@/src/theme/ThemeContext';
import { useTranslation } from 'react-i18next';

export default function AsignacionesScreen() {
  const { colors } = useTheme();
  const { t } = useTranslation();
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

  const fetchUsers = useCallback(async () => {
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
  }, [token]);

  useFocusEffect(
    useCallback(() => {
      fetchUsers();
    }, [fetchUsers])
  );

  const tutors = users.filter(u => u.role === 'tutor' && u.is_active);
  const students = users.filter(u => u.role === 'estudiante' && u.is_active);

  const handleManualAssignment = async () => {
    if (!selectedTutor || !selectedStudent) {
      Alert.alert(t('common.error'), t('admin.selectStudentTutor'));
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
      Alert.alert(t('common.success'), t('admin.studentAssigned'));
      setSelectedStudent(null);
      setSelectedTutor(null);
    } catch (e: any) {
      console.error(e);
      Alert.alert(t('common.error'), e.response?.data?.detail || t('admin.assignmentError'));
    } finally {
      setIsAssigning(false);
    }
  };

  const handleBulkTransfer = async () => {
    if (!fromTutor || !toTutor) {
      Alert.alert(t('common.error'), t('admin.selectBothTutors'));
      return;
    }
    if (fromTutor === toTutor) {
      Alert.alert(t('common.error'), t('admin.differentTutors'));
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
      Alert.alert(t('common.success'), res.data.message);
      setFromTutor(null);
      setToTutor(null);
    } catch (e: any) {
      console.error(e);
      Alert.alert(t('common.error'), e.response?.data?.detail || t('admin.bulkError'));
    } finally {
      setIsTransferring(false);
    }
  };

  const handleSorteo = () => {
    Alert.alert(
      t('admin.confirmDraw'),
      t('admin.confirmDrawMessage'),
      [
        { text: t('common.cancel'), style: "cancel" },
        { 
          text: t('admin.run'),
          style: "destructive",
          onPress: async () => {
            setIsExecuting(true);
            try {
              const res = await client.post('/admin/sorteo', null, {
                headers: { Authorization: `Bearer ${token}` }
              });
              Alert.alert(t('admin.drawFinished'), res.data.message);
            } catch (e: any) {
              console.error(e);
              Alert.alert(t('common.error'), e.response?.data?.detail || t('admin.drawError'));
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
        <Text className="text-xl font-bold text-text dark:text-white text-center mb-2">{t('admin.semesterDraw')}</Text>
        <Text className="text-primary dark:text-white text-center mb-6 text-sm">
          {t('admin.drawDescription')}
        </Text>
        
        <Pressable 
          onPress={handleSorteo}
          disabled={isExecuting}
          className={`bg-primary w-full py-3 rounded-xl items-center shadow-sm ${isExecuting ? 'opacity-70' : ''}`}
        >
          {isExecuting ? (
            <ActivityIndicator color="white" />
          ) : (
            <Text className="text-white font-bold">{t('admin.runAlgorithm')}</Text>
          )}
        </Pressable>
      </View>

      {/* Reasignación Grupal (Bulk Transfer) */}
      <View style={{ backgroundColor: colors.surface }} className=" p-6 rounded-2xl shadow-sm border border-primary/20 dark:border-white mb-6">
        <Text className="text-xl font-bold text-text dark:text-white mb-2">{t('admin.bulkReassignment')}</Text>
        <Text className="text-xs text-primary dark:text-white mb-4">{t('admin.bulkDescription')}</Text>
        
        {loading ? (
          <ActivityIndicator color={colors.primary} />
        ) : (
          <>
            <Text className="text-xs font-bold text-text dark:text-white mb-1">{t('admin.sourceTutor')}</Text>
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

            <Text className="text-xs font-bold text-text dark:text-white mb-1">{t('admin.destinationTutor')}</Text>
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
                <Text className="text-white font-bold">{t('admin.transferGroup')}</Text>
              )}
            </Pressable>
          </>
        )}
      </View>

      {/* Asignación Manual */}
      <View style={{ backgroundColor: colors.surface }} className=" p-6 rounded-2xl shadow-sm border border-primary/20 dark:border-white mb-10">
        <Text className="text-xl font-bold text-text dark:text-white mb-4">{t('admin.exceptionManagement')}</Text>
        
        {loading ? (
          <ActivityIndicator color={colors.primary} />
        ) : (
          <>
            <Text className="text-xs font-bold text-text dark:text-white mb-1">{t('admin.selectStudent')}</Text>
            <ScrollView horizontal showsHorizontalScrollIndicator={false} className="mb-4">
              {students.length === 0 ? (
                <Text className="text-gray-400 dark:text-white italic py-2">{t('admin.noActiveStudents')}</Text>
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

            <Text className="text-xs font-bold text-text dark:text-white mb-1">{t('admin.selectNewTutor')}</Text>
            <ScrollView horizontal showsHorizontalScrollIndicator={false} className="mb-6">
              {tutors.length === 0 ? (
                <Text className="text-gray-400 dark:text-white italic py-2">{t('admin.noActiveTutors')}</Text>
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
                <Text className="text-white font-bold">{t('admin.linkStudentTutor')}</Text>
              )}
            </Pressable>
          </>
        )}
      </View>
    </ScrollView>
  );
}
