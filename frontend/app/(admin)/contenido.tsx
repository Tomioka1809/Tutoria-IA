import {
  View,
  Text,
  ScrollView,
  ActivityIndicator,
  Pressable,
  Alert,
  Modal,
  TextInput,
  Platform
} from 'react-native';
import { useAuthStore } from '../../src/store/auth';
import { useState, useCallback } from 'react';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import client from '../../src/api/client';
import { fetchAllPages } from '@/src/api/paginated';
import { useFocusEffect } from 'expo-router';
import { Feather, Ionicons } from '@expo/vector-icons';
import { useTheme } from '@/src/theme/ThemeContext';
import { useTranslation } from 'react-i18next';

const getSafeErrorMessage = (error: unknown): string =>
  error instanceof Error ? error.message : 'unknown_error';

export default function ContenidoScreen() {
  const { colors } = useTheme();
  const { t } = useTranslation();
  const token = useAuthStore(state => state.token);

  const insets = useSafeAreaInsets();
  const minimumBottomPadding = Platform.OS === 'ios' ? 24 : 12;
  const bottomPadding = Math.max(insets.bottom, minimumBottomPadding);
  const tabBarBaseHeight = 62;
  const totalTabBarHeight = tabBarBaseHeight + bottomPadding;
  const scrollBottomPadding = totalTabBarHeight + 24;

  const [corpus, setCorpus] = useState<any[]>([]);
  const [quotes, setQuotes] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Search States
  const [corpusSearch, setCorpusSearch] = useState('');
  const [quoteSearch, setQuoteSearch] = useState('');

  // Expandable Items State (Set of Corpus IDs)
  const [expandedItems, setExpandedItems] = useState<Set<number>>(new Set());

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

  const toggleExpandItem = (id: number) => {
    setExpandedItems(prev => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  };

  const fetchData = useCallback(async () => {
    setError(null);
    setLoading(true);
    try {
      const [corpusData, resQ] = await Promise.all([
        fetchAllPages<any>('/admin/corpus', {
          config: { headers: { Authorization: `Bearer ${token}` } },
        }),
        client.get('/admin/quotes', { headers: { Authorization: `Bearer ${token}` } })
      ]);
      setCorpus(corpusData);
      setQuotes(resQ.data);
    } catch (error: unknown) {
      console.log('[AdminContent] No se pudo cargar el contenido:', getSafeErrorMessage(error));
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
      fetchData();
    }, [fetchData])
  );

  const handleDeleteCorpus = (id: number) => {
    Alert.alert(t('admin.deleteDocumentTitle'), t('admin.deleteDocumentMessage'), [
      { text: t('common.cancel'), style: "cancel" },
      {
        text: t('common.delete'),
        style: "destructive",
        onPress: async () => {
          try {
            await client.delete(`/admin/corpus/${id}`, { headers: { Authorization: `Bearer ${token}` } });
            fetchData();
          } catch (error: unknown) {
            console.log('[AdminContent] Error al eliminar documento:', getSafeErrorMessage(error));
            const detail = (error as any)?.response?.data?.detail;
            Alert.alert(t('common.error'), typeof detail === 'string' ? detail : t('common.error'));
          }
        }
      }
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
    } catch (error: unknown) {
      console.log('[AdminContent] Error al guardar documento:', getSafeErrorMessage(error));
      const detail = (error as any)?.response?.data?.detail;
      Alert.alert(t('common.error'), typeof detail === 'string' ? detail : t('common.error'));
    } finally {
      setIsSavingCorpus(false);
    }
  };

  const handleDeleteQuote = (id: number) => {
    Alert.alert(t('admin.deleteDocumentTitle'), t('admin.deleteQuoteMessage'), [
      { text: t('common.cancel'), style: "cancel" },
      {
        text: t('common.delete'),
        style: "destructive",
        onPress: async () => {
          try {
            await client.delete(`/admin/quotes/${id}`, { headers: { Authorization: `Bearer ${token}` } });
            fetchData();
          } catch (error: unknown) {
            console.log('[AdminContent] Error al eliminar frase:', getSafeErrorMessage(error));
            const detail = (error as any)?.response?.data?.detail;
            Alert.alert(t('common.error'), typeof detail === 'string' ? detail : t('common.error'));
          }
        }
      }
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
    } catch (error: unknown) {
      console.log('[AdminContent] Error al guardar frase:', getSafeErrorMessage(error));
      const detail = (error as any)?.response?.data?.detail;
      Alert.alert(t('common.error'), typeof detail === 'string' ? detail : t('common.error'));
    } finally {
      setIsSavingQuote(false);
    }
  };

  const filteredCorpus = corpus.filter(c =>
    c.source.toLowerCase().includes(corpusSearch.toLowerCase()) ||
    c.text_content.toLowerCase().includes(corpusSearch.toLowerCase())
  );

  const filteredQuotes = quotes.filter(q =>
    q.text.toLowerCase().includes(quoteSearch.toLowerCase())
  );

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
            onPress={fetchData}
            disabled={loading}
            style={{ backgroundColor: colors.primary }}
            className={`px-6 py-3 rounded-xl items-center shadow-sm ${loading ? 'opacity-50' : ''}`}
          >
            <Text className="text-white font-bold">{t('common.retry')}</Text>
          </Pressable>
        </View>
      ) : (
        <>
          {/* Sección Chatbot */}
          <View
            style={{ backgroundColor: colors.surface, borderColor: colors.border }}
            className="p-4 rounded-2xl shadow-sm mb-6 border mt-2"
          >
            <View className="flex-row justify-between items-center mb-4">
              <View>
                <Text className="text-xl font-bold text-text dark:text-white">
                  {t('admin.knowledgeBase')}
                </Text>
                <Text className="text-xs text-text/70 dark:text-white/70">
                  {t('admin.ragFiles')}
                </Text>
              </View>
              <Pressable
                onPress={() => {
                  setEditingCorpusId(null);
                  setNewSource('');
                  setNewText('');
                  setCorpusModal(true);
                }}
                style={{ backgroundColor: colors.primary }}
                className="p-2 rounded-lg"
              >
                <Feather name="plus" size={20} color="white" />
              </Pressable>
            </View>

            <View
              style={{ backgroundColor: colors.background, borderColor: colors.border }}
              className="flex-row rounded-xl items-center px-4 py-2 mb-4 border"
            >
              <Feather name="search" size={20} color={colors.primary} />
              <TextInput
                value={corpusSearch}
                onChangeText={setCorpusSearch}
                placeholder={t('admin.searchDocuments')}
                placeholderTextColor={colors.textSecondary}
                style={{ color: colors.text }}
                className="flex-1 ml-2 text-sm py-1"
              />
            </View>

            {filteredCorpus.length === 0 ? (
              <Text style={{ color: colors.textSecondary }} className="italic py-3 text-center text-sm">
                {t('admin.noDocuments', { defaultValue: 'No hay documentos guardados.' })}
              </Text>
            ) : (
              filteredCorpus.map(c => {
                const isExpanded = expandedItems.has(c.id);
                return (
                  <View
                    key={c.id}
                    style={{ backgroundColor: colors.background, borderColor: colors.border }}
                    className="p-3 rounded-xl mb-3 border"
                  >
                    <View className="flex-row justify-between items-start mb-2">
                      <Text className="font-bold text-text dark:text-white text-sm flex-1 mr-2">
                        {c.source}
                      </Text>
                      <View className="flex-row">
                        <Pressable onPress={() => handleEditCorpus(c)} className="p-1 mr-1">
                          <Feather name="edit-2" size={18} color={colors.primary} />
                        </Pressable>
                        <Pressable onPress={() => handleDeleteCorpus(c.id)} className="p-1">
                          <Feather name="trash-2" size={18} color="#DC2626" />
                        </Pressable>
                      </View>
                    </View>

                    <Text
                      className="text-xs text-text/80 dark:text-white/80 leading-5"
                      numberOfLines={isExpanded ? undefined : 2}
                    >
                      {c.text_content}
                    </Text>

                    <Pressable
                      onPress={() => toggleExpandItem(c.id)}
                      className="mt-2 flex-row items-center self-start"
                    >
                      <Text style={{ color: colors.primary }} className="text-xs font-semibold mr-1">
                        {isExpanded
                          ? t('common.showLess', { defaultValue: 'Ver menos' })
                          : t('common.showMore', { defaultValue: 'Ver más' })}
                      </Text>
                      <Feather
                        name={isExpanded ? 'chevron-up' : 'chevron-down'}
                        size={14}
                        color={colors.primary}
                      />
                    </Pressable>
                  </View>
                );
              })
            )}
          </View>

          {/* Sección Frases */}
          <View
            style={{ backgroundColor: colors.surface, borderColor: colors.border }}
            className="p-4 rounded-2xl shadow-sm mb-6 border"
          >
            <View className="flex-row justify-between items-center mb-4">
              <View>
                <Text className="text-xl font-bold text-text dark:text-white">
                  {t('admin.motivationalQuotes')}
                </Text>
                <Text className="text-xs text-text/70 dark:text-white/70">
                  {t('admin.gamificationManager')}
                </Text>
              </View>
              <Pressable
                onPress={() => {
                  setEditingQuoteId(null);
                  setNewQuote('');
                  setQuoteModal(true);
                }}
                style={{ backgroundColor: colors.primary }}
                className="p-2 rounded-lg"
              >
                <Feather name="plus" size={20} color="white" />
              </Pressable>
            </View>

            <View
              style={{ backgroundColor: colors.background, borderColor: colors.border }}
              className="flex-row rounded-xl items-center px-4 py-2 mb-4 border"
            >
              <Feather name="search" size={20} color={colors.primary} />
              <TextInput
                value={quoteSearch}
                onChangeText={setQuoteSearch}
                placeholder={t('admin.searchQuotes')}
                placeholderTextColor={colors.textSecondary}
                style={{ color: colors.text }}
                className="flex-1 ml-2 text-sm py-1"
              />
            </View>

            {filteredQuotes.length === 0 ? (
              <Text style={{ color: colors.textSecondary }} className="italic py-3 text-center text-sm">
                {t('admin.noQuotes', { defaultValue: 'No hay frases guardadas.' })}
              </Text>
            ) : (
              filteredQuotes.map(q => (
                <View
                  key={q.id}
                  style={{ backgroundColor: colors.background, borderColor: colors.border }}
                  className="p-3 rounded-xl mb-3 flex-row justify-between items-center border-l-4 border-l-amber-400 border"
                >
                  <Text className="text-sm font-semibold text-text dark:text-white flex-1 italic mr-2">
                    &ldquo;{q.text}&rdquo;
                  </Text>
                  <View className="flex-row">
                    <Pressable onPress={() => handleEditQuote(q)} className="p-1 mr-1">
                      <Feather name="edit-2" size={18} color={colors.primary} />
                    </Pressable>
                    <Pressable onPress={() => handleDeleteQuote(q.id)} className="p-1">
                      <Feather name="trash-2" size={18} color="#DC2626" />
                    </Pressable>
                  </View>
                </View>
              ))
            )}
          </View>
        </>
      )}

      {/* Modal Corpus */}
      <Modal visible={corpusModal} animationType="slide" transparent onRequestClose={() => setCorpusModal(false)}>
        <View className="flex-1 justify-end bg-black/50">
          <View
            style={{ backgroundColor: colors.surface, borderColor: colors.border }}
            className="p-6 rounded-t-3xl border-t shadow-lg"
          >
            <View className="flex-row justify-between items-center mb-4">
              <Text className="text-lg font-bold text-text dark:text-white">
                {editingCorpusId ? t('admin.editDocument') : t('admin.newDocument')}
              </Text>
              <Pressable onPress={() => setCorpusModal(false)} className="p-1">
                <Feather name="x" size={24} color={colors.text} />
              </Pressable>
            </View>

            <TextInput
              value={newSource}
              onChangeText={setNewSource}
              placeholder={t('admin.documentTitlePlaceholder')}
              placeholderTextColor={colors.textSecondary}
              style={{ backgroundColor: colors.background, color: colors.text, borderColor: colors.border }}
              className="rounded-xl p-3 mb-3 border text-sm"
            />
            <TextInput
              value={newText}
              onChangeText={setNewText}
              placeholder={t('admin.documentContentPlaceholder')}
              placeholderTextColor={colors.textSecondary}
              multiline
              numberOfLines={5}
              style={{ backgroundColor: colors.background, color: colors.text, borderColor: colors.border }}
              className="rounded-xl p-3 mb-6 h-32 border text-sm"
              textAlignVertical="top"
            />
            <Pressable
              onPress={handleSaveCorpus}
              disabled={isSavingCorpus}
              style={{ backgroundColor: colors.primary }}
              className={`p-4 rounded-xl items-center shadow-sm ${isSavingCorpus ? 'opacity-50' : ''}`}
            >
              {isSavingCorpus ? (
                <ActivityIndicator color="white" />
              ) : (
                <Text className="text-white font-bold">
                  {editingCorpusId ? t('admin.updateVector') : t('admin.vectorizeSave')}
                </Text>
              )}
            </Pressable>
          </View>
        </View>
      </Modal>

      {/* Modal Quote */}
      <Modal visible={quoteModal} animationType="slide" transparent onRequestClose={() => setQuoteModal(false)}>
        <View className="flex-1 justify-end bg-black/50">
          <View
            style={{ backgroundColor: colors.surface, borderColor: colors.border }}
            className="p-6 rounded-t-3xl border-t shadow-lg"
          >
            <View className="flex-row justify-between items-center mb-4">
              <Text className="text-lg font-bold text-text dark:text-white">
                {editingQuoteId ? t('admin.editQuote') : t('admin.newQuote')}
              </Text>
              <Pressable onPress={() => setQuoteModal(false)} className="p-1">
                <Feather name="x" size={24} color={colors.text} />
              </Pressable>
            </View>

            <TextInput
              value={newQuote}
              onChangeText={setNewQuote}
              placeholder={t('admin.quotePlaceholder')}
              placeholderTextColor={colors.textSecondary}
              multiline
              style={{ backgroundColor: colors.background, color: colors.text, borderColor: colors.border }}
              className="rounded-xl p-3 mb-6 h-24 border text-sm"
              textAlignVertical="top"
            />
            <Pressable
              onPress={handleSaveQuote}
              disabled={isSavingQuote}
              style={{ backgroundColor: colors.primary }}
              className={`p-4 rounded-xl items-center shadow-sm ${isSavingQuote ? 'opacity-50' : ''}`}
            >
              {isSavingQuote ? (
                <ActivityIndicator color="white" />
              ) : (
                <Text className="text-white font-bold">
                  {editingQuoteId ? t('common.update') : t('common.save')}
                </Text>
              )}
            </Pressable>
          </View>
        </View>
      </Modal>
    </ScrollView>
  );
}
