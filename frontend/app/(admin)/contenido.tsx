import { View, Text, ScrollView, ActivityIndicator, Pressable, Alert, Modal, TextInput } from 'react-native';
import { useAuthStore } from '../../src/store/auth';
import { useState, useCallback } from 'react';
import client from '../../src/api/client';
import { useFocusEffect } from 'expo-router';
import { Feather } from '@expo/vector-icons';
import { useTheme } from '@/src/theme/ThemeContext';

export default function ContenidoScreen() {
  const { colors } = useTheme();
  const token = useAuthStore(state => state.token);
  const [corpus, setCorpus] = useState<any[]>([]);
  const [quotes, setQuotes] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  // Search States
  const [corpusSearch, setCorpusSearch] = useState('');
  const [quoteSearch, setQuoteSearch] = useState('');

  // Modals for Corpus
  const [corpusModal, setCorpusModal] = useState(false);
  const [newSource, setNewSource] = useState('');
  const [newText, setNewText] = useState('');
  const [isSavingCorpus, setIsSavingCorpus] = useState(false);
  const [editingCorpusId, setEditingCorpusId] = useState<number | null>(null);

  // Modals for Quote
  const [quoteModal, setQuoteModal] = useState(false);
  const [newQuote, setNewQuote] = useState('');
  const [isSavingQuote, setIsSavingQuote] = useState(false);
  const [editingQuoteId, setEditingQuoteId] = useState<number | null>(null);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [resC, resQ] = await Promise.all([
        client.get('/admin/corpus', { headers: { Authorization: `Bearer ${token}` } }),
        client.get('/admin/quotes', { headers: { Authorization: `Bearer ${token}` } })
      ]);
      setCorpus(resC.data);
      setQuotes(resQ.data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useFocusEffect(
    useCallback(() => {
      fetchData();
    }, [])
  );

  const handleDeleteCorpus = (id: number) => {
    Alert.alert("Eliminar", "¿Borrar este documento del cerebro de TutorIA?", [
      { text: "Cancelar", style: "cancel" },
      { text: "Borrar", style: "destructive", onPress: async () => {
        await client.delete(`/admin/corpus/${id}`, { headers: { Authorization: `Bearer ${token}` } });
        fetchData();
      }}
    ]);
  };

  const handleEditCorpus = (c: any) => {
    setEditingCorpusId(c.id);
    setNewSource(c.source);
    setNewText(c.text_content);
    setCorpusModal(true);
  };

  const handleSaveCorpus = async () => {
    if (!newSource || !newText) return;
    setIsSavingCorpus(true);
    try {
      if (editingCorpusId) {
        await client.put(`/admin/corpus/${editingCorpusId}`, { source: newSource, text_content: newText }, { headers: { Authorization: `Bearer ${token}` } });
      } else {
        await client.post('/admin/corpus', { source: newSource, text_content: newText }, { headers: { Authorization: `Bearer ${token}` } });
      }
      setCorpusModal(false);
      setNewSource(''); setNewText(''); setEditingCorpusId(null);
      fetchData();
    } catch(e) { console.error(e); } finally { setIsSavingCorpus(false); }
  };

  const handleDeleteQuote = (id: number) => {
    Alert.alert("Eliminar", "¿Borrar esta frase motivacional?", [
      { text: "Cancelar", style: "cancel" },
      { text: "Borrar", style: "destructive", onPress: async () => {
        await client.delete(`/admin/quotes/${id}`, { headers: { Authorization: `Bearer ${token}` } });
        fetchData();
      }}
    ]);
  };

  const handleEditQuote = (q: any) => {
    setEditingQuoteId(q.id);
    setNewQuote(q.text);
    setQuoteModal(true);
  };

  const handleSaveQuote = async () => {
    if (!newQuote) return;
    setIsSavingQuote(true);
    try {
      if (editingQuoteId) {
        await client.put(`/admin/quotes/${editingQuoteId}`, { text: newQuote }, { headers: { Authorization: `Bearer ${token}` } });
      } else {
        await client.post('/admin/quotes', { text: newQuote }, { headers: { Authorization: `Bearer ${token}` } });
      }
      setQuoteModal(false);
      setNewQuote(''); setEditingQuoteId(null);
      fetchData();
    } catch(e) { console.error(e); } finally { setIsSavingQuote(false); }
  };

  const filteredCorpus = corpus.filter(c => 
    c.source.toLowerCase().includes(corpusSearch.toLowerCase()) || 
    c.text_content.toLowerCase().includes(corpusSearch.toLowerCase())
  );

  const filteredQuotes = quotes.filter(q => 
    q.text.toLowerCase().includes(quoteSearch.toLowerCase())
  );

  return (
    <ScrollView className="flex-1 bg-border p-4">
      {/* Sección Chatbot */}
      <View style={{ backgroundColor: colors.surface }} className=" p-4 rounded-2xl shadow-sm mb-6 border border-primary/20 mt-2">
        <View className="flex-row justify-between items-center mb-4">
          <View>
            <Text className="text-xl font-bold text-text">Base de Conocimiento IA</Text>
            <Text className="text-xs text-primary">Archivos RAG para TutorIA</Text>
          </View>
          <Pressable onPress={() => { setEditingCorpusId(null); setNewSource(''); setNewText(''); setCorpusModal(true); }} className="bg-primary p-2 rounded-lg">
            <Feather name="plus" size={20} color="white" />
          </Pressable>
        </View>

        <View className="flex-row bg-gray-50 rounded-xl items-center px-4 py-2 mb-4 border border-gray-200">
          <Feather name="search" size={20} color={colors.primary} />
          <TextInput 
            value={corpusSearch}
            onChangeText={setCorpusSearch}
            placeholder="Buscar documentos..."
            className="flex-1 ml-2 text-text"
            placeholderTextColor="#A0A0A0"
          />
        </View>

        {loading ? <ActivityIndicator color={colors.primary} /> : filteredCorpus.map(c => (
          <View key={c.id} className="bg-gray-50 p-3 rounded-xl mb-2 flex-row justify-between items-center">
            <View className="flex-1 mr-2">
              <Text className="font-bold text-text text-sm">{c.source}</Text>
              <Text className="text-xs text-gray-500" numberOfLines={2}>{c.text_content}</Text>
            </View>
            <View className="flex-row">
              <Pressable onPress={() => handleEditCorpus(c)} className="p-2 mr-1">
                <Feather name="edit-2" size={18} color={colors.primary} />
              </Pressable>
              <Pressable onPress={() => handleDeleteCorpus(c.id)} className="p-2">
                <Feather name="trash-2" size={18} color="#DC2626" />
              </Pressable>
            </View>
          </View>
        ))}
      </View>

      {/* Sección Frases */}
      <View style={{ backgroundColor: colors.surface }} className=" p-4 rounded-2xl shadow-sm mb-10 border border-primary/20">
        <View className="flex-row justify-between items-center mb-4">
          <View>
            <Text className="text-xl font-bold text-text">Frases de Motivación</Text>
            <Text className="text-xs text-primary">Gestor de Gamificación</Text>
          </View>
          <Pressable onPress={() => { setEditingQuoteId(null); setNewQuote(''); setQuoteModal(true); }} className="bg-primary p-2 rounded-lg">
            <Feather name="plus" size={20} color="white" />
          </Pressable>
        </View>

        <View className="flex-row bg-gray-50 rounded-xl items-center px-4 py-2 mb-4 border border-gray-200">
          <Feather name="search" size={20} color={colors.primary} />
          <TextInput 
            value={quoteSearch}
            onChangeText={setQuoteSearch}
            placeholder="Buscar frases..."
            className="flex-1 ml-2 text-text"
            placeholderTextColor="#A0A0A0"
          />
        </View>

        {loading ? <ActivityIndicator color={colors.primary} /> : filteredQuotes.map(q => (
          <View key={q.id} className="bg-gray-50 p-3 rounded-xl mb-2 flex-row justify-between items-center border-l-4 border-yellow-400">
            <Text className="text-sm font-semibold text-text flex-1 italic mr-2">"{q.text}"</Text>
            <View className="flex-row">
              <Pressable onPress={() => handleEditQuote(q)} className="p-2 mr-1">
                <Feather name="edit-2" size={18} color={colors.primary} />
              </Pressable>
              <Pressable onPress={() => handleDeleteQuote(q.id)} className="p-2">
                <Feather name="trash-2" size={18} color="#DC2626" />
              </Pressable>
            </View>
          </View>
        ))}
      </View>

      {/* Modal Corpus */}
      <Modal visible={corpusModal} animationType="slide" transparent>
        <View className="flex-1 justify-end bg-black/50">
          <View style={{ backgroundColor: colors.surface }} className=" p-6 rounded-t-3xl">
            <View className="flex-row justify-between items-center mb-4">
              <Text className="text-lg font-bold text-text">{editingCorpusId ? 'Editar Documento IA' : 'Nuevo Documento IA'}</Text>
              <Pressable onPress={() => setCorpusModal(false)}><Feather name="x" size={24} color={colors.text} /></Pressable>
            </View>
            <TextInput 
              value={newSource} onChangeText={setNewSource} placeholder="Título (ej. Reglamento)"
              className="bg-gray-100 rounded-lg p-3 mb-3 text-text"
            />
            <TextInput 
              value={newText} onChangeText={setNewText} placeholder="Contenido del documento..."
              multiline numberOfLines={5} className="bg-gray-100 rounded-lg p-3 mb-6 h-32 text-text" textAlignVertical="top"
            />
            <Pressable onPress={handleSaveCorpus} disabled={isSavingCorpus} className="bg-primary p-4 rounded-xl items-center shadow-sm">
              {isSavingCorpus ? <ActivityIndicator color="white" /> : <Text className="text-white font-bold">{editingCorpusId ? 'Actualizar Vector' : 'Vectorizar y Guardar'}</Text>}
            </Pressable>
          </View>
        </View>
      </Modal>

      {/* Modal Quote */}
      <Modal visible={quoteModal} animationType="slide" transparent>
        <View className="flex-1 justify-end bg-black/50">
          <View style={{ backgroundColor: colors.surface }} className=" p-6 rounded-t-3xl">
            <View className="flex-row justify-between items-center mb-4">
              <Text className="text-lg font-bold text-text">{editingQuoteId ? 'Editar Frase' : 'Nueva Frase'}</Text>
              <Pressable onPress={() => setQuoteModal(false)}><Feather name="x" size={24} color={colors.text} /></Pressable>
            </View>
            <TextInput 
              value={newQuote} onChangeText={setNewQuote} placeholder="Escribe la frase..."
              multiline className="bg-gray-100 rounded-lg p-3 mb-6 h-24 text-text" textAlignVertical="top"
            />
            <Pressable onPress={handleSaveQuote} disabled={isSavingQuote} className="bg-primary p-4 rounded-xl items-center shadow-sm">
              {isSavingQuote ? <ActivityIndicator color="white" /> : <Text className="text-white font-bold">{editingQuoteId ? 'Actualizar' : 'Guardar'}</Text>}
            </Pressable>
          </View>
        </View>
      </Modal>
    </ScrollView>
  );
}
