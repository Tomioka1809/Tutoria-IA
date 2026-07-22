import React, { useState } from 'react';
import { View, Text, TextInput, Modal, Pressable, ScrollView } from 'react-native';
import { Feather } from '@expo/vector-icons';
import DateTimePicker from '@react-native-community/datetimepicker';
import { Picker } from '@react-native-picker/picker';
import { User } from '@/src/types';
import { useTheme } from '@/src/theme/ThemeContext';
import { useTranslation } from 'react-i18next';

interface AddActivityModalProps {
  isOpen: boolean;
  onClose: () => void;
  selectedDate: Date;
  userRole?: string;
  students: User[];
  onAdd: (activity: {
    name: string;
    type: 'Tutoría Académica' | 'Tutoría Personal' | 'Tutoría Profesional' | 'Trabajos';
    date: string;
    time: string;
    studentId?: number | null;
    status?: string;
    notes?: string;
    location?: string;
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
  const { colors, isDark } = useTheme();
  const { t } = useTranslation();
  const isTutor = userRole === 'tutor' || userRole === 'admin';

  const [name, setName] = useState('');
  const [type, setType] = useState<'Tutoría Académica' | 'Tutoría Personal' | 'Tutoría Profesional' | 'Trabajos'>('Tutoría Académica');

  const [status, setStatus] = useState('pendiente');
  const [notes, setNotes] = useState('');
  const [location, setLocation] = useState('');

  const [selectedStudentId, setSelectedStudentId] = useState<number | null>(null);
  const [studentSearch, setStudentSearch] = useState('');

  const [date, setDate] = useState(() => new Date(selectedDate));
  const [time, setTime] = useState(() => {
    const initTime = new Date(selectedDate);
    initTime.setHours(10, 0, 0, 0);
    return initTime;
  });
  const [showDatePicker, setShowDatePicker] = useState(false);
  const [showTimePicker, setShowTimePicker] = useState(false);

  React.useEffect(() => {
    if (isOpen) {
      const initDate = new Date(selectedDate);
      setDate(initDate);
      const initTime = new Date(selectedDate);
      initTime.setHours(10, 0, 0, 0);
      setTime(initTime);
      setType(isTutor ? 'Tutoría Académica' : 'Trabajos');
      setStatus('pendiente');
      setNotes('');
      setLocation('');
      setName('');
      setStudentSearch('');
      setSelectedStudentId(null);
    }
  }, [isOpen, selectedDate, isTutor]);

  const handleSubmit = () => {
    if (!name.trim()) {
      alert(t('calendar.nameRequired'));
      return;
    }

    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    const dateStr = `${year}-${month}-${day}`;

    const hours = String(time.getHours()).padStart(2, '0');
    const minutes = String(time.getMinutes()).padStart(2, '0');
    const timeStr = `${hours}:${minutes}`;

    onAdd({
      name,
      type,
      date: dateStr,
      time: timeStr,
      studentId: selectedStudentId,
      status,
      notes,
      location,
    });

    onClose();
  };

  const onDateChange = (_event: any, selectedValue?: Date) => {
    setShowDatePicker(false);
    if (selectedValue) {
      setDate(selectedValue);
    }
  };

  const onTimeChange = (_event: any, selectedValue?: Date) => {
    setShowTimePicker(false);
    if (selectedValue) {
      setTime(selectedValue);
    }
  };

  const filteredStudents = (students || []).filter((s) => {
    const fullName = s?.full_name || '';
    return fullName.toLowerCase().includes((studentSearch || '').toLowerCase());
  });

  const typesConfig = [
    { id: 'Tutoría Académica' as const, label: t('calendar.academicShort'), icon: 'book-open', bgColor: 'bg-[#F3E8FF]', activeBgColor: 'bg-primary', textColor: 'text-primary', visible: isTutor },
    { id: 'Tutoría Personal' as const, label: t('calendar.personalShort'), icon: 'user', bgColor: 'bg-[#FCE7F3]', activeBgColor: 'bg-[#ec4899]', textColor: 'text-[#ec4899]', visible: isTutor },
    { id: 'Tutoría Profesional' as const, label: t('calendar.professionalShort'), icon: 'briefcase', bgColor: 'bg-[#E0E7FF]', activeBgColor: 'bg-[#4F46E5]', textColor: 'text-[#4F46E5]', visible: isTutor },
    { id: 'Trabajos' as const, label: t('calendar.work'), icon: 'file-text', bgColor: 'bg-[#F5F3FF]', activeBgColor: 'bg-[#7c3aed]', textColor: 'text-[#7c3aed]', visible: true },
  ];

  return (
    <Modal visible={isOpen} animationType="fade" transparent={true}>
      <View className="flex-1 bg-black/45 justify-end">
        <Pressable className="absolute inset-0" onPress={onClose} />
        
        <View style={{ backgroundColor: colors.surface }} className=" rounded-t-[40px] px-6 pt-8 pb-10 shadow-2xl border border-gray-100 max-h-[90%]">
          <View className="w-12 h-1 bg-gray-300 rounded-full align-self-center mx-auto mb-6" />
          
          <View className="flex-row justify-between items-center mb-6">
            <Text style={{ color: colors.text }} className="text-xl font-bold ">{t('calendar.addActivity')}</Text>
            <Pressable onPress={onClose}>
              <Text className="text-primary font-bold text-sm">{t('common.cancel')}</Text>
            </Pressable>
          </View>

          <ScrollView showsVerticalScrollIndicator={false}>
            <View className="mb-4">
              <Text className="text-xs font-bold text-textSecondary mb-2 uppercase tracking-wider">{t('calendar.activityName')}</Text>
              <TextInput
                value={name}
                onChangeText={setName}
                placeholder={t('calendar.activityNamePlaceholder')}
                placeholderTextColor="#A1A1AA"
                style={{ color: colors.text, backgroundColor: colors.surface }} className=" border border-gray-200 rounded-2xl px-4 py-3.5  font-semibold"
              />
            </View>

            <View className="mb-4">
              <Text className="text-xs font-bold text-textSecondary mb-2 uppercase tracking-wider">{t('calendar.activityType')}</Text>
              <View className="flex-row flex-wrap justify-between">
                {typesConfig
                  .filter((tConfig) => tConfig.visible)
                  .map((item) => {
                    const isActive = type === item.id;
                    return (
                      <Pressable
                        key={item.id}
                        onPress={() => setType(item.id)}
                        className={`p-3 rounded-2xl mb-3 flex-row items-center border w-[48%] ${
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
                          className={`text-[11px] font-bold flex-1`}
                          style={{ color: isActive ? '#FFFFFF' : colors.text }}
                        >
                          {item.label}
                        </Text>
                      </Pressable>
                    );
                  })}
              </View>
            </View>

            {type.includes('Tutoría') && isTutor && (
              <View className="mb-4 bg-[#F5F3FF] border border-primary/20 rounded-2xl p-4">
                <Text style={{ color: isDark ? '#FFFFFF' : colors.primary }} className="text-xs font-bold mb-2 uppercase tracking-wider">
                  {t('calendar.assignStudent')}
                </Text>
                
                <View style={{ backgroundColor: colors.surface }} className="flex-row items-center  border border-gray-200 rounded-xl px-3 py-1.5 mb-3 shadow-sm">
                  <Feather name="search" size={14} color={colors.textSecondary} className="mr-2" />
                  <TextInput
                    value={studentSearch}
                    onChangeText={setStudentSearch}
                    placeholder={t('calendar.searchStudent')}
                    placeholderTextColor="#A1A1AA"
                    style={{ color: colors.text }} className="flex-1 text-xs font-semibold  p-0"
                  />
                </View>

                <ScrollView 
                  style={{ maxHeight: 110 }} 
                  nestedScrollEnabled={true}
                  className="bg-surface/70 rounded-xl p-1"
                >
                  <Pressable
                    onPress={() => setSelectedStudentId(null)}
                    className={`flex-row items-center justify-between p-2.5 rounded-lg mb-1 ${
                      selectedStudentId === null ? 'bg-primary/10' : 'bg-transparent'
                    }`}
                  >
                    <Text className={`text-xs font-semibold`} style={{ color: selectedStudentId === null ? (isDark ? '#FFFFFF' : colors.primary) : colors.text, fontWeight: selectedStudentId === null ? 'bold' : 'normal' }}>
                      {t('calendar.allGroup')}
                    </Text>
                    {selectedStudentId === null && (
                      <Feather name="users" size={12} color={colors.primary} />
                    )}
                  </Pressable>

                  {filteredStudents.length > 0 ? (
                    filteredStudents.map((student) => {
                      const isSelected = selectedStudentId === student.id;
                      return (
                        <Pressable
                          key={student.id}
                          onPress={() => setSelectedStudentId(student.id)}
                          className={`flex-row items-center justify-between p-2.5 rounded-lg mb-1 ${
                            isSelected ? 'bg-primary/10' : 'bg-transparent'
                          }`}
                        >
                          <Text className={`text-xs font-semibold`} style={{ color: isSelected ? (isDark ? '#FFFFFF' : colors.primary) : colors.text, fontWeight: isSelected ? 'bold' : 'normal' }}>
                            {student.full_name}
                          </Text>
                          {isSelected && (
                            <Feather name="check" size={12} color={colors.primary} />
                          )}
                        </Pressable>
                      );
                    })
                  ) : (
                    <Text className="text-center text-[11px] text-textSecondary py-4">
                      {t('calendar.noMoreStudents')}
                    </Text>
                  )}
                </ScrollView>
              </View>
            )}

            <View className="flex-row justify-between mb-4">
              <View className="w-[48%]">
                <Text className="text-xs font-bold text-textSecondary mb-2 uppercase tracking-wider">{t('calendar.date')}</Text>
                <Pressable
                  onPress={() => setShowDatePicker(true)}
                  style={{ backgroundColor: colors.surface }} className=" border border-gray-200 rounded-2xl px-4 py-3.5 flex-row justify-between items-center"
                >
                  <Text style={{ color: colors.text }} className=" font-semibold">
                    {date.toLocaleDateString()}
                  </Text>
                  <Feather name="calendar" size={16} color={colors.textSecondary} />
                </Pressable>
                {showDatePicker && (
                  <DateTimePicker
                    value={date}
                    mode="date"
                    display="default"
                    onChange={onDateChange}
                  />
                )}
              </View>

              <View className="w-[48%]">
                <Text className="text-xs font-bold text-textSecondary mb-2 uppercase tracking-wider">{t('calendar.time')}</Text>
                <Pressable
                  onPress={() => setShowTimePicker(true)}
                  style={{ backgroundColor: colors.surface }} className=" border border-gray-200 rounded-2xl px-4 py-3.5 flex-row justify-between items-center"
                >
                  <Text style={{ color: colors.text }} className=" font-semibold">
                    {time.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </Text>
                  <Feather name="clock" size={16} color={colors.textSecondary} />
                </Pressable>
                {showTimePicker && (
                  <DateTimePicker
                    value={time}
                    mode="time"
                    is24Hour={true}
                    display="spinner"
                    onChange={onTimeChange}
                  />
                )}
              </View>
            </View>

            <View className="flex-row justify-between mb-4">
              <View className="w-[48%]">
                <Text className="text-xs font-bold text-textSecondary mb-2 uppercase tracking-wider">{t('calendar.status')}</Text>
                <View style={{ backgroundColor: colors.surface }} className=" border border-gray-200 rounded-2xl overflow-hidden">
                  <Picker
                    selectedValue={status}
                    onValueChange={(itemValue) => setStatus(itemValue)}
                    style={{ height: 50, color: colors.text }}
                  >
                    <Picker.Item label="Pendiente" value="pendiente" />
                    <Picker.Item label="Programada" value="programada" />
                    <Picker.Item label="Completada" value="completada" />
                    <Picker.Item label="Cancelada" value="cancelada" />
                  </Picker>
                </View>
              </View>
              <View className="w-[48%]">
                <Text className="text-xs font-bold text-textSecondary mb-2 uppercase tracking-wider">{t('calendar.location')}</Text>
                <TextInput
                  value={location}
                  onChangeText={setLocation}
                  placeholder={t('calendar.locationPlaceholder')}
                  placeholderTextColor="#A1A1AA"
                  style={{ color: colors.text, backgroundColor: colors.surface }} className=" border border-gray-200 rounded-2xl px-4 py-[13px]  font-semibold h-[50px]"
                />
              </View>
            </View>

            <View className="mb-6">
              <Text className="text-xs font-bold text-textSecondary mb-2 uppercase tracking-wider">{t('calendar.notes')}</Text>
              <TextInput
                value={notes}
                onChangeText={setNotes}
                placeholder={t('calendar.notesPlaceholder')}
                placeholderTextColor="#A1A1AA"
                multiline
                numberOfLines={3}
                textAlignVertical="top"
                style={{ color: colors.text, backgroundColor: colors.surface }} className=" border border-gray-200 rounded-2xl px-4 py-3.5  font-semibold h-24"
              />
            </View>

            <Pressable
              onPress={handleSubmit}
              className="bg-primary rounded-2xl py-4 items-center justify-center shadow-lg shadow-[#9A3BEE]/25 mb-4"
            >
              <Text className="text-white font-bold text-base">{t('calendar.saveActivity')}</Text>
            </Pressable>
          </ScrollView>
        </View>
      </View>
    </Modal>
  );
}
