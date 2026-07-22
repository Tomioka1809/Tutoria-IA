import { View, Text, ScrollView, ActivityIndicator, Pressable, Alert, Modal, TextInput } from 'react-native';
import { useAuthStore } from '../../src/store/auth';
import { useState, useCallback } from 'react';
import client from '../../src/api/client';
import { useFocusEffect } from 'expo-router';
import { Feather } from '@expo/vector-icons';
import { useTheme } from '@/src/theme/ThemeContext';
import { useTranslation } from 'react-i18next';

export default function ContenidoScreen() {
  const { colors } = useTheme();
  const { t } = useTranslation();
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

  const fetchData = useCallback(async () => {
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
  }, [token]);

  useFocusEffect(
    useCallback(() => {
      fetchData();
    }, [fetchData])
  );

  const handleDeleteCorpus = (id: number) => {
    Alert.alert(t('admin.deleteDocumentTitle'), t('admin.deleteDocumentMessage'), [
      { text: t('common.cancel'), style: "cancel" },
      { text: t('common.delete'), style: "destructive", onPress: async () => {
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
    Alert.alert(t('admin.deleteDocumentTitle'), t('admin.deleteQuoteMessage'), [
      { text: t('common.cancel'), style: "cancel" },
      { text: t('common.delete'), style: "destructive", onPress: async () => {
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
    <ScrollView className="flex-1 bg-background dark:bg-black p-4">
      {/* Sección Chatbot */}
      <View style={{ backgroundColor: colors.surface }} className=" p-4 rounded-2xl shadow-sm mb-6 border border-primary/20 dark:border-white mt-2">
        <View className="flex-row justify-between items-center mb-4">
          <View>
            <Text className="text-xl font-bold text-text dark:text-white">{t('admin.knowledgeBase')}</Text>
            <Text className="text-xs text-primary dark:text-white">{t('admin.ragFiles')}</Text>
          </View>
          <Pressable onPress={() => { setEditingCorpusId(null); setNewSource(''); setNewText(''); setCorpusModal(true); }} className="bg-primary p-2 rounded-lg">
            <Feather name="plus" size={20} color="white" />
          </Pressable>
        </View>

        <View className="flex-row bg-gray-50 dark:bg-surface rounded-xl items-center px-4 py-2 mb-4 border border-gray-200 dark:border-white">
          <Feather name="search" size={20} color={colors.primary} />
          <TextInput 
            value={corpusSearch}
            onChangeText={setCorpusSearch}
            placeholder={t('admin.searchDocuments')}
            className="flex-1 ml-2 text-text dark:text-gray-300"
            placeholderTextColor="#A0A0A0"
          />
        </View>

        {loading ? <ActivityIndicator color={colors.primary} /> : filteredCorpus.map(c => (
          <View key={c.id} className="bg-gray-50 dark:bg-surface p-3 rounded-xl mb-2 flex-row justify-between items-center dark:border dark:border-white">
            <View className="flex-1 mr-2">
              <Text className="font-bold text-text dark:text-white text-sm">{c.source}</Text>
              <Text className="text-xs text-gray-500 dark:text-white" numberOfLines={2}>{c.text_content}</Text>
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
      <View style={{ backgroundColor: colors.surface }} className=" p-4 rounded-2xl shadow-sm mb-10 border border-primary/20 dark:border-white">
        <View className="flex-row justify-between items-center mb-4">
          <View>
            <Text className="text-xl font-bold text-text dark:text-white">{t('admin.motivationalQuotes')}</Text>
            <Text className="text-xs text-primary dark:text-white">{t('admin.gamificationManager')}</Text>
          </View>
          <Pressable onPress={() => { setEditingQuoteId(null); setNewQuote(''); setQuoteModal(true); }} className="bg-primary p-2 rounded-lg">
            <Feather name="plus" size={20} color="white" />
          </Pressable>
        </View>

        <View className="flex-row bg-gray-50 dark:bg-surface rounded-xl items-center px-4 py-2 mb-4 border border-gray-200 dark:border-white">
          <Feather name="search" size={20} color={colors.primary} />
          <TextInput 
            value={quoteSearch}
            onChangeText={setQuoteSearch}
            placeholder={t('admin.searchQuotes')}
            className="flex-1 ml-2 text-text dark:text-gray-300"
            placeholderTextColor="#A0A0A0"
          />
        </View>

        {loading ? <ActivityIndicator color={colors.primary} /> : filteredQuotes.map(q => (
          <View key={q.id} className="bg-gray-50 dark:bg-surface p-3 rounded-xl mb-2 flex-row justify-between items-center border-l-4 border-yellow-400 dark:border dark:border-white">
            <Text className="text-sm font-semibold text-text dark:text-white flex-1 italic mr-2">&ldquo;{q.text}&rdquo;</Text>
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
          <View style={{ backgroundColor: colors.surface }} className=" p-6 rounded-t-3xl border border-transparent dark:border-white">
            <View className="flex-row justify-between items-center mb-4">
              <Text className="text-lg font-bold text-text dark:text-white">{editingCorpusId ? t('admin.editDocument') : t('admin.newDocument')}</Text>
              <Pressable onPress={() => setCorpusModal(false)}><Feather name="x" size={24} color={colors.text} /></Pressable>
            </View>
            <TextInput 
              value={newSource} onChangeText={setNewSource} placeholder={t('admin.documentTitlePlaceholder')}
              className="bg-gray-100 dark:bg-background rounded-lg p-3 mb-3 text-text dark:text-white"
            />
            <TextInput 
              value={newText} onChangeText={setNewText} placeholder={t('admin.documentContentPlaceholder')}
              multiline numberOfLines={5} className="bg-gray-100 dark:bg-background rounded-lg p-3 mb-6 h-32 text-text dark:text-white" textAlignVertical="top"
            />
            <Pressable onPress={handleSaveCorpus} disabled={isSavingCorpus} className="bg-primary p-4 rounded-xl items-center shadow-sm">
              {isSavingCorpus ? <ActivityIndicator color="white" /> : <Text className="text-white font-bold">{editingCorpusId ? t('admin.updateVector') : t('admin.vectorizeSave')}</Text>}
            </Pressable>
          </View>
        </View>
      </Modal>

      {/* Modal Quote */}
      <Modal visible={quoteModal} animationType="slide" transparent>
        <View className="flex-1 justify-end bg-black/50">
          <View style={{ backgroundColor: colors.surface }} className=" p-6 rounded-t-3xl border border-transparent dark:border-white">
            <View className="flex-row justify-between items-center mb-4">
              <Text className="text-lg font-bold text-text dark:text-white">{editingQuoteId ? t('admin.editQuote') : t('admin.newQuote')}</Text>
              <Pressable onPress={() => setQuoteModal(false)}><Feather name="x" size={24} color={colors.text} /></Pressable>
            </View>
            <TextInput 
              value={newQuote} onChangeText={setNewQuote} placeholder={t('admin.quotePlaceholder')}
              multiline className="bg-gray-100 dark:bg-background rounded-lg p-3 mb-6 h-24 text-text dark:text-white" textAlignVertical="top"
            />
            <Pressable onPress={handleSaveQuote} disabled={isSavingQuote} className="bg-primary p-4 rounded-xl items-center shadow-sm">
              {isSavingQuote ? <ActivityIndicator color="white" /> : <Text className="text-white font-bold">{editingQuoteId ? t('common.update') : t('common.save')}</Text>}
            </Pressable>
          </View>
        </View>
      </Modal>
    </ScrollView>
  );
}
