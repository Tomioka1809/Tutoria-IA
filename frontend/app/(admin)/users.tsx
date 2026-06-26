import { View, Text, FlatList, Pressable, Alert, ActivityIndicator, Modal, TextInput, ScrollView } from 'react-native';
import { useState, useCallback } from 'react';
import client from '../../src/api/client';
import { useAuthStore } from '../../src/store/auth';
import { useFocusEffect } from 'expo-router';
import { Feather } from '@expo/vector-icons';
import { useTheme } from '@/src/theme/ThemeContext';

export default function UsersApprovalScreen() {
  const { colors } = useTheme();
  const token = useAuthStore(state => state.token);
  const [users, setUsers] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
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

  const toggleStatus = (id: number, currentStatus: boolean, name: string) => {
    const action = currentStatus ? "Desactivar" : "Activar";
    Alert.alert(`${action} Usuario`, `¿Estás seguro de ${action.toLowerCase()} a ${name}?`, [
      { text: "Cancelar", style: "cancel" },
      { 
        text: action, 
        style: currentStatus ? "destructive" : "default",
        onPress: async () => {
          try {
            await client.patch(`/admin/users/${id}/status`, { is_active: !currentStatus }, {
              headers: { Authorization: `Bearer ${token}` }
            });
            fetchUsers();
          } catch(e) {
            console.error(e);
            Alert.alert("Error", "No se pudo actualizar el estado.");
          }
        }
      }
    ]);
  };

  const handleCreateStaff = async () => {
    if (!newEmail || !newName || !newPassword) {
      Alert.alert("Error", "Completa todos los campos");
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
      Alert.alert("Éxito", "Administrador creado correctamente.");
      setModalVisible(false);
      setNewEmail('');
      setNewName('');
      setNewPassword('');
      fetchUsers();
    } catch(e: any) {
      console.error(e);
      Alert.alert("Error", e.response?.data?.detail || "No se pudo crear.");
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
    } catch(e) {
      console.error(e);
    } finally {
      setLoadingTutorStudents(false);
    }
  };

  const handleUpdateCapacity = async () => {
    if (!newCapacity || isNaN(Number(newCapacity))) {
      Alert.alert("Error", "Ingresa una capacidad válida.");
      return;
    }
    setIsUpdatingCapacity(true);
    try {
      await client.patch(`/admin/users/${selectedTutor.id}/capacity`, { max_capacity: parseInt(newCapacity, 10) }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      Alert.alert("Éxito", "Capacidad actualizada.");
      setTutorModalVisible(false);
      fetchUsers();
    } catch (e: any) {
      console.error(e);
      Alert.alert("Error", e.response?.data?.detail || "No se pudo actualizar.");
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
      className={`p-4 rounded-xl shadow-sm mb-3 flex-row justify-between items-center border ${item.is_active ? 'bg-surface border-primary/20' : 'bg-gray-200 border-gray-300 opacity-80'}`}
    >
      <View className="flex-1">
        <View className="flex-row items-center mb-1">
          <Text className="text-lg font-bold text-text flex-shrink" numberOfLines={1}>{item.full_name}</Text>
          {item.role === 'tutor' && (
            <View className="ml-2 bg-border px-2 py-0.5 rounded-md border border-primary/30">
              <Text className="text-[10px] font-bold text-primary">
                Carga: {item.current_load || 0}/{item.tutor_profile?.max_capacity || 15}
              </Text>
            </View>
          )}
        </View>
        <Text className="text-primary text-xs mb-2">{item.email}</Text>
        <View className={`self-start px-2 py-0.5 rounded-full ${item.is_active ? 'bg-green-100' : 'bg-red-100'}`}>
          <Text className={`text-[10px] font-bold ${item.is_active ? 'text-green-700' : 'text-red-700'}`}>
            {item.is_active ? 'ACTIVO' : 'INACTIVO'}
          </Text>
        </View>
      </View>
      <Pressable 
        onPress={(e) => { e.stopPropagation(); toggleStatus(item.id, item.is_active, item.full_name); }}
        className={`${item.is_active ? 'bg-red-500' : 'bg-primary'} py-2 px-4 rounded-lg ml-2`}
      >
        <Text className="text-white font-bold text-xs">{item.is_active ? 'Desactivar' : 'Activar'}</Text>
      </Pressable>
    </Pressable>
  );

  return (
    <View className="flex-1 bg-border p-4">
      <View className="flex-row justify-between items-center mb-4 mt-2">
        <Text className="text-xl font-bold text-text">Gestión de Usuarios</Text>
        <Pressable 
          onPress={() => setModalVisible(true)}
          className="bg-primary px-3 py-2 rounded-lg flex-row items-center shadow-sm"
        >
          <Feather name="plus" size={16} color="white" />
          <Text className="text-white font-bold ml-1 text-xs">Admin</Text>
        </Pressable>
      </View>

      <View style={{ backgroundColor: colors.surface }} className="flex-row  rounded-xl items-center px-4 py-2 mb-4 border border-primary/20">
        <Feather name="search" size={20} color={colors.primary} />
        <TextInput 
          value={searchQuery}
          onChangeText={setSearchQuery}
          placeholder="Buscar por nombre o correo..."
          className="flex-1 ml-2 text-text"
          placeholderTextColor="#A0A0A0"
        />
      </View>

      <View style={{ backgroundColor: colors.surface }} className="flex-row  rounded-xl p-1 mb-4 shadow-sm border border-primary/20">
        <Pressable 
          className={`flex-1 py-2 rounded-lg items-center ${filter === 'tutor' ? 'bg-primary' : ''}`}
          onPress={() => setFilter('tutor')}
        >
          <Text className={`font-bold ${filter === 'tutor' ? 'text-white' : 'text-text/60'}`}>Tutores</Text>
        </Pressable>
        <Pressable 
          className={`flex-1 py-2 rounded-lg items-center ${filter === 'estudiante' ? 'bg-primary' : ''}`}
          onPress={() => setFilter('estudiante')}
        >
          <Text className={`font-bold ${filter === 'estudiante' ? 'text-white' : 'text-text/60'}`}>Alumnos</Text>
        </Pressable>
        <Pressable 
          className={`flex-1 py-2 rounded-lg items-center ${filter === 'admin' ? 'bg-primary' : ''}`}
          onPress={() => setFilter('admin')}
        >
          <Text className={`font-bold ${filter === 'admin' ? 'text-white' : 'text-text/60'}`}>Admins</Text>
        </Pressable>
      </View>

      {loading ? (
        <ActivityIndicator size="large" color={colors.primary} className="mt-10" />
      ) : filteredUsers.length === 0 ? (
        <Text className="text-primary text-center mt-10">No hay usuarios en esta categoría.</Text>
      ) : (
        <FlatList 
          data={filteredUsers}
          keyExtractor={item => item.id.toString()}
          renderItem={renderItem}
          contentContainerStyle={{ paddingBottom: 20 }}
        />
      )}

      {/* Modal Crear Personal */}
      <Modal visible={modalVisible} animationType="slide" transparent={true}>
        <View className="flex-1 justify-end bg-black/50">
          <View style={{ backgroundColor: colors.surface }} className=" p-6 rounded-t-3xl shadow-lg">
            <View className="flex-row justify-between items-center mb-6">
              <Text className="text-xl font-bold text-text">Registrar Administrador</Text>
              <Pressable onPress={() => setModalVisible(false)}>
                <Feather name="x" size={24} color={colors.text} />
              </Pressable>
            </View>

            <View className="mb-4">
              <Text className="text-xs font-bold text-text mb-2">Nombre Completo</Text>
              <TextInput 
                value={newName} onChangeText={setNewName}
                placeholder="Ej. Juan Pérez"
                className="bg-gray-50 border border-gray-200 rounded-xl px-4 py-3 text-text"
              />
            </View>
            <View className="mb-4">
              <Text className="text-xs font-bold text-text mb-2">Correo Electrónico</Text>
              <TextInput 
                value={newEmail} onChangeText={setNewEmail}
                placeholder="correo@institucion.edu" keyboardType="email-address" autoCapitalize="none"
                className="bg-gray-50 border border-gray-200 rounded-xl px-4 py-3 text-text"
              />
            </View>
            <View className="mb-8">
              <Text className="text-xs font-bold text-text mb-2">Contraseña Temporal</Text>
              <TextInput 
                value={newPassword} onChangeText={setNewPassword}
                placeholder="Mínimo 6 caracteres" secureTextEntry
                className="bg-gray-50 border border-gray-200 rounded-xl px-4 py-3 text-text"
              />
            </View>

            <Pressable 
              onPress={handleCreateStaff}
              disabled={isCreating}
              className={`bg-primary w-full py-4 rounded-xl items-center shadow-sm ${isCreating ? 'opacity-70' : ''}`}
            >
              {isCreating ? <ActivityIndicator color="white" /> : <Text className="text-white font-bold">Crear y Autorizar</Text>}
            </Pressable>
          </View>
        </View>
      </Modal>

      {/* Modal Detalles del Tutor */}
      <Modal visible={tutorModalVisible} animationType="slide" transparent={true}>
        <View className="flex-1 justify-end bg-black/50">
          <View style={{ backgroundColor: colors.surface }} className=" p-6 rounded-t-3xl shadow-lg max-h-[90%]">
            {selectedTutor && (
              <>
                <View className="flex-row justify-between items-center mb-6">
                  <Text className="text-xl font-bold text-text">Detalles del Tutor</Text>
                  <Pressable onPress={() => setTutorModalVisible(false)}>
                    <Feather name="x" size={24} color={colors.text} />
                  </Pressable>
                </View>

                <ScrollView showsVerticalScrollIndicator={false}>
                  <View className="bg-gray-50 p-4 rounded-xl border border-gray-200 mb-6">
                    <Text className="text-lg font-bold text-text mb-1">{selectedTutor.full_name}</Text>
                    <Text className="text-primary text-sm mb-3">{selectedTutor.email}</Text>
                    
                    <View className="flex-row items-center mb-2">
                      <Feather name="map-pin" size={16} color={colors.primary} />
                      <Text className="ml-2 text-text text-sm">Oficina: {selectedTutor.tutor_profile?.office_location || 'No asignada'}</Text>
                    </View>
                    <View className="flex-row items-center mb-2">
                      <Feather name="book-open" size={16} color={colors.primary} />
                      <Text className="ml-2 text-text text-sm">Especialidad: {selectedTutor.tutor_profile?.expertise_areas || 'No especificada'}</Text>
                    </View>
                    <View className="flex-row items-center">
                      <Feather name="users" size={16} color={colors.primary} />
                      <Text className="ml-2 text-text text-sm font-bold">Alumnos Actuales: {selectedTutor.current_load || 0}</Text>
                    </View>
                  </View>

                  <View className="mb-6">
                    <Text className="text-xs font-bold text-text mb-2">Límite Máximo de Estudiantes</Text>
                    <View className="flex-row items-center">
                      <TextInput 
                        value={newCapacity} onChangeText={setNewCapacity}
                        placeholder="Ej. 15" keyboardType="numeric"
                        className="flex-1 bg-gray-50 border border-gray-200 rounded-xl px-4 py-3 text-text text-lg font-bold mr-2"
                      />
                      <Pressable 
                        onPress={handleUpdateCapacity}
                        disabled={isUpdatingCapacity}
                        className={`bg-primary px-4 py-3 rounded-xl items-center justify-center shadow-sm ${isUpdatingCapacity ? 'opacity-70' : ''}`}
                      >
                        {isUpdatingCapacity ? <ActivityIndicator size="small" color="white" /> : <Text className="text-white font-bold">Guardar</Text>}
                      </Pressable>
                    </View>
                    <Text className="text-[10px] text-gray-500 mt-1 ml-1">
                      El algoritmo respetará este límite exacto al asignar alumnos.
                    </Text>
                  </View>

                  <View className="mb-4">
                    <Text className="text-xs font-bold text-text mb-2">Alumnos a cargo</Text>
                    {loadingTutorStudents ? (
                      <ActivityIndicator color={colors.primary} className="mt-4 mb-4" />
                    ) : tutorStudents.length === 0 ? (
                      <Text className="text-gray-500 text-sm">Este tutor no tiene alumnos asignados actualmente.</Text>
                    ) : (
                      tutorStudents.map(student => (
                        <View key={student.id} className="bg-gray-50 border border-gray-200 rounded-lg p-3 mb-2 flex-row items-center">
                          <View className="w-8 h-8 rounded-full bg-border items-center justify-center mr-3">
                            <Feather name="user" size={14} color={colors.primary} />
                          </View>
                          <View className="flex-1">
                            <Text className="text-text font-bold text-sm">{student.full_name}</Text>
                            <Text className="text-primary text-[10px]">{student.student_code || student.email}</Text>
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
