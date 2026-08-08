import * as i18nextModule from 'i18next';
import { initReactI18next } from 'react-i18next';
import en from './locales/en.json';
import es from './locales/es.json';
import { usePreferencesStore } from '../store/preferences';

const i18n = i18nextModule.default || i18nextModule;

const resources = {
  en: { translation: en },
  es: { translation: es },
};

i18n
  .use(initReactI18next)
  .init({
    resources,
    lng: usePreferencesStore.getState().language, // initial language
    fallbackLng: 'es',
    interpolation: {
      escapeValue: false, // react already safes from xss
    },
  });

// Subscribe to language changes in the store to update i18n automatically
usePreferencesStore.subscribe((state, prevState) => {
  if (state.language !== prevState.language) {
    i18n.changeLanguage(state.language);
  }
});

export default i18n;
