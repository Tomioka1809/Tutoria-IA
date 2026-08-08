import { View, Text, FlatList, Pressable, Alert, ActivityIndicator, Modal, TextInput, ScrollView, Platform } from 'react-native';
import { useState, useCallback } from 'react';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import client from '../../src/api/client';
import { fetchAllPages } from '@/src/api/paginated';
import { useAuthStore } from '../../src/store/auth';
import { useFocusEffect } from 'expo-router';
import { Feather } from '@expo/vector-icons';
import { useTheme } from '@/src/theme/ThemeContext';
import { useTranslation } from 'react-i18next';

const getSafeErrorMessage = (error: unknown): string =>
  error instanceof Error ? error.message : 'unknown_error';

export default function UsersApprovalScreen() {
  const { colors } = useTheme();
  const { t } = useTranslation();
  const token = useAuthStore(state => state.token);
  const insets = useSafeAreaInsets();

  const minimumBottomPadding = Platform.OS === 'ios' ? 24 : 12;
  const bottomPadding = Math.max(insets.bottom, minimumBottomPadding);
  const tabBarBaseHeight = 62;
  const totalTabBarHeight = tabBarBaseHeight + bottomPadding;
  const listBottomPadding = totalTabBarHeight + 24;

  const [users, setUsers] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<'tutor' | 'estudiante' | 'admin'>('tutor');
  const [searchQuery, setSearchQuery] = useState('');

  // Modal State: Create Admin
  const [modalVisible, setModalVisible] = useState(false);
  const [newEmail, setNewEmail] = useState('');
  const [newName, setNewName] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [isCreating, setIsCreating] = useState(false);

  // Modal State: Tutor Details
  const [tutorModalVisible, setTutorModalVisible] = useState(false);
  const [selectedTutor, setSelectedTutor] = useState<any>(null);
  const [newCapacity, setNewCapacity] = useState('');
  const [isUpdatingCapacity, setIsUpdatingCapacity] = useState(false);
  const [tutorStudents, setTutorStudents] = useState<any[]>([]);
  const [loadingTutorStudents, setLoadingTutorStudents] = useState(false);

  const fetchUsers = useCallback(async () => {
    setError(null);
    setLoading(true);
    try {
      const data = await fetchAllPages<any>('/admin/users', {
        config: { headers: { Authorization: `Bearer ${token}` } },
      });
      setUsers(data);
    } catch (error: unknown) {
      console.log('[AdminUsers] No se pudieron cargar los usuarios:', getSafeErrorMessage(error));
      setError(t('errors.network', {
        defaultValue: 'No fue posible conectarse con el servidor. Revisa tu conexión a internet.'
      }));
    } finally {
      setLoading(false);
    }
  }, [token, t]);

  useFocusEffect(
    useCallback(() => {
      fetchUsers();
    }, [fetchUsers])
  );

  const toggleStatus = (id: number, currentStatus: boolean, name: string) => {
    const action = currentStatus ? t('admin.deactivate') : t('admin.activate');
    Alert.alert(t('admin.confirmStatusTitle', { action }), t('admin.confirmStatusMessage', { action: action.toLowerCase(), name }), [
      { text: t('common.cancel'), style: "cancel" },
      { 
        text: action, 
        style: currentStatus ? "destructive" : "default",
        onPress: async () => {
          try {
            await client.patch(`/admin/users/${id}/status`, { is_active: !currentStatus }, {
              headers: { Authorization: `Bearer ${token}` }
            });
            fetchUsers();
          } catch(error: unknown) {
            console.log('[AdminUsers] Error al cambiar estado:', getSafeErrorMessage(error));
            Alert.alert(t('common.error'), t('admin.statusError'));
          }
        }
      }
    ]);
  };

  const handleCreateStaff = async () => {
    if (!newEmail || !newName || !newPassword) {
      Alert.alert(t('common.error'), t('admin.completeFields'));
      return;
    }
    setIsCreating(true);
    try {
      await client.post('/admin/users', {
        email: newEmail.trim().toLowerCase(),
        password: newPassword,
        full_name: newName,
        role: 'admin'
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      Alert.alert(t('common.success'), t('admin.adminCreated'));
      setModalVisible(false);
      setNewEmail('');
      setNewName('');
      setNewPassword('');
      fetchUsers();
    } catch(error: any) {
      console.log('[AdminUsers] Error al crear admin:', getSafeErrorMessage(error));
      Alert.alert(t('common.error'), error.response?.data?.detail || t('admin.createError'));
    } finally {
      setIsCreating(false);
    }
  };

  const openTutorDetails = async (tutor: any) => {
    if (tutor.role !== 'tutor') return;
    setSelectedTutor(tutor);
    setNewCapacity(String(tutor.tutor_profile?.max_capacity || 15));
    setTutorModalVisible(true);
    setTutorStudents([]);
    
    setLoadingTutorStudents(true);
    try {
      const res = await client.get(`/admin/users/${tutor.id}/students`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setTutorStudents(res.data);
    } catch(error: unknown) {
      console.log('[AdminUsers] Error al obtener estudiantes del tutor:', getSafeErrorMessage(error));
    } finally {
      setLoadingTutorStudents(false);
    }
  };

  const handleUpdateCapacity = async () => {
    if (!newCapacity || isNaN(Number(newCapacity))) {
      Alert.alert(t('common.error'), t('admin.validCapacity'));
      return;
    }
    setIsUpdatingCapacity(true);
    try {
      await client.patch(`/admin/users/${selectedTutor.id}/capacity`, { max_capacity: parseInt(newCapacity, 10) }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      Alert.alert(t('common.success'), t('admin.capacityUpdated'));
      setTutorModalVisible(false);
      fetchUsers();
    } catch (error: any) {
      console.log('[AdminUsers] Error al actualizar capacidad:', getSafeErrorMessage(error));
      Alert.alert(t('common.error'), error.response?.data?.detail || t('admin.updateError'));
    } finally {
      setIsUpdatingCapacity(false);
    }
  };

  const filteredUsers = users.filter(u => {
    const matchesRole = u.role === filter;
    const matchesSearch = u.full_name.toLowerCase().includes(searchQuery.toLowerCase()) || 
                          u.email.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesRole && matchesSearch;
  });

  const renderItem = ({ item }: { item: any }) => (
    <Pressable 
      onPress={() => item.role === 'tutor' ? openTutorDetails(item) : null}
      className={`p-4 rounded-xl shadow-sm mb-3 flex-row justify-between items-center border dark:bg-black dark:border-white ${item.is_active ? 'bg-surface border-primary/20' : 'bg-gray-200 border-gray-300 opacity-80'}`}
    >
      <View className="flex-1">
        <View className="flex-row items-center mb-1">
          <Text className="text-lg font-bold text-text dark:text-white flex-shrink" numberOfLines={1}>{item.full_name}</Text>
          {item.role === 'tutor' && (
            <View className="ml-2 bg-purple-100 dark:bg-purple-900/40 px-2 py-0.5 rounded-md border border-purple-200 dark:border-purple-800">
              <Text className="text-[10px] font-bold text-purple-800 dark:text-purple-300">
                {t('admin.load', { current: item.current_load || 0, max: item.tutor_profile?.max_capacity || 15 })}
              </Text>
            </View>
          )}
        </View>
        <Text className="text-primary dark:text-white text-xs mb-2">{item.email}</Text>
        <View className={`self-start px-2 py-0.5 rounded-full ${item.is_active ? 'bg-green-100 dark:bg-green-900/40' : 'bg-red-100 dark:bg-red-900/40'}`}>
          <Text className={`text-[10px] font-bold ${item.is_active ? 'text-green-800 dark:text-green-300' : 'text-red-800 dark:text-red-300'}`}>
            {item.is_active ? t('admin.active') : t('admin.inactive')}
          </Text>
        </View>
      </View>
      <Pressable 
        onPress={(e) => { e.stopPropagation(); toggleStatus(item.id, item.is_active, item.full_name); }}
        className={`${item.is_active ? 'bg-red-500' : 'bg-primary'} py-2 px-4 rounded-lg ml-2`}
      >
        <Text className="text-white font-bold text-xs">{item.is_active ? t('admin.deactivate') : t('admin.activate')}</Text>
      </Pressable>
    </Pressable>
  );

  return (
    <View className="flex-1 bg-background dark:bg-black p-4">
      <View className="flex-row justify-between items-center mb-4 mt-2">
        <Text className="text-xl font-bold text-text dark:text-white">{t('admin.userManagement')}</Text>
        <Pressable 
          onPress={() => setModalVisible(true)}
          className="bg-primary px-3 py-2 rounded-lg flex-row items-center shadow-sm"
        >
          <Feather name="plus" size={16} color="white" />
          <Text className="text-white font-bold ml-1 text-xs">Admin</Text>
        </Pressable>
      </View>

      <View style={{ backgroundColor: colors.surface }} className="flex-row rounded-xl items-center px-4 py-2 mb-4 border border-primary/20 dark:border-white">
        <Feather name="search" size={20} color={colors.primary} />
        <TextInput 
          value={searchQuery}
          onChangeText={setSearchQuery}
          placeholder={t('admin.searchUsers')}
          className="flex-1 ml-2 text-text dark:text-white"
          placeholderTextColor={colors.textSecondary}
        />
      </View>

      <View style={{ backgroundColor: colors.surface }} className="flex-row rounded-xl p-1 mb-4 shadow-sm border border-primary/20 dark:border-white">
        <Pressable 
          className={`flex-1 py-2 rounded-lg items-center ${filter === 'tutor' ? 'bg-primary' : ''}`}
          onPress={() => setFilter('tutor')}
        >
          <Text className={`font-bold ${filter === 'tutor' ? 'text-white' : 'text-text/60 dark:text-white'}`}>{t('admin.tutors')}</Text>
        </Pressable>
        <Pressable 
          className={`flex-1 py-2 rounded-lg items-center ${filter === 'estudiante' ? 'bg-primary' : ''}`}
          onPress={() => setFilter('estudiante')}
        >
          <Text className={`font-bold ${filter === 'estudiante' ? 'text-white' : 'text-text/60 dark:text-white'}`}>{t('admin.students')}</Text>
        </Pressable>
        <Pressable 
          className={`flex-1 py-2 rounded-lg items-center ${filter === 'admin' ? 'bg-primary' : ''}`}
          onPress={() => setFilter('admin')}
        >
          <Text className={`font-bold ${filter === 'admin' ? 'text-white' : 'text-text/60 dark:text-white'}`}>{t('admin.admins')}</Text>
        </Pressable>
      </View>

      {loading ? (
        <ActivityIndicator size="large" color={colors.primary} className="mt-10" />
      ) : error ? (
        <View style={{ backgroundColor: colors.surface }} className="p-6 rounded-2xl shadow-sm border border-red-200 dark:border-red-800 items-center my-6">
          <Feather name="alert-circle" size={40} color="#DC2626" style={{ marginBottom: 12 }} />
          <Text className="text-text dark:text-white text-center font-medium mb-4 text-sm">
            {error}
          </Text>
          <Pressable
            onPress={fetchUsers}
            disabled={loading}
            style={{ backgroundColor: colors.primary }}
            className={`px-6 py-3 rounded-xl items-center shadow-sm ${loading ? 'opacity-70' : ''}`}
          >
            <Text className="text-white font-bold text-sm">{t('common.retry')}</Text>
          </Pressable>
        </View>
      ) : filteredUsers.length === 0 ? (
        <Text className="text-primary dark:text-white text-center mt-10">{t('admin.noUsers')}</Text>
      ) : (
        <FlatList 
          data={filteredUsers}
          keyExtractor={item => item.id.toString()}
          renderItem={renderItem}
          contentContainerStyle={{ paddingBottom: listBottomPadding }}
        />
      )}

      {/* Modal Crear Personal */}
      <Modal visible={modalVisible} animationType="slide" transparent={true}>
        <View className="flex-1 justify-end bg-black/50">
          <View style={{ backgroundColor: colors.surface }} className="p-6 rounded-t-3xl shadow-lg border border-transparent dark:border-white">
            <View className="flex-row justify-between items-center mb-6">
              <Text className="text-xl font-bold text-text dark:text-white">{t('admin.registerAdmin')}</Text>
              <Pressable onPress={() => setModalVisible(false)}>
                <Feather name="x" size={24} color={colors.text} />
              </Pressable>
            </View>

            <View className="mb-4">
              <Text className="text-xs font-bold text-text dark:text-white mb-2">{t('admin.fullName')}</Text>
              <TextInput 
                value={newName} onChangeText={setNewName}
                placeholder={t('admin.fullNamePlaceholder')}
                placeholderTextColor={colors.textSecondary}
                className="bg-gray-50 dark:bg-background border border-gray-200 dark:border-white rounded-xl px-4 py-3 text-text dark:text-white"
              />
            </View>
            <View className="mb-4">
              <Text className="text-xs font-bold text-text dark:text-white mb-2">{t('admin.email')}</Text>
              <TextInput 
                value={newEmail} onChangeText={setNewEmail}
                placeholder="correo@institucion.edu" keyboardType="email-address" autoCapitalize="none"
                placeholderTextColor={colors.textSecondary}
                className="bg-gray-50 dark:bg-background border border-gray-200 dark:border-white rounded-xl px-4 py-3 text-text dark:text-white"
              />
            </View>
            <View className="mb-8">
              <Text className="text-xs font-bold text-text dark:text-white mb-2">{t('admin.temporaryPassword')}</Text>
              <TextInput 
                value={newPassword} onChangeText={setNewPassword}
                placeholder={t('admin.temporaryPasswordPlaceholder')} secureTextEntry
                placeholderTextColor={colors.textSecondary}
                className="bg-gray-50 dark:bg-background border border-gray-200 dark:border-white rounded-xl px-4 py-3 text-text dark:text-white"
              />
            </View>

            <Pressable 
              onPress={handleCreateStaff}
              disabled={isCreating}
              className={`bg-primary w-full py-4 rounded-xl items-center shadow-sm ${isCreating ? 'opacity-70' : ''}`}
            >
              {isCreating ? <ActivityIndicator color="white" /> : <Text className="text-white font-bold">{t('admin.createAuthorize')}</Text>}
            </Pressable>
          </View>
        </View>
      </Modal>

      {/* Modal Detalles del Tutor */}
      <Modal visible={tutorModalVisible} animationType="slide" transparent={true}>
        <View className="flex-1 justify-end bg-black/50">
          <View style={{ backgroundColor: colors.surface }} className="p-6 rounded-t-3xl shadow-lg max-h-[90%] border border-transparent dark:border-white">
            {selectedTutor && (
              <>
                <View className="flex-row justify-between items-center mb-6">
                  <Text className="text-xl font-bold text-text dark:text-white">{t('admin.tutorDetails')}</Text>
                  <Pressable onPress={() => setTutorModalVisible(false)}>
                    <Feather name="x" size={24} color={colors.text} />
                  </Pressable>
                </View>

                <ScrollView showsVerticalScrollIndicator={false}>
                  <View className="bg-gray-50 dark:bg-background p-4 rounded-xl border border-gray-200 dark:border-white mb-6">
                    <Text className="text-lg font-bold text-text dark:text-white mb-1">{selectedTutor.full_name}</Text>
                    <Text className="text-primary dark:text-white text-sm mb-3">{selectedTutor.email}</Text>
                    
                    <View className="flex-row items-center mb-2">
                      <Feather name="map-pin" size={16} color={colors.primary} />
                      <Text className="ml-2 text-text dark:text-white text-sm">{t('admin.office', { value: selectedTutor.tutor_profile?.office_location || t('common.notSpecified') })}</Text>
                    </View>
                    <View className="flex-row items-center mb-2">
                      <Feather name="book-open" size={16} color={colors.primary} />
                      <Text className="ml-2 text-text dark:text-white text-sm">{t('admin.specialty', { value: selectedTutor.tutor_profile?.expertise_areas || t('common.notSpecified') })}</Text>
                    </View>
                    <View className="flex-row items-center">
                      <Feather name="users" size={16} color={colors.primary} />
                      <Text className="ml-2 text-text dark:text-white text-sm font-bold">{t('admin.currentStudents', { count: selectedTutor.current_load || 0 })}</Text>
                    </View>
                  </View>

                  <View className="mb-6">
                    <Text className="text-xs font-bold text-text dark:text-white mb-2">{t('admin.maxStudents')}</Text>
                    <View className="flex-row items-center">
                      <TextInput 
                        value={newCapacity} onChangeText={setNewCapacity}
                        placeholder="Ej. 15" keyboardType="numeric"
                        placeholderTextColor={colors.textSecondary}
                        className="flex-1 bg-gray-50 dark:bg-background border border-gray-200 dark:border-white rounded-xl px-4 py-3 text-text dark:text-white text-lg font-bold mr-2"
                      />
                      <Pressable 
                        onPress={handleUpdateCapacity}
                        disabled={isUpdatingCapacity}
                        className={`bg-primary px-4 py-3 rounded-xl items-center justify-center shadow-sm ${isUpdatingCapacity ? 'opacity-70' : ''}`}
                      >
                        {isUpdatingCapacity ? <ActivityIndicator size="small" color="white" /> : <Text className="text-white font-bold">{t('common.save')}</Text>}
                      </Pressable>
                    </View>
                    <Text className="text-[10px] text-gray-500 dark:text-white mt-1 ml-1">
                      {t('admin.capacityHint')}
                    </Text>
                  </View>

                  <View className="mb-4">
                    <Text className="text-xs font-bold text-text dark:text-white mb-2">{t('admin.studentsInCharge')}</Text>
                    {loadingTutorStudents ? (
                      <ActivityIndicator color={colors.primary} className="mt-4 mb-4" />
                    ) : tutorStudents.length === 0 ? (
                      <Text className="text-gray-500 dark:text-white text-sm">{t('admin.noAssignedStudents')}</Text>
                    ) : (
                      tutorStudents.map(student => (
                        <View key={student.id} className="bg-gray-50 dark:bg-background border border-gray-200 dark:border-white rounded-lg p-3 mb-2 flex-row items-center">
                          <View className="w-8 h-8 rounded-full bg-border items-center justify-center mr-3">
                            <Feather name="user" size={14} color={colors.primary} />
                          </View>
                          <View className="flex-1">
                            <Text className="text-text dark:text-white font-bold text-sm">{student.full_name}</Text>
                            <Text className="text-primary dark:text-white text-[10px]">{student.student_code || student.email}</Text>
                          </View>
                        </View>
                      ))
                    )}
                  </View>
                </ScrollView>
              </>
            )}
          </View>
        </View>
      </Modal>
    </View>
  );
}
