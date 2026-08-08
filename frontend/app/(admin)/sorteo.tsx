import {
  View,
  Text,
  Pressable,
  Alert,
  ActivityIndicator,
  ScrollView,
  Platform,
  Modal,
  FlatList,
  TextInput
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useState, useCallback } from 'react';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import client from '../../src/api/client';
import { fetchAllPages } from '@/src/api/paginated';
import { useAuthStore } from '../../src/store/auth';
import { useFocusEffect } from 'expo-router';
import { useTheme } from '@/src/theme/ThemeContext';
import { useTranslation } from 'react-i18next';

const getSafeErrorMessage = (error: unknown): string =>
  error instanceof Error ? error.message : 'unknown_error';

type SelectorType = 'fromTutor' | 'toTutor' | 'student' | 'newTutor' | null;

export default function AsignacionesScreen() {
  const { colors } = useTheme();
  const { t } = useTranslation();
  const token = useAuthStore(state => state.token);

  const insets = useSafeAreaInsets();
  const minimumBottomPadding = Platform.OS === 'ios' ? 24 : 12;
  const bottomPadding = Math.max(insets.bottom, minimumBottomPadding);
  const tabBarBaseHeight = 62;
  const totalTabBarHeight = tabBarBaseHeight + bottomPadding;
  const scrollBottomPadding = totalTabBarHeight + 24;

  const [isExecuting, setIsExecuting] = useState(false);
  const [users, setUsers] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [selectedTutor, setSelectedTutor] = useState<number | null>(null);
  const [selectedStudent, setSelectedStudent] = useState<number | null>(null);
  const [isAssigning, setIsAssigning] = useState(false);

  // Bulk Transfer
  const [fromTutor, setFromTutor] = useState<number | null>(null);
  const [toTutor, setToTutor] = useState<number | null>(null);
  const [isTransferring, setIsTransferring] = useState(false);

  // Selector Modal state
  const [activeSelector, setActiveSelector] = useState<SelectorType>(null);
  const [selectorSearch, setSelectorSearch] = useState('');

  const fetchUsers = useCallback(async () => {
    setError(null);
    setLoading(true);
    try {
      const data = await fetchAllPages<any>('/admin/users', {
        config: { headers: { Authorization: `Bearer ${token}` } },
      });
      setUsers(data);
    } catch (error: unknown) {
      console.log('[AdminAssignments] No se pudieron cargar los datos:', getSafeErrorMessage(error));
      setError(
        t('errors.network', {
          defaultValue:
            'No fue posible conectarse con el servidor. Revisa tu conexión a internet.'
        })
      );
    } finally {
      setLoading(false);
    }
  }, [token, t]);

  useFocusEffect(
    useCallback(() => {
      fetchUsers();
    }, [fetchUsers])
  );

  const tutors = users.filter(u => u.role === 'tutor' && u.is_active);
  const students = users.filter(u => u.role === 'estudiante' && u.is_active);

  const openSelector = (type: SelectorType) => {
    setSelectorSearch('');
    setActiveSelector(type);
  };

  const closeSelector = () => {
    setSelectorSearch('');
    setActiveSelector(null);
  };

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
    } catch (error: unknown) {
      console.log('[AdminAssignments] Error en asignación manual:', getSafeErrorMessage(error));
      const detail = (error as any)?.response?.data?.detail;
      Alert.alert(t('common.error'), typeof detail === 'string' ? detail : t('admin.assignmentError'));
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
    } catch (error: unknown) {
      console.log('[AdminAssignments] Error en reasignación grupal:', getSafeErrorMessage(error));
      const detail = (error as any)?.response?.data?.detail;
      Alert.alert(t('common.error'), typeof detail === 'string' ? detail : t('admin.bulkError'));
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
            } catch (error: unknown) {
              console.log('[AdminAssignments] Error en ejecución de sorteo:', getSafeErrorMessage(error));
              const detail = (error as any)?.response?.data?.detail;
              Alert.alert(t('common.error'), typeof detail === 'string' ? detail : t('admin.drawError'));
            } finally {
              setIsExecuting(false);
            }
          }
        }
      ]
    );
  };

  const selectedFromTutorObj = tutors.find(t => t.id === fromTutor);
  const selectedToTutorObj = tutors.find(t => t.id === toTutor);
  const selectedStudentObj = students.find(s => s.id === selectedStudent);
  const selectedNewTutorObj = tutors.find(t => t.id === selectedTutor);

  const getModalTitle = () => {
    if (activeSelector === 'fromTutor') return t('admin.sourceTutor');
    if (activeSelector === 'toTutor') return t('admin.destinationTutor');
    if (activeSelector === 'student') return t('admin.selectStudent');
    if (activeSelector === 'newTutor') return t('admin.selectNewTutor');
    return '';
  };

  const getModalItems = () => {
    let list: any[] = [];
    if (activeSelector === 'fromTutor') {
      list = tutors;
    } else if (activeSelector === 'toTutor') {
      list = tutors.filter(t => t.id !== fromTutor);
    } else if (activeSelector === 'student') {
      list = students;
    } else if (activeSelector === 'newTutor') {
      list = tutors;
    }

    const query = selectorSearch.trim().toLowerCase();
    if (!query) return list;

    return list.filter(item => {
      const nameMatch = item.full_name?.toLowerCase().includes(query);
      const emailMatch = item.email ? item.email.toLowerCase().includes(query) : false;
      return nameMatch || emailMatch;
    });
  };

  const modalItems = getModalItems();

  return (
    <ScrollView
      className="flex-1 bg-background dark:bg-black p-4"
      contentContainerStyle={{ paddingBottom: scrollBottomPadding }}
    >
      {loading ? (
        <ActivityIndicator size="large" color={colors.primary} className="mt-10" />
      ) : error ? (
        <View
          style={{ backgroundColor: colors.surface }}
          className="p-6 rounded-2xl shadow-sm border border-red-200 dark:border-red-800 items-center my-6"
        >
          <Ionicons name="alert-circle" size={40} color="#DC2626" style={{ marginBottom: 12 }} />
          <Text className="text-text dark:text-white text-center font-medium mb-4 text-sm">
            {error}
          </Text>
          <Pressable
            onPress={fetchUsers}
            disabled={loading}
            style={{ backgroundColor: colors.primary }}
            className={`px-6 py-3 rounded-xl items-center shadow-sm ${loading ? 'opacity-50' : ''}`}
          >
            <Text className="text-white font-bold">{t('common.retry')}</Text>
          </Pressable>
        </View>
      ) : (
        <>
          {/* Sorteo Masivo */}
          <View
            style={{ backgroundColor: colors.surface, borderColor: colors.border }}
            className="p-6 rounded-2xl shadow-sm border mb-6 items-center"
          >
            <Ionicons name="shuffle" size={50} color={colors.primary} style={{ marginBottom: 10 }} />
            <Text className="text-xl font-bold text-text dark:text-white text-center mb-2">
              {t('admin.semesterDraw')}
            </Text>
            <Text className="text-text/70 dark:text-white/70 text-center mb-6 text-sm">
              {t('admin.drawDescription')}
            </Text>

            <Pressable
              onPress={handleSorteo}
              disabled={isExecuting}
              style={{ backgroundColor: colors.primary }}
              className={`w-full py-3 rounded-xl items-center shadow-sm ${isExecuting ? 'opacity-50' : ''}`}
            >
              {isExecuting ? (
                <ActivityIndicator color="white" />
              ) : (
                <Text className="text-white font-bold">{t('admin.runAlgorithm')}</Text>
              )}
            </Pressable>
          </View>

          {/* Reasignación Grupal (Bulk Transfer) */}
          <View
            style={{ backgroundColor: colors.surface, borderColor: colors.border }}
            className="p-6 rounded-2xl shadow-sm border mb-6"
          >
            <Text className="text-xl font-bold text-text dark:text-white mb-2">
              {t('admin.bulkReassignment')}
            </Text>
            <Text className="text-xs text-text/70 dark:text-white/70 mb-4">
              {t('admin.bulkDescription')}
            </Text>

            {/* Selector Tutor de origen */}
            <Text className="text-xs font-bold text-text dark:text-white mb-1">
              {t('admin.sourceTutor')}
            </Text>
            <Pressable
              onPress={() => openSelector('fromTutor')}
              style={{
                backgroundColor: colors.surface,
                borderColor: fromTutor ? colors.primary : colors.border,
              }}
              className="flex-row items-center justify-between p-3.5 rounded-xl border mb-4 shadow-sm"
            >
              <Text
                style={{ color: fromTutor ? colors.text : colors.textSecondary }}
                className={`flex-1 mr-2 text-sm ${fromTutor ? 'font-semibold' : ''}`}
                numberOfLines={1}
              >
                {selectedFromTutorObj ? selectedFromTutorObj.full_name : t('common.select', { defaultValue: 'Seleccionar' })}
              </Text>
              <Ionicons
                name="chevron-down"
                size={18}
                color={fromTutor ? colors.primary : colors.textSecondary}
              />
            </Pressable>

            {/* Selector Tutor de destino */}
            <Text className="text-xs font-bold text-text dark:text-white mb-1">
              {t('admin.destinationTutor')}
            </Text>
            <Pressable
              onPress={() => openSelector('toTutor')}
              style={{
                backgroundColor: colors.surface,
                borderColor: toTutor ? colors.primary : colors.border,
              }}
              className="flex-row items-center justify-between p-3.5 rounded-xl border mb-6 shadow-sm"
            >
              <Text
                style={{ color: toTutor ? colors.text : colors.textSecondary }}
                className={`flex-1 mr-2 text-sm ${toTutor ? 'font-semibold' : ''}`}
                numberOfLines={1}
              >
                {selectedToTutorObj ? selectedToTutorObj.full_name : t('common.select', { defaultValue: 'Seleccionar' })}
              </Text>
              <Ionicons
                name="chevron-down"
                size={18}
                color={toTutor ? colors.primary : colors.textSecondary}
              />
            </Pressable>

            <Pressable
              onPress={handleBulkTransfer}
              disabled={isTransferring || !fromTutor || !toTutor || fromTutor === toTutor}
              style={{ backgroundColor: colors.primary }}
              className={`w-full py-3 rounded-xl items-center shadow-sm ${(isTransferring || !fromTutor || !toTutor || fromTutor === toTutor) ? 'opacity-50' : ''}`}
            >
              {isTransferring ? (
                <ActivityIndicator color="white" />
              ) : (
                <Text className="text-white font-bold">{t('admin.transferGroup')}</Text>
              )}
            </Pressable>
          </View>

          {/* Asignación Manual */}
          <View
            style={{ backgroundColor: colors.surface, borderColor: colors.border }}
            className="p-6 rounded-2xl shadow-sm border mb-6"
          >
            <Text className="text-xl font-bold text-text dark:text-white mb-4">
              {t('admin.exceptionManagement')}
            </Text>

            {/* Selector Estudiante */}
            <Text className="text-xs font-bold text-text dark:text-white mb-1">
              {t('admin.selectStudent')}
            </Text>
            <Pressable
              onPress={() => openSelector('student')}
              style={{
                backgroundColor: colors.surface,
                borderColor: selectedStudent ? colors.primary : colors.border,
              }}
              className="flex-row items-center justify-between p-3.5 rounded-xl border mb-4 shadow-sm"
            >
              <Text
                style={{ color: selectedStudent ? colors.text : colors.textSecondary }}
                className={`flex-1 mr-2 text-sm ${selectedStudent ? 'font-semibold' : ''}`}
                numberOfLines={1}
              >
                {selectedStudentObj ? selectedStudentObj.full_name : t('common.select', { defaultValue: 'Seleccionar' })}
              </Text>
              <Ionicons
                name="chevron-down"
                size={18}
                color={selectedStudent ? colors.primary : colors.textSecondary}
              />
            </Pressable>

            {/* Selector Nuevo Tutor */}
            <Text className="text-xs font-bold text-text dark:text-white mb-1">
              {t('admin.selectNewTutor')}
            </Text>
            <Pressable
              onPress={() => openSelector('newTutor')}
              style={{
                backgroundColor: colors.surface,
                borderColor: selectedTutor ? colors.primary : colors.border,
              }}
              className="flex-row items-center justify-between p-3.5 rounded-xl border mb-6 shadow-sm"
            >
              <Text
                style={{ color: selectedTutor ? colors.text : colors.textSecondary }}
                className={`flex-1 mr-2 text-sm ${selectedTutor ? 'font-semibold' : ''}`}
                numberOfLines={1}
              >
                {selectedNewTutorObj ? selectedNewTutorObj.full_name : t('common.select', { defaultValue: 'Seleccionar' })}
              </Text>
              <Ionicons
                name="chevron-down"
                size={18}
                color={selectedTutor ? colors.primary : colors.textSecondary}
              />
            </Pressable>

            <Pressable
              onPress={handleManualAssignment}
              disabled={isAssigning || !selectedStudent || !selectedTutor}
              style={{ backgroundColor: colors.primary }}
              className={`w-full py-3 rounded-xl items-center shadow-sm ${(isAssigning || !selectedStudent || !selectedTutor) ? 'opacity-50' : ''}`}
            >
              {isAssigning ? (
                <ActivityIndicator color="white" />
              ) : (
                <Text className="text-white font-bold">{t('admin.linkStudentTutor')}</Text>
              )}
            </Pressable>
          </View>
        </>
      )}

      {/* Modal de Selección Reutilizable */}
      <Modal
        visible={activeSelector !== null}
        animationType="slide"
        transparent
        onRequestClose={closeSelector}
      >
        <View className="flex-1 justify-end bg-black/50">
          <Pressable className="flex-1" onPress={closeSelector} />
          <View
            style={{ backgroundColor: colors.surface, maxHeight: '80%' }}
            className="rounded-t-3xl p-5 border-t border-gray-200 dark:border-gray-800"
          >
            {/* Header Modal */}
            <View className="flex-row items-center justify-between mb-4">
              <Text className="text-lg font-bold text-text dark:text-white">
                {getModalTitle()}
              </Text>
              <Pressable
                onPress={closeSelector}
                className="p-1 rounded-full bg-gray-100 dark:bg-gray-800"
              >
                <Ionicons name="close" size={20} color={colors.text} />
              </Pressable>
            </View>

            {/* Buscador */}
            <View
              style={{ backgroundColor: colors.background, borderColor: colors.border }}
              className="flex-row items-center px-3 py-2.5 rounded-xl border mb-4"
            >
              <Ionicons name="search" size={18} color={colors.textSecondary} />
              <TextInput
                value={selectorSearch}
                onChangeText={setSelectorSearch}
                placeholder={t('admin.searchUsers', { defaultValue: 'Buscar por nombre o correo...' })}
                placeholderTextColor={colors.textSecondary}
                className="flex-1 ml-2.5 text-text dark:text-white text-sm py-0.5"
                autoCapitalize="none"
                autoCorrect={false}
              />
              {selectorSearch.length > 0 ? (
                <Pressable onPress={() => setSelectorSearch('')}>
                  <Ionicons name="close-circle" size={18} color={colors.textSecondary} />
                </Pressable>
              ) : null}
            </View>

            {/* Lista Vertical */}
            <FlatList
              data={modalItems}
              keyExtractor={item => item.id.toString()}
              contentContainerStyle={{ paddingBottom: Math.max(insets.bottom, 16) }}
              showsVerticalScrollIndicator={true}
              ListEmptyComponent={
                <Text style={{ color: colors.textSecondary }} className="text-center py-8 italic text-sm">
                  {t('admin.noMatches', { defaultValue: 'No se encontraron resultados' })}
                </Text>
              }
              renderItem={({ item }) => {
                let isSelected = false;
                if (activeSelector === 'fromTutor') isSelected = fromTutor === item.id;
                else if (activeSelector === 'toTutor') isSelected = toTutor === item.id;
                else if (activeSelector === 'student') isSelected = selectedStudent === item.id;
                else if (activeSelector === 'newTutor') isSelected = selectedTutor === item.id;

                const handleSelect = () => {
                  if (activeSelector === 'fromTutor') {
                    setFromTutor(item.id);
                    if (toTutor === item.id) setToTutor(null);
                  } else if (activeSelector === 'toTutor') {
                    setToTutor(item.id);
                  } else if (activeSelector === 'student') {
                    setSelectedStudent(item.id);
                  } else if (activeSelector === 'newTutor') {
                    setSelectedTutor(item.id);
                  }
                  closeSelector();
                };

                return (
                  <Pressable
                    onPress={handleSelect}
                    style={{
                      backgroundColor: isSelected ? colors.primary : colors.surface,
                      borderColor: isSelected ? colors.primary : colors.border,
                    }}
                    className="flex-row items-center justify-between p-3.5 rounded-xl border mb-2.5 shadow-sm"
                  >
                    <View className="flex-1 mr-2">
                      <Text
                        style={{ color: isSelected ? '#FFFFFF' : colors.text }}
                        className={`text-sm ${isSelected ? 'font-bold' : ''}`}
                      >
                        {item.full_name}
                      </Text>
                      {item.email ? (
                        <Text
                          style={{ color: isSelected ? '#E0E7FF' : colors.textSecondary }}
                          className="text-xs mt-0.5"
                        >
                          {item.email}
                        </Text>
                      ) : null}
                    </View>
                    {isSelected ? (
                      <Ionicons name="checkmark-circle" size={20} color="#FFFFFF" />
                    ) : null}
                  </Pressable>
                );
              }}
            />
          </View>
        </View>
      </Modal>
    </ScrollView>
  );
}
