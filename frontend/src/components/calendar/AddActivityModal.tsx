import React, { useState } from 'react';
import { View, Text, TextInput, Modal, Pressable, ScrollView } from 'react-native';
import { Feather, FontAwesome, Ionicons } from '@expo/vector-icons';

interface AddActivityModalProps {
  isOpen: boolean;
  onClose: () => void;
  selectedDate: Date;
  onAdd: (activity: {
    name: string;
    type: 'Tutoría Académica' | 'Reunión con Tutor' | 'Sesión de Apoyo Psicológico' | 'Entrega de Tarea';
    date: string;
    time: string;
  }) => void;
}

export function AddActivityModal({
  isOpen,
  onClose,
  selectedDate,
  onAdd,
}: AddActivityModalProps) {
  const [name, setName] = useState('');
  const [type, setType] = useState<'Tutoría Académica' | 'Reunión con Tutor' | 'Sesión de Apoyo Psicológico' | 'Entrega de Tarea'>('Tutoría Académica');
  
  // Formatear la fecha seleccionada a YYYY-MM-DD
  const formatDateString = (date: Date) => {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
  };

  const [dateStr, setDateStr] = useState(formatDateString(selectedDate));
  const [timeStr, setTimeStr] = useState('10:00'); // Hora por defecto en formato 24h

  // Actualizar la fecha en el input cuando cambia la seleccionada en el calendario
  React.useEffect(() => {
    setDateStr(formatDateString(selectedDate));
  }, [selectedDate, isOpen]);

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

    onAdd({
      name,
      type,
      date: dateStr,
      time: timeStr,
    });

    // Resetear formulario
    setName('');
    setType('Tutoría Académica');
    setTimeStr('10:00');
    onClose();
  };

  // Definir estilos y colores para los 4 tipos de actividades en el selector
  const typesConfig = [
    {
      id: 'Tutoría Académica' as const,
      label: 'Tutoría Académica',
      icon: 'book-open',
      iconSet: 'Feather' as const,
      bgColor: 'bg-[#F3E8FF]',
      activeBgColor: 'bg-[#9A3BEE]',
      textColor: 'text-[#9A3BEE]',
    },
    {
      id: 'Reunión con Tutor' as const,
      label: 'Reunión con Tutor',
      icon: 'calendar',
      iconSet: 'Feather' as const,
      bgColor: 'bg-[#E0F2FE]',
      activeBgColor: 'bg-[#0ea5e9]',
      textColor: 'text-[#0ea5e9]',
    },
    {
      id: 'Sesión de Apoyo Psicológico' as const,
      label: 'Apoyo Psicológico',
      icon: 'heart-o',
      iconSet: 'FontAwesome' as const,
      bgColor: 'bg-[#FCE7F3]',
      activeBgColor: 'bg-[#ec4899]',
      textColor: 'text-[#ec4899]',
    },
    {
      id: 'Entrega de Tarea' as const,
      label: 'Entrega de Tarea',
      icon: 'file-text',
      iconSet: 'Feather' as const,
      bgColor: 'bg-[#F5F3FF]',
      activeBgColor: 'bg-[#7c3aed]',
      textColor: 'text-[#7c3aed]',
    },
  ];

  return (
    <Modal visible={isOpen} animationType="fade" transparent={true}>
      {/* Fondo semi-transparente que simula el desenfoque */}
      <View className="flex-1 bg-black/45 justify-end">
        <Pressable className="absolute inset-0" onPress={onClose} />
        
        {/* Contenedor Flotante del Modal */}
        <View className="bg-white rounded-t-[40px] px-6 pt-8 pb-10 shadow-2xl border border-gray-100 max-h-[85%]">
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
                placeholder="Ej. Estudiar Cálculo / Reunión Semanal"
                placeholderTextColor="#A1A1AA"
                className="bg-[#F8F9FA] border border-gray-200 rounded-2xl px-4 py-3.5 text-[#111130] font-semibold"
              />
            </View>

            {/* Selector: Tipo de Actividad */}
            <View className="mb-5">
              <Text className="text-xs font-bold text-[#8E8EA0] mb-2 uppercase tracking-wider">Tipo de Actividad</Text>
              <View className="flex-row flex-wrap justify-between">
                {typesConfig.map((item) => {
                  const isActive = type === item.id;
                  return (
                    <Pressable
                      key={item.id}
                      onPress={() => setType(item.id)}
                      className={`w-[48%] p-3 rounded-2xl mb-3 flex-row items-center border ${
                        isActive
                          ? `${item.activeBgColor} border-transparent`
                          : `${item.bgColor} border-gray-100`
                      }`}
                    >
                      <View className="mr-2.5">
                        {item.iconSet === 'Feather' ? (
                          <Feather
                            name={item.icon as any}
                            size={16}
                            color={isActive ? '#FFFFFF' : '#4B5563'}
                          />
                        ) : (
                          <FontAwesome
                            name={item.icon as any}
                            size={16}
                            color={isActive ? '#FFFFFF' : '#4B5563'}
                          />
                        )}
                      </View>
                      <Text
                        className={`text-[11px] font-bold flex-1 ${
                          isActive ? 'text-white' : 'text-[#1E1E2F]'
                        }`}
                        numberOfLines={1}
                      >
                        {item.label}
                      </Text>
                    </Pressable>
                  );
                })}
              </View>
            </View>

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
