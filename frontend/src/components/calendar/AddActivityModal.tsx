import React, { useState } from 'react';
import { View, Text, TextInput, Modal, Pressable, ScrollView } from 'react-native';
import { Feather } from '@expo/vector-icons';
import { User } from '@/src/types';

interface AddActivityModalProps {
  isOpen: boolean;
  onClose: () => void;
  selectedDate: Date;
  userRole?: string;
  students: User[];
  onAdd: (activity: {
    name: string;
    type: 'Tutoría Académica' | 'Sesión de Apoyo Psicológico' | 'Trabajos';
    date: string;
    time: string;
    studentId?: number;
  }) => void;
}

export function AddActivityModal({
  isOpen,
  onClose,
  selectedDate,
  userRole,
  students,
  onAdd,
}: AddActivityModalProps) {
  const isTutor = userRole === 'tutor' || userRole === 'admin';
  
  const [name, setName] = useState('');
  const [type, setType] = useState<'Tutoría Académica' | 'Sesión de Apoyo Psicológico' | 'Trabajos'>(
    isTutor ? 'Tutoría Académica' : 'Sesión de Apoyo Psicológico'
  );

  const [selectedStudentId, setSelectedStudentId] = useState<number | null>(null);
  const [studentSearch, setStudentSearch] = useState('');

  // Formatear la fecha seleccionada a YYYY-MM-DD
  const formatDateString = (date: Date) => {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
  };

  const [dateStr, setDateStr] = useState(formatDateString(selectedDate));
  const [timeStr, setTimeStr] = useState('10:00'); // Hora por defecto en formato 24h

  // Sincronizar y limpiar formulario al abrir/cerrar modal
  React.useEffect(() => {
    if (isOpen) {
      setDateStr(formatDateString(selectedDate));
      setType(isTutor ? 'Tutoría Académica' : 'Sesión de Apoyo Psicológico');
      setStudentSearch('');
      if (students && students.length > 0) {
        setSelectedStudentId(students[0].id);
      } else {
        setSelectedStudentId(null);
      }
    } else {
      setSelectedStudentId(null);
      setStudentSearch('');
    }
  }, [isOpen, selectedDate, userRole, students]);

  const handleSubmit = () => {
    if (!name.trim()) {
      alert('Por favor ingresa un nombre para la actividad.');
      return;
    }
    if (!dateStr.match(/^\d{4}-\d{2}-\d{2}$/)) {
      alert('Por favor ingresa la fecha en formato AAAA-MM-DD.');
      return;
    }
    if (!timeStr.match(/^\d{2}:\d{2}$/)) {
      alert('Por favor ingresa la hora en formato HH:MM (24h).');
      return;
    }

    if (type === 'Tutoría Académica') {
      if (!selectedStudentId) {
        alert('Por favor selecciona un estudiante.');
        return;
      }
      onAdd({
        name,
        type,
        date: dateStr,
        time: timeStr,
        studentId: selectedStudentId,
      });
    } else {
      onAdd({
        name,
        type,
        date: dateStr,
        time: timeStr,
      });
    }

    // Resetear formulario
    setName('');
    setStudentSearch('');
    setTimeStr('10:00');
    onClose();
  };

  // Filtrar estudiantes por búsqueda
  const filteredStudents = (students || []).filter((s) => {
    const fullName = s?.full_name || '';
    return fullName.toLowerCase().includes((studentSearch || '').toLowerCase());
  });

  // Configuración de los tipos de actividades (se quita Reunión con Tutor y se cambia Entrega de Tarea a Trabajos)
  const typesConfig = [
    {
      id: 'Tutoría Académica' as const,
      label: 'Tutoría Académica',
      icon: 'book-open',
      bgColor: 'bg-[#F3E8FF]',
      activeBgColor: 'bg-[#9A3BEE]',
      textColor: 'text-[#9A3BEE]',
      visible: isTutor, // Solo visible para docentes
    },
    {
      id: 'Sesión de Apoyo Psicológico' as const,
      label: 'Apoyo Psicológico',
      icon: 'heart',
      bgColor: 'bg-[#FCE7F3]',
      activeBgColor: 'bg-[#ec4899]',
      textColor: 'text-[#ec4899]',
      visible: true, // Visible para todos
    },
    {
      id: 'Trabajos' as const,
      label: 'Trabajos',
      icon: 'file-text',
      bgColor: 'bg-[#F5F3FF]',
      activeBgColor: 'bg-[#7c3aed]',
      textColor: 'text-[#7c3aed]',
      visible: true, // Visible para todos
    },
  ];

  return (
    <Modal visible={isOpen} animationType="fade" transparent={true}>
      <View className="flex-1 bg-black/45 justify-end">
        <Pressable className="absolute inset-0" onPress={onClose} />
        
        <View className="bg-white rounded-t-[40px] px-6 pt-8 pb-10 shadow-2xl border border-gray-100 max-h-[90%]">
          <View className="w-12 h-1 bg-gray-300 rounded-full align-self-center mx-auto mb-6" />
          
          <View className="flex-row justify-between items-center mb-6">
            <Text className="text-xl font-bold text-[#1E1E2F]">Añadir Actividad</Text>
            <Pressable onPress={onClose}>
              <Text className="text-[#9A3BEE] font-bold text-sm">Cancelar</Text>
            </Pressable>
          </View>

          <ScrollView showsVerticalScrollIndicator={false}>
            {/* Input: Nombre */}
            <View className="mb-4">
              <Text className="text-xs font-bold text-[#8E8EA0] mb-2 uppercase tracking-wider">Nombre de la actividad</Text>
              <TextInput
                value={name}
                onChangeText={setName}
                placeholder="Ej. Clase de Álgebra / Tarea de Física"
                placeholderTextColor="#A1A1AA"
                className="bg-[#F8F9FA] border border-gray-200 rounded-2xl px-4 py-3.5 text-[#111130] font-semibold"
              />
            </View>

            {/* Selector: Tipo de Actividad (filtrado por rol) */}
            <View className="mb-4">
              <Text className="text-xs font-bold text-[#8E8EA0] mb-2 uppercase tracking-wider">Tipo de Actividad</Text>
              <View className="flex-row flex-wrap justify-between">
                {typesConfig
                  .filter((t) => t.visible)
                  .map((item) => {
                    const isActive = type === item.id;
                    const isFullWidth = item.id === 'Tutoría Académica';
                    return (
                      <Pressable
                        key={item.id}
                        onPress={() => setType(item.id)}
                        className={`p-3 rounded-2xl mb-3 flex-row items-center border ${
                          isFullWidth ? 'w-full' : 'w-[48%]'
                        } ${
                          isActive
                            ? `${item.activeBgColor} border-transparent`
                            : `${item.bgColor} border-gray-100`
                        }`}
                      >
                        <View className="mr-2">
                          <Feather
                            name={item.icon as any}
                            size={14}
                            color={isActive ? '#FFFFFF' : '#4B5563'}
                          />
                        </View>
                        <Text
                          className={`text-[11px] font-bold flex-1 ${
                            isActive ? 'text-white' : 'text-[#1E1E2F]'
                          }`}
                        >
                          {item.label}
                        </Text>
                      </Pressable>
                    );
                  })}
              </View>
            </View>

            {/* Apartado para seleccionar estudiante (Solo si es Tutoría Académica) */}
            {type === 'Tutoría Académica' && isTutor && (
              <View className="mb-4 bg-[#F5F3FF] border border-[#9A3BEE]/20 rounded-2xl p-4">
                <Text className="text-xs font-bold text-[#9A3BEE] mb-2 uppercase tracking-wider">
                  Asignar Estudiante
                </Text>
                
                {/* Buscador de estudiantes */}
                <View className="flex-row items-center bg-white border border-gray-200 rounded-xl px-3 py-1.5 mb-3 shadow-sm">
                  <Feather name="search" size={14} color="#8E8EA0" className="mr-2" />
                  <TextInput
                    value={studentSearch}
                    onChangeText={setStudentSearch}
                    placeholder="Buscar estudiante..."
                    placeholderTextColor="#A1A1AA"
                    className="flex-1 text-xs font-semibold text-[#111130] p-0"
                  />
                </View>

                {/* Lista de estudiantes */}
                <ScrollView 
                  style={{ maxHeight: 110 }} 
                  nestedScrollEnabled={true}
                  className="bg-white/70 rounded-xl p-1"
                >
                  {filteredStudents.length > 0 ? (
                    filteredStudents.map((student) => {
                      const isSelected = selectedStudentId === student.id;
                      return (
                        <Pressable
                          key={student.id}
                          onPress={() => setSelectedStudentId(student.id)}
                          className={`flex-row items-center justify-between p-2.5 rounded-lg mb-1 ${
                            isSelected ? 'bg-[#9A3BEE]/10' : 'bg-transparent'
                          }`}
                        >
                          <Text className={`text-xs font-semibold ${
                            isSelected ? 'text-[#9A3BEE] font-bold' : 'text-[#1E1E2F]'
                          }`}>
                            {student.full_name}
                          </Text>
                          {isSelected && (
                            <Feather name="check" size={12} color="#9A3BEE" />
                          )}
                        </Pressable>
                      );
                    })
                  ) : (
                    <Text className="text-center text-[11px] text-[#8E8EA0] py-4">
                      No se encontraron estudiantes
                    </Text>
                  )}
                </ScrollView>
              </View>
            )}

            {/* Grid: Fecha y Hora */}
            <View className="flex-row justify-between mb-6">
              <View className="w-[48%]">
                <Text className="text-xs font-bold text-[#8E8EA0] mb-2 uppercase tracking-wider">Fecha (AAAA-MM-DD)</Text>
                <TextInput
                  value={dateStr}
                  onChangeText={setDateStr}
                  placeholder="2026-05-19"
                  placeholderTextColor="#A1A1AA"
                  className="bg-[#F8F9FA] border border-gray-200 rounded-2xl px-4 py-3.5 text-[#111130] font-semibold text-center"
                />
              </View>

              <View className="w-[48%]">
                <Text className="text-xs font-bold text-[#8E8EA0] mb-2 uppercase tracking-wider">Hora (HH:MM)</Text>
                <TextInput
                  value={timeStr}
                  onChangeText={setTimeStr}
                  placeholder="10:00"
                  placeholderTextColor="#A1A1AA"
                  className="bg-[#F8F9FA] border border-gray-200 rounded-2xl px-4 py-3.5 text-[#111130] font-semibold text-center"
                />
              </View>
            </View>

            {/* Botón de Submit */}
            <Pressable
              onPress={handleSubmit}
              className="bg-[#9A3BEE] rounded-2xl py-4 items-center justify-center shadow-lg shadow-[#9A3BEE]/25 mb-4"
            >
              <Text className="text-white font-bold text-base">Guardar Actividad</Text>
            </Pressable>
          </ScrollView>
        </View>
      </View>
    </Modal>
  );
}
